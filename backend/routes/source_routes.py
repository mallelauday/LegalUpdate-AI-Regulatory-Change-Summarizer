import uuid
import logging
from flask import Blueprint, request
from database.firebase_db import FirestoreManager, get_utc_now
from utils.helpers import api_response, token_required, roles_required
from services.regulatory_service import RegulatoryService

logger = logging.getLogger("legalupdate.sources")
source_bp = Blueprint("sources", __name__, url_prefix="/api/sources")

@source_bp.route("", methods=["GET"])
@token_required
def list_sources():
    """List all regulatory sources."""
    db = FirestoreManager.get_db()
    sources = []
    for doc in db.collection("regulatory_sources").stream():
        sources.append(doc.to_dict())
    return api_response(data=sources, message="Regulatory sources retrieved.")

@source_bp.route("", methods=["POST"])
@token_required
@roles_required("admin")
def create_source():
    """Add a new official regulatory source (Admin only)."""
    data = request.get_json() or {}
    source_code = data.get("source_code", "").strip().upper()
    name = data.get("name", "").strip()
    base_url = data.get("base_url", "").strip()
    crawl_url = data.get("crawl_url", "").strip()

    if not source_code or not name or not crawl_url:
        return api_response(error="source_code, name, and crawl_url are required fields.", status_code=400)

    db = FirestoreManager.get_db()
    # Check duplicate
    for doc in db.collection("regulatory_sources").where("source_code", "==", source_code).limit(1).stream():
        return api_response(error=f"Source with code '{source_code}' already exists.", status_code=409)

    source_id = f"src-{source_code.lower()}"
    new_source = {
        "source_id": source_id,
        "source_code": source_code,
        "name": name,
        "jurisdiction": data.get("jurisdiction", "India"),
        "regulator_type": data.get("regulator_type", "Statutory Regulatory Authority"),
        "base_url": base_url,
        "crawl_url": crawl_url,
        "category": data.get("category", "General Regulatory Oversight"),
        "is_active": data.get("is_active", True),
        "crawl_frequency_minutes": int(data.get("crawl_frequency_minutes", 60)),
        "last_crawled_at": None,
        "created_at": get_utc_now(),
        "description": data.get("description", "")
    }

    db.collection("regulatory_sources").document(source_id).set(new_source)
    return api_response(data=new_source, message="Regulatory source added successfully.", status_code=201)

@source_bp.route("/<source_id>", methods=["PUT"])
@token_required
@roles_required("admin")
def update_source(source_id):
    """Update regulatory source configuration (Admin only)."""
    data = request.get_json() or {}
    db = FirestoreManager.get_db()
    doc_ref = db.collection("regulatory_sources").document(source_id)

    if not doc_ref.get().exists:
        return api_response(error=f"Source {source_id} not found.", status_code=404)

    allowed_updates = ["name", "base_url", "crawl_url", "category", "is_active",
                       "crawl_frequency_minutes", "description", "regulator_type"]
    update_data = {k: v for k, v in data.items() if k in allowed_updates}
    update_data["updated_at"] = get_utc_now()

    doc_ref.update(update_data)
    return api_response(message="Source configuration updated.")

@source_bp.route("/<source_id>/crawl", methods=["POST"])
@token_required
@roles_required("admin", "reviewer")
def trigger_crawl(source_id):
    """Trigger an immediate live crawl for this regulatory source."""
    db = FirestoreManager.get_db()
    doc_ref = db.collection("regulatory_sources").document(source_id)
    snapshot = doc_ref.get()

    if not snapshot.exists:
        return api_response(error=f"Source {source_id} not found.", status_code=404)

    source_data = snapshot.to_dict()
    result = RegulatoryService.ingest_url_or_source(
        source_code=source_data.get("source_code"),
        target_url=source_data.get("crawl_url"),
        user_id=request.current_user["sub"]
    )

    if not result.get("success"):
        return api_response(error=result.get("error"), status_code=400)

    return api_response(data=result, message=result.get("message"))

