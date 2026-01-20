from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import Users
from app import db, limiter
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint("auth", __name__)

# 🔐 Register
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    nim_nip = data.get("nim_nip")
    name = data.get("name")
    password = data.get("password")
    role = data.get("role")

    if Users.query.get(nim_nip):
        return jsonify({"error": "User sudah terdaftar"}), 409

    hashed_pw = generate_password_hash(password)
    user = Users(nim_nip=nim_nip, name=name, password=hashed_pw, role=role)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registrasi berhasil"}), 201

# 🔐 Login (protected by rate limiter)
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    nim_nip = data.get("nim_nip")
    password = data.get("password")

    user = Users.query.get(nim_nip)
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Login gagal"}), 401

    # Gunakan hanya nim_nip sebagai identity
    token = create_access_token(identity=user.nim_nip)
    return jsonify({
        "message": "Login berhasil",
        "access_token": token,
        "name": user.name,
        "role": user.role
    }), 200

# 🔐 Logout (dummy)
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Logout berhasil (client-side token deletion)"}), 200

# 🔐 Profile
@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    nim_nip = get_jwt_identity()
    user = Users.query.get(nim_nip)
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    return jsonify({
        "nim_nip": user.nim_nip,
        "name": user.name,
        "role": user.role,
        "created_at": str(user.created_at)
    })
