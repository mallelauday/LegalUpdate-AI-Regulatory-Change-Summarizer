import logging
from flask import Blueprint, request
from services.firecrawl_monitor_service import FirecrawlMonitorService
from database.firebase_db import FirestoreManager
from utils.helpers import api_response, token_required, roles_required

logger = logging.getLogger("legalupdate.monitoring_routes")
monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/api/monitoring")

@monitoring_bp.route("/status", methods=["GET"])
@token_required
def get_monitoring_status():
    """
    Returns live monitoring system health, active 15-minute monitor counts,
    and ingestion queue statistics.
    """
    db = FirestoreManager.get_db()
    monitors = FirecrawlMonitorService.get_monitors()

    jobs = [doc.to_dict() for doc in db.collection("ingestion_jobs").stream()]
    pending_jobs = sum(1 for j in jobs if j.get("status") == "pending")
    processing_jobs = sum(1 for j in jobs if j.get("status") == "processing")
    completed_jobs = sum(1 for j in jobs if j.get("status") == "completed")
    failed_jobs = sum(1 for j in jobs if j.get("status") == "failed")

    active_monitors = sum(1 for m in monitors if m.get("is_active", True))

    return api_response(data={
        "monitoring_engine": "Firecrawl 15-Minute Regulatory Monitor",
        "schedule": "every 15 minutes",
        "timezone": "Asia/Kolkata",
        "total_monitors": len(monitors),
        "active_monitors": active_monitors,
        "worker_queue": {
            "pending": pending_jobs,
            "processing": processing_jobs,
            "completed": completed_jobs,
            "failed": failed_jobs,
            "total_jobs": len(jobs)
        },
        "monitors": monitors
    }, message="Monitoring status retrieved.")

@monitoring_bp.route("/sources", methods=["GET"])
@token_required
def get_monitored_sources():
    """Returns the list of 4 monitored regulatory sources and their schedules."""
    monitors = FirecrawlMonitorService.get_monitors()
    return api_response(data=monitors, message="Monitored sources retrieved.")

@monitoring_bp.route("/trigger", methods=["POST"])
@token_required
@roles_required("admin", "senior_reviewer", "compliance_reviewer", "reviewer")
def trigger_monitor_run():
    """Manually triggers a monitor run for all or a specific monitor."""
    body = request.get_json(silent=True) or {}
    monitor_id = body.get("monitor_id")

    result = FirecrawlMonitorService.trigger_monitor(monitor_id)
    if result.get("success"):
        return api_response(data=result, message=result.get("message"))
    return api_response(error=result.get("error"), status_code=400)

@monitoring_bp.route("/<monitor_id>/toggle", methods=["POST"])
@token_required
@roles_required("admin", "senior_reviewer", "reviewer")
def toggle_monitor(monitor_id):
    """Pause or resume an automated monitor."""
    body = request.get_json(silent=True) or {}
    is_active = body.get("is_active")

    result = FirecrawlMonitorService.toggle_monitor(monitor_id, is_active)
    if result.get("success"):
        return api_response(data=result.get("monitor"), message="Monitor state updated.")
    return api_response(error=result.get("error"), status_code=400)

@monitoring_bp.route("/jobs", methods=["GET"])
@token_required
def list_ingestion_jobs():
    """Lists recent background ingestion and monitoring jobs."""
    db = FirestoreManager.get_db()
    jobs = [doc.to_dict() for doc in db.collection("ingestion_jobs").stream()]
    # Sort reverse by created_at
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return api_response(data=jobs[:50], message="Recent ingestion jobs retrieved.")
