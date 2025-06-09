import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session
)

import firebase_admin
from firebase_admin import credentials, firestore


# ────────────────────────────────────────────────
# 1. Flask & Firebase init
# ────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
cred_path = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.path.join(BASE_DIR, "credentials.json")
)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-prod")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "123456")
VN_TZ = timezone(timedelta(hours=7))   # UTC+7


# ────────────────────────────────────────────────
# 2. Helper
# ────────────────────────────────────────────────
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def check_and_update(qr_code: str, is_manual: bool = False):
    """
    Logic chung cho /scan (POST JSON) và /manual_checkin (POST form):
    - Chặn quét lặp <1h
    - Giới hạn 3 lần/ngày
    - Luôn tăng total_days
    - Cập nhật last_scan_time, scan_count_today
    Trả về tuple (ok: bool, message: str, status_code: int)
    """
    user_ref = db.collection("users").document(qr_code)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return False, "Mã QR không tồn tại.", 404

    now          = datetime.now(VN_TZ)
    one_hour_ago = now - timedelta(hours=1)
    today_str    = now.strftime("%Y-%m-%d")

    # Lặp <1h?
    if list(db.collection("qr_checkins")
               .where("qr_code", "==", qr_code)
               .where("timestamp", ">", one_hour_ago)
               .limit(1)
               .stream()):
        return False, "Đã quét trong vòng 1 giờ qua.", 403

    user_data = user_doc.to_dict() or {}
    if user_data.get("last_scan_date") == today_str and \
       user_data.get("scan_count_today", 0) >= 3:
        return False, "Đã quét tối đa 3 lần hôm nay.", 403

    # Ghi log qr_checkins
    db.collection("qr_checkins").add({
        "qr_code": qr_code,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "method": "manual" if is_manual else "qr"
    })

    # Cập nhật user
    updates = {
        "total_days": firestore.Increment(1),
        "last_scan_time": firestore.SERVER_TIMESTAMP
    }
    if user_data.get("last_scan_date") == today_str:
        updates["scan_count_today"] = firestore.Increment(1)
    else:
        updates["scan_count_today"] = 1
        updates["last_scan_date"]   = today_str

    user_ref.update(updates)
    return True, "Điểm danh thành công!", 200


# ────────────────────────────────────────────────
# 3. Auth routes
# ────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Sai tài khoản hoặc mật khẩu.")

    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ────────────────────────────────────────────────
# 4. Dashboard
# ────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html",
                           username=session.get("username"),
                           message=request.args.get("message"))


# ────────────────────────────────────────────────
# 5. QR-scan (GET + POST)
# ────────────────────────────────────────────────
@app.route("/scan", methods=["GET"])
@login_required
def scan():          # endpoint = 'scan'
    return render_template("scan.html")


@app.route("/scan", methods=["POST"])
@login_required
def scan_qr():
    data = request.get_json(silent=True) or {}
    qr_code = data.get("qr_code", "").strip()

    if not qr_code:
        return jsonify({"status": "error", "message": "Thiếu mã QR"}), 400

    ok, msg, code = check_and_update(qr_code)
    status = "ok" if ok else "error"
    return jsonify({"status": status, "message": msg}), code


# ────────────────────────────────────────────────
# 5bis. Manual check-in từ form Dashboard
# ────────────────────────────────────────────────
@app.route("/manual_checkin", methods=["POST"])
@login_required
def manual_checkin():
    qr_code = request.form.get("input_value", "").strip()
    if not qr_code:
        return redirect(url_for("dashboard", message="Thiếu mã QR / mã thẻ."))

    ok, msg, _ = check_and_update(qr_code, is_manual=True)
    return redirect(url_for("dashboard", message=msg))


# ────────────────────────────────────────────────
# 6. Health-check
# ────────────────────────────────────────────────
@app.route("/healthz")
def healthz():
    return "OK", 200


# ────────────────────────────────────────────────
# 7. Run local
# ────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
