import logging
import uuid
import datetime
import requests
from config import Config
from database.firebase_db import FirestoreManager, get_utc_now

logger = logging.getLogger("legalupdate.firecrawl_monitor")

class FirecrawlMonitorService:
    """
    Manages automated 15-minute regulatory source monitoring schedules for RBI, SEBI, MCA, and IRDAI.
    Persists monitor states in the 'monitor_configs' Firestore collection.
    """

    DEFAULT_MONITORS = [
        {
            "monitor_id": "mon-rbi",
            "source_code": "RBI",
            "source_id": "src-rbi",
            "name": "Reserve Bank of India (RBI) Monitor",
            "crawl_url": "https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx",
            "schedule": "every 15 minutes",
            "cron": "*/15 * * * *",
            "timezone": "Asia/Kolkata",
            "is_active": True,
            "category": "Banking & Payment Systems",
            "description": "Continuous 15-minute monitoring of RBI circulars, master directions, and regulatory notifications."
        },
        {
            "monitor_id": "mon-sebi",
            "source_code": "SEBI",
            "source_id": "src-sebi",
            "name": "Securities and Exchange Board of India (SEBI) Monitor",
            "crawl_url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&smid=0&ssid=7",
            "schedule": "every 15 minutes",
            "cron": "*/15 * * * *",
            "timezone": "Asia/Kolkata",
            "is_active": True,
            "category": "Capital Markets & Intermediaries",
            "description": "Continuous 15-minute monitoring of SEBI regulatory instructions, LODR amendments, and compliance circulars."
        },
        {
            "monitor_id": "mon-mca",
            "source_code": "MCA",
            "source_id": "src-mca",
            "name": "Ministry of Corporate Affairs (MCA) Monitor",
            "crawl_url": "https://www.mca.gov.in/content/mca/global/en/notifications-circulars/circulars.html",
            "schedule": "every 15 minutes",
            "cron": "*/15 * * * *",
            "timezone": "Asia/Kolkata",
            "is_active": True,
            "category": "Corporate Law & Governance",
            "description": "Continuous 15-minute monitoring of MCA general circulars, statutory rules, and company compliance updates."
        },
        {
            "monitor_id": "mon-irdai",
            "source_code": "IRDAI",
            "source_id": "src-irdai",
            "name": "Insurance Regulatory and Development Authority (IRDAI) Monitor",
            "crawl_url": "https://irdai.gov.in/circulars",
            "schedule": "every 15 minutes",
            "cron": "*/15 * * * *",
            "timezone": "Asia/Kolkata",
            "is_active": True,
            "category": "Insurance Sector",
            "description": "Continuous 15-minute monitoring of IRDAI master circulars, prudential guidelines, and solvency requirements."
        }
    ]

    @classmethod
    def init_monitors(cls, webhook_url: str = None) -> list:
        """
        Initializes or synchronizes the 4 regulatory monitors in Firestore 'monitor_configs'.
        Optionally registers live monitor schedules with the Firecrawl API if configured.
        """
        db = FirestoreManager.get_db()
        coll = db.collection("monitor_configs")
        initialized = []

        now = get_utc_now()
        for default in cls.DEFAULT_MONITORS:
            doc_ref = coll.document(default["monitor_id"])
            doc = doc_ref.get()

            if not doc.exists:
                data = dict(default)
                data["id"] = default["monitor_id"]
                data["webhook_url"] = webhook_url or "/api/webhooks/firecrawl"
                data["last_checked_at"] = now
                # Next run is scheduled 15 minutes from now
                next_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
                data["next_check_at"] = next_dt.isoformat()
                data["created_at"] = now
                data["updated_at"] = now
                data["total_runs"] = 0
                data["detected_changes"] = 0
                doc_ref.set(data)
                initialized.append(data)
                logger.info("Initialized monitor config: %s (%s)", data["name"], data["schedule"])
            else:
                initialized.append(doc.to_dict())

        return initialized

    @classmethod
    def get_monitors(cls) -> list:
        """Returns all configured regulatory monitors."""
        db = FirestoreManager.get_db()
        monitors = [doc.to_dict() for doc in db.collection("monitor_configs").stream()]
        if not monitors:
            return cls.init_monitors()
        return monitors

    @classmethod
    def get_monitor(cls, monitor_id: str):
        """Returns a single monitor configuration."""
        db = FirestoreManager.get_db()
        doc = db.collection("monitor_configs").document(monitor_id).get()
        return doc.to_dict() if doc.exists else None

    @classmethod
    def toggle_monitor(cls, monitor_id: str, is_active: bool = None) -> dict:
        """Toggles or sets the active state of a regulatory monitor."""
        db = FirestoreManager.get_db()
        doc_ref = db.collection("monitor_configs").document(monitor_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {"success": False, "error": f"Monitor {monitor_id} not found."}

        data = doc.to_dict()
        new_status = not data.get("is_active", True) if is_active is None else is_active
        doc_ref.update({
            "is_active": new_status,
            "updated_at": get_utc_now()
        })
        logger.info("Monitor %s status changed to is_active=%s", monitor_id, new_status)
        data["is_active"] = new_status
        return {"success": True, "monitor": data}

    @classmethod
    def trigger_monitor(cls, monitor_id: str = None) -> dict:
        """
        Manually triggers a monitor check, enqueuing an ingestion job for background processing.
        If monitor_id is None, triggers all active monitors.
        """
        db = FirestoreManager.get_db()
        monitors = cls.get_monitors()
        if monitor_id:
            monitors = [m for m in monitors if m.get("monitor_id") == monitor_id or m.get("id") == monitor_id]

        if not monitors:
            return {"success": False, "error": f"No matching monitors found for trigger: {monitor_id}"}

        enqueued_jobs = []
        now = get_utc_now()

        for m in monitors:
            job_id = f"job-{uuid.uuid4().hex[:10]}"
            job_data = {
                "id": job_id,
                "job_id": job_id,
                "monitor_id": m.get("monitor_id") or m.get("id"),
                "source_code": m.get("source_code"),
                "source_id": m.get("source_id"),
                "url": m.get("crawl_url"),
                "type": "scheduled_monitor_check",
                "status": "pending",
                "claimed_by": None,
                "claimed_at": None,
                "created_at": now,
                "completed_at": None,
                "retry_count": 0,
                "error": None
            }
            db.collection("ingestion_jobs").document(job_id).set(job_data)
            enqueued_jobs.append(job_id)

            # Update monitor's last checked timestamp
            db.collection("monitor_configs").document(m.get("monitor_id") or m.get("id")).update({
                "last_checked_at": now,
                "total_runs": m.get("total_runs", 0) + 1,
                "updated_at": now
            })

            # Write system log
            db.collection("system_logs").add({
                "event": "monitor_triggered",
                "monitor_id": m.get("monitor_id") or m.get("id"),
                "job_id": job_id,
                "timestamp": now,
                "source": "FirecrawlMonitorService"
            })

        logger.info("Triggered %d monitor check(s). Jobs enqueued: %s", len(enqueued_jobs), enqueued_jobs)
        return {
            "success": True,
            "enqueued_count": len(enqueued_jobs),
            "job_ids": enqueued_jobs,
            "message": f"Successfully enqueued {len(enqueued_jobs)} background ingestion job(s)."
        }
