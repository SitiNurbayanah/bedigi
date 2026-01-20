import qrcode
from io import BytesIO

def generate_qr_bytes(data: str) -> bytes:
    qr = qrcode.make(f"http://localhost:8000/files/view_file/{data}")
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return buffer.getvalue()
