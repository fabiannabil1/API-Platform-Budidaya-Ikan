from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from

products_bp = Blueprint('products', __name__)

@products_bp.route("/api/products", methods=["GET"])
@swag_from('docs/products/list_products.yml')
def get_products():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT p.*, u.name as created_by_name 
                FROM products p 
                LEFT JOIN users u ON p.created_by = u.id 
                WHERE p.stock > 0
                ORDER BY p.created_at DESC
            """)
            products = cur.fetchall()
    return jsonify(products)

@products_bp.route("/api/products/<int:id>", methods=["GET"])
@swag_from('docs/products/get_product.yml')
def get_product(id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT p.*, u.name as created_by_name 
                FROM products p 
                LEFT JOIN users u ON p.created_by = u.id 
                WHERE p.id = %s
            """, (id,))
            product = cur.fetchone()
            
            if not product:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
                
    return jsonify(product)

@products_bp.route("/api/products", methods=["POST"])
@jwt_required()
@swag_from('docs/products/create_product.yml')
def create_product():
    data = request.json
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    stock = data.get("stock")
    image_url = data.get("image_url")
    created_by = get_jwt_identity()

    if not name or not price or stock is None:
        return jsonify({"error": "Nama, harga, dan stok harus diisi"}), 400

    if price <= 0 or stock < 0:
        return jsonify({"error": "Harga harus lebih dari 0 dan stok tidak boleh negatif"}), 400

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO products (name, description, price, stock, image_url, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, name, description, price, stock, image_url, created_at, updated_at
            """, (name, description, price, stock, image_url, created_by))
            
            new_product = cur.fetchone()
            conn.commit()

    return jsonify(new_product), 201

@products_bp.route("/api/products/<int:id>", methods=["PUT"])
@jwt_required()
@swag_from('docs/products/update_product.yml')
def update_product(id):
    current_user = get_jwt_identity()
    data = request.json
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if product exists and user is the creator
            cur.execute("SELECT created_by FROM products WHERE id = %s", (id,))
            product = cur.fetchone()
            
            if not product:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
            
            if str(product['created_by']) != current_user:
                return jsonify({"error": "Tidak memiliki izin untuk mengedit produk ini"}), 403

            # Validate price and stock if provided
            price = data.get("price")
            stock = data.get("stock")
            
            if price is not None and price <= 0:
                return jsonify({"error": "Harga harus lebih dari 0"}), 400
            
            if stock is not None and stock < 0:
                return jsonify({"error": "Stok tidak boleh negatif"}), 400

            # Update product
            cur.execute("""
                UPDATE products 
                SET name = COALESCE(%s, name),
                    description = COALESCE(%s, description),
                    price = COALESCE(%s, price),
                    stock = COALESCE(%s, stock),
                    image_url = COALESCE(%s, image_url),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, name, description, price, stock, image_url, created_at, updated_at
            """, (data.get("name"), data.get("description"), price, stock, data.get("image_url"), id))
            
            updated_product = cur.fetchone()
            conn.commit()

    return jsonify(updated_product)

@products_bp.route("/api/products/<int:id>", methods=["DELETE"])
@jwt_required()
@swag_from('docs/products/delete_product.yml')
def delete_product(id):
    current_user = get_jwt_identity()
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if product exists and user is the creator
            cur.execute("SELECT created_by FROM products WHERE id = %s", (id,))
            product = cur.fetchone()
            
            if not product:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
            
            if str(product['created_by']) != current_user:
                return jsonify({"error": "Tidak memiliki izin untuk menghapus produk ini"}), 403

            # Delete product
            cur.execute("DELETE FROM products WHERE id = %s", (id,))
            conn.commit()

    return jsonify({"message": "Produk berhasil dihapus"}), 200

@products_bp.route("/api/products/<int:id>/stock", methods=["PUT"])
@jwt_required()
@swag_from('docs/products/update_stock.yml')
def update_stock(id):
    current_user = get_jwt_identity()
    data = request.json
    new_stock = data.get("stock")
    
    if new_stock is None or new_stock < 0:
        return jsonify({"error": "Stok harus diisi dan tidak boleh negatif"}), 400
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if product exists and user is the creator
            cur.execute("SELECT created_by FROM products WHERE id = %s", (id,))
            product = cur.fetchone()
            
            if not product:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
            
            if str(product['created_by']) != current_user:
                return jsonify({"error": "Tidak memiliki izin untuk mengubah stok produk ini"}), 403

            # Update stock
            cur.execute("""
                UPDATE products 
                SET stock = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, name, stock, updated_at
            """, (new_stock, id))
            
            updated_product = cur.fetchone()
            conn.commit()

    return jsonify(updated_product)
