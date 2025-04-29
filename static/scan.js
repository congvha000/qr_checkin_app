// static/scan.js

document.addEventListener("DOMContentLoaded", () => {
  const resultDiv    = document.getElementById("scan-result");
  const rescanBtn    = document.getElementById("rescan-btn");
  const html5QrCode  = new Html5Qrcode("reader");

  // Chuyển ENDPOINT về Flask route
  const ENDPOINT = "/api/checkin";

  function startScanner() {
    resultDiv.innerText     = "";
    rescanBtn.style.display = "none";

    html5QrCode
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        onScanSuccess
      )
      .catch(err => {
        console.error("Camera không khởi động được:", err);
        resultDiv.innerText     = "Không thể truy cập camera.";
        rescanBtn.style.display = "inline-block";
      });
  }

  async function onScanSuccess(decodedText) {
    // dừng camera
    await html5QrCode.stop();

    try {
      console.log("[scan.js] Gửi payload lên Flask:", decodedText);
      const res = await fetch(ENDPOINT, {
        method:      "POST",
        headers:     { "Content-Type": "application/json" },
        credentials: "same-origin",           // để giữ session cookie
        body:        JSON.stringify({ qr_code: decodedText })
      });
      console.log("[scan.js] Response status:", res.status);

      const data = await res.json();
      console.log("[scan.js] Response JSON:", data);

      if (res.ok) {
        resultDiv.innerText = "✅ " + data.message;
      } else {
        resultDiv.innerText = "❌ " + data.message;
      }
    } catch (e) {
      console.error("Lỗi khi gọi server:", e);
      resultDiv.innerText = "❌ Lỗi kết nối server.";
    } finally {
      rescanBtn.style.display = "inline-block";
    }
  }

  rescanBtn.addEventListener("click", startScanner);

  // Bắt đầu lần đầu
  startScanner();
});
