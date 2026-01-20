from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image, UnidentifiedImageError
import base64
import fitz  # PyMuPDF


def embed_qr_to_pdf(pdf_bytes: bytes, qr_bytes: bytes, signer_data: list = None) -> bytes:
    try:
        if isinstance(qr_bytes, str):
            qr_bytes = base64.b64decode(qr_bytes)

        img = Image.open(BytesIO(qr_bytes))
        img.verify()
        qr_img = ImageReader(BytesIO(qr_bytes))
    except (UnidentifiedImageError, base64.binascii.Error, ValueError) as e:
        raise ValueError("QR code image is not valid or cannot be identified.") from e

    # ✅ Urutkan signer_data berdasarkan urutan agar tag #1 = signer urutan 1, dst
    if signer_data:
        signer_data = sorted(signer_data, key=lambda x: int(x["urutan"]))

    # Temukan posisi marker dan hapus tag
    marker_map, cleaned_pdf_bytes = extract_and_replace_signer_tags(pdf_bytes, signer_data)

    original_pdf = PdfReader(BytesIO(cleaned_pdf_bytes))
    output = PdfWriter()

    for i, page in enumerate(original_pdf.pages):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        # Tambahkan QR code di kanan bawah halaman
        can.drawImage(qr_img, 460, 20, width=100, height=100)

        # Tambahkan nama/NIM di posisi marker
        if i in marker_map:
            for marker in marker_map[i]:
                x, y = marker["position"]
                signer = marker["signer"]
                can.setFont("Helvetica", 10)
                can.drawString(x, y, f"{signer['name']} ({signer['nim_nip']})")

        can.save()
        packet.seek(0)

        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        output.add_page(page)

    result = BytesIO()
    output.write(result)
    result.seek(0)
    return result.read()


def extract_and_replace_signer_tags(pdf_bytes: bytes, signer_data: list):
    """
    Temukan tag #1, #2, dst. Hapus tag, simpan posisi untuk watermark.
    """
    if not signer_data:
        return {}, pdf_bytes

    marker_map = {}

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            marker_map[page_num] = []

            for signer in signer_data:
                tag = f"#{signer['urutan']}"
                matches = page.search_for(tag)

                for rect in matches:
                    marker_map[page_num].append({
                        "position": (rect.x0, rect.y1),
                        "signer": signer
                    })
                    # Hapus tag dari PDF dengan anotasi redaksi
                    page.add_redact_annot(rect, fill=(1, 1, 1))  # putih

            page.apply_redactions()

        output = BytesIO()
        doc.save(output)
        output.seek(0)

        return marker_map, output.read()
