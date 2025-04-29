import qrcode

def generate_qr(data: str, filename: str = "4.png"):
    """
    Tạo mã QR từ chuỗi data và lưu vào filename.
    """
    # Tạo QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Vẽ ảnh
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"Đã lưu mã QR vào {filename}")

# KHỐI NÀY PHẢI CHÍNH XÁC NHƯ DƯỚI
if __name__ == "__main__":
    generate_qr("4")
