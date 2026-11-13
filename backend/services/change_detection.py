import hashlib
import difflib
import logging
from datetime import datetime, timezone
from database.firebase_db import FirestoreManager, get_utc_now

logger = logging.getLogger("legalupdate.change_detection")

class ChangeDetectionService:
    @staticmethod
    def generate_hash(text: str) -> str:
        if not text:
            return ""
        normalized = " ".join(text.split()).strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def evaluate_scraped_document(cls, source_id: str, source_code: str,
                                  title: str, url: str, content: str,
                                  published_date: str = "",
                                  document_id: str = "") -> dict:
        """
        Evaluates a scraped document against stored Firestore records:
        Returns:
          - "status": "NEW" | "MODIFIED" | "UNCHANGED"
          - "diff": Diff breakdown if modified
          - "existing_update": Existing Firestore record if present
          - "content_hash": Computed content hash
        """
        db = FirestoreManager.get_db()
        content_hash = cls.generate_hash(content)

        # Step 1: Check existing updates by URL or Document ID
        updates_coll = db.collection("regulatory_updates")
        existing_doc = None

        if document_id:
            for doc in updates_coll.where("document_id", "==", document_id).limit(1).stream():
                existing_doc = doc.to_dict()
                break

        if not existing_doc and url:
            for doc in updates_coll.where("source_url", "==", url).limit(1).stream():
                existing_doc = doc.to_dict()
                break

        if not existing_doc:
            # Entirely new regulatory document
            return {
                "status": "NEW",
                "content_hash": content_hash,
                "existing_update": None,
                "diff": None
            }

        # Step 2: Compare content hash
        stored_hash = existing_doc.get("content_hash", "")
        if stored_hash == content_hash:
            return {
                "status": "UNCHANGED",
                "content_hash": content_hash,
                "existing_update": existing_doc,
                "diff": None
            }

        # Step 3: Content has changed -> compute unified diff
        old_content = existing_doc.get("content", "")
        diff_info = cls.compute_diff(old_content, content)

        return {
            "status": "MODIFIED",
            "content_hash": content_hash,
            "existing_update": existing_doc,
            "diff": diff_info
        }

    @staticmethod
    def compute_diff(old_text: str, new_text: str) -> dict:
        old_lines = (old_text or "").splitlines()
        new_lines = (new_text or "").splitlines()

        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile="Prior Version",
            tofile="Revised Version",
            lineterm=""
        ))

        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "has_changes": additions > 0 or deletions > 0,
            "additions": additions,
            "deletions": deletions,
            "diff_lines": diff[:250],
            "computed_at": get_utc_now()
        }

