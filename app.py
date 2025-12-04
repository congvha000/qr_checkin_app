#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR‑Check‑in App – Flask application
"""

from __future__ import annotations

import os
import pathlib
from datetime import datetime, timedelta, timezone

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from flask_login import (
    LoginManager, login_required, login_user,
    logout_user, current_user, UserMixin
)

import firebase_admin
from firebase_admin import credentials, firestore


# ───────────────────────────────────────────────
# 🔧 CONFIG
# ───────────────────────────────────────────────
APP_TIMEZONE = timezone(timedelta(hours=7))  # Asia/Ho_Chi_Minh
ADMIN_USER   = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS   = os.getenv("ADMIN_PASS", "123456")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")


# ───────────────────────────────────────────────
# 👤 LOGIN MANAGER
# ───────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = "login"


# ───────────────────────────────────────────────
# 🔥 FIREBASE ADMIN (CHUẨN 2025)
# ───────────────────────────────────────────────
def init_firebase():
    """
    Khởi tạo Firebase Admin một lần duy nhất.
    Không dùng firebase_admin._apps (đã không còn hỗ trợ).
    """
    try:
        firebase_admin.get_app()      # nếu đã init → OK
    except ValueError:
        # chưa init → tiến hành init
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

        if not cred_path:
            BASE_DIR = pathlib.Path(__file__).resolve().parent
            cred_path = BASE_DIR / "credentials.json"

        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)


init_firebase()
db = firestore.client()


# ───────────────────────────────────────────────
# 👥 USER MODEL
# ───────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, uid: str, name: str):
        self.id = uid
        self.name = name


@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USER:
        return User(uid=ADMIN_USER, name="Administrator")
    return None


# ───────────────────────────────────────────────
# 🔄 BUSINESS LOGIC
# ───────────────────────────────────────────────
def check_and_update(qr_code: str, *, is_manual: bool = False):
    now = datetime.now(APP_TIMEZONE)
    one_hour_ago = now - timedelta(hours=1)

    # 1) User tồn tại?
    user_ref = db.collection("users").document(qr_code)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return False, "Mã số thẻ không tồn tại!"

    user_data = user_doc.to_dict() or {}

    # 2) Kiểm tra trùng <1h
    dup_q = (
        db.collection("qr_checkins")
        .where("qr_code", "==", qr_code)
        .where("timestamp", ">", one_hour_ago)
        .order_by("timestamp")
        .limit(1)
    )
    if list(dup_q.stream()):
        return False, "Đã điểm danh trong 1 giờ qua!"

    # 3) Mỗi ngày tối đa 3 lần
    today = now.strftime("%Y-%m-%d")
    if (user_data.get("last_scan_date") == today and
            user_data.get("scan_count_today", 0) >= 3):
        return False, "Đã vượt quá 3 lần trong ngày!"

    # 4) Lưu log
    db.collection("qr_checkins").add({
        "qr_code": qr_code,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "method": "manual" if is_manual else "scan",
    })

    # 5) Cập nhật user
    updates = {
        "total_days": firestore.Increment(1),
        "last_scan_time": firestore.SERVER_TIMESTAMP,
    }

    if user_data.get("last_scan_date") == today:
        updates["scan_count_today"] = firestore.Increment(1)
    else:
        updates["scan_count_today"] = 1
        updates["last_scan_date"] = today

    user_ref.set(updates, merge=True)
    return True, "✅ Điểm danh thành công!"


# ───────────────────────────────────────────────
# 🌐 ROUTES
# ───────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USER and password == ADMIN_PASS:
            login_user(User(uid=ADMIN_USER, name="Administrator"))
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Sai tài khoản hoặc mật khẩu!")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/manual_checkin", methods=["POST"])
@login_required
def manual_checkin():
    qr_code = request.form.get("qr_code", "").strip()

    if not qr_code.isdigit():
        flash("Mã số thẻ phải là số!", "warning")
        return redirect(url_for("dashboard"))

    ok, msg = check_and_update(qr_code, is_manual=True)
    flash(msg, "success" if ok else "warning")
    return redirect(url_for("dashboard"))


@app.route("/scan", methods=["GET", "POST"])
@login_required
def scan():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        qr_code = str(data.get("qr_code", "")).strip()

        if not qr_code.isdigit():
            return jsonify({"message": "Mã số thẻ phải là số!"}), 400

        ok, msg = check_and_update(qr_code, is_manual=False)
        return jsonify({"message": msg}), 200 if ok else 400

    return render_template("scan.html")


# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────
if __name__ == "__main__":
    debug_mode = bool(int(os.getenv("FLASK_DEBUG", "1")))
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
