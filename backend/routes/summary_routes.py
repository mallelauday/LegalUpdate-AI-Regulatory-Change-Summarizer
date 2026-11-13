import logging
from flask import Blueprint, request
from database.firebase_db import FirestoreManager, get_utc_now
from utils.helpers import api_response, token_required, roles_required
from services.groq_service import GroqSummarizerService

logger = logging.getLogger("legalupdate.summaries")
summary_bp = Blueprint("summaries", __name__, url_prefix="/api/summaries")

@summary_bp.route("/<update_id>", methods=["GET"])
@token_required
def get_summary(update_id):
    """Retrieve AI-generated summary for a given regulatory update."""
    db = FirestoreManager.get_db()
    doc_ref = db.collection("ai_summaries").document(f"sum-{update_id}")
    snapshot = doc_ref.get()

    if not snapshot.exists:
        return api_response(error=f"Summary for update {update_id} not found.", status_code=404)

    return api_response(data=snapshot.to_dict(), message="AI summary retrieved.")

@summary_bp.route("/<update_id>/regenerate", methods=["POST"])
@token_required
@roles_required("admin", "reviewer")
def regenerate_summary(update_id):
    """
    Regenerates summary using Groq Llama model with fresh Memento context.
    """
    db = FirestoreManager.get_db()
    upd_snap = db.collection("regulatory_updates").document(update_id).get()

    if not upd_snap.exists:
        return api_response(error=f"Update {update_id} not found.", status_code=404)

    upd_data = upd_snap.to_dict()

    new_summary = GroqSummarizerService.generate_summary(
        title=upd_data.get("title"),
        content=upd_data.get("content", ""),
        source_url=upd_data.get("source_url", ""),
        source_code=upd_data.get("source_code", "CUSTOM"),
        document_id=upd_data.get("document_id", ""),
        published_date=upd_data.get("published_date", "")
    )

    summary_doc = dict(new_summary)
    summary_doc["id"] = f"sum-{update_id}"
    summary_doc["update_id"] = update_id
    summary_doc["created_at"] = get_utc_now()
    summary_doc["is_approved"] = False

    db.collection("ai_summaries").document(summary_doc["id"]).set(summary_doc)

    return api_response(data=summary_doc, message="AI summary regenerated successfully.")

