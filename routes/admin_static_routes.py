from flask import Blueprint, send_from_directory, current_app
import os

admin_static_bp = Blueprint('admin_static', __name__)

@admin_static_bp.route('/admin/<path:filename>')
def serve_admin_files(filename):
    """Serve admin web interface files"""
    admin_dir = os.path.join(current_app.root_path, '..', 'admin_web')
    return send_from_directory(admin_dir, filename)

@admin_static_bp.route('/admin/')
@admin_static_bp.route('/admin')
def serve_admin_index():
    """Serve admin index page"""
    admin_dir = os.path.join(current_app.root_path, '..', 'admin_web')
    return send_from_directory(admin_dir, 'index.html')