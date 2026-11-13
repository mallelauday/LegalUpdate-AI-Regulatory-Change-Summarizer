import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from config import Config
from database.firebase_db import FirestoreManager, get_utc_now

logger = logging.getLogger("legalupdate.memento")

class MementoMemoryService:
    """
    Memento Historical Memory Integration Layer.
    
    Architecture Note:
    Implements a bitemporal memory model tracking:
      1. valid_time: The date/period when a regulatory rule was enacted/valid.
      2. transaction_time: The timestamp when the compliance team ingested/reviewed it.
    
    Provides persistent context retrieval across regulatory circulars, amendment chains,
    and prior approved legal interpretations. Integrates with Firestore 'historical_context'
    and supports modular connection to hosted Memento / MCP memory servers.
    """

    @classmethod
    def recall_context_for_update(cls, regulator: str, title: str, content: str) -> dict:
        """
        Retrieves relevant historical regulatory context and past approved interpretations.
        """
        db = FirestoreManager.get_db()
        memories = []

        try:
            # Query memories matching regulator
            query = db.collection("historical_context").where("regulator", "==", regulator)
            for doc in query.stream():
                memories.append(doc.to_dict())
        except Exception as e:
            logger.error("Error querying Memento memory store: %s", e)

        # Keyword matching across memories for relevance ranking
        keywords = [w.lower() for w in (title + " " + content[:500]).split() if len(w) > 4]
        scored_memories = []

        for mem in memories:
            score = 0
            insight = mem.get("recalled_context") or mem.get("recalled_insight", "")
            text_corpus = (
                insight + " " +
                mem.get("precedent_ref", "") + " " +
                " ".join(mem.get("entity_tags", []))
            ).lower()

            for kw in keywords:
                if kw in text_corpus:
                    score += 1

            scored_memories.append((score, mem))

        scored_memories.sort(key=lambda x: x[0], reverse=True)

        if scored_memories and (scored_memories[0][0] > 0 or len(memories) > 0):
            top_memory = scored_memories[0][1]
            return {
                "has_precedent": True,
                "memory_id": top_memory.get("memory_id"),
                "precedent_ref": top_memory.get("precedent_ref"),
                "precedent_date": top_memory.get("precedent_date"),
                "recalled_insight": top_memory.get("recalled_context") or top_memory.get("recalled_insight"),
                "continuity_status": top_memory.get("continuity_status", "Related Regulatory Precedent"),
                "entity_tags": top_memory.get("entity_tags", [regulator])
            }

        # Fallback synthesized context if no direct predecessor was previously ingested
        return {
            "has_precedent": False,
            "memory_id": f"mem-init-{regulator.lower()}",
            "precedent_ref": "First Recorded Circular in Series",
            "precedent_date": "Not Specified in Archive",
            "recalled_insight": f"No previous amendments or prior conflicting interpretations on file for {regulator} under this specific subject matter.",
            "continuity_status": "New Regulatory Inception",
            "entity_tags": [regulator, "Baseline Policy"]
        }

    @classmethod
    def ingest_approved_interpretation(cls, update_id: str, document_id: str, regulator: str,
                                      title: str, approved_summary: str, reviewer_comments: str,
                                      valid_date: str) -> dict:
        """
        Ingests a human-approved legal interpretation into Memento memory store for future LLM recall.
        """
        db = FirestoreManager.get_db()
        memory_id = f"mem-{document_id.replace('/', '-').lower()}"
        
        mem_doc = {
            "id": f"ctx-{update_id}",
            "memory_id": memory_id,
            "update_id": update_id,
            "document_id": document_id,
            "regulator": regulator,
            "precedent_ref": document_id,
            "precedent_date": valid_date,
            "recalled_context": f"Approved Interpretation: {approved_summary} | Reviewer Guidance: {reviewer_comments}",
            "continuity_status": "Human-Approved Precedent",
            "valid_time": valid_date,
            "transaction_time": get_utc_now(),
            "entity_tags": [regulator, "Approved Precedent", "Compliance"],
            "created_at": get_utc_now()
        }

        try:
            db.collection("historical_context").document(mem_doc["id"]).set(mem_doc)
            logger.info("Ingested memory reference into Memento store: %s", memory_id)
            return {"success": True, "memory_id": memory_id}
        except Exception as e:
            logger.error("Failed to ingest memory reference: %s", e)
            return {"success": False, "error": str(e)}

    @classmethod
    def search_memories(cls, query_text: str, regulator: str = None) -> list:
        """Search historical memories across all regulators or a filtered regulator."""
        db = FirestoreManager.get_db()
        results = []
        try:
            coll = db.collection("historical_context")
            stream = coll.stream()
            q_lower = query_text.lower() if query_text else ""

            for doc in stream:
                data = doc.to_dict()
                if regulator and data.get("regulator") != regulator:
                    continue
                if not q_lower:
                    results.append(data)
                else:
                    haystack = (
                        data.get("document_id", "") + " " +
                        data.get("precedent_ref", "") + " " +
                        data.get("recalled_context", "") + " " +
                        " ".join(data.get("entity_tags", []))
                    ).lower()
                    if q_lower in haystack:
                        results.append(data)
        except Exception as e:
            logger.error("Error searching Memento memories: %s", e)

        return results

