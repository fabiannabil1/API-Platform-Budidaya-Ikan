from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from

articles_bp = Blueprint('articles', __name__)

@articles_bp.route("/api/articles", methods=["GET"])
@swag_from('docs/articles/list_articles.yml')
def get_articles():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, u.name as author_name 
                FROM articles a 
                LEFT JOIN users u ON a.author_id = u.id 
                ORDER BY a.created_at DESC
            """)
            articles = cur.fetchall()
    return jsonify(articles)

@articles_bp.route("/api/articles/<int:id>", methods=["GET"])
@swag_from('docs/articles/get_article.yml')
def get_article(id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, u.name as author_name 
                FROM articles a 
                LEFT JOIN users u ON a.author_id = u.id 
                WHERE a.id = %s
            """, (id,))
            article = cur.fetchone()
            
            if not article:
                return jsonify({"error": "Artikel tidak ditemukan"}), 404
                
    return jsonify(article)

@articles_bp.route("/api/articles", methods=["POST"])
@jwt_required()
@swag_from('docs/articles/create_article.yml')
def create_article():
    data = request.json
    title = data.get("title")
    content = data.get("content")
    image_url = data.get("image_url")
    author_id = get_jwt_identity()

    if not title or not content:
        return jsonify({"error": "Judul dan konten harus diisi"}), 400

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO articles (title, content, image_url, author_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id, title, content, image_url, created_at, updated_at
            """, (title, content, image_url, author_id))
            
            new_article = cur.fetchone()
            conn.commit()

    return jsonify(new_article), 201

@articles_bp.route("/api/articles/<int:id>", methods=["PUT"])
@jwt_required()
@swag_from('docs/articles/update_article.yml')
def update_article(id):
    current_user = get_jwt_identity()
    data = request.json
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if article exists and user is the author
            cur.execute("SELECT author_id FROM articles WHERE id = %s", (id,))
            article = cur.fetchone()
            
            if not article:
                return jsonify({"error": "Artikel tidak ditemukan"}), 404
            
            if str(article['author_id']) != current_user:
                return jsonify({"error": "Tidak memiliki izin untuk mengedit artikel ini"}), 403

            # Update article
            cur.execute("""
                UPDATE articles 
                SET title = COALESCE(%s, title),
                    content = COALESCE(%s, content),
                    image_url = COALESCE(%s, image_url),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, title, content, image_url, created_at, updated_at
            """, (data.get("title"), data.get("content"), data.get("image_url"), id))
            
            updated_article = cur.fetchone()
            conn.commit()

    return jsonify(updated_article)

@articles_bp.route("/api/articles/<int:id>", methods=["DELETE"])
@jwt_required()
@swag_from('docs/articles/delete_article.yml')
def delete_article(id):
    current_user = get_jwt_identity()
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if article exists and user is the author
            cur.execute("SELECT author_id FROM articles WHERE id = %s", (id,))
            article = cur.fetchone()
            
            if not article:
                return jsonify({"error": "Artikel tidak ditemukan"}), 404
            
            if str(article['author_id']) != current_user:
                return jsonify({"error": "Tidak memiliki izin untuk menghapus artikel ini"}), 403

            # Delete article
            cur.execute("DELETE FROM articles WHERE id = %s", (id,))
            conn.commit()

    return jsonify({"message": "Artikel berhasil dihapus"}), 200
