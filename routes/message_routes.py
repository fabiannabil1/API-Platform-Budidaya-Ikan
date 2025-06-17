from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection  # koneksi db postgresql
from flasgger import swag_from

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chats")

# Helper: buat atau ambil chat_id berdasarkan phone
def get_or_create_chat(user1_phone, user2_phone):
    # Ambil user_id dari phone number
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get user IDs from phone numbers
            cur.execute("SELECT id FROM users WHERE phone = %s", (user1_phone,))
            user1 = cur.fetchone()
            cur.execute("SELECT id FROM users WHERE phone = %s", (user2_phone,))
            user2 = cur.fetchone()
            
            if not user1 or not user2:
                raise ValueError("One or both users not found")
            
            user1_id = user1["id"]
            user2_id = user2["id"]
            
            # Sort IDs to ensure consistent ordering
            pair = sorted([user1_id, user2_id])
            
            # Check if chat already exists
            cur.execute("""
                SELECT id FROM chats 
                WHERE user1_id = %s AND user2_id = %s
            """, (pair[0], pair[1]))
            chat = cur.fetchone()
            
            if chat:
                return chat["id"]
            
            # Create new chat
            cur.execute("""
                INSERT INTO chats (user1_id, user2_id)
                VALUES (%s, %s) RETURNING id
            """, (pair[0], pair[1]))
            new_chat = cur.fetchone()
            conn.commit()
            return new_chat["id"]

# Helper: get user_id from phone
def get_user_id_by_phone(phone):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM public.users where phone = %s", (phone,))
            user = cur.fetchone()
            return user["id"] if user else None

# Helper: get user phone from JWT (assuming JWT contains phone)
def get_current_user_phone(user_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT phone FROM public.users where id = %s", (user_id,))
            user = cur.fetchone()
            return user["phone"] if user else None

def get_user_id_from_jwt():
    payload = get_jwt_identity()  # asumsi kamu pakai flask_jwt_extended
    return int(payload)  # atau payload["sub"], tergantung isi JWT-mu


# 🔹 [GET] List semua chat milik user berdasarkan phone
@chat_bp.route("/getmessage", methods=["GET"])
@jwt_required()
@swag_from('docs/chat/list_user_chats.yml')
def list_user_chats():
    user_id = get_jwt_identity()  # pastikan JWT menyimpan 'user_id'
    
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    c.id AS chat_id,
                    u.id AS partner_id,
                    u.phone AS partner_phone,
                    u.name AS partner_name,
                    up.profile_picture,
                    m.message AS last_message,
                    m.sent_at
                FROM chats c
                JOIN users u ON (u.id = CASE WHEN c.user1_id = %s THEN c.user2_id ELSE c.user1_id END)
                LEFT JOIN user_profiles up ON up.user_id = u.id
                LEFT JOIN LATERAL (
                    SELECT message, sent_at FROM messages
                    WHERE chat_id = c.id
                    ORDER BY sent_at DESC LIMIT 1
                ) m ON true
                WHERE c.user1_id = %s OR c.user2_id = %s
                ORDER BY m.sent_at DESC NULLS LAST
            """, (user_id, user_id, user_id))
            chats = cur.fetchall()

    return jsonify({"data": chats}), 200

# 🔹 [GET] Ambil semua pesan dari chat dengan user tertentu berdasarkan phone
@chat_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
@swag_from('docs/chat/get_chat_messages.yml')
def get_chat_messages(id):
    my_id = get_user_id_from_jwt()  # ganti: ambil ID langsung dari JWT
    partner_id = id
    
    if not my_id or not partner_id:
        return jsonify({"error": "One or both users not found"}), 404
    
    pair = sorted([my_id, partner_id])
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM chats WHERE user1_id = %s AND user2_id = %s", (pair[0], pair[1]))
            chat = cur.fetchone()
            
            if not chat:
                return jsonify({"data": []}), 200
            
            chat_id = chat["id"]
            cur.execute("""
                SELECT 
                    m.sender_id,
                    u.phone AS sender_phone,
                    m.message, 
                    m.sent_at
                FROM messages m
                JOIN users u ON u.id = m.sender_id
                WHERE m.chat_id = %s
                ORDER BY m.sent_at ASC
            """, (chat_id,))
            messages = cur.fetchall()
    
    return jsonify({"chat_id": chat_id, "messages": messages}), 200


# 🔹 [POST] Kirim pesan berdasarkan phone
@chat_bp.route("/send", methods=["POST"])
@jwt_required()
@swag_from('docs/chat/send_message.yml')
def send_message():
    current_user = get_jwt_identity()
    data = request.get_json()
    sender_phone = get_current_user_phone(current_user)
    receiver_phone = data.get("receiver_phone")
    message = data.get("message")

    print(f"Sender Phone: {sender_phone}, Receiver Phone: {receiver_phone}, Message: {message}")

    if not all([receiver_phone, message]):
        return jsonify({"error": "Field tidak lengkap. Diperlukan receiver_phone dan message"}), 400

    try:
        if not current_user:
            return jsonify({"error": "Sender not found"}), 404
        
        receiver_id = get_user_id_by_phone(receiver_phone)
        if not receiver_id:
            return jsonify({"error": "Receiver not found"}), 404
        
        chat_id = get_or_create_chat(sender_phone, receiver_phone)
        
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO messages (chat_id, sender_id, message)
                    VALUES (%s, %s, %s)
                    RETURNING id, chat_id, sender_id, message, sent_at
                """, (chat_id, current_user, message))
                msg = cur.fetchone()
                
                # Add sender phone to response
                msg_with_phone = dict(msg)
                msg_with_phone['sender_phone'] = sender_phone
                
                conn.commit()
        
        return jsonify({"message": "Pesan terkirim", "data": msg_with_phone}), 201
        
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔹 [GET] Search user by phone (untuk mencari kontak chat)
@chat_bp.route("/search/<int:id>", methods=["GET"])
@jwt_required()
@swag_from('docs/chat/search_user_by_id.yml')
def search_user_by_phone(id):
    phone = get_current_user_phone(id)
    if not phone:
        return jsonify({"error": "User not found"}), 404
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    u.phone,
                    u.name,
                    up.profile_picture
                FROM users u
                LEFT JOIN user_profiles up ON up.user_id = u.id
                WHERE u.phone = %s
            """, (phone,))
            user = cur.fetchone()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"data": user}), 200