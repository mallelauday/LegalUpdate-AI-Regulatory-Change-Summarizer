# LegalUpdate AI — REST API Documentation
**Regulatory Change Summarizer & Monitoring Suite**

- **Base URL (Local):** `http://127.0.0.1:5000`
- **Base URL (Render Production):** `https://legalupdate-ai-api.onrender.com`
- **Authentication:** Bearer JWT Token (`Authorization: Bearer <token>`)

---

## Standard Response Format

All responses follow a consistent envelope structure:

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {},
  "error": null,
  "meta": { "total": 1, "page": 1, "limit": 20 }
}
```

---

## 1. System Health & Diagnostics

### `GET /health` / `GET /api/health`
Top-level health diagnostic for container probes and uptime monitors.
- **Access:** Public
- **Response:**
  ```json
  {
    "success": true,
    "data": {
      "status": "operational",
      "service": "LegalUpdate AI - Regulatory Change Summarizer",
      "version": "1.0.0",
      "python_version": "3.14.2",
      "monitoring_schedule": "every 15 minutes (Asia/Kolkata)",
      "monitored_authorities": ["RBI", "SEBI", "MCA", "IRDAI"],
      "integrations": {
        "firebase_firestore": { "is_live": true, "mode": "Live Google Cloud Firestore" },
        "groq_llm": { "is_configured": true, "model": "llama-3.3-70b-versatile" },
        "firecrawl_scraper": { "is_configured": true, "webhook_endpoint": "/api/webhooks/firecrawl" },
        "memento_memory": { "status": "Active Bitemporal Memory Engine with Hosted MCP" }
      }
    }
  }
  ```

---

## 2. Authentication & Users

### `POST /api/auth/login`
Authenticates a user and returns a 7-day signed JWT session token.
- **Payload:**
  ```json
  {
    "email": "admin@legalupdate.ai",
    "password": "admin123"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "data": {
      "token": "eyJhbGciOi...",
      "user": {
        "uid": "usr-admin-01",
        "email": "admin@legalupdate.ai",
        "display_name": "Sarah Jenkins",
        "role": "admin",
        "department": "Legal & Regulatory Compliance Head"
      }
    }
  }
  ```

### `GET /api/auth/me`
Retrieves currently authenticated user details.
- **Access:** Authenticated

### `GET /api/auth/users`
Lists all user accounts.
- **Access:** `admin` only

---

## 3. Regulatory Updates & Change Management

### `GET /api/updates` (Alias: `GET /api/regulatory-updates`)
Lists regulatory updates with search, filtering, and pagination.
- **Query Parameters:**
  - `regulator`: `RBI` | `SEBI` | `MCA` | `IRDAI`
  - `status`: `pending_review` | `approved` | `rejected` | `needs_modification`
  - `search`: Keyword string
  - `page`: Integer (default 1)
  - `limit`: Integer (default 20)

### `GET /api/updates/stats`
Dashboard aggregate metrics and regulator coverage breakdown.

### `GET /api/updates/:update_id`
Retrieves a single update, its versions, and its AI summary.

### `GET /api/updates/:update_id/versions`
Retrieves all historical versions and unified text diffs for a document.

---

## 4. Automated 15-Minute Monitoring & Ingestion Queue

### `GET /api/monitoring/status`
Returns live status of the 4 regulatory monitors and the background worker queue.
- **Response:**
  ```json
  {
    "success": true,
    "data": {
      "monitoring_engine": "Firecrawl 15-Minute Regulatory Monitor",
      "schedule": "every 15 minutes",
      "timezone": "Asia/Kolkata",
      "total_monitors": 4,
      "active_monitors": 4,
      "worker_queue": {
        "pending": 0,
        "processing": 0,
        "completed": 14,
        "failed": 0
      },
      "monitors": [...]
    }
  }
  ```

### `GET /api/monitoring/sources`
Returns monitor configurations for RBI, SEBI, MCA, and IRDAI.

### `POST /api/monitoring/trigger`
Manually triggers an immediate monitor run.
- **Access:** `admin`, `senior_reviewer`, `compliance_reviewer`
- **Payload:** `{"monitor_id": "mon-rbi"}` (or empty for all 4)

### `POST /api/monitoring/:monitor_id/toggle`
Pauses or resumes a monitor.
- **Access:** `admin`, `senior_reviewer`
- **Payload:** `{"is_active": false}`

---

## 5. Firecrawl Webhooks

### `POST /api/webhooks/firecrawl`
Incoming webhook endpoint for Firecrawl crawler and monitor notifications.
- **Headers:**
  - `x-firecrawl-signature`: `sha256=<HMAC_HEX_DIGEST>`
- **Payload:**
  ```json
  {
    "id": "wh-event-827361",
    "url": "https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx?Id=12999",
    "data": {
      "title": "Master Direction on Digital Payment Security",
      "markdown": "Mandatory controls for scheduled commercial banks...",
      "metadata": { "publishedDate": "2026-11-20" }
    }
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "data": { "job_id": "job-wh-09a27c1f", "status": "enqueued" },
    "message": "Webhook received and enqueued for background processing."
  }
  ```

---

## 6. Human Legal Review Workflow

### `GET /api/reviews/queue`
Retrieves items pending human review (`pending_review` or `needs_modification`).

### `POST /api/reviews/:update_id`
Submits a human legal review decision.
- **Access:** `admin`, `senior_reviewer`, `compliance_reviewer`
- **Payload:**
  ```json
  {
    "decision": "approved",
    "comments": "Confirmed compliance timeline with Risk Committee.",
    "edited_summary": "Optional refined executive text..."
  }
  ```
- **Side Effect:** Automatically synchronizes the approved precedent into Google Cloud Firestore and the hosted **Memento AGI MCP** knowledge graph (`write-node`).

### `GET /api/reviews/:update_id/history`
Returns immutable audit log of reviews for a document.

---

## 7. Memento Historical Memory

### `GET /api/memory/search` (Alias: `GET /api/historical-context`)
Searches past regulatory precedents and approved interpretations.
- **Query Parameters:**
  - `query`: Keyword string
  - `regulator`: `RBI` | `SEBI` | `MCA` | `IRDAI`
