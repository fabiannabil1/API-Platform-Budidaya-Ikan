from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/api/login", methods=["POST"])
@swag_from('docs/auth/login.yml')
def login():
    data = request.json
    print(data)
    phone = data.get("nomor_hp") or data.get("phone")
    if not phone:
        phone = data.get("phone")  # untuk kompatibilitas dengan versi sebelumnya
    password = data.get("password")

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, password FROM users WHERE phone=%s", (phone,))
            user = cur.fetchone()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Nomor HP atau password salah"}), 401

    access_token = create_access_token(identity=str(user["id"]))
    return jsonify(access_token=access_token)


@auth_bp.route("/api/register", methods=["POST"])
@swag_from('docs/auth/register.yml')
def register():
    data = request.json
    # print(data)
    phone = data.get("nomor_hp") or data.get("phone")
    password = data.get("password")
    name = data.get("name")
    address = data.get("address")  # untuk user_profiles
    role = data.get("role", "biasa")

    if role not in ["mitra", "biasa"]:
        return jsonify({"error": "Role tidak valid"}), 400

    if not phone or not password:
        return jsonify({"error": "Phone dan password harus diisi"}), 400

    hashed_password = generate_password_hash(password)

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Cek duplikasi
            cur.execute("SELECT id FROM users WHERE phone=%s", (phone,))
            if cur.fetchone():
                return jsonify({"error": "Nomor HP telah terdaftar"}), 409

            # Insert ke tabel users
            cur.execute(
                "INSERT INTO users (name, phone, password, role) VALUES (%s, %s, %s, %s) RETURNING id",
                (name, phone, hashed_password, role)
            )
            user_id = cur.fetchone()[0]

            # Insert ke user_profiles
            cur.execute(
                "INSERT INTO user_profiles (user_id, address) VALUES (%s, %s)",
                (user_id, address)
            )

            conn.commit()

    return jsonify({"message": "Registrasi berhasil"}), 201
