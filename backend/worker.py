import os
import sys
import time
import signal
import uuid
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import Config
from database.firebase_db import FirestoreManager, get_utc_now
from services.firecrawl_service import FirecrawlService
from services.regulatory_service import RegulatoryService
from services.change_detection import ChangeDetectionService
from services.groq_service import GroqSummarizerService
from services.memento_service import MementoMemoryService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [worker] %(message)s"
)
logger = logging.getLogger("legalupdate.worker")

class BackgroundIngestionWorker:
    """
    Render Background Worker Daemon.
    Decouples web scraping, change detection, Groq LLM summarization,
    and Memento memory ingestion from the synchronous web API.
    """

    def __init__(self, poll_interval: int = None):
        self.running = True
        self.poll_interval = poll_interval or Config.WORKER_POLL_INTERVAL
        self.worker_id = f"worker-{os.getpid()}-{uuid.uuid4().hex[:6]}"
        self.db = FirestoreManager.get_db()

        # Handle process termination cleanly
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info("Received shutdown signal (%s). Finishing active jobs and terminating gracefully...", signum)
        self.running = False

    def process_pending_jobs(self) -> int:
        """
        Fetches and processes all pending ingestion jobs.
        Returns the number of jobs processed.
        """
        try:
            query = self.db.collection("ingestion_jobs").where("status", "==", "pending")
            pending_docs = list(query.stream())
        except Exception as e:
            logger.error("Error fetching pending ingestion jobs: %s", e)
            return 0

        if not pending_docs:
            return 0

        logger.info("Found %d pending ingestion job(s) to process.", len(pending_docs))
        processed_count = 0

        for doc_snap in pending_docs:
            if not self.running:
                break
            job_data = doc_snap.to_dict()
            job_id = job_data.get("job_id") or doc_snap.id

            # Step 1: Claim the job atomically
            doc_ref = self.db.collection("ingestion_jobs").document(job_id)
            try:
                doc_ref.update({
                    "status": "processing",
                    "claimed_by": self.worker_id,
                    "claimed_at": get_utc_now(),
                    "updated_at": get_utc_now()
                })
            except Exception as e:
                logger.warning("Could not claim job %s (may have been claimed by another worker): %s", job_id, e)
                continue

            # Step 2: Execute pipeline
            logger.info("[%s] Processing job %s (Source: %s, URL: %s)",
                        self.worker_id, job_id, job_data.get("source_code"), job_data.get("url"))

            try:
                result = self._execute_job(job_data)
                # Mark completed
                doc_ref.update({
                    "status": "completed",
                    "completed_at": get_utc_now(),
                    "result": result,
                    "error": None,
                    "updated_at": get_utc_now()
                })

                # Write log
                self.db.collection("system_logs").add({
                    "event": "job_completed",
                    "job_id": job_id,
                    "worker_id": self.worker_id,
                    "source_code": job_data.get("source_code"),
                    "timestamp": get_utc_now()
                })
                processed_count += 1
                logger.info("[%s] Job %s completed successfully.", self.worker_id, job_id)

            except Exception as e:
                retry_count = job_data.get("retry_count", 0) + 1
                is_failed = retry_count >= 3
                new_status = "failed" if is_failed else "pending"

                logger.error("[%s] Error processing job %s (attempt %d): %s",
                             self.worker_id, job_id, retry_count, e, exc_info=True)

                doc_ref.update({
                    "status": new_status,
                    "retry_count": retry_count,
                    "error": str(e),
                    "updated_at": get_utc_now()
                })

                self.db.collection("system_logs").add({
                    "event": "job_failed" if is_failed else "job_retried",
                    "job_id": job_id,
                    "worker_id": self.worker_id,
                    "error": str(e),
                    "attempt": retry_count,
                    "timestamp": get_utc_now()
                })

        return processed_count

    def _execute_job(self, job_data: dict) -> dict:
        """
        Executes ingestion, change detection, Groq LLM summarization,
        and persistence for a single job.
        """
        source_code = job_data.get("source_code", "RBI")
        target_url = job_data.get("url")
        custom_title = job_data.get("title")
        pre_content = job_data.get("content")

        # If job already has content (e.g. delivered via Firecrawl webhook payload)
        if pre_content and len(pre_content.strip()) > 50:
            title = custom_title or f"{source_code} Official Regulatory Circular"
            pub_date = datetime.today().strftime("%Y-%m-%d")
            doc_id = f"{source_code}/{pub_date[:4]}/{uuid.uuid4().hex[:6].upper()}"

            eval_res = ChangeDetectionService.evaluate_scraped_document(
                source_id=f"src-{source_code.lower()}",
                source_code=source_code,
                title=title,
                url=target_url,
                content=pre_content,
                published_date=pub_date,
                document_id=doc_id
            )

            status = eval_res["status"]
            content_hash = eval_res["content_hash"]

            if status == "UNCHANGED":
                return {
                    "change_status": "UNCHANGED",
                    "message": "Content hash matches existing document. Duplicate avoided.",
                    "update_id": eval_res["existing_update"].get("id")
                }

            # Generate AI Summary
            ai_summary_data = GroqSummarizerService.generate_summary(
                title=title,
                content=pre_content,
                source_url=target_url,
                source_code=source_code,
                document_id=doc_id,
                published_date=pub_date
            )

            update_id = f"upd-{source_code.lower()}-{uuid.uuid4().hex[:8]}"
            now = get_utc_now()

            # Store in Firestore
            self.db.collection("regulatory_updates").document(update_id).set({
                "id": update_id,
                "document_id": doc_id,
                "source_id": f"src-{source_code.lower()}",
                "source_code": source_code,
                "title": title,
                "source_url": target_url,
                "published_date": pub_date,
                "collected_at": now,
                "current_status": "pending_review",
                "version": 1,
                "content": pre_content,
                "content_hash": content_hash,
                "created_at": now,
                "updated_at": now
            })

            # Store version 1
            self.db.collection("document_versions").document(f"ver-{update_id}-1").set({
                "id": f"ver-{update_id}-1",
                "update_id": update_id,
                "version_number": 1,
                "title": title,
                "content": pre_content,
                "content_hash": content_hash,
                "diff": None,
                "created_at": now
            })

            # Store AI Summary
            ai_sum_record = dict(ai_summary_data)
            ai_sum_record["id"] = f"sum-{update_id}"
            ai_sum_record["update_id"] = update_id
            ai_sum_record["created_at"] = now
            ai_sum_record["is_approved"] = False
            self.db.collection("ai_summaries").document(ai_sum_record["id"]).set(ai_sum_record)

            # Store Notification
            self.db.collection("notifications").add({
                "title": f"New Regulatory Circular: {title[:60]}...",
                "regulator": source_code,
                "update_id": update_id,
                "type": "new_circular",
                "read": False,
                "created_at": now
            })

            return {
                "change_status": "NEW",
                "update_id": update_id,
                "document_id": doc_id,
                "title": title
            }
        else:
            # Fall back to full regulatory scraping pipeline
            result = RegulatoryService.ingest_url_or_source(
                source_code=source_code,
                target_url=target_url,
                custom_title=custom_title,
                user_id="background_worker"
            )

            if result.get("success") and result.get("update_id"):
                # Create notification
                self.db.collection("notifications").add({
                    "title": f"New Ingestion Completed: {source_code}",
                    "regulator": source_code,
                    "update_id": result.get("update_id"),
                    "type": "new_circular",
                    "read": False,
                    "created_at": get_utc_now()
                })

            return result

    def run_daemon(self):
        """Continuously polls and executes ingestion jobs."""
        logger.info("=" * 60)
        logger.info("LegalUpdate AI Background Worker started.")
        logger.info("Worker ID:      %s", self.worker_id)
        logger.info("Poll Interval:  %d seconds", self.poll_interval)
        logger.info("Database Mode:  %s", "Live Google Cloud Firestore" if FirestoreManager.is_live_firebase() else "Local Firestore State Store")
        logger.info("=" * 60)

        # Heartbeat counter
        ticks = 0

        while self.running:
            try:
                processed = self.process_pending_jobs()
                if processed > 0:
                    logger.info("Processed %d job(s) in this iteration.", processed)

                ticks += 1
                if ticks % 6 == 0:
                    # Every ~60 seconds log worker health heartbeat
                    logger.info("Worker heartbeat: active and listening for ingestion queue jobs...")

            except Exception as e:
                logger.error("Unhandled error in worker loop: %s", e, exc_info=True)

            # Sleep in 1-second slices so shutdown is instant
            for _ in range(self.poll_interval):
                if not self.running:
                    break
                time.sleep(1)

        logger.info("Worker %s shut down successfully.", self.worker_id)

def main():
    parser = argparse.ArgumentParser(description="LegalUpdate AI Render Background Worker")
    parser.add_argument("--once", action="store_true", help="Process pending queue jobs once and exit immediately.")
    parser.add_argument("--interval", type=int, default=None, help="Poll interval in seconds.")
    args = parser.parse_args()

    worker = BackgroundIngestionWorker(poll_interval=args.interval)
    if args.once:
        logger.info("Running single worker iteration (--once)...")
        count = worker.process_pending_jobs()
        logger.info("Finished single iteration. Processed %d job(s).", count)
    else:
        worker.run_daemon()

if __name__ == "__main__":
    main()
