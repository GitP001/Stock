from flask import Flask
from api.routes import api_bp
from database.connect import init_db

def create_app():
    app = Flask(__name__)
    # Register your Blueprint
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize DB
    init_db(app)

    return app