from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# ======== Google Form Config =========
FORM_URL = "https://docs.google.com/forms/d/1p7cgQicxFbuZiFmn0s4lCVGWn3x8DXJ1Xe5Xy913MAo/formResponse"
ENTRY_ID = "entry.1800109557"  # Đây là ID đúng để map câu trả lời QR

# ======== Giao diện =========

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

# ======== API điểm danh QR =========

@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    data = request.get_json()
    qr_code = data.get('qr_code')
    if qr_code:
        payload = {
            ENTRY_ID: qr_code
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(FORM_URL, data=payload, headers=headers)
        if response.status_code in [200, 302]:
            return jsonify({'message': 'Điểm danh thành công!'})
        else:
            return jsonify({'message': 'Không gửi được form!'}), 500
    return jsonify({'message': 'QR không hợp lệ!'}), 400

# ======== Chạy app =========

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
