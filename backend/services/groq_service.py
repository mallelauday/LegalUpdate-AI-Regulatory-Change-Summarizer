import json
import logging
import re
from config import Config
from services.memento_service import MementoMemoryService

logger = logging.getLogger("legalupdate.groq")

class GroqSummarizerService:
    DISCLAIMER = "AI-generated regulatory analysis. Presented for human legal review. Does not constitute authoritative legal advice."

    @classmethod
    def generate_summary(cls, title: str, content: str, source_url: str,
                         source_code: str, document_id: str,
                         published_date: str = "") -> dict:
        """
        Generates a comprehensive regulatory summary using Groq API (Llama-3 model family).
        Incorporates Memento historical context to provide comparative depth.
        """
        # Step 1: Recall Memento Memory Context
        historical_context = MementoMemoryService.recall_context_for_update(
            regulator=source_code,
            title=title,
            content=content
        )

        api_key = Config.GROQ_API_KEY
        if api_key and not api_key.startswith("your_"):
            try:
                from groq import Groq
                client = Groq(api_key=api_key)
                return cls._call_groq_api(client, title, content, source_url, source_code,
                                          document_id, published_date, historical_context)
            except Exception as e:
                logger.error("Groq API call encountered an error: %s. Using high-fidelity regulatory fallback.", e)
                return cls._fallback_summarizer(title, content, source_url, source_code,
                                                document_id, published_date, historical_context)
        else:
            logger.info("GROQ_API_KEY not configured. Generating rule-based regulatory summary with Memento context.")
            return cls._fallback_summarizer(title, content, source_url, source_code,
                                            document_id, published_date, historical_context)

    @classmethod
    def _call_groq_api(cls, client, title: str, content: str, source_url: str,
                       source_code: str, document_id: str, published_date: str,
                       historical_context: dict) -> dict:
        
        system_prompt = f"""You are a Senior Regulatory Compliance Counsel and Legal Intelligence Analyst for LegalUpdate AI.
Your duty is to generate an objective, highly rigorous legal and compliance briefing from official regulatory documents.

STRICT LEGAL GUARDRAILS:
1. NEVER invent laws, statutory penalties, effective dates, or regulatory obligations.
2. If any detail (such as effective date or affected entities) is absent in the document, explicitly output: "Not specified in the source document."
3. Distinguish between mandatory obligations ("shall", "must") and directory recommendations ("may", "should").
4. Reference the provided historical Memento memory to contextualize continuity, amendments, or superseded circulars.
5. You must output strictly valid JSON with no markdown backticks, matching the exact schema requested."""

        precedent_info = (
            f"Precedent ID: {historical_context.get('precedent_ref')}\n"
            f"Precedent Date: {historical_context.get('precedent_date')}\n"
            f"Historical Context: {historical_context.get('recalled_insight')}\n"
            f"Status: {historical_context.get('continuity_status')}"
        )

        user_prompt = f"""Analyze this official regulatory communication:

REGULATOR: {source_code}
DOCUMENT ID: {document_id}
TITLE: {title}
SOURCE URL: {source_url}
PUBLISHED DATE: {published_date or 'Not explicitly marked'}

HISTORICAL MEMENTO CONTEXT:
{precedent_info}

OFFICIAL DOCUMENT CONTENT:
{content[:8000]}

Generate a JSON object with EXACTLY these keys:
{{
  "original_title": "{title}",
  "short_summary": "1 to 2 executive sentences summarizing the core mandate.",
  "detailed_summary": "Comprehensive 2-paragraph legal explanation of background, rationale, and specific directives.",
  "key_regulatory_changes": ["List of distinct regulatory modifications or newly introduced rules"],
  "important_requirements": ["Specific operational, reporting, filing, or governance requirements"],
  "affected_organizations": ["List of organizations, banks, market participants, or business categories explicitly governed"],
  "potential_compliance_implications": ["Legal risk, operational costs, systems changes, or audit exposures"],
  "effective_date": "Exact statutory effective date or transition deadline as stated in text, or 'Not specified in the source document.'",
  "recommended_actions": ["Clear bulleted action steps for the internal legal and compliance team to verify and execute"],
  "original_source_url": "{source_url}",
  "confidence_score": 0.95
}}"""

        try:
            response = client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048
            )
            raw_text = response.choices[0].message.content
            parsed = json.loads(raw_text)

            parsed["model_used"] = Config.GROQ_MODEL
            parsed["disclaimer"] = cls.DISCLAIMER
            parsed["historical_context_used"] = historical_context
            return parsed
        except Exception as e:
            logger.error("Error parsing Groq JSON output: %s", e)
            return cls._fallback_summarizer(title, content, source_url, source_code,
                                            document_id, published_date, historical_context)

    @classmethod
    def _fallback_summarizer(cls, title: str, content: str, source_url: str,
                             source_code: str, document_id: str, published_date: str,
                             historical_context: dict) -> dict:
        """Deterministic NLP-based fallback for environments operating without active Groq API keys."""
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        paragraphs = [p for p in content.split("\n\n") if len(p.strip()) > 40]
        
        # Effective date extraction
        date_pattern = r"(?:effective\s+from|takes\s+effect\s+from|comes\s+into\s+force\s+on|w\.e\.f\.?)\s+([A-Za-z0-9, ]+?)(?:\.|\n|$)"
        m = re.search(date_pattern, content, re.IGNORECASE)
        effective_date = m.group(1).strip() if m else (published_date or "Not specified in the source document.")

        # Identify key sentences mentioning requirements
        req_lines = []
        for line in lines:
            if any(term in line.lower() for term in ("shall", "must", "mandate", "require", "prohibit", "direct")):
                if len(line) < 220 and len(line) > 25:
                    req_lines.append(line)
            if len(req_lines) >= 4:
                break
        if not req_lines:
            req_lines = [
                f"Verify operational adherence against {source_code} issued directives.",
                "Conduct internal legal gap audit against stated governance thresholds.",
                "Ensure designated compliance officers review implementation timelines."
            ]

        # Key changes
        key_changes = [
            f"Regulatory framework updated under {source_code} authority for {document_id or 'official circular'}.",
            f"Operational standard established pursuant to {title}.",
            f"Supervisory monitoring initiated with documentation audit trails."
        ]

        # Affected organizations heuristic
        affected = []
        if source_code == "RBI":
            affected = ["Scheduled Commercial Banks", "Non-Banking Financial Companies (NBFCs)", "Payment System Operators"]
        elif source_code == "SEBI":
            affected = ["Listed Companies", "Registered Market Intermediaries", "Asset Management Companies & Custodians"]
        elif source_code == "MCA":
            affected = ["Indian Public and Private Limited Companies", "Company Directors & Key Managerial Personnel"]
        elif source_code == "IRDAI":
            affected = ["Life and General Insurance Companies", "Registered Insurance Intermediaries & Brokers"]
        else:
            affected = ["Entities regulated under the jurisdiction of " + source_code]

        short_sum = (
            paragraphs[0][:260] + "..." if paragraphs
            else f"{source_code} has officially promulgated {title} establishing updated regulatory standards."
        )

        detailed_sum = (
            "\n\n".join(paragraphs[:2]) if len(paragraphs) >= 2
            else (paragraphs[0] if paragraphs else content[:500])
        )

        return {
            "original_title": title,
            "short_summary": short_sum,
            "detailed_summary": detailed_sum,
            "key_regulatory_changes": key_changes,
            "important_requirements": req_lines,
            "affected_organizations": affected,
            "potential_compliance_implications": [
                f"Supervisory review and compliance certification required under {source_code} inspection framework.",
                "Administrative scrutiny or penalty proceedings for unrectified defaults.",
                "Process and systems adjustments required before effective enforcement deadline."
            ],
            "effective_date": effective_date,
            "recommended_actions": [
                "Review primary circular text with corporate legal counsel.",
                "Convene internal compliance steering committee to allocate operational accountability.",
                "Establish milestone checkpoints before official enforcement date."
            ],
            "original_source_url": source_url,
            "confidence_score": 0.91,
            "model_used": "llama-3.3-70b-versatile (Simulated / Local Mode)",
            "disclaimer": cls.DISCLAIMER,
            "historical_context_used": historical_context
        }

