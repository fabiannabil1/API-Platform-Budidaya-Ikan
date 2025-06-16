from flask import Blueprint, request, jsonify, send_from_directory, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from
from werkzeug.utils import secure_filename
from datetime import datetime
import os


profiles_bp = Blueprint('profiles', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profiles_bp.route("/api/profile", methods=["GET"])
@jwt_required()
@swag_from('docs/profiles/get_profile.yml')
def get_my_profile():
    current_user = get_jwt_identity()
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT u.id, u.name, u.phone, u.role, u.created_at,
                       up.address, up.profile_picture, up.bio
                FROM users u 
                LEFT JOIN user_profiles up ON u.id = up.user_id 
                WHERE u.id = %s
            """, (current_user,))
            profile = cur.fetchone()
            
            if not profile:
                return jsonify({"error": "Profil tidak ditemukan"}), 404
                
    return jsonify(profile)

@profiles_bp.route("/api/profiles/<int:user_id>", methods=["GET"])
@swag_from('docs/profiles/get_user_profile.yml')
def get_user_profile(user_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT u.id, u.name, u.role, u.created_at,
                       up.address, up.profile_picture, up.bio
                FROM users u 
                LEFT JOIN user_profiles up ON u.id = up.user_id 
                WHERE u.id = %s
            """, (user_id,))
            profile = cur.fetchone()
            
            if not profile:
                return jsonify({"error": "Profil tidak ditemukan"}), 404
                
    return jsonify(profile)


@profiles_bp.route('/uploads/profiles/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['PROFILE_FOLDER'], filename)

@profiles_bp.route("/api/profile", methods=["PUT"])
@jwt_required()
@swag_from('docs/profiles/update_profile.yml')
def update_profile():
    current_user = get_jwt_identity()
    if request.content_type.startswith('application/json'):
        data = request.get_json()
        file = None
    elif request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        file = request.files.get("image")
    else:
        return jsonify({"error": "Content-Type tidak didukung"}), 415


    # Handle image upload
    file = request.files.get("image")
    filename = None
    image_url = None

    if file:
        if allowed_file(file.filename):
            filename = f"{datetime.utcnow().timestamp()}_{secure_filename(file.filename)}"
            save_path = os.path.join(current_app.config['PROFILE_FOLDER'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            image_url = request.host_url.rstrip('/') + url_for('.uploaded_file', filename=filename)
        else:
            return jsonify({"error": "Tipe file tidak diperbolehkan"}), 400

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Update user table jika ada perubahan nama
                if data.get("name"):
                    cur.execute("""
                        UPDATE users 
                        SET name = %s
                        WHERE id = %s
                    """, (data["name"], current_user))

                # Cek apakah profil sudah ada
                cur.execute("SELECT id FROM user_profiles WHERE user_id = %s", (current_user,))
                profile_exists = cur.fetchone()

                # Gunakan gambar baru jika ada, jika tidak gunakan gambar lama
                if profile_exists:
                    cur.execute("""
                        UPDATE user_profiles 
                        SET address = COALESCE(%s, address),
                            profile_picture = COALESCE(%s, profile_picture),
                            bio = COALESCE(%s, bio)
                        WHERE user_id = %s
                    """, (
                        data.get("address"),
                        image_url,  # Ganti dengan image_url
                        data.get("bio"),
                        current_user
                    ))
                else:
                    cur.execute("""
                        INSERT INTO user_profiles (user_id, address, profile_picture, bio)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        current_user,
                        data.get("address"),
                        image_url,
                        data.get("bio")
                    ))

                # Ambil data profil terbaru
                cur.execute("""
                    SELECT u.id, u.name, u.phone, u.role, u.created_at,
                           up.address, up.profile_picture, up.bio
                    FROM users u 
                    LEFT JOIN user_profiles up ON u.id = up.user_id 
                    WHERE u.id = %s
                """, (current_user,))
                updated_profile = cur.fetchone()
                conn.commit()

        return jsonify(updated_profile)

    except Exception as e:
        return jsonify({"error": "Terjadi kesalahan saat memperbarui profil", "details": str(e)}), 500

@profiles_bp.route("/api/profiles", methods=["GET"])
@swag_from('docs/profiles/list_profiles.yml')
def get_all_profiles():
    role_filter = request.args.get('role')
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if role_filter:
                cur.execute("""
                SELECT u.id, u.name, u.phone, u.role, u.created_at,
                       up.address, up.profile_picture, up.bio
                FROM users u 
                LEFT JOIN user_profiles up ON u.id = up.user_id 
                WHERE u.role = %s
                ORDER BY u.created_at DESC
            """, (role_filter,))
            else:
                cur.execute("""
                SELECT u.id, u.name, u.phone, u.role, u.created_at,
                       up.address, up.profile_picture, up.bio
                FROM users u 
                LEFT JOIN user_profiles up ON u.id = up.user_id 
                ORDER BY u.created_at DESC
            """)
            profiles = cur.fetchall()
                
    return jsonify(profiles)
