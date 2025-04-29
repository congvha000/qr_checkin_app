from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_to_a_secret")

# ======== Cấu hình admin account =========
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "123456")

# ======== Cấu hình Google Sheets =========
SCOPES       = ['https://www.googleapis.com/auth/spreadsheets']
CREDS        = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
GS_CLIENT    = gspread.authorize(CREDS)
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "YOUR_SPREADSHEET_ID")
GSHEET       = GS_CLIENT.open_by_key(SPREADSHEET_ID)
WSHEET       = GSHEET.worksheet('trang1')   # Tên sheet của bạn

def process_scan(qr_value):
    """
    Xử lý quét QR:
      - qr_value phải là số nguyên dương tương ứng STT (cột A)
      - nếu không hợp lệ hoặc không tồn tại trong STT → từ chối
      - ngược lại, kiểm tra 1h/lần và tối đa 3 lần/ngày
      - cập nhật cột C (total_days), D (last_scan), E (scans_today)
    """
    # 0. Validate đầu vào
    try:
        stt = int(qr_value)
        if stt <= 0:
            raise ValueError
    except Exception:
        return "QR không hợp lệ (phải là số nguyên dương tương ứng STT)."

    now = datetime.now()

    # 1. Tìm dòng theo STT ở cột A
    all_stt = WSHEET.col_values(1)  # ['STT', '1', '2', ...]
    if str(stt) not in all_stt:
        return f"QR = {stt} không khớp bất kỳ STT nào."
    row = all_stt.index(str(stt)) + 1

    # 2. Đọc hiện trạng
    total_days_cell  = WSHEET.cell(row, 3).value or '0'
    last_scan_cell   = WSHEET.cell(row, 4).value    # ISO string hoặc None
    scans_today_cell = WSHEET.cell(row, 5).value or '0'

    total_days  = int(total_days_cell)
    scans_today = int(scans_today_cell)

    # 3. Reset scans_today nếu đã qua ngày mới
    if last_scan_cell:
        last_scan = datetime.fromisoformat(last_scan_cell)
        if last_scan.date() != now.date():
            scans_today = 0

    # 4. Kiểm tra giờ cách ly ≥1h và tối đa 3 lần/ngày
    if last_scan_cell:
        last_scan = datetime.fromisoformat(last_scan_cell)
        if now - last_scan < timedelta(hours=1):
            return f"Chỉ được quét mỗi mã 1 lần mỗi giờ. Lần trước: {last_scan_cell}"
    if scans_today >= 3:
        return "Bạn đã quét 3 lần trong ngày, vui lòng quay lại ngày mai."

    # 5. Thỏa điều kiện → cập nhật
    total_days  += 1
    scans_today += 1

    WSHEET.update_cell(row, 3, total_days)  # Cột C
    WSHEET.update_cell(row, 4, now.isoformat(sep=' ', timespec='seconds'))  # Cột D
    WSHEET.update_cell(row, 5, scans_today)  # Cột E

    return (f"Quét thành công STT={stt}:\n"
            f"- Tổng ngày đi lễ: {total_days}\n"
            f"- Lần quét hôm nay: {scans_today}")

# ======== Routes ==========

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u == ADMIN_USER and p == ADMIN_PASS:
            session['logged_in'] = True
            session['username']  = u
            return redirect(url_for('dashboard'))
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

@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    if not session.get('logged_in'):
        return jsonify({'message': 'Chưa đăng nhập'}), 401

    data    = request.get_json(silent=True) or {}
    qr_code = data.get('qr_code')
    message = process_scan(qr_code)
    status  = 200 if message.startswith("Quét thành công") else 400
    return jsonify({'message': message}), status

# ======== Run App =========

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
