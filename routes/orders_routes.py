from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from

orders_bp = Blueprint('orders', __name__)

@orders_bp.route("/api/orders", methods=["GET"])
@jwt_required()
@swag_from('docs/orders/list_orders.yml')
def get_my_orders():
    current_user = get_jwt_identity()
    print(f"Current user ID: {current_user}")

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Ambil semua orders milik user
            cur.execute("""
                SELECT o.*, COUNT(oi.id) AS total_items
                FROM orders o 
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE o.user_id = %s
                GROUP BY o.id
                ORDER BY o.order_date DESC
            """, (current_user,))
            orders = cur.fetchall()

            # Untuk setiap order, ambil item + produk
            for order in orders:
                cur.execute("""
                    SELECT 
                        oi.product_id, 
                        oi.quantity, 
                        oi.price, 
                        p.name AS product_name, 
                        p.image_url
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                """, (order['id'],))
                items = cur.fetchall()

                # Gabungkan product info dalam item
                for item in items:
                    item['product'] = {
                        'name': item.pop('product_name'),
                        'image_url': item.pop('image_url')
                    }

                order['items'] = items

    return jsonify(orders)

@orders_bp.route("/api/orders/<int:id>", methods=["GET"])
@jwt_required()
@swag_from('docs/orders/get_order.yml')
def get_order(id):
    current_user = get_jwt_identity()
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get order details
            cur.execute("""
                SELECT * FROM orders 
                WHERE id = %s AND user_id = %s
            """, (id, current_user))
            order = cur.fetchone()
            
            if not order:
                return jsonify({"error": "Pesanan tidak ditemukan"}), 404
            
            # Get order items
            cur.execute("""
                SELECT oi.*, p.name as product_name, p.image_url
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (id,))
            order_items = cur.fetchall()
            
            order['items'] = order_items
    
    return jsonify(order)

@orders_bp.route("/api/orders", methods=["POST"])
@jwt_required()
@swag_from('docs/orders/create_order.yml')
def create_order():
    current_user = get_jwt_identity()
    data = request.json
    items = data.get("items", [])
    
    if not items:
        return jsonify({"error": "Items pesanan harus diisi"}), 400
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            total_amount = 0
            
            # Validate items and calculate total
            for item in items:
                product_id = item.get("product_id")
                quantity = item.get("quantity")
                
                if not product_id or not quantity or quantity <= 0:
                    return jsonify({"error": "Product ID dan quantity harus valid"}), 400
                
                # Check product availability
                cur.execute("SELECT price, stock FROM products WHERE id = %s", (product_id,))
                product = cur.fetchone()
                
                if not product:
                    return jsonify({"error": f"Produk dengan ID {product_id} tidak ditemukan"}), 404
                
                if product['stock'] < quantity:
                    return jsonify({"error": f"Stok produk tidak mencukupi. Tersedia: {product['stock']}"}), 400
                
                total_amount += product['price'] * quantity
            
            # Create order
            cur.execute("""
                INSERT INTO orders (user_id, total_amount)
                VALUES (%s, %s)
                RETURNING id, order_date, total_amount, status
            """, (current_user, total_amount))
            
            new_order = cur.fetchone()
            order_id = new_order['id']
            
            # Create order items and update stock
            for item in items:
                product_id = item.get("product_id")
                quantity = item.get("quantity")
                
                # Get current price
                cur.execute("SELECT price FROM products WHERE id = %s", (product_id,))
                price = cur.fetchone()['price']
                
                # Insert order item
                cur.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, product_id, quantity, price))
                
                # Update product stock
                cur.execute("""
                    UPDATE products 
                    SET stock = stock - %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (quantity, product_id))
            
            conn.commit()
    
    return jsonify(new_order), 201

@orders_bp.route("/api/orders/<int:id>/status", methods=["PUT"])
@jwt_required()
@swag_from('docs/orders/update_order_status.yml')
def update_order_status(id):
    current_user = get_jwt_identity()
    data = request.json
    new_status = data.get("status")
    
    if new_status not in ["pending", "paid", "shipped", "cancelled"]:
        return jsonify({"error": "Status tidak valid"}), 400
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if order exists and belongs to user
            cur.execute("SELECT status FROM orders WHERE id = %s AND user_id = %s", (id, current_user))
            order = cur.fetchone()
            
            if not order:
                return jsonify({"error": "Pesanan tidak ditemukan"}), 404
            
            # Only allow certain status transitions
            current_status = order['status']
            if current_status == "shipped" and new_status != "shipped":
                return jsonify({"error": "Pesanan yang sudah dikirim tidak dapat diubah statusnya"}), 400
            
            if current_status == "cancelled":
                return jsonify({"error": "Pesanan yang sudah dibatalkan tidak dapat diubah statusnya"}), 400
            
            # If cancelling, restore stock
            if new_status == "cancelled" and current_status != "cancelled":
                cur.execute("""
                    SELECT oi.product_id, oi.quantity
                    FROM order_items oi
                    WHERE oi.order_id = %s
                """, (id,))
                order_items = cur.fetchall()
                
                for item in order_items:
                    cur.execute("""
                        UPDATE products 
                        SET stock = stock + %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (item['quantity'], item['product_id']))
            
            # Update order status
            cur.execute("""
                UPDATE orders 
                SET status = %s
                WHERE id = %s
                RETURNING id, order_date, total_amount, status
            """, (new_status, id))
            
            updated_order = cur.fetchone()
            conn.commit()
    
    return jsonify(updated_order)