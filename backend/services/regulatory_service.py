import uuid
import logging
from datetime import datetime, timezone
from database.firebase_db import FirestoreManager, get_utc_now
from services.firecrawl_service import FirecrawlService
from services.change_detection import ChangeDetectionService
from services.groq_service import GroqSummarizerService
from services.memento_service import MementoMemoryService

logger = logging.getLogger("legalupdate.regulatory_service")

class RegulatoryService:
    @classmethod
    def ingest_url_or_source(cls, source_code: str, target_url: str = None,
                              custom_title: str = None, user_id: str = "system") -> dict:
        """
        Orchestrates full regulatory pipeline:
        Scrape (Firecrawl) -> Change Detection -> AI Summary (Groq + Memento) -> Firestore Persistence.
        """
        db = FirestoreManager.get_db()

        # Resolve Source
        source_doc = None
        for doc in db.collection("regulatory_sources").where("source_code", "==", source_code).limit(1).stream():
            source_doc = doc.to_dict()
            break

        url_to_crawl = target_url or (source_doc.get("crawl_url") if source_doc else None)
        if not url_to_crawl:
            return {"success": False, "error": f"No valid URL configured for source '{source_code}'."}

        # Step 1: Scrape content using Firecrawl
        logger.info("Executing scrape for source [%s] on URL: %s", source_code, url_to_crawl)
        scrape_result = FirecrawlService.scrape_url(url_to_crawl)
        if not scrape_result.get("success"):
            return {
                "success": False,
                "error": scrape_result.get("error", "Failed to retrieve page content from target URL"),
                "url": url_to_crawl
            }

        title = custom_title or scrape_result.get("title") or f"{source_code} Official Regulatory Circular"
        content = scrape_result.get("content", "")
        pub_date = scrape_result.get("published_date") or datetime.today().strftime("%Y-%m-%d")

        # Derive Document Identifier
        doc_id = f"{source_code}/{pub_date[:4]}/{uuid.uuid4().hex[:6].upper()}"

        # Step 2: Change Detection
        eval_result = ChangeDetectionService.evaluate_scraped_document(
            source_id=source_doc.get("source_id") if source_doc else source_code,
            source_code=source_code,
            title=title,
            url=url_to_crawl,
            content=content,
            published_date=pub_date,
            document_id=doc_id
        )

        status = eval_result["status"]
        content_hash = eval_result["content_hash"]

        # If document already exists and has not changed
        if status == "UNCHANGED":
            existing = eval_result["existing_update"]
            logger.info("Document already stored with identical content hash: %s. Preventing duplication.", existing.get("id"))
            return {
                "success": True,
                "change_status": "UNCHANGED",
                "message": "Regulatory document already up to date. No modifications detected.",
                "update_id": existing.get("id"),
                "document_id": existing.get("document_id")
            }

        # Step 3: Handle NEW document
        if status == "NEW":
            update_id = f"upd-{source_code.lower()}-{uuid.uuid4().hex[:8]}"

            # Generate AI Summary with Groq & Memento context
            ai_summary_data = GroqSummarizerService.generate_summary(
                title=title,
                content=content,
                source_url=url_to_crawl,
                source_code=source_code,
                document_id=doc_id,
                published_date=pub_date
            )

            # Store in Firestore
            update_record = {
                "id": update_id,
                "document_id": doc_id,
                "source_id": source_doc.get("source_id") if source_doc else f"src-{source_code.lower()}",
                "source_code": source_code,
                "title": title,
                "source_url": url_to_crawl,
                "published_date": pub_date,
                "collected_at": get_utc_now(),
                "current_status": "pending_review",
                "version": 1,
                "content": content,
                "content_hash": content_hash,
                "created_at": get_utc_now(),
                "updated_at": get_utc_now()
            }
            db.collection("regulatory_updates").document(update_id).set(update_record)

            # Store Version 1
            version_record = {
                "id": f"ver-{update_id}-1",
                "update_id": update_id,
                "version_number": 1,
                "title": title,
                "content": content,
                "content_hash": content_hash,
                "diff": None,
                "created_at": get_utc_now()
            }
            db.collection("document_versions").document(version_record["id"]).set(version_record)

            # Store AI Summary
            ai_sum_record = dict(ai_summary_data)
            ai_sum_record["id"] = f"sum-{update_id}"
            ai_sum_record["update_id"] = update_id
            ai_sum_record["created_at"] = get_utc_now()
            ai_sum_record["is_approved"] = False
            db.collection("ai_summaries").document(ai_sum_record["id"]).set(ai_sum_record)

            # Store Historical Memory Context
            hist_ctx = ai_summary_data.get("historical_context_used", {})
            hist_record = {
                "id": f"ctx-{update_id}",
                "memory_id": hist_ctx.get("memory_id", f"mem-{update_id}"),
                "update_id": update_id,
                "document_id": doc_id,
                "regulator": source_code,
                "precedent_ref": hist_ctx.get("precedent_ref", "First Recorded Inception"),
                "precedent_date": hist_ctx.get("precedent_date", pub_date),
                "recalled_context": hist_ctx.get("recalled_insight", "Baseline regulatory standard."),
                "continuity_status": hist_ctx.get("continuity_status", "New Regulation"),
                "valid_time": pub_date,
                "transaction_time": get_utc_now(),
                "entity_tags": [source_code, "Regulatory Change", "Compliance"],
                "created_at": get_utc_now()
            }
            db.collection("historical_context").document(hist_record["id"]).set(hist_record)

            # Update Source timestamp
            if source_doc:
                db.collection("regulatory_sources").document(source_doc.get("id", source_doc.get("source_id"))).update({
                    "last_crawled_at": get_utc_now()
                })

            return {
                "success": True,
                "change_status": "NEW",
                "message": f"Successfully scraped and ingested new regulatory update ({doc_id}).",
                "update_id": update_id,
                "document_id": doc_id,
                "ai_summary": ai_summary_data
            }

        # Step 4: Handle MODIFIED document
        if status == "MODIFIED":
            existing = eval_result["existing_update"]
            update_id = existing["id"]
            current_version = existing.get("version", 1)
            new_version = current_version + 1
            diff_data = eval_result["diff"]

            # Store New Document Version
            version_record = {
                "id": f"ver-{update_id}-{new_version}",
                "update_id": update_id,
                "version_number": new_version,
                "title": title,
                "content": content,
                "content_hash": content_hash,
                "diff": diff_data,
                "created_at": get_utc_now()
            }
            db.collection("document_versions").document(version_record["id"]).set(version_record)

            # Generate Updated AI Summary
            ai_summary_data = GroqSummarizerService.generate_summary(
                title=f"{title} (Amendment / Revision v{new_version})",
                content=content,
                source_url=url_to_crawl,
                source_code=source_code,
                document_id=existing.get("document_id", doc_id),
                published_date=pub_date
            )

            # Update Main Record
            db.collection("regulatory_updates").document(update_id).update({
                "content": content,
                "content_hash": content_hash,
                "version": new_version,
                "current_status": "pending_review",
                "updated_at": get_utc_now()
            })

            # Update AI Summary
            db.collection("ai_summaries").document(f"sum-{update_id}").set(ai_summary_data)

            return {
                "success": True,
                "change_status": "MODIFIED",
                "message": f"Detected modifications to {existing.get('document_id')}. Advanced to version {new_version}.",
                "update_id": update_id,
                "version": new_version,
                "diff": diff_data,
                "ai_summary": ai_summary_data
            }

    @classmethod
    def apply_human_review(cls, update_id: str, decision: str, reviewer_id: str,
                           reviewer_name: str, reviewer_email: str,
                           comments: str = "", edited_summary: str = None) -> dict:
        """
        Executes human review workflow:
        Sets status: 'approved' | 'rejected' | 'needs_modification'.
        If approved, ingests interpretation into Memento historical memory store.
        """
        db = FirestoreManager.get_db()

        # Fetch update
        upd_ref = db.collection("regulatory_updates").document(update_id)
        snapshot = upd_ref.get()
        if not snapshot.exists:
            return {"success": False, "error": f"Update {update_id} not found."}

        update_data = snapshot.to_dict()

        valid_decisions = ("approved", "rejected", "needs_modification", "pending_review")
        if decision not in valid_decisions:
            return {"success": False, "error": f"Invalid review decision '{decision}'. Must be one of {valid_decisions}."}

        # Update status
        upd_ref.update({
            "current_status": decision,
            "updated_at": get_utc_now()
        })

        # Record in review_history
        review_id = f"rev-{update_id}-{uuid.uuid4().hex[:6]}"
        review_record = {
            "id": review_id,
            "update_id": update_id,
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "reviewer_email": reviewer_email,
            "decision": decision,
            "comments": comments,
            "edited_summary": edited_summary,
            "reviewed_at": get_utc_now()
        }
        db.collection("review_history").document(review_id).set(review_record)

        # If edited_summary was submitted, update ai_summaries approval flag and custom text
        if edited_summary or decision == "approved":
            sum_ref = db.collection("ai_summaries").document(f"sum-{update_id}")
            sum_snap = sum_ref.get()
            if sum_snap.exists:
                sum_data = sum_snap.to_dict()
                if edited_summary:
                    sum_data["human_edited_summary"] = edited_summary
                sum_data["is_approved"] = (decision == "approved")
                sum_ref.set(sum_data)

        # Ingest into Memento if approved
        if decision == "approved":
            final_summary = edited_summary or "Approved regulatory summary on file."
            MementoMemoryService.ingest_approved_interpretation(
                update_id=update_id,
                document_id=update_data.get("document_id"),
                regulator=update_data.get("source_code"),
                title=update_data.get("title"),
                approved_summary=final_summary,
                reviewer_comments=comments,
                valid_date=update_data.get("published_date")
            )

        return {
            "success": True,
            "message": f"Review decision '{decision}' recorded successfully.",
            "review_record": review_record
        }

