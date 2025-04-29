from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_to_a_secret")

# ======== Cấu hình admin account =========
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "123456")

# ======== Apps Script Web App URL =========
APPSCRIPT_URL = "https://script.google.com/macros/s/AKfycbxWmZbO7-lVZ_w9pXo85LdbYVz1ZhqAOS8yYImc7APXw3mJ2bciKekMjLFYmggfIPmNbA/exec"

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
        error = "Tài khoản hoặc mật khẩu không chính xác"
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # Cho phép truyền message khi điểm danh bằng tay xong
    message = request.args.get('message')
    return render_template('dashboard.html', username=session.get('username'), message=message)

@app.route('/scan')
def scan():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('scan.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ======== API điểm danh QR =========
@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Chưa đăng nhập'}), 401

    data = request.get_json(silent=True) or {}
    qr_code = data.get('qr_code')
    if not qr_code:
        return jsonify({'success': False, 'message': 'QR không hợp lệ!'}), 400

    try:
        resp = requests.post(APPSCRIPT_URL, json={'qr_code': qr_code})
        result = resp.json()
    except Exception:
        return jsonify({'success': False, 'message': 'Lỗi kết nối Sheets API'}), 502

    ok = bool(result.get('success'))
    msg = result.get('message', '')
    status_code = 200 if ok else 400
    return jsonify({'success': ok, 'message': msg}), status_code

# ======== API điểm danh bằng tay =========
@app.route('/manual_checkin', methods=['POST'])
def manual_checkin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    input_value = request.form.get('input_value')
    if not input_value:
        return redirect(url_for('dashboard', message="Vui lòng nhập STT hoặc Tên"))

    try:
        # Nếu input là số => QR_CODE
        int(input_value)
        payload = {'qr_code': input_value}
    except ValueError:
        # Nếu input là chữ => NAME
        payload = {'name': input_value}

    try:
        resp = requests.post(APPSCRIPT_URL, json=payload)
        result = resp.json()
    except Exception:
        return redirect(url_for('dashboard', message="Lỗi kết nối đến Sheets API"))

    message = result.get('message', 'Đã xử lý xong.')
    return redirect(url_for('dashboard', message=message))

# ======== Run App =========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
