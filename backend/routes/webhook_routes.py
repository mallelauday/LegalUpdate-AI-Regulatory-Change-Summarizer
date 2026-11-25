import hmac
import hashlib
import json
import logging
import uuid
from flask import Blueprint, request
from config import Config
from database.firebase_db import FirestoreManager, get_utc_now
from utils.helpers import api_response

logger = logging.getLogger("legalupdate.webhooks")
webhook_bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")

def verify_firecrawl_signature(payload_bytes: bytes, signature_header: str) -> bool:
    """
    Validates HMAC-SHA256 signature from Firecrawl webhook header.
    Header format: sha256=<hex_digest> or direct <hex_digest>
    """
    secret = Config.FIRECRAWL_WEBHOOK_SECRET or Config.SECRET_KEY
    if not secret:
        logger.warning("No webhook secret configured; permitting in development mode.")
        return True

    if not signature_header:
        # In development without external webhook caller, log warning
        if Config.DEBUG:
            logger.warning("Missing x-firecrawl-signature header; allowed because DEBUG=True.")
            return True
        return False

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    clean_header = signature_header.replace("sha256=", "").strip()
    return hmac.compare_digest(clean_header, expected_signature)

@webhook_bp.route("/firecrawl", methods=["POST"])
def handle_firecrawl_webhook():
    """
    Firecrawl Webhook Ingestion Endpoint.
    1. Verifies HMAC-SHA256 signature.
    2. Validates payload and ensures idempotency in 'webhook_events'.
    3. Enqueues job into 'ingestion_jobs' collection for background worker processing.
    4. Immediately responds with 200 OK.
    """
    raw_body = request.get_data()
    sig_header = request.headers.get("x-firecrawl-signature") or request.headers.get("X-Firecrawl-Signature") or ""

    if not verify_firecrawl_signature(raw_body, sig_header):
        logger.error("Firecrawl webhook signature validation failed.")
        return api_response(error="Invalid webhook signature.", status_code=401)

    try:
        payload = request.get_json(force=True) or {}
    except Exception as e:
        logger.error("Failed to parse webhook JSON body: %s", e)
        return api_response(error="Malformed JSON payload.", status_code=400)

    db = FirestoreManager.get_db()
    now = get_utc_now()

    # Deduce unique event ID for idempotency
    event_id = payload.get("id") or payload.get("eventId") or hashlib.sha256(raw_body).hexdigest()[:20]

    # Check for duplicate event
    existing_event = db.collection("webhook_events").document(event_id).get()
    if existing_event.exists:
        logger.info("Webhook event %s already processed (idempotency key matched).", event_id)
        return api_response(
            data={"event_id": event_id, "status": "duplicate"},
            message="Webhook event already processed."
        )

    # Extract source and document data from Firecrawl webhook payload
    # Firecrawl webhook format typically includes data object with url, markdown/html, metadata
    event_data = payload.get("data", payload)
    target_url = event_data.get("url") or payload.get("url") or ""
    page_title = event_data.get("metadata", {}).get("title") or event_data.get("title") or ""
    page_content = event_data.get("markdown") or event_data.get("content") or ""

    # Deduce regulator from URL or source hints
    source_code = "RBI"
    url_lower = target_url.lower()
    if "sebi.gov.in" in url_lower:
        source_code = "SEBI"
    elif "mca.gov.in" in url_lower:
        source_code = "MCA"
    elif "irdai.gov.in" in url_lower:
        source_code = "IRDAI"
    elif "source_code" in payload:
        source_code = payload["source_code"]

    job_id = f"job-wh-{uuid.uuid4().hex[:10]}"

    # Save to webhook_events
    db.collection("webhook_events").document(event_id).set({
        "id": event_id,
        "event_id": event_id,
        "job_id": job_id,
        "source": "firecrawl",
        "source_code": source_code,
        "url": target_url,
        "status": "enqueued",
        "received_at": now
    })

    # Enqueue into ingestion_jobs for Background Worker
    job_record = {
        "id": job_id,
        "job_id": job_id,
        "event_id": event_id,
        "type": "firecrawl_webhook_event",
        "source_code": source_code,
        "url": target_url,
        "title": page_title,
        "content": page_content,
        "status": "pending",
        "claimed_by": None,
        "claimed_at": None,
        "created_at": now,
        "completed_at": None,
        "retry_count": 0,
        "error": None
    }
    db.collection("ingestion_jobs").document(job_id).set(job_record)

    # Record in system_logs
    db.collection("system_logs").add({
        "event": "webhook_received",
        "event_id": event_id,
        "job_id": job_id,
        "source_code": source_code,
        "timestamp": now
    })

    logger.info("Firecrawl webhook ingested and job enqueued: %s (Regulator: %s)", job_id, source_code)
    return api_response(
        data={"job_id": job_id, "event_id": event_id, "status": "enqueued"},
        message="Webhook received and enqueued for background processing.",
        status_code=200
    )
