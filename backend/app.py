from flask import Flask
from flask_cors import CORS
from config.settings import Config
from database.connect import init_db
from api.routes import api_bp

def create_app():
    """
    Application factory function that creates and configures the Flask app.
    """
    app = Flask(__name__)

    # Enable CORS for Flutter app
    CORS(app)

    # Configure app
    app.config.from_object(Config)

    # Initialize database
    init_db(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def health_check():
        """Simple health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "endpoints": ["/api/news", "/api/news/update", "/api/news/api-usage"]
        }

    return app