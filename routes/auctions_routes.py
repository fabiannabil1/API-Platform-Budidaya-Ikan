from flask import Blueprint, request, jsonify, send_from_directory, current_app, url_for
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os

auction_bp = Blueprint('auction', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auction_bp.route("/api/auctions", methods=["GET"])
@jwt_required()
@swag_from('docs/auction/list_auctions.yml')
def list_auctions():
    user_id = get_jwt_identity()
    print(f"User ID: {user_id}")
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, l.name as location_name
                FROM auctions a
                LEFT JOIN locations l ON a.location_id = l.id
                WHERE a.user_id != %s
                ORDER BY a.created_at DESC
            """, (user_id,))
            auctions = cur.fetchall()
            return jsonify(auctions)


@auction_bp.route('/uploads/auctions/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['AUCTION_FOLDER'], filename)

@auction_bp.route("/api/auctions", methods=["POST"])
@jwt_required()
@swag_from('docs/auction/create_auction.yml')
def create_auction():
    user_id = get_jwt_identity()
    data = request.form
    required_fields = ["title", "description", "starting_price", "deadline", "location_id"]
    
    file = request.files.get("image")

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Field wajib diisi"}), 400

    filename = None
    if file and allowed_file(file.filename):
        filename = f"{datetime.utcnow().timestamp()}_{secure_filename(file.filename)}"
        save_path = os.path.join(current_app.config['AUCTION_FOLDER'], filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
    
    image_url = None
    if filename:
        image_url = request.host_url.rstrip('/') + url_for('auction.uploaded_file', filename=filename)
    else:
        return jsonify({"error": "Gambar wajib diunggah"}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user or user[0] != 'mitra':
                return jsonify({"error": "Hanya mitra yang bisa membuat auction"}), 403

            cur.execute("""
                INSERT INTO auctions (user_id, title, description, starting_price, current_price, deadline, location_id, status, created_at, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', NOW(), %s)
                RETURNING id
            """, (
                user_id,
                data["title"],
                data["description"],
                data["starting_price"],
                data["starting_price"],
                data["deadline"],
                data["location_id"],
                image_url
            ))
            auction_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "Auction berhasil dibuat", "auction_id": auction_id}), 201

@auction_bp.route("/api/auctions/<int:auction_id>", methods=["PUT"])
@jwt_required()
@swag_from('docs/auction/update_auction.yml')
def update_auction(auction_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM auctions WHERE id = %s", (auction_id,))
            auction = cur.fetchone()
            if not auction:
                return jsonify({"error": "Auction tidak ditemukan"}), 404
            if auction[0] != user_id:
                return jsonify({"error": "Tidak diizinkan mengubah"}), 403

            cur.execute("""
                UPDATE auctions SET
                    title = %s,
                    description = %s,
                    starting_price = %s,
                    deadline = %s,
                    location_id = %s
                WHERE id = %s
            """, (
                data.get("title"),
                data.get("description"),
                data.get("starting_price"),
                data.get("deadline"),
                data.get("location_id"),
                auction_id
            ))
            conn.commit()
            return jsonify({"message": "Auction berhasil diperbarui"})

@auction_bp.route("/api/auctions/<int:auction_id>", methods=["DELETE"])
@jwt_required()
@swag_from('docs/auction/delete_auction.yml')
def delete_auction(auction_id):
    user_id = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM auctions WHERE id = %s", (auction_id,))
            auction = cur.fetchone()
            if not auction:
                return jsonify({"error": "Auction tidak ditemukan"}), 404
            if auction[0] != user_id:
                return jsonify({"error": "Tidak diizinkan menghapus"}), 403

            cur.execute("DELETE FROM auctions WHERE id = %s", (auction_id,))
            conn.commit()
            return jsonify({"message": "Auction berhasil dihapus"})

@auction_bp.route("/api/auctions/<int:auction_id>/close", methods=["POST"])
@jwt_required()
@swag_from('docs/auction/close_auction.yml')
def close_auction(auction_id):
    user_id = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, status FROM auctions WHERE id = %s", (auction_id,))
            auction = cur.fetchone()
            if not auction:
                return jsonify({"error": "Auction tidak ditemukan"}), 404
            if auction[0] != user_id:
                return jsonify({"error": "Tidak diizinkan menutup"}), 403
            if auction[1] == 'closed':
                return jsonify({"message": "Auction sudah ditutup"})

            # Cari pemenang
            cur.execute("""
                SELECT user_id FROM bids
                WHERE auction_id = %s
                ORDER BY bid_amount DESC, bid_time ASC
                LIMIT 1
            """, (auction_id,))
            winner = cur.fetchone()
            winner_id = winner[0] if winner else None

            cur.execute("UPDATE auctions SET status = 'closed', winner_id = %s WHERE id = %s", (winner_id, auction_id))
            conn.commit()
            return jsonify({"message": "Auction berhasil ditutup", "winner_id": winner_id})

@auction_bp.route("/api/auctions/<int:auction_id>/highest_bid", methods=["GET"])
@jwt_required()
@swag_from('docs/auction/highest_bid.yml')
def highest_bid(auction_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT b.*, u.name AS bidder_name
                FROM bids b
                JOIN users u ON b.user_id = u.id
                WHERE b.auction_id = %s
                ORDER BY b.bid_amount DESC, b.bid_time ASC
                LIMIT 1
            """, (auction_id,))
            highest = cur.fetchone()
            if highest:
                return jsonify(highest)
            else:
                return jsonify({"message": "Belum ada penawaran"})

@auction_bp.route("/api/auctions/<int:auction_id>/bid", methods=["POST"])
@jwt_required()
@swag_from('docs/auction/place_bid.yml')
def place_bid(auction_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    if "bid_amount" not in data:
        return jsonify({"error": "bid_amount wajib diisi"}), 400

    bid_amount = data["bid_amount"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_price, status FROM auctions WHERE id = %s", (auction_id,))
            auction = cur.fetchone()
            if not auction:
                return jsonify({"error": "Auction tidak ditemukan"}), 404
            if auction[1] != 'open':
                return jsonify({"error": "Auction sudah ditutup"}), 400
            current_price = auction[0]

            if bid_amount <= current_price:
                return jsonify({"error": f"Penawaran harus > harga saat ini ({current_price})"}), 400

            cur.execute("""
                INSERT INTO bids (auction_id, user_id, bid_amount)
                VALUES (%s, %s, %s)
            """, (auction_id, user_id, bid_amount))

            cur.execute("UPDATE auctions SET current_price = %s WHERE id = %s", (bid_amount, auction_id))

            conn.commit()
            return jsonify({"message": "Penawaran berhasil", "bid_amount": bid_amount}), 201

@auction_bp.route("/api/auctions/close_expired", methods=["POST"])
def close_expired_auctions():
    """Menutup auction yang sudah melewati deadline dan menentukan pemenangnya"""
    now = datetime.now()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM auctions
                WHERE status = 'open' AND deadline < %s
            """, (now,))
            expired_auctions = cur.fetchall()

            for auction in expired_auctions:
                auction_id = auction[0]

                cur.execute("""
                    SELECT user_id FROM bids
                    WHERE auction_id = %s
                    ORDER BY bid_amount DESC, bid_time ASC
                    LIMIT 1
                """, (auction_id,))
                winner = cur.fetchone()
                winner_id = winner[0] if winner else None

                cur.execute("""
                    UPDATE auctions
                    SET status = 'closed', winner_id = %s
                    WHERE id = %s
                """, (winner_id, auction_id))

            conn.commit()

    return jsonify({"message": "Semua auction expired telah ditutup"}), 200
