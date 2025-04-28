// static/scan.js

document.addEventListener("DOMContentLoaded", () => {
    const resultDiv = document.getElementById("scan-result");
    const rescanBtn = document.getElementById("rescan-btn");
    const html5QrCode = new Html5Qrcode("reader");
    const ENDPOINT = "https://script.google.com/macros/s/AKfycbyoK3UGWKOdYYGB7lPRGL2yFNUpUwDcKyjzd07VQ0fs1ZO2z-848OB_KzGU5LqNYfq-rg/exec";
  
    function startScanner() {
      // Ẩn kết quả & nút quét tiếp trước khi start
      resultDiv.innerText = "";
      rescanBtn.style.display = "none";
  
      html5QrCode
        .start(
          { facingMode: "environment" },
          { fps: 10, qrbox: 250 },
          onScanSuccess
        )
        .catch(err => {
          console.error("Camera không khởi động được:", err);
          resultDiv.innerText = "Không thể truy cập camera.";
        });
    }
  
    function onScanSuccess(decodedText, decodedResult) {
      html5QrCode
        .stop()
        .then(() => {
          // Gửi kết quả
          return fetch(ENDPOINT, {
            method: "POST",
            mode: "no-cors",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ qr_code: decodedText })
          });
        })
        .then(() => {
          // Hiển thị kết quả thành công
          resultDiv.innerText = "✅ Điểm danh thành công!";
          // Hiện nút quét tiếp
          rescanBtn.style.display = "inline-block";
        })
        .catch(err => {
          console.error(err);
          resultDiv.innerText = "❌ Lỗi khi điểm danh. Vui lòng thử lại.";
          rescanBtn.style.display = "inline-block";
        });
    }
  
    // Khi bấm Quét tiếp, gọi lại startScanner
    rescanBtn.addEventListener("click", () => {
      startScanner();
    });
  
    // Khởi chạy lần đầu
    startScanner();
  });
  