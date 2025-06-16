from flask import Blueprint, request, jsonify, current_app, url_for, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from
from werkzeug.utils import secure_filename
from datetime import datetime
import os

products_bp = Blueprint('products', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@products_bp.route('/uploads/products/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['PRODUCT_FOLDER'], filename)

@products_bp.route("/api/products", methods=["GET"])
@swag_from('docs/products/list_products.yml')
def get_products():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT p.*, u.name as created_by_name 
                FROM products p 
                LEFT JOIN users u ON p.created_by = u.id 
                WHERE p.stock > 0 AND (p.is_deleted IS NULL OR p.is_deleted = FALSE)
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
                WHERE p.id = %s AND (p.is_deleted IS NULL OR p.is_deleted = FALSE)
            """, (id,))
            product = cur.fetchone()
            
            if not product:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
                
    return jsonify(product)

@products_bp.route("/api/products", methods=["POST"])
@jwt_required()
@swag_from('docs/products/create_product.yml')
def create_product():
    if request.content_type.startswith('application/json'):
        data = request.get_json()
        file = None
    elif request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        file = request.files.get("image")
    else:
        return jsonify({"error": "Content-Type tidak didukung"}), 415

    name = data.get("name")
    description = data.get("description")
    price = float(data.get("price", 0))
    stock = int(data.get("stock", 0))
    created_by = get_jwt_identity()

    if not name or not price or stock is None:
        return jsonify({"error": "Nama, harga, dan stok harus diisi"}), 400

    if price <= 0 or stock < 0:
        return jsonify({"error": "Harga harus lebih dari 0 dan stok tidak boleh negatif"}), 400

    # Handle image upload
    image_url = None
    if file:
        if allowed_file(file.filename):
            filename = f"{datetime.utcnow().timestamp()}_{secure_filename(file.filename)}"
            save_path = os.path.join(current_app.config['PRODUCT_FOLDER'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            image_url = request.host_url.rstrip('/') + url_for('.uploaded_file', filename=filename)
        else:
            return jsonify({"error": "Tipe file tidak diperbolehkan"}), 400
    else:
        image_url = data.get("image_url")  # Fallback to image_url if no file uploaded

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
    
    if request.content_type.startswith('application/json'):
        data = request.get_json()
        file = None
    elif request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        file = request.files.get("image")
    else:
        return jsonify({"error": "Content-Type tidak didukung"}), 415
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if product exists and user is the creator
            cur.execute("SELECT created_by FROM products WHERE id = %s AND (is_deleted IS NULL OR is_deleted = FALSE)", (id,))
            product = cur.fetchone()
            
            if not product:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
            
            if str(product['created_by']) != current_user:
                return jsonify({"error": "Tidak memiliki izin untuk mengedit produk ini"}), 403

            # Validate price and stock if provided
            price = float(data.get("price", 0)) if data.get("price") else None
            stock = int(data.get("stock", 0)) if data.get("stock") else None
            
            if price is not None and price <= 0:
                return jsonify({"error": "Harga harus lebih dari 0"}), 400
            
            if stock is not None and stock < 0:
                return jsonify({"error": "Stok tidak boleh negatif"}), 400

            # Handle image upload
            image_url = None
            if file:
                if allowed_file(file.filename):
                    filename = f"{datetime.utcnow().timestamp()}_{secure_filename(file.filename)}"
                    save_path = os.path.join(current_app.config['PRODUCT_FOLDER'], filename)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    file.save(save_path)
                    image_url = request.host_url.rstrip('/') + url_for('.uploaded_file', filename=filename)
                else:
                    return jsonify({"error": "Tipe file tidak diperbolehkan"}), 400
            else:
                image_url = data.get("image_url")  # Fallback to image_url if no file uploaded

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
            """, (data.get("name"), data.get("description"), price, stock, image_url, id))
            
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
            cur.execute("SELECT created_by FROM products WHERE id = %s AND (is_deleted IS NULL OR is_deleted = FALSE)", (id,))
            product = cur.fetchone()
            
            if not product:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
            
            if str(product['created_by']) != current_user:
                return jsonify({"error": "Tidak memiliki izin untuk menghapus produk ini"}), 403

            # Soft delete product by setting is_deleted to TRUE
            cur.execute("UPDATE products SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (id,))
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
            cur.execute("SELECT created_by FROM products WHERE id = %s AND (is_deleted IS NULL OR is_deleted = FALSE)", (id,))
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
