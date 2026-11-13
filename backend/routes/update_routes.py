import logging
from flask import Blueprint, request
from database.firebase_db import FirestoreManager
from utils.helpers import api_response, token_required

logger = logging.getLogger("legalupdate.updates")
update_bp = Blueprint("updates", __name__, url_prefix="/api/updates")

@update_bp.route("/stats", methods=["GET"])
@token_required
def get_dashboard_stats():
    """Retrieve aggregate statistics for the dashboard overview."""
    db = FirestoreManager.get_db()

    updates = [doc.to_dict() for doc in db.collection("regulatory_updates").stream()]
    sources = [doc.to_dict() for doc in db.collection("regulatory_sources").stream()]

    total_updates = len(updates)
    pending_reviews = sum(1 for u in updates if u.get("current_status") == "pending_review")
    approved_updates = sum(1 for u in updates if u.get("current_status") == "approved")
    rejected_updates = sum(1 for u in updates if u.get("current_status") == "rejected")
    needs_mod = sum(1 for u in updates if u.get("current_status") == "needs_modification")

    # Group by regulator
    by_regulator = {}
    for u in updates:
        code = u.get("source_code", "OTHER")
        by_regulator[code] = by_regulator.get(code, 0) + 1

    active_sources = sum(1 for s in sources if s.get("is_active", True))

    return api_response(data={
        "total_updates": total_updates,
        "pending_reviews": pending_reviews,
        "approved_updates": approved_updates,
        "rejected_updates": rejected_updates,
        "needs_modification": needs_mod,
        "active_sources": active_sources,
        "by_regulator": by_regulator,
        "recent_activity": updates[:5]
    }, message="Dashboard statistics retrieved.")

@update_bp.route("", methods=["GET"])
@token_required
def list_updates():
    """
    List regulatory updates with search, regulator filtering, status filtering, and pagination.
    """
    db = FirestoreManager.get_db()
    regulator = request.args.get("regulator")
    status = request.args.get("status")
    search = request.args.get("search", "").strip().lower()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    all_updates = [doc.to_dict() for doc in db.collection("regulatory_updates").stream()]

    # Filter
    filtered = []
    for u in all_updates:
        if regulator and u.get("source_code") != regulator:
            continue
        if status and u.get("current_status") != status:
            continue
        if search:
            haystack = (
                u.get("title", "") + " " +
                u.get("document_id", "") + " " +
                u.get("content", "")[:300]
            ).lower()
            if search not in haystack:
                continue
        filtered.append(u)

    # Sort descending by published_date / collected_at
    filtered.sort(key=lambda x: str(x.get("published_date") or x.get("collected_at", "")), reverse=True)

    total_count = len(filtered)
    start = (page - 1) * limit
    paginated = filtered[start:start + limit]

    return api_response(
        data=paginated,
        meta={
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1
        },
        message="Regulatory updates retrieved."
    )

@update_bp.route("/<update_id>", methods=["GET"])
@token_required
def get_update_detail(update_id):
    """Retrieve comprehensive details of a single regulatory update."""
    db = FirestoreManager.get_db()
    doc_ref = db.collection("regulatory_updates").document(update_id)
    snapshot = doc_ref.get()

    if not snapshot.exists:
        return api_response(error=f"Update {update_id} not found.", status_code=404)

    update_data = snapshot.to_dict()

    # Fetch AI Summary
    summary_snap = db.collection("ai_summaries").document(f"sum-{update_id}").get()
    summary_data = summary_snap.to_dict() if summary_snap.exists else None

    # Fetch Document Versions
    versions = []
    for v_doc in db.collection("document_versions").where("update_id", "==", update_id).stream():
        versions.append(v_doc.to_dict())
    versions.sort(key=lambda x: x.get("version_number", 1), reverse=True)

    # Fetch Historical Context (Memento)
    hist_snap = db.collection("historical_context").document(f"ctx-{update_id}").get()
    hist_data = hist_snap.to_dict() if hist_snap.exists else None

    # Fetch Review History
    reviews = []
    for r_doc in db.collection("review_history").where("update_id", "==", update_id).stream():
        reviews.append(r_doc.to_dict())
    reviews.sort(key=lambda x: x.get("reviewed_at", ""), reverse=True)

    payload = {
        "update": update_data,
        "ai_summary": summary_data,
        "versions": versions,
        "historical_context": hist_data,
        "reviews": reviews
    }

    return api_response(data=payload, message="Update details retrieved.")

@update_bp.route("/<update_id>/versions", methods=["GET"])
@token_required
def get_update_versions(update_id):
    """Retrieve version history and text diffs for a regulatory update."""
    db = FirestoreManager.get_db()
    versions = []
    for doc in db.collection("document_versions").where("update_id", "==", update_id).stream():
        versions.append(doc.to_dict())

    versions.sort(key=lambda x: x.get("version_number", 1), reverse=True)
    return api_response(data=versions, message="Version history retrieved.")

