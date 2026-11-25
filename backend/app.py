import logging
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from database.firebase_db import FirestoreManager
from utils.helpers import api_response, token_required

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

    # Initialize Firestore Database and Regulatory Monitors
    with app.app_context():
        FirestoreManager.get_db()
        try:
            from services.firecrawl_monitor_service import FirecrawlMonitorService
            FirecrawlMonitorService.init_monitors()
        except Exception as e:
            logger.warning("Could not pre-initialize Firecrawl monitors: %s", e)

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.source_routes import source_bp
    from routes.update_routes import update_bp
    from routes.scrape_routes import scrape_bp
    from routes.summary_routes import summary_bp
    from routes.review_routes import review_bp
    from routes.memory_routes import memory_bp
    from routes.webhook_routes import webhook_bp
    from routes.monitoring_routes import monitoring_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(source_bp)
    app.register_blueprint(update_bp)
    app.register_blueprint(scrape_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(memory_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(monitoring_bp)

    # Root and API Health Check
    def get_health_data():
        return {
            "status": "operational",
            "service": "LegalUpdate AI - Regulatory Change Summarizer",
            "version": "1.0.0",
            "python_version": "3.14.2",
            "monitoring_schedule": "every 15 minutes (Asia/Kolkata)",
            "monitored_authorities": ["RBI", "SEBI", "MCA", "IRDAI"],
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
                    "api_url": Config.FIRECRAWL_API_URL,
                    "webhook_endpoint": "/api/webhooks/firecrawl"
                },
                "memento_memory": {
                    "storage_path": Config.MEMENTO_STORAGE_PATH,
                    "mcp_url": Config.MEMENTO_MCP_URL,
                    "status": "Active Bitemporal Memory Engine with Hosted MCP"
                }
            }
        }

    @app.route("/health", methods=["GET"])
    def root_health_check():
        """Top-level health check endpoint for Render / health monitors."""
        return api_response(data=get_health_data(), message="LegalUpdate AI backend is healthy and operational.")

    @app.route("/api/health", methods=["GET"])
    def api_health_check():
        """API namespace health check endpoint."""
        return api_response(data=get_health_data(), message="LegalUpdate AI backend is healthy and operational.")

    # Route Aliases required by prompt specifications
    @app.route("/api/regulatory-updates", methods=["GET"])
    @token_required
    def alias_regulatory_updates():
        """Alias for /api/updates (list regulatory updates)."""
        from routes.update_routes import list_updates
        return list_updates()

    @app.route("/api/ai-summaries", methods=["GET"])
    @token_required
    def alias_ai_summaries():
        """Alias for listing all AI summaries."""
        db = FirestoreManager.get_db()
        summaries = [doc.to_dict() for doc in db.collection("ai_summaries").stream()]
        return api_response(data=summaries, message="AI summaries retrieved.")

    @app.route("/api/historical-context", methods=["GET"])
    @token_required
    def alias_historical_context():
        """Alias for querying historical context memories."""
        from services.memento_service import MementoMemoryService
        query_text = request.args.get("query", "")
        regulator = request.args.get("regulator", "")
        memories = MementoMemoryService.search_memories(query_text, regulator)
        return api_response(data=memories, message="Historical context memories retrieved.")

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
