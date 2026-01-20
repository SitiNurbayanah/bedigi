from . import db
from sqlalchemy.sql import func

class Users(db.Model):
    __tablename__ = "Users"
    nim_nip = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    files = db.relationship("Files", backref="pengaju", lazy=True)
    signed_files = db.relationship("FileSigns", backref="signer_user", lazy=True, foreign_keys="FileSigns.signer_nim")

    def __repr__(self):
        return f"<User {self.name} - {self.nim_nip}>"


class Files(db.Model):
    __tablename__ = "Files"
    id_file = db.Column(db.Integer, primary_key=True)
    pengaju_nim = db.Column(db.String(20), db.ForeignKey("Users.nim_nip"), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    jenis_file = db.Column(db.String(50), nullable=False)
    tanggal_diajukan = db.Column(db.DateTime(timezone=True), server_default=func.now())
    file_before_signed = db.Column(db.LargeBinary, nullable=False)
    file_after_signed = db.Column(db.LargeBinary)
    global_status = db.Column(db.String(100), default="Menunggu TTD Dosen Terkait")
    unique_code = db.Column(db.String(100), unique=True, nullable=False)
    qr_code = db.Column(db.LargeBinary)

    signers = db.relationship("FileSigns", backref="file", lazy=True)

    def __repr__(self):
        return f"<File {self.filename} by {self.pengaju_nim}>"


class FileSigns(db.Model):
    __tablename__ = "FileSigns"
    id_filesigner = db.Column(db.Integer, primary_key=True)
    id_file = db.Column(db.Integer, db.ForeignKey("Files.id_file"), nullable=False)
    signer_nim = db.Column(db.String(20), db.ForeignKey("Users.nim_nip"), nullable=False)  # GANTI ini
    sign_status = db.Column(db.String(50), nullable=False, default="menunggu dosen")
    urutan_signer = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Signer {self.signer_nim} - File {self.id_file}>"
