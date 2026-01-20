from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Files, FileSigns, Users
from app.utils.pdf_sign import embed_qr_to_pdf

sign_bp = Blueprint("sign", __name__)

# 📄 Dosen lihat file yang perlu ditandatangani
@sign_bp.route("/dosen_preview", methods=["GET"])
@jwt_required()
def dosen_preview():
    nim_nip = get_jwt_identity()
    user = Users.query.get(nim_nip)

    if not user or user.role != "dosen":
        return jsonify({"error": "Akses hanya untuk dosen"}), 403

    signs = FileSigns.query.filter_by(signer_nim=user.nim_nip).all()

    result = []
    for sign in signs:
        file = sign.file
        result.append({
            "filename": file.filename,
            "jenis_file": file.jenis_file,
            "tanggal_diajukan": str(file.tanggal_diajukan),
            "global_status": file.global_status,
            "sign_status": sign.sign_status,
            "unique_code": file.unique_code,
            "role_pengaju": file.pengaju.role,
            "name": file.pengaju.name
        })

    return jsonify(result)

# ✍️ Dosen tanda tangan file
@sign_bp.route("/dosen_sign/<unique_code>", methods=["POST"])
@jwt_required()
def dosen_sign(unique_code):
    nim_nip = get_jwt_identity()
    user = Users.query.get(nim_nip)

    if not user or user.role != "dosen":
        return jsonify({"error": "Akses hanya untuk dosen"}), 403

    file = Files.query.filter_by(unique_code=unique_code).first()
    if not file:
        return jsonify({"error": "File tidak ditemukan"}), 404

    sign = FileSigns.query.filter_by(id_file=file.id_file, signer_nim=user.nim_nip).first()
    if not sign or sign.sign_status != "menunggu dosen":
        return jsonify({"error": "Tidak dapat menandatangani file ini"}), 403

    # Set status tanda tangan dosen
    sign.sign_status = "signed"
    db.session.commit()

    # Cek apakah masih ada dosen yang belum tanda tangan
    remaining_dosen = FileSigns.query.join(Users, FileSigns.signer_nim == Users.nim_nip) \
        .filter(
            FileSigns.id_file == file.id_file,
            FileSigns.sign_status == "menunggu dosen",
            Users.role == "dosen"
        ).first()

    if not remaining_dosen:
        # Update status semua kajur menjadi "menunggu kajur"
        kajur_signs = FileSigns.query.join(Users, FileSigns.signer_nim == Users.nim_nip) \
            .filter(
                FileSigns.id_file == file.id_file,
                FileSigns.sign_status == "menunggu dosen",
                Users.role == "kajur"
            ).all()

        for kajur_sign in kajur_signs:
            kajur_sign.sign_status = "menunggu kajur"

        if kajur_signs:
            file.global_status = "Diajukan ke Ketua Jurusan"
        else:
            file.global_status = "Completed"
            file.file_after_signed = embed_qr_to_pdf(file.file_before_signed, file.qr_code)

    db.session.commit()
    return jsonify({"message": "Berhasil tanda tangan sebagai dosen"})

# 📄 Kajur lihat file yang siap ditandatangani
@sign_bp.route("/kajur_preview", methods=["GET"])
@jwt_required()
def kajur_preview():
    nim_nip = get_jwt_identity()
    user = Users.query.get(nim_nip)

    if not user or user.role != "kajur":
        return jsonify({"error": "Akses hanya untuk ketua jurusan"}), 403

    signs = FileSigns.query.filter_by(signer_nim=user.nim_nip, sign_status="menunggu kajur").all()

    result = []
    for sign in signs:
        file = sign.file
        waiting_dosen = FileSigns.query.join(Users, FileSigns.signer_nim == Users.nim_nip) \
            .filter(
                FileSigns.id_file == file.id_file,
                FileSigns.sign_status == "menunggu dosen",
                Users.role == "dosen"
            ).first()
        if waiting_dosen:
            continue

        result.append({
            "filename": file.filename,
            "jenis_file": file.jenis_file,
            "tanggal_diajukan": str(file.tanggal_diajukan),
            "global_status": file.global_status,
            "unique_code": file.unique_code,
            "role_pengaju": file.pengaju.role,
            "name": file.pengaju.name
        })

    return jsonify(result)

# ✍️ Kajur tanda tangan file
@sign_bp.route("/kajur_sign/<unique_code>", methods=["POST"])
@jwt_required()
def kajur_sign(unique_code):
    nim_nip = get_jwt_identity()
    user = Users.query.get(nim_nip)

    if not user or user.role != "kajur":
        return jsonify({"error": "Akses hanya untuk ketua jurusan"}), 403

    file = Files.query.filter_by(unique_code=unique_code).first()
    if not file:
        return jsonify({"error": "File tidak ditemukan"}), 404

    sign = FileSigns.query.filter_by(id_file=file.id_file, signer_nim=user.nim_nip).first()
    if not sign or sign.sign_status != "menunggu kajur":
        return jsonify({"error": "Tidak dapat menandatangani file ini"}), 403

    # 🚫 Cek apakah masih ada dosen yang belum tanda tangan
    remaining_dosen = FileSigns.query.join(Users, FileSigns.signer_nim == Users.nim_nip) \
        .filter(
            FileSigns.id_file == file.id_file,
            FileSigns.sign_status == "menunggu dosen",
            Users.role == "dosen"
        ).first()

    if remaining_dosen:
        return jsonify({"error": "Masih ada dosen yang belum tanda tangan. Kajur belum bisa tanda tangan."}), 403

    # ✅ Semua dosen sudah tanda tangan → kajur bisa lanjut
    sign.sign_status = "completed"
    file.global_status = "Completed"
    file.file_after_signed = embed_qr_to_pdf(file.file_before_signed, file.qr_code)

    db.session.commit()
    return jsonify({"message": "Berhasil tanda tangan sebagai kajur"})
