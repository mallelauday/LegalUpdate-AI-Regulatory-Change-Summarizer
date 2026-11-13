import logging
from flask import Blueprint, request
from database.firebase_db import FirestoreManager
from utils.helpers import api_response, token_required, roles_required
from services.regulatory_service import RegulatoryService

logger = logging.getLogger("legalupdate.reviews")
review_bp = Blueprint("reviews", __name__, url_prefix="/api/reviews")

@review_bp.route("/queue", methods=["GET"])
@token_required
def get_review_queue():
    """Retrieve all updates pending human legal review."""
    db = FirestoreManager.get_db()
    pending = []

    for doc in db.collection("regulatory_updates").where("current_status", "in", ["pending_review", "needs_modification"]).stream():
        pending.append(doc.to_dict())

    pending.sort(key=lambda x: str(x.get("collected_at", "")), reverse=True)
    return api_response(data=pending, message="Pending review queue retrieved.")

@review_bp.route("/<update_id>", methods=["POST"])
@token_required
@roles_required("admin", "reviewer")
def submit_review(update_id):
    """
    Submits human legal review decision:
    Payload: {
      "decision": "approved" | "rejected" | "needs_modification",
      "comments": "Internal legal justification...",
      "edited_summary": "Human refined summary..."
    }
    """
    data = request.get_json() or {}
    decision = data.get("decision")
    comments = data.get("comments", "")
    edited_summary = data.get("edited_summary")

    if not decision:
        return api_response(error="Field 'decision' is required.", status_code=400)

    curr_user = request.current_user
    result = RegulatoryService.apply_human_review(
        update_id=update_id,
        decision=decision,
        reviewer_id=curr_user["sub"],
        reviewer_name=curr_user.get("name", "Reviewer"),
        reviewer_email=curr_user.get("email", ""),
        comments=comments,
        edited_summary=edited_summary
    )

    if not result.get("success"):
        return api_response(error=result.get("error"), status_code=400)

    return api_response(data=result.get("review_record"), message=result.get("message"))

@review_bp.route("/<update_id>/history", methods=["GET"])
@token_required
def get_review_history(update_id):
    """Retrieve audit timeline of all human review decisions for an update."""
    db = FirestoreManager.get_db()
    history = []
    for doc in db.collection("review_history").where("update_id", "==", update_id).stream():
        history.append(doc.to_dict())

    history.sort(key=lambda x: str(x.get("reviewed_at", "")), reverse=True)
    return api_response(data=history, message="Review history audit trail retrieved.")

