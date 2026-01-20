from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Files, FileSigns, Users
from app.utils.qr import generate_qr_bytes
from app.utils.pdf_sign import embed_qr_to_pdf
import uuid
from io import BytesIO

files_bp = Blueprint("files", __name__)

# 🔼 Ajukan file
@files_bp.route("/ajukan", methods=["POST"])
@jwt_required()
def ajukan_file():
    nim_nip = get_jwt_identity()
    user = Users.query.get(nim_nip)

    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    file = request.files.get("file")
    filename = request.form.get("filename")
    jenis_file = request.form.get("jenis_file")
    signer_nims = request.form.getlist("signer_nim")
    urutan_signers = request.form.getlist("urutan_signer")

    if not all([file, filename, jenis_file, signer_nims, urutan_signers]):
        return jsonify({"error": "Data tidak lengkap"}), 400

    unique_code = str(uuid.uuid4())
    qr_binary = generate_qr_bytes(unique_code)
    file_binary = file.read()

    # Simpan file dulu tanpa tanda tangan
    new_file = Files(
        pengaju_nim=user.nim_nip,
        filename=filename,
        jenis_file=jenis_file,
        file_before_signed=b"",
        qr_code=qr_binary,
        unique_code=unique_code,
        global_status="Menunggu TTD Dosen"
    )
    db.session.add(new_file)
    db.session.flush()

    # Ambil data signer untuk menentukan role dan nama
    signer_users = Users.query.filter(Users.nim_nip.in_(signer_nims)).all()
    signer_roles = {u.nim_nip: u.role for u in signer_users}
    signer_lookup = {u.nim_nip: u.name for u in signer_users}

    # Gabungkan dan urutkan berdasarkan urutan_signer
    signer_pairs = sorted(
        zip(signer_nims, urutan_signers),
        key=lambda x: int(x[1])
    )

    signer_objs = []
    signer_data = []

    # Cek apakah ada dosen di daftar signer
    ada_dosen = any(
        signer_roles.get(nim, "dosen") == "dosen"
        for nim, _ in signer_pairs
    )

    for nim, urutan in signer_pairs:
        role = signer_roles.get(nim, "dosen")

        # Atur status: jika ada dosen, semua status awal = "menunggu dosen"
        # Kajur akan aktif ketika semua dosen selesai
        if ada_dosen:
            sign_status = "menunggu dosen"
        else:
            sign_status = "menunggu kajur" if role == "kajur" else "menunggu dosen"

        signer_obj = FileSigns(
            id_file=new_file.id_file,
            signer_nim=nim,
            sign_status=sign_status,
            urutan_signer=int(urutan)
        )
        db.session.add(signer_obj)
        signer_objs.append(signer_obj)

        signer_data.append({
            "urutan": int(urutan),
            "name": signer_lookup.get(nim, "Unknown"),
            "nim_nip": nim
        })

    db.session.flush()

    # Generate PDF with watermark + QR
    pdf_signed = embed_qr_to_pdf(file_binary, qr_binary, signer_data=signer_data)
    new_file.file_before_signed = pdf_signed

    db.session.commit()

    return jsonify({
        "message": "File berhasil diajukan",
        "unique_code": unique_code
    }), 201


# 👁️ Lihat file (before/after signed)
@files_bp.route("/view_file/<code>", methods=["GET"])
def view_file(code):
    file = Files.query.filter_by(unique_code=code).first()
    if not file:
        return jsonify({"error": "File tidak ditemukan"}), 404

    pdf_bytes = file.file_after_signed if file.file_after_signed else file.file_before_signed
    return send_file(BytesIO(pdf_bytes), download_name=f"{file.filename}.pdf", as_attachment=True)

@files_bp.route("/file_detail/<code>", methods=["GET"])
def file_detail(code):
    file = Files.query.filter_by(unique_code=code).first()
    if not file:
        return jsonify({"error": "File tidak ditemukan"}), 404

    # Ambil semua penandatangan untuk file ini
    signer_entries = FileSigns.query.filter_by(id_file=file.id_file).order_by(FileSigns.urutan_signer).all()

    signer_details = []
    for entry in signer_entries:
        user = Users.query.get(entry.signer_nim)
        signer_details.append({
            "name": user.name,
            "nim_nip": user.nim_nip,
            "role": user.role,
            "sign_status": entry.sign_status,
            "status_icon": "✅" if entry.sign_status == "signed" or entry.sign_status == "completed" else "❌"
        })

    return jsonify({
        "filename": file.filename,
        "jenis_file": file.jenis_file,
        "tanggal_diajukan": str(file.tanggal_diajukan),
        "global_status": file.global_status,
        "pengaju": file.pengaju.name,
        "role_pengaju": file.pengaju.role,
        "signers": signer_details
    })

# 📄 Mahasiswa preview card
@files_bp.route("/mhs_preview", methods=["GET"])
@jwt_required()
def mhs_preview():
    nim_nip = get_jwt_identity()
    files = Files.query.filter_by(pengaju_nim=nim_nip).all()

    return jsonify([
        {
            "filename": f.filename,
            "jenis_file": f.jenis_file,
            "tanggal_diajukan": str(f.tanggal_diajukan),
            "global_status": f.global_status,
            "unique_code": f.unique_code
        } for f in files
    ])


# 📄 Admin lihat semua file
@files_bp.route("/admin_preview", methods=["GET"])
@jwt_required()
def admin_preview():
    nim_nip = get_jwt_identity()
    user = Users.query.get(nim_nip)

    if user.role != "admin":
        return jsonify({"error": "Akses hanya untuk admin"}), 403

    files = Files.query.all()
    return jsonify([
        {
            "filename": f.filename,
            "jenis_file": f.jenis_file,
            "tanggal_diajukan": str(f.tanggal_diajukan),
            "global_status": f.global_status,
            "name": f.pengaju.name,
            "role_pengaju": f.pengaju.role
        } for f in files
    ])
