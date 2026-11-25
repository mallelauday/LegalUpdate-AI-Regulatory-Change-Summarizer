import os
import json
import logging
import requests
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
    
    Integrates directly with:
      - Hosted Memento AGI MCP Service (JSON-RPC over https://api.mementoagi.com/mcp)
      - Google Cloud Firestore / Local Firestore 'historical_context' collection.
    """

    @classmethod
    def _call_mcp_tool(cls, tool_name: str, arguments: dict):
        """Dispatches a JSON-RPC 2.0 tool call to the hosted Memento MCP server."""
        api_key = Config.MEMENTO_API_KEY
        if not api_key or api_key.startswith("your_"):
            return None

        url = Config.MEMENTO_MCP_URL or "https://api.mementoagi.com/mcp"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=4)
            if res.status_code == 200:
                return res.json().get("result", {})
            logger.warning("Hosted Memento MCP returned HTTP %s: %s", res.status_code, res.text[:200])
        except Exception as e:
            logger.warning("Memento MCP tool '%s' timed out or unreachable: %s. Continuing with Firestore memory.", tool_name, e)
        return None

    @classmethod
    def recall_context_for_update(cls, regulator: str, title: str, content: str) -> dict:
        """
        Retrieves relevant historical regulatory context and past approved interpretations.
        Queries both hosted Memento MCP knowledge graph and Firestore historical_context.
        """
        # Step 1: Optional hosted Memento MCP Search
        mcp_insight = None
        try:
            mcp_query = f"{regulator} {title[:80]}"
            mcp_res = cls._call_mcp_tool("full-search", {"query": mcp_query})
            if mcp_res:
                content_items = mcp_res.get("content", [])
                if content_items and isinstance(content_items, list):
                    text_parts = [c.get("text", "") for c in content_items if isinstance(c, dict)]
                    if text_parts:
                        mcp_insight = " ".join(text_parts)[:400]
                        logger.info("Retrieved precedent from hosted Memento MCP: %s...", mcp_insight[:80])
        except Exception as e:
            logger.warning("Hosted Memento search failed: %s", e)

        # Step 2: Query Firestore 'historical_context'
        db = FirestoreManager.get_db()
        memories = []

        try:
            query = db.collection("historical_context").where("regulator", "==", regulator)
            for doc in query.stream():
                memories.append(doc.to_dict())
        except Exception as e:
            logger.error("Error querying Firestore historical_context store: %s", e)

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
            insight_text = top_memory.get("recalled_context") or top_memory.get("recalled_insight")
            if mcp_insight:
                insight_text = f"{insight_text} | Memento MCP Precedent: {mcp_insight}"

            return {
                "has_precedent": True,
                "memory_id": top_memory.get("memory_id"),
                "precedent_ref": top_memory.get("precedent_ref"),
                "precedent_date": top_memory.get("precedent_date"),
                "recalled_insight": insight_text,
                "recalled_context": insight_text,
                "continuity_status": top_memory.get("continuity_status", "Related Regulatory Precedent"),
                "entity_tags": top_memory.get("entity_tags", [regulator])
            }

        # If MCP provided insight even if Firestore was empty
        if mcp_insight:
            return {
                "has_precedent": True,
                "memory_id": f"mcp-{regulator.lower()}",
                "precedent_ref": "Hosted Memento MCP Graph Node",
                "precedent_date": "Historical Precedent",
                "recalled_insight": mcp_insight,
                "recalled_context": mcp_insight,
                "continuity_status": "Active Knowledge Graph Precedent",
                "entity_tags": [regulator, "Hosted Memento"]
            }

        # Fallback synthesized baseline
        return {
            "has_precedent": False,
            "memory_id": f"mem-init-{regulator.lower()}",
            "precedent_ref": "First Recorded Circular in Series",
            "precedent_date": "Not Specified in Archive",
            "recalled_insight": f"No previous amendments or prior conflicting interpretations on file for {regulator} under this specific subject matter.",
            "recalled_context": f"No previous amendments or prior conflicting interpretations on file for {regulator} under this specific subject matter.",
            "continuity_status": "New Regulatory Inception",
            "entity_tags": [regulator, "Baseline Policy"]
        }

    @classmethod
    def ingest_approved_interpretation(cls, update_id: str, document_id: str, regulator: str,
                                      title: str, approved_summary: str, reviewer_comments: str,
                                      valid_date: str) -> dict:
        """
        Ingests a human-approved legal interpretation into:
        1. Google Cloud Firestore / Local Firestore 'historical_context'
        2. Hosted Memento MCP memory store via 'write-node'
        """
        db = FirestoreManager.get_db()
        memory_id = f"mem-{document_id.replace('/', '-').lower()}"
        recalled_text = f"Approved Interpretation: {approved_summary} | Reviewer Guidance: {reviewer_comments}"

        mem_doc = {
            "id": f"ctx-{update_id}",
            "memory_id": memory_id,
            "update_id": update_id,
            "document_id": document_id,
            "regulator": regulator,
            "precedent_ref": document_id,
            "precedent_date": valid_date,
            "recalled_context": recalled_text,
            "recalled_insight": recalled_text,
            "continuity_status": "Human-Approved Precedent",
            "valid_time": valid_date,
            "transaction_time": get_utc_now(),
            "entity_tags": [regulator, "Approved Precedent", "Compliance"],
            "created_at": get_utc_now()
        }

        # 1. Store in Firestore
        try:
            db.collection("historical_context").document(mem_doc["id"]).set(mem_doc)
            logger.info("Ingested memory reference into Firestore: %s", memory_id)
        except Exception as e:
            logger.error("Failed to ingest memory into Firestore: %s", e)

        # 2. Write to Hosted Memento MCP server
        try:
            node_path = f"precedents/{document_id.replace('/', '_').lower()}.md"
            node_content = (
                f"# Regulatory Precedent: {title}\n\n"
                f"- **Regulator:** {regulator}\n"
                f"- **Document ID:** {document_id}\n"
                f"- **Valid Date:** {valid_date}\n"
                f"- **Enacted At:** {get_utc_now()}\n\n"
                f"## Approved Interpretation\n{approved_summary}\n\n"
                f"## Reviewer Guidance & Action Requirements\n{reviewer_comments}\n"
            )
            mcp_res = cls._call_mcp_tool("write-node", {
                "path": node_path,
                "content": node_content
            })
            if mcp_res:
                logger.info("Successfully synchronized precedent to hosted Memento MCP: %s", node_path)
        except Exception as e:
            logger.warning("Could not sync precedent to hosted Memento MCP: %s", e)

        return {"success": True, "memory_id": memory_id}

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
                        data.get("recalled_insight", "") + " " +
                        " ".join(data.get("entity_tags", []))
                    ).lower()
                    if q_lower in haystack:
                        results.append(data)
        except Exception as e:
            logger.error("Error searching Memento memories: %s", e)

        return results
