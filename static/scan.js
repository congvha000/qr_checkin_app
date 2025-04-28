// scan.js

// Khi DOM đã sẵn sàng thì khởi chạy QR scanner
document.addEventListener("DOMContentLoaded", () => {
    const resultDiv = document.getElementById("scan-result");
    const html5QrCode = new Html5Qrcode("reader");
  
    function onScanSuccess(decodedText, decodedResult) {
      // Dừng scan ngay khi có kết quả
      html5QrCode
        .stop()
        .then(() => {
          // Gửi kết quả lên server
          return fetch("/api/checkin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ qr_code: decodedText }),
          });
        })
        .then((res) => res.json())
        .then((data) => {
          // Hiển thị message lên trang thay vì alert
          resultDiv.innerText = data.message;
        })
        .catch((err) => {
          console.error(err);
          resultDiv.innerText = "Lỗi khi điểm danh. Vui lòng thử lại.";
        });
    }
  
    // Cấu hình và start HTML5 QR code
    html5QrCode.start(
      { facingMode: "environment" }, // camera sau
      { fps: 10, qrbox: 250 },       // 10fps, khung vuông 250px
      onScanSuccess
    ).catch((err) => {
      console.error("Không thể khởi chạy camera:", err);
      resultDiv.innerText = "Không thể truy cập camera.";
    });
  });
  