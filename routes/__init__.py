from .auth_routes import auth_bp
from .auctions_routes import auction_bp
from .bids_routes import bids_bp
from .welcome import welcome_bp
from .articles_routes import articles_bp
from .products_routes import products_bp
from .profiles_routes import profiles_bp
from .orders_routes import orders_bp
from .location_routes import location_bp
from .message_routes import chat_bp
from .fish_freshness import fish_detection_bp
from .change_role_routes import change_role_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(auction_bp)
    app.register_blueprint(bids_bp)
    app.register_blueprint(welcome_bp)
    app.register_blueprint(articles_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(fish_detection_bp)
    app.register_blueprint(change_role_bp)
