from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Đổi thành bí mật riêng nếu bạn muốn
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

# ======== Định nghĩa database model =========

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    password = db.Column(db.String(150))

class Checkin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qr_code = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ======== Tạo database nếu chưa có =========

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="123456")  # Tài khoản mặc định
        db.session.add(admin)
        db.session.commit()

# ======== Định nghĩa các trang web (route) =========

# Trang login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            return "Sai tài khoản hoặc mật khẩu!"
    return render_template('login.html')

# Trang dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Trang scan QR
@app.route('/scan')
def scan():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('scan.html')

# API checkin khi quét QR
@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    data = request.get_json()
    qr_code = data.get('qr_code')
    if qr_code:
        new_checkin = Checkin(qr_code=qr_code)
        db.session.add(new_checkin)
        db.session.commit()
        return jsonify({'message': 'Điểm danh thành công!'})
    return jsonify({'message': 'QR không hợp lệ!'}), 400

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# ======== Chạy ứng dụng =========

if __name__ == '__main__':
    app.run(debug=True)
