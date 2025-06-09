// static/scan.js

document.addEventListener("DOMContentLoaded", () => {
  const resultDiv    = document.getElementById("scan-result");
  const rescanBtn    = document.getElementById("rescan-btn");
  const html5QrCode  = new Html5Qrcode("reader");

  // ✅ Địa chỉ Flask server (nội bộ)
  const ENDPOINT = "http://127.0.0.1:5000/scan";

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
        resultDiv.innerText     = "❌ Không thể truy cập camera.";
        rescanBtn.style.display = "inline-block";
      });
  }

  async function onScanSuccess(decodedText) {
    await html5QrCode.stop(); // Dừng camera sau khi quét

    try {
      console.log("[scan.js] Gửi mã QR về Flask:", decodedText);

      const res = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ qr_code: decodedText })
      });

      const data = await res.json();
      console.log("[scan.js] Phản hồi từ Flask:", data);

      if (res.ok) {
        resultDiv.innerText = "✅ Điểm danh thành công!";
      } else {
        resultDiv.innerText = "❌ " + (data.message || "Có lỗi xảy ra.");
      }

    } catch (e) {
      console.error("Lỗi kết nối server:", e);
      resultDiv.innerText = "❌ Không kết nối được đến server.";
    } finally {
      rescanBtn.style.display = "inline-block";
    }
  }

  rescanBtn.addEventListener("click", startScanner);

  // Bắt đầu quét lần đầu
  startScanner();
});
