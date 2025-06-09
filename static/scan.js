// static/scan.js
// --------------------------------------------------
// Quét QR bằng html5-qrcode và gửi mã về server Flask
// --------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  const resultDiv   = document.getElementById("scan-result");
  const rescanBtn   = document.getElementById("rescan-btn");
  const html5QrCode = new Html5Qrcode("reader");

  // ✔️ Endpoint động: luôn dùng cùng origin với trang đang chạy
  const ENDPOINT = `${window.location.origin}/scan`;

  // --------------------- Khởi động camera ---------------------
  function startScanner() {
    resultDiv.innerText     = "";
    rescanBtn.style.display = "none";

    html5QrCode
      .start(
        { facingMode: "environment" },   // camera sau
        { fps: 10, qrbox: 250 },         // tốc độ & khung quét
        onScanSuccess                    // callback
      )
      .catch(err => {
        console.error("Camera không khởi động được:", err);
        resultDiv.innerText     = "❌ Không thể truy cập camera.";
        rescanBtn.style.display = "inline-block";
      });
  }

  // --------------------- Xử lý khi quét thành công ---------------------
  async function onScanSuccess(decodedText) {
    await html5QrCode.stop();            // Tạm dừng camera

    try {
      console.log("[scan.js] Gửi mã QR:", decodedText);

      const res = await fetch(ENDPOINT, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ qr_code: decodedText })
      });

      const data = await res.json();
      console.log("[scan.js] Phản hồi:", data);

      if (res.ok) {
        resultDiv.innerText = "✅ Điểm danh thành công!";
      } else {
        resultDiv.innerText = "❌ " + (data.message || "Có lỗi xảy ra.");
      }

    } catch (err) {
      console.error("Lỗi kết nối server:", err);
      resultDiv.innerText = "❌ Không kết nối được tới máy chủ.";
    } finally {
      rescanBtn.style.display = "inline-block";
    }
  }

  // --------------------- Nút quét lại ---------------------
  rescanBtn.addEventListener("click", startScanner);

  // Bắt đầu quét ngay khi trang load
  startScanner();
});
