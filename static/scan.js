// static/scan.js

document.addEventListener("DOMContentLoaded", () => {
    const resultDiv = document.getElementById("scan-result");
    const html5QrCode = new Html5Qrcode("reader");
    const ENDPOINT = "https://script.google.com/macros/s/AKfycbyoK3UGWKOdYYGB7lPRGL2yFNUpUwDcKyjzd07VQ0fs1ZO2z-848OB_KzGU5LqNYfq-rg/exec";
  
    function onScanSuccess(decodedText, decodedResult) {
      html5QrCode
        .stop()
        .then(() => {
          return fetch(ENDPOINT, {
            method: "POST",
            mode: "no-cors",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ qr_code: decodedText })
          });
        })
        .then(() => {
          resultDiv.innerText = "✅ Điểm danh thành công!";
        })
        .catch((err) => {
          console.error(err);
          resultDiv.innerText = "❌ Lỗi khi điểm danh. Vui lòng thử lại.";
        });
    }
  
    html5QrCode
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        onScanSuccess
      )
      .catch((err) => {
        console.error("Camera không khởi động được:", err);
        resultDiv.innerText = "Không thể truy cập camera.";
      });
  });
  