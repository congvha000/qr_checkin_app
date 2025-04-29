// static/scan.js

document.addEventListener("DOMContentLoaded", () => {
  const resultDiv = document.getElementById("scan-result");
  const rescanBtn = document.getElementById("rescan-btn");
  const html5QrCode = new Html5Qrcode("reader");

  // Đã đổi thành URL của Apps Script Web App bạn deploy
  const ENDPOINT = "https://script.google.com/macros/s/AKfycbxP2E8Dtxm2e5bQHoIUzyV6zgHW55x1ZiSjDA4GtkiScdAHfLbMZRRw8oIGp5XhJDNEqw/exec";

  function startScanner() {
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
        rescanBtn.style.display = "inline-block";
      });
  }

  async function onScanSuccess(decodedText, decodedResult) {
    await html5QrCode.stop();
    try {
      const res = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ qr_code: decodedText })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        resultDiv.innerText = "✅ " + data.message;
      } else {
        resultDiv.innerText = "❌ " + (data.message || "Điểm danh thất bại");
      }
    } catch (e) {
      console.error("Lỗi khi gọi server:", e);
      resultDiv.innerText = "❌ Lỗi kết nối server.";
    } finally {
      rescanBtn.style.display = "inline-block";
    }
  }

  rescanBtn.addEventListener("click", () => {
    startScanner();
  });

  // Khởi động lần đầu
  startScanner();
});
