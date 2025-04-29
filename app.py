from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_to_a_secret")

# ======== Cấu hình admin account =========
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "123456")

# ======== Apps Script Web App URL =========
# Đã dán URL bạn cung cấp ở đây:
APPSCRIPT_URL = "https://script.google.com/macros/s/AKfycbzsUMCWKIhlaVAnN0gONFcwSwaPVi12VGjUhXcIupPSSuVfi-nE-2aSnK_cAVcPPWD2gw/exec"

# ======== Routes ==========
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "Tài khoản hoặc mật khẩu không chính xác"
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/scan')
def scan():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('scan.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ======== API điểm danh QR (Apps Script) =========
@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    if not session.get('logged_in'):
        return jsonify({'message': 'Chưa đăng nhập'}), 401

    data = request.get_json(silent=True) or {}
    qr_code = data.get('qr_code')
    if not qr_code:
        return jsonify({'message': 'QR không hợp lệ!'}), 400

    # Gửi payload JSON tới Apps Script Web App
    resp = requests.post(APPSCRIPT_URL, json={'qr_code': qr_code})
    try:
        result = resp.json()  # { success: bool, message: str }
    except ValueError:
        return jsonify({'message': 'Lỗi phản hồi từ Sheets API'}), 502

    status_code = 200 if result.get('success') else 400
    return jsonify({'message': result.get('message')}), status_code

# ======== Run App =========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
