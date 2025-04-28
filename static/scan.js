// static/scan.js

// Khi DOM đã sẵn sàng thì khởi chạy QR scanner
document.addEventListener("DOMContentLoaded", () => {
    const resultDiv = document.getElementById("scan-result");
    const html5QrCode = new Html5Qrcode("reader");
  
    function onScanSuccess(decodedText, decodedResult) {
      // Dừng scan ngay khi có kết quả để tránh gửi lặp
      html5QrCode
        .stop()
        .then(() => {
          // Gửi kết quả thẳng tới Google Apps Script URL của bạn
          return fetch(
            "https://script.google.com/macros/s/AKfycbxwUligBm_KRrM5Ai2SlnclC6HYADD7A6zjOrgWmBDXjaoNTZ4-VtdhXX19wEYQ4tb0-Q/exec",
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ qr_code: decodedText }),
            }
          );
        })
        .then((res) => res.json())
        .then((data) => {
          // Hiển thị message phản hồi từ Apps Script
          resultDiv.innerText = data.status === "ok"
            ? "Điểm danh thành công!"
            : `Lỗi: ${data.message || "Không xác định"}`;
        })
        .catch((err) => {
          console.error(err);
          resultDiv.innerText = "Lỗi khi điểm danh. Vui lòng thử lại.";
        });
    }
  
    // Cấu hình và start HTML5 QR code
    html5QrCode
      .start(
        { facingMode: "environment" }, // camera sau
        { fps: 10, qrbox: 250 },       // 10fps, khung vuông 250px
        onScanSuccess
      )
      .catch((err) => {
        console.error("Không thể khởi chạy camera:", err);
        resultDiv.innerText = "Không thể truy cập camera.";
      });
  });
  