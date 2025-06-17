from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from
import datetime

change_role_bp = Blueprint('change_role', __name__)

@change_role_bp.route("/api/role-change/request", methods=["POST"])
@jwt_required()
@swag_from('docs/role_change/request_role_change.yml')
def request_role_change():
    """Request a role change from 'biasa' to 'mitra'"""
    current_user = get_jwt_identity()
    data = request.json
    reason = data.get("reason", "")  # Make reason optional with empty string default
        
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check current role
            cur.execute("SELECT role FROM users WHERE id = %s", (current_user,))
            user = cur.fetchone()
            
            if not user:
                return jsonify({"error": "User tidak ditemukan"}), 404
                
            if user['role'] != 'biasa':
                return jsonify({"error": "Hanya user biasa yang dapat mengajukan perubahan role"}), 400
                
            # Check if there's already a pending request
            cur.execute("""
                SELECT id FROM role_change_requests 
                WHERE user_id = %s AND status = 'pending'
            """, (current_user,))
            
            if cur.fetchone():
                return jsonify({"error": "Anda sudah memiliki pengajuan yang sedang diproses"}), 400
                
            # Create new request
            cur.execute("""
                INSERT INTO role_change_requests (user_id, reason, requested_at, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING id
            """, (current_user, reason, datetime.datetime.now()))
            
            request_id = cur.fetchone()['id']
            conn.commit()
            
    return jsonify({
        "message": "Pengajuan perubahan role berhasil dibuat",
        "request_id": request_id
    }), 201

@change_role_bp.route("/api/role-change/requests", methods=["GET"])
@jwt_required()
@swag_from('docs/role_change/list_role_requests.yml')
def list_role_change_requests():
    """List all role change requests (admin only)"""
    current_user = get_jwt_identity()
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if admin
            cur.execute("SELECT role FROM users WHERE id = %s", (current_user,))
            user = cur.fetchone()
            
            if not user or user['role'] != 'admin':
                return jsonify({"error": "Unauthorized"}), 403
                
            # Get all requests with user details
            cur.execute("""
                SELECT r.*, u.name, u.phone
                FROM role_change_requests r
                JOIN users u ON r.user_id = u.id
                ORDER BY r.requested_at DESC
            """)
            
            requests = cur.fetchall()
            
    return jsonify({"data": requests}), 200

@change_role_bp.route("/api/role-change/<int:request_id>/approve", methods=["PUT"])
@jwt_required()
@swag_from('docs/role_change/approve_role_request.yml')
def approve_role_change(request_id):
    """Approve a role change request (admin only)"""
    current_user = get_jwt_identity()
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if admin
            cur.execute("SELECT role FROM users WHERE id = %s", (current_user,))
            user = cur.fetchone()
            
            if not user or user['role'] != 'admin':
                return jsonify({"error": "Unauthorized"}), 403
                
            # Get request details
            cur.execute("""
                SELECT user_id, status 
                FROM role_change_requests 
                WHERE id = %s
            """, (request_id,))
            
            request = cur.fetchone()
            
            if not request:
                return jsonify({"error": "Permintaan tidak ditemukan"}), 404
                
            if request['status'] != 'pending':
                return jsonify({"error": "Permintaan ini sudah diproses"}), 400
                
            # Update request status and user role
            cur.execute("""
                UPDATE role_change_requests
                SET status = 'approved',
                    processed_at = %s,
                    processed_by = %s
                WHERE id = %s
            """, (datetime.datetime.now(), current_user, request_id))
            
            cur.execute("""
                UPDATE users
                SET role = 'mitra'
                WHERE id = %s
            """, (request['user_id'],))
            
            conn.commit()
            
    return jsonify({"message": "Permintaan perubahan role disetujui"}), 200

@change_role_bp.route("/api/role-change/<int:request_id>/reject", methods=["PUT"])
@jwt_required()
@swag_from('docs/role_change/reject_role_request.yml')
def reject_role_change(request_id):
    """Reject a role change request (admin only)"""
    current_user = get_jwt_identity()
    data = request.json
    rejection_reason = data.get("reason")
    
    if not rejection_reason:
        return jsonify({"error": "Alasan penolakan harus diisi"}), 400
        
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if admin
            cur.execute("SELECT role FROM users WHERE id = %s", (current_user,))
            user = cur.fetchone()
            
            if not user or user['role'] != 'admin':
                return jsonify({"error": "Unauthorized"}), 403
                
            # Get request details
            cur.execute("""
                SELECT status 
                FROM role_change_requests 
                WHERE id = %s
            """, (request_id,))
            
            req = cur.fetchone()
            
            if not req:
                return jsonify({"error": "Permintaan tidak ditemukan"}), 404
                
            if req['status'] != 'pending':
                return jsonify({"error": "Permintaan ini sudah diproses"}), 400
                
            # Update request status
            cur.execute("""
                UPDATE role_change_requests
                SET status = 'rejected',
                    rejection_reason = %s,
                    processed_at = %s,
                    processed_by = %s
                WHERE id = %s
            """, (rejection_reason, datetime.datetime.now(), current_user, request_id))
            
            conn.commit()
            
    return jsonify({"message": "Permintaan perubahan role ditolak"}), 200
