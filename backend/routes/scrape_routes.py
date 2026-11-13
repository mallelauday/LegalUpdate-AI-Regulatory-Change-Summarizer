import logging
from flask import Blueprint, request
from utils.helpers import api_response, token_required, roles_required
from services.firecrawl_service import FirecrawlService
from services.change_detection import ChangeDetectionService
from services.regulatory_service import RegulatoryService

logger = logging.getLogger("legalupdate.scrape")
scrape_bp = Blueprint("scrape", __name__, url_prefix="/api/scrape")

@scrape_bp.route("/url", methods=["POST"])
@token_required
@roles_required("admin", "reviewer")
def scrape_custom_url():
    """
    Ingest and summarize a regulatory circular directly from a user-supplied URL.
    Payload: {"url": "...", "source_code": "RBI", "custom_title": "..."}
    """
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    source_code = data.get("source_code", "CUSTOM").strip().upper()
    custom_title = data.get("custom_title")

    if not url:
        return api_response(error="Target URL is required.", status_code=400)

    user_id = request.current_user["sub"]
    result = RegulatoryService.ingest_url_or_source(
        source_code=source_code,
        target_url=url,
        custom_title=custom_title,
        user_id=user_id
    )

    if not result.get("success"):
        return api_response(error=result.get("error", "Scrape failed."), status_code=400)

    return api_response(data=result, message=result.get("message", "URL processed successfully."))

@scrape_bp.route("/preview", methods=["POST"])
@token_required
def preview_scrape():
    """
    Extracts content using Firecrawl without saving to Firestore,
    allowing legal counsel to inspect extracted markdown and metadata.
    """
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return api_response(error="URL is required for preview.", status_code=400)

    scraped = FirecrawlService.scrape_url(url)
    return api_response(data=scraped, message="Preview extracted successfully.")

