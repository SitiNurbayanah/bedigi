from app import create_app, db
from app.models import Users
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()

    # Tambah user awal
    users = [
        Users(nim_nip="2023001", name="Mahasiswa", password=generate_password_hash("12345"), role="mahasiswa"),
        Users(nim_nip="1988001", name="Dosen A", password=generate_password_hash("dosen123"), role="dosen"),
        Users(nim_nip="1988002", name="Dosen B", password=generate_password_hash("dosen123"), role="dosen"),
        Users(nim_nip="1977001", name="Kajur", password=generate_password_hash("kajur123"), role="kajur"),
        Users(nim_nip="admin001", name="Admin Sistem", password=generate_password_hash("admin123"), role="admin"),
    ]

    db.session.bulk_save_objects(users)
    db.session.commit()

    print("✅ User awal berhasil dimasukkan")
