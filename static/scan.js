function onScanSuccess(decodedText, decodedResult) {
    console.log(`QR Code: ${decodedText}`);
    fetch('/api/checkin', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ qr_code: decodedText })
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(err => console.error(err));
}

var html5QrCode = new Html5Qrcode("reader");
html5QrCode.start(
    { facingMode: "environment" }, // Dùng camera sau
    { fps: 10, qrbox: 250 },
    onScanSuccess
);
