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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(BASE_DIR, "credentials.json")   # ✔️ luôn đúng dù chạy ở đâu

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
                           username=session.get("username"))


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
    """Xử lý JSON {"qr_code": "..."}"""
    data = request.get_json(silent=True) or {}
    qr_code = data.get("qr_code")

    if not qr_code:
        return jsonify({"status": "error", "message": "Thiếu mã QR"}), 400

    try:
        # a) Tìm user
        user_ref = db.collection("users").document(qr_code)
        user_doc = user_ref.get()
        if not user_doc.exists:
            return jsonify({"status": "error", "message": "Mã QR không tồn tại"}), 404

        # b) Chặn quét lặp trong 1 giờ
        now = datetime.now(VN_TZ)
        one_hour_ago = now - timedelta(hours=1)

        dup_check = (
            db.collection("qr_checkins")
              .where("qr_code", "==", qr_code)
              .where("timestamp", ">", one_hour_ago)
              .order_by("timestamp", direction=firestore.Query.DESCENDING)
              .limit(1)
        )
        if list(dup_check.stream()):
            return jsonify({"status": "error",
                            "message": "Đã quét trong vòng 1 giờ trước."}), 403

        # c) Kiểm tra giới hạn 3 lần/ngày
        user_data = user_doc.to_dict() or {}
        prev_date = user_data.get("last_scan_date")          # YYYY-MM-DD
        today_str = now.strftime("%Y-%m-%d")

        if prev_date == today_str and user_data.get("scan_count_today", 0) >= 3:
            return jsonify({"status": "error",
                            "message": "Đã quét tối đa 3 lần hôm nay."}), 403

        # d) Ghi log vào qr_checkins
        db.collection("qr_checkins").add({
            "qr_code": qr_code,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        # e) Cập nhật document users
        updates = {
            "total_days": firestore.Increment(1),            # ✔️ luôn +1
            "last_scan_time": firestore.SERVER_TIMESTAMP
        }

        if prev_date == today_str:
            updates["scan_count_today"] = firestore.Increment(1)
        else:
            updates["scan_count_today"] = 1
            updates["last_scan_date"]   = today_str

        user_ref.update(updates)

        return jsonify({"status": "ok", "message": "Điểm danh thành công!"}), 200

    except Exception as e:
        app.logger.exception(e)
        return jsonify({"status": "error", "message": str(e)}), 500


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
