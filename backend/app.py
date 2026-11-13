import logging
import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database.firebase_db import FirestoreManager
from utils.helpers import api_response

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("legalupdate.app")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for all frontend client origins
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize Firestore Database
    with app.app_context():
        FirestoreManager.get_db()

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.source_routes import source_bp
    from routes.update_routes import update_bp
    from routes.scrape_routes import scrape_bp
    from routes.summary_routes import summary_bp
    from routes.review_routes import review_bp
    from routes.memory_routes import memory_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(source_bp)
    app.register_blueprint(update_bp)
    app.register_blueprint(scrape_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(memory_bp)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """System health and integration diagnostic endpoint."""
        return api_response(data={
            "status": "operational",
            "service": "LegalUpdate AI - Regulatory Change Summarizer",
            "version": "1.0.0",
            "python_version": "3.14.2",
            "integrations": {
                "firebase_firestore": {
                    "is_live": FirestoreManager.is_live_firebase(),
                    "mode": "Live Google Cloud Firestore" if FirestoreManager.is_live_firebase() else "Local Firestore State Store"
                },
                "groq_llm": {
                    "is_configured": Config.is_groq_configured(),
                    "model": Config.GROQ_MODEL
                },
                "firecrawl_scraper": {
                    "is_configured": Config.is_firecrawl_configured(),
                    "api_url": Config.FIRECRAWL_API_URL
                },
                "memento_memory": {
                    "storage_path": Config.MEMENTO_STORAGE_PATH,
                    "status": "Active Bitemporal Memory Engine"
                }
            }
        }, message="LegalUpdate AI backend is healthy and running.")

    @app.errorhandler(404)
    def handle_404(e):
        return api_response(error="API route not found.", status_code=404)

    @app.errorhandler(405)
    def handle_405(e):
        return api_response(error="HTTP method not allowed.", status_code=405)

    @app.errorhandler(500)
    def handle_500(e):
        logger.error("Internal server error: %s", e)
        return api_response(error="Internal server error occurred.", status_code=500)

    return app

app = create_app()

if __name__ == "__main__":
    port = Config.PORT
    logger.info("Starting LegalUpdate AI server on port %d...", port)
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)

