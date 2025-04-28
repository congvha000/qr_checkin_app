from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_to_a_secret")

# ======== Google Form Config =========
FORM_URL = "https://docs.google.com/forms/d/1p7cgQicxFbuZiFmn0s4lCVGWn3x8DXJ1Xe5Xy913MAo/formResponse"
ENTRY_ID = "entry.1800109557"

# ======== Routes ==========

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # TODO: Thay bằng logic xác thực thực
        if username and password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "Vui lòng điền đầy đủ tên đăng nhập và mật khẩu."
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

# ======== API điểm danh QR =========

@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    data = request.get_json()
    qr_code = data.get('qr_code')
    if qr_code:
        payload = { ENTRY_ID: qr_code }
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
        resp = requests.post(FORM_URL, data=payload, headers=headers)
        if resp.status_code in (200, 302):
            return jsonify({'message': 'Điểm danh thành công!'})
        else:
            return jsonify({'message': 'Không gửi được form!'}), 500
    return jsonify({'message': 'QR không hợp lệ!'}), 400

# ======== Run App =========

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
