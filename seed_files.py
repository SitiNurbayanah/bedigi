from app import create_app, db
from app.models import Files, FileSigns
import uuid

app = create_app()

with app.app_context():
    # Buat dummy file
    dummy_pdf = b"%PDF-1.4\n%..."  # bisa ganti dengan file real jika mau

    unique_code = str(uuid.uuid4())

    file = Files(
        pengaju_nim="2023001",
        filename="Contoh File",
        jenis_file="laporan",
        file_before_signed=dummy_pdf,
        global_status="Menunggu TTD Dosen Terkait",
        unique_code=unique_code,
        qr_code=b"FAKEQRDATA"
    )
    db.session.add(file)
    db.session.flush()

    sign1 = FileSigns(id_file=file.id_file, signer_nim="1988001", sign_status="menunggu dosen", urutan_signer=1)
    sign2 = FileSigns(id_file=file.id_file, signer_nim="1977001", sign_status="menunggu kajur", urutan_signer=2)

    db.session.add_all([sign1, sign2])
    db.session.commit()

    print(f"✅ Dummy file berhasil dibuat dengan unique_code: {unique_code}")
