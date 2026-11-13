import logging
from flask import Blueprint, request
from database.firebase_db import FirestoreManager
from utils.helpers import api_response, token_required
from services.memento_service import MementoMemoryService

logger = logging.getLogger("legalupdate.memory_routes")
memory_bp = Blueprint("memory", __name__, url_prefix="/api/memory")

@memory_bp.route("/search", methods=["GET"])
@token_required
def search_historical_memories():
    """
    Search historical Memento memory layer across past circulars and approved interpretations.
    Query params: ?q=keywords&regulator=RBI
    """
    q = request.args.get("q", "").strip()
    regulator = request.args.get("regulator", "").strip().upper() or None

    results = MementoMemoryService.search_memories(query_text=q, regulator=regulator)
    return api_response(data=results, message="Historical memories retrieved.")

@memory_bp.route("/<memory_id>", methods=["GET"])
@token_required
def get_memory_detail(memory_id):
    """Retrieve details of a specific Memento historical memory reference."""
    db = FirestoreManager.get_db()
    for doc in db.collection("historical_context").where("memory_id", "==", memory_id).limit(1).stream():
        return api_response(data=doc.to_dict(), message="Memory record retrieved.")

    return api_response(error=f"Memory {memory_id} not found.", status_code=404)

