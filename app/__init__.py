from routes import register_routes
from .extensions import jwt, cors, swagger
from flask import Flask
from .config import Config
import os

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'photos')  # misal folder upload
AUCTION_FOLDER = os.path.join(os.getcwd(), 'uploads', 'auctions')  # misal folder auction
PROFILE_FOLDER = os.path.join(os.getcwd(), 'uploads', 'profiles')  # misal folder auction



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['AUCTION_FOLDER'] = AUCTION_FOLDER
    app.config['PROFILE_FOLDER'] = PROFILE_FOLDER

    cors.init_app(app)
    jwt.init_app(app)
    swagger.init_app(app)

    register_routes(app)

    return app
