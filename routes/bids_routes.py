from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from

bids_bp = Blueprint("bids", __name__)

@bids_bp.route("/api/bids", methods=["GET"])
@jwt_required()
@swag_from('docs/bids/user_bids.yml')
def get_user_bids():
    """Menampilkan semua bid dari user yang sedang login"""
    user_id = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT b.*, a.title as auction_title
                FROM bids b
                JOIN auctions a ON b.auction_id = a.id
                WHERE b.user_id = %s
                ORDER BY b.bid_time DESC
            """, (user_id,))
            bids = cur.fetchall()
            return jsonify(bids)

@bids_bp.route("/api/auctions/<int:auction_id>/bids", methods=["GET"])
@jwt_required()
@swag_from('docs/bids/auction_bids.yml')
def get_auction_bids(auction_id):
    """Menampilkan semua bid dari satu auction"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT b.*, u.name as bidder_name
                FROM bids b
                JOIN users u ON b.user_id = u.id
                WHERE b.auction_id = %s
                ORDER BY b.bid_amount DESC, b.bid_time ASC
            """, (auction_id,))
            bids = cur.fetchall()
            return jsonify(bids)

@bids_bp.route("/api/auctions/<int:auction_id>/bids/me", methods=["GET"])
@jwt_required()
@swag_from('docs/bids/my_bids_on_auction.yml')
def get_my_bids_on_auction(auction_id):
    """Menampilkan bid dari user yang login pada auction tertentu"""
    user_id = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM bids
                WHERE user_id = %s AND auction_id = %s
                ORDER BY bid_time DESC
            """, (user_id, auction_id))
            bids = cur.fetchall()
            return jsonify(bids)

@bids_bp.route("/api/auctions/<int:auction_id>/bids/history", methods=["GET"])
@jwt_required()
@swag_from('docs/bids/history.yml')
def bid_history(auction_id):
    """Menampilkan riwayat penawaran pada auction (secara kronologis)"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT b.*, u.name as bidder_name
                FROM bids b
                JOIN users u ON b.user_id = u.id
                WHERE b.auction_id = %s
                ORDER BY b.bid_time ASC
            """, (auction_id,))
            history = cur.fetchall()
            return jsonify(history)
