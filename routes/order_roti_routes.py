from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from
from decimal import Decimal

order_roti_bp = Blueprint('order_roti', __name__)

@order_roti_bp.route("/api/order-roti", methods=["GET"])
@swag_from('docs/order_roti/list_orders.yml')
def list_order_roti():
    """List all order roti"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT o.*, 
                       p.name as product_name,
                       p.price as product_price
                FROM order_roti o
                LEFT JOIN products p ON o.id_product = p.id
                ORDER BY o.created_at DESC
            """)
            orders = cur.fetchall()
    
    # Convert Decimal to float for JSON serialization
    for order in orders:
        if order['koordinat_pemesan_lat']:
            order['koordinat_pemesan_lat'] = float(order['koordinat_pemesan_lat'])
        if order['koordinat_pemesan_lng']:
            order['koordinat_pemesan_lng'] = float(order['koordinat_pemesan_lng'])
        if order['total_harga']:
            order['total_harga'] = float(order['total_harga'])
    
    return jsonify(orders)

@order_roti_bp.route("/api/order-roti/<int:id>", methods=["GET"])
@swag_from('docs/order_roti/get_order.yml')
def get_order_roti(id):
    """Get specific order roti by ID"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT o.*, 
                       p.name as product_name,
                       p.price as product_price,
                       p.image_url as product_image
                FROM order_roti o
                LEFT JOIN products p ON o.id_product = p.id
                WHERE o.id = %s
            """, (id,))
            order = cur.fetchone()
            
            if not order:
                return jsonify({"error": "Order roti tidak ditemukan"}), 404
    
    # Convert Decimal to float for JSON serialization
    if order['koordinat_pemesan_lat']:
        order['koordinat_pemesan_lat'] = float(order['koordinat_pemesan_lat'])
    if order['koordinat_pemesan_lng']:
        order['koordinat_pemesan_lng'] = float(order['koordinat_pemesan_lng'])
    if order['total_harga']:
        order['total_harga'] = float(order['total_harga'])
    
    return jsonify(order)

@order_roti_bp.route("/api/order-roti", methods=["POST"])
@swag_from('docs/order_roti/create_order.yml')
def create_order_roti():
    """Create new order roti"""
    data = request.json
    
    # Validate required fields
    required_fields = ['nama_pemesan', 'id_product', 'total_harga']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Field {field} harus diisi"}), 400
    
    nama_pemesan = data.get('nama_pemesan')
    id_product = data.get('id_product')
    koordinat_pemesan_lat = data.get('koordinat_pemesan_lat')
    koordinat_pemesan_lng = data.get('koordinat_pemesan_lng')
    total_harga = data.get('total_harga')
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Validate product exists
            cur.execute("SELECT id, name, price FROM products WHERE id = %s", (id_product,))
            product = cur.fetchone()
            if not product:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
            
            # Create order
            cur.execute("""
                INSERT INTO order_roti (nama_pemesan, id_product, 
                                      koordinat_pemesan_lat, koordinat_pemesan_lng, total_harga)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, nama_pemesan, id_product, 
                         koordinat_pemesan_lat, koordinat_pemesan_lng, total_harga, created_at
            """, (nama_pemesan, id_product, koordinat_pemesan_lat, koordinat_pemesan_lng, total_harga))
            
            new_order = cur.fetchone()
            conn.commit()
    
    # Convert Decimal to float for JSON serialization
    if new_order['koordinat_pemesan_lat']:
        new_order['koordinat_pemesan_lat'] = float(new_order['koordinat_pemesan_lat'])
    if new_order['koordinat_pemesan_lng']:
        new_order['koordinat_pemesan_lng'] = float(new_order['koordinat_pemesan_lng'])
    if new_order['total_harga']:
        new_order['total_harga'] = float(new_order['total_harga'])
    
    return jsonify(new_order), 201

@order_roti_bp.route("/api/order-roti/<int:id>", methods=["PUT"])
@swag_from('docs/order_roti/update_order.yml')
def update_order_roti(id):
    """Update order roti"""
    data = request.json
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if order exists
            cur.execute("SELECT id FROM order_roti WHERE id = %s", (id,))
            order = cur.fetchone()
            if not order:
                return jsonify({"error": "Order roti tidak ditemukan"}), 404
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            if 'nama_pemesan' in data:
                update_fields.append("nama_pemesan = %s")
                update_values.append(data['nama_pemesan'])
            
            if 'id_product' in data:
                # Validate product exists
                cur.execute("SELECT id FROM products WHERE id = %s", (data['id_product'],))
                product = cur.fetchone()
                if not product:
                    return jsonify({"error": "Produk tidak ditemukan"}), 404
                update_fields.append("id_product = %s")
                update_values.append(data['id_product'])
            
            if 'koordinat_pemesan_lat' in data:
                update_fields.append("koordinat_pemesan_lat = %s")
                update_values.append(data['koordinat_pemesan_lat'])
            
            if 'koordinat_pemesan_lng' in data:
                update_fields.append("koordinat_pemesan_lng = %s")
                update_values.append(data['koordinat_pemesan_lng'])
            
            if 'total_harga' in data:
                update_fields.append("total_harga = %s")
                update_values.append(data['total_harga'])
            
            if not update_fields:
                return jsonify({"error": "Tidak ada field yang akan diupdate"}), 400
            
            # Execute update
            update_values.append(id)
            cur.execute(f"""
                UPDATE order_roti 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, nama_pemesan, id_product,
                         koordinat_pemesan_lat, koordinat_pemesan_lng, total_harga, created_at
            """, update_values)
            
            updated_order = cur.fetchone()
            conn.commit()
    
    # Convert Decimal to float for JSON serialization
    if updated_order['koordinat_pemesan_lat']:
        updated_order['koordinat_pemesan_lat'] = float(updated_order['koordinat_pemesan_lat'])
    if updated_order['koordinat_pemesan_lng']:
        updated_order['koordinat_pemesan_lng'] = float(updated_order['koordinat_pemesan_lng'])
    if updated_order['total_harga']:
        updated_order['total_harga'] = float(updated_order['total_harga'])
    
    return jsonify(updated_order)

@order_roti_bp.route("/api/order-roti/<int:id>", methods=["DELETE"])
@swag_from('docs/order_roti/delete_order.yml')
def delete_order_roti(id):
    """Delete order roti"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if order exists
            cur.execute("SELECT id FROM order_roti WHERE id = %s", (id,))
            order = cur.fetchone()
            if not order:
                return jsonify({"error": "Order roti tidak ditemukan"}), 404
            
            # Delete order
            cur.execute("DELETE FROM order_roti WHERE id = %s", (id,))
            conn.commit()
    
    return jsonify({"message": "Order roti berhasil dihapus"}), 200
