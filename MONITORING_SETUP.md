# LegalUpdate AI — Automated Regulatory Monitoring & Webhooks
**15-Minute Scheduled Monitoring Architecture**

This document details the automated monitoring architecture that allows LegalUpdate AI to discover, diff, summarize, and index official circulars even when the user's computer is switched off.

---

## 1. Monitored Regulatory Authorities

LegalUpdate AI continuously monitors 4 official Indian authorities on a **15-minute schedule** (`*/15 * * * *`, Timezone: `Asia/Kolkata`):

| Regulator | Source Code | Monitored Listing URL | Frequency |
|-----------|-------------|-----------------------|-----------|
| **Reserve Bank of India** | `RBI` | `https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx` | Every 15 min |
| **Securities and Exchange Board of India** | `SEBI` | `https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&smid=0&ssid=7` | Every 15 min |
| **Ministry of Corporate Affairs** | `MCA` | `https://www.mca.gov.in/content/mca/global/en/notifications-circulars/circulars.html` | Every 15 min |
| **Insurance Regulatory & Development Authority** | `IRDAI` | `https://irdai.gov.in/circulars` | Every 15 min |

---

## 2. Webhook Ingestion (`POST /api/webhooks/firecrawl`)

When Firecrawl crawls a monitored URL or detects page modifications, it emits an HTTP POST request to:

```
https://<YOUR_RENDER_URL>/api/webhooks/firecrawl
```

### Signature Verification:
- Header: `x-firecrawl-signature: sha256=<hex>`
- The backend verifies HMAC-SHA256 against `FIRECRAWL_WEBHOOK_SECRET` in constant time (`hmac.compare_digest`).

### Idempotency:
- Every event ID is checked against the `webhook_events` Firestore collection.
- Duplicate event transmissions are detected and safely acknowledged without triggering duplicate jobs.

### Fast Response:
- The webhook endpoint validates the payload, logs the event, creates a job in `ingestion_jobs` with status `pending`, and immediately returns `200 OK`.
- Web scraping, LLM calls, and diffing never block the webhook response.

---

## 3. Render Background Worker (`worker.py`)

The background worker runs as an independent daemon (or container) on Render:

1. **Job Claim:** Polls `ingestion_jobs` where `status == "pending"`, setting `status = "processing"` and `claimed_by = "worker-<pid>"`.
2. **Extraction:** Uses Firecrawl API (with domestic fallback) to extract clean markdown text and dates.
3. **Change Detection:** Computes normalized SHA-256 hash. If unchanged, marks duplicate avoided. If modified, calculates additions/deletions and unified diffs.
4. **Historical Precedents:** Calls hosted **Memento AGI MCP** (`full-search`) and queries `historical_context` for past circular precedents.
5. **AI Summarization:** Calls **Groq LLM** (`llama-3.3-70b-versatile` / `openai/gpt-oss-120b`) producing a 10-point JSON summary with legal disclaimers.
6. **Persistence:** Atomically commits to `regulatory_updates`, `document_versions`, `ai_summaries`, `notifications`, and `system_logs`.
7. **Completion:** Marks job `completed` with full audit metadata.

---

## 4. Monitoring Management Endpoints

- `GET /api/monitoring/status`: Live counts of active monitors and worker queue status.
- `GET /api/monitoring/sources`: Lists the 4 monitors, schedules, URLs, and last run timestamps.
- `POST /api/monitoring/trigger`: Manually triggers an immediate check.
- `POST /api/monitoring/:monitor_id/toggle`: Pauses or resumes a monitor.
- `GET /api/monitoring/jobs`: Lists recent background ingestion jobs.
