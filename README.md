# LegalUpdate AI — Regulatory Change Summarizer & Monitoring Suite

[![Python 3.14.2](https://img.shields.io/badge/Python-3.14.2-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![React 19](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61dafb.svg)](https://react.dev/)
[![Groq LLM](https://img.shields.io/badge/AI%20Model-Groq%20Llama--3-orange.svg)](https://groq.com/)
[![Firecrawl](https://img.shields.io/badge/Scraping-Firecrawl%20v1-red.svg)](https://firecrawl.dev/)
[![Memento MCP](https://img.shields.io/badge/Memory-Hosted%20Memento%20MCP-purple.svg)](https://mementoagi.com/)
[![Firebase Firestore](https://img.shields.io/badge/Database-Firebase%20Firestore-yellow.svg)](https://firebase.google.com/)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed%20(100%25)-success.svg)](./TESTING.md)

**LegalUpdate AI** is an enterprise-grade Generative AI regulatory intelligence and compliance monitoring platform. It continuously tracks official regulatory circulars from **RBI**, **SEBI**, **MCA**, and **IRDAI** on an automated **15-minute schedule**, detects modifications via normalized SHA-256 hashing, retrieves precedent context from **hosted Memento AGI MCP**, synthesizes 10-point structured legal summaries using **Groq LLM (Llama-3 70B)**, and supports human legal counsel review workflows.

---

## 1. System Architecture & Workflow

```
                                      ┌───────────────────────────────┐
                                      │   Firecrawl Scheduled Crawl   │
                                      │  (15-min interval Asia/Cal)   │
                                      └──────────────┬────────────────┘
                                                     │ Webhook POST
                                                     ▼
┌─────────────────────────┐             ┌───────────────────────────────┐
│     Vercel Frontend     │             │       Render Web Service      │
│  React 19 + Vite (SPA)  │─── REST ───▶│    Flask API + CORS           │
│  Auto-polling Dashboard │             │    /api/webhooks/firecrawl    │
└─────────────────────────┘             └──────────────┬────────────────┘
                                                       │ Enqueues job
                                                       ▼
                                        ┌───────────────────────────────┐
                                        │   Firestore Ingestion Queue   │
                                        │     ('ingestion_jobs')        │
                                        └──────────────┬────────────────┘
                                                       │ Claims job
                                                       ▼
                                        ┌───────────────────────────────┐
                                        │    Render Background Worker   │
                                        │          (worker.py)          │
                                        ├───────────────────────────────┤
                                        │ 1. Firecrawl Scraper          │
                                        │ 2. Change Detection (SHA-256) │
                                        │ 3. Hosted Memento AGI MCP     │
                                        │ 4. Groq LLM (Llama-3 70B)     │
                                        │ 5. Firestore Persistence      │
                                        └───────────────────────────────┘
```

---

## 2. Core Features & Capabilities

1. **Automated 15-Minute Monitoring & Firecrawl Webhooks:**
   - 4 official Indian authorities monitored on a 15-minute cadence (`Asia/Kolkata`):
     - **Reserve Bank of India (RBI):** Master Directions, prudential norms, digital lending guidelines.
     - **Securities and Exchange Board of India (SEBI):** LODR circulars, mutual fund guidelines, disclosure mandates.
     - **Ministry of Corporate Affairs (MCA):** Companies Act statutory rules, CSR amendments, significant beneficial ownership.
     - **Insurance Regulatory & Development Authority (IRDAI):** Solvency margins, policyholder protection guidelines.
   - Secure webhook receiver (`POST /api/webhooks/firecrawl`) with HMAC-SHA256 signature verification and idempotency protection.

2. **Decoupled Background Processing (Render Background Worker):**
   - Webhooks enqueue jobs into `ingestion_jobs` collection.
   - Dedicated daemon (`worker.py`) claims jobs atomically, diffs content, queries Memento, runs Groq summarization, and updates Firestore without blocking web API response times.

3. **Zero-Hallucination Groq LLM Summarization:**
   - Powered by `llama-3.3-70b-versatile` with automatic fallback to high-capacity Groq completion models.
   - Structured 10-point JSON output: short summary, detailed legal background, key changes, mandatory obligations, affected organizations, compliance implications, effective date (or explicit disclosure of missing data), and recommended counsel actions.
   - Prominent non-authoritative AI disclaimer on every output.

4. **Hosted Memento AGI MCP Precedent Memory:**
   - Direct integration with hosted Memento MCP JSON-RPC service (`https://api.mementoagi.com/mcp`).
   - `full-search` queries historical precedents to contextualize regulatory continuity.
   - `write-node` persists approved legal interpretations to knowledge graph nodes for future recall.

5. **12 Production Firestore Collections:**
   - `users`, `regulatory_sources`, `monitor_configs`, `ingestion_jobs`, `webhook_events`, `regulatory_updates`, `document_versions`, `ai_summaries`, `historical_context`, `review_history`, `notifications`, `system_logs`.
   - Dual-mode `FirestoreManager`: Live Google Cloud Firestore with zero-config Local Firestore fallback.

6. **4-Tier Role-Based Access Control (RBAC):**
   - `admin`: Complete source, monitor, and user management.
   - `senior_reviewer`: Full review queue approval, edits, and monitor management.
   - `compliance_reviewer`: Review queue verification and comments.
   - `viewer`: Read-only intelligence exploration and export.

7. **Production Executive React Dashboard:**
   - React 19 + Vite with 10 responsive pages styled in executive Navy/Slate.
   - 20-second automated polling for real-time live ingestion updates.
   - Side-by-side unified diff viewer, AI summary inspector, and review modal.

---

## 3. Technology Stack

| Component | Technology | Version / Provider | Purpose |
|---|---|---|---|
| **Programming Language** | Python | `3.14.2` | Core backend runtime and computational logic |
| **Backend Framework** | Flask & Flask-CORS | `3.1.3` / `6.0.5` | Modular REST API server and routing |
| **Frontend Framework** | React.js (Vite) | `React 19.x` / `Vite 6.x` | Modern reactive dashboard client |
| **Frontend Styling** | Modern CSS | Custom Navy/Slate Theme | Responsive, executive legal dashboard aesthetic |
| **AI Model** | Groq API | `llama-3.3-70b-versatile` | Ultra-low latency, high-reasoning legal summarization |
| **Web Scraping** | Firecrawl API | Firecrawl v1 REST / Webhooks | Automated crawling and clean markdown extraction |
| **Database** | Firebase Firestore | `google-cloud-firestore 2.34+` | Real-time NoSQL persistent document database |
| **Authentication** | Firebase Auth / JWT | Firebase Admin SDK / PyJWT | Token verification and 4-tier role authorization |
| **Historical Memory** | Memento AGI MCP | Hosted JSON-RPC 2.0 Engine | Bitemporal precedent retrieval and continuity |
| **Backend Hosting** | Render | Web Service + Background Worker | Production cloud hosting and decoupled queuing |
| **Frontend Hosting** | Vercel | Static SPA Hosting | High-speed global edge network deployment |

---

## 4. Environment Variables Reference

Copy `backend/.env.example` to `backend/.env` and configure your credentials:

```bash
# Server Environment
PORT=5000
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=your-flask-secret-key-change-in-production
JWT_SECRET=your-jwt-signing-secret-change-in-production

# Firebase Firestore & Authentication
FIREBASE_SERVICE_ACCOUNT_KEY=./firebase-service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# Groq LLM API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Firecrawl Web Scraping & Scheduled Monitoring
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
FIRECRAWL_API_URL=https://api.firecrawl.dev/v1
FIRECRAWL_WEBHOOK_SECRET=your_firecrawl_webhook_secret_here

# Memento Historical Memory (Hosted MCP & Local Store)
MEMENTO_API_KEY=your_memento_api_key_here
MEMENTO_STORAGE_PATH=./data/memento_store
MEMENTO_MCP_URL=https://api.mementoagi.com/mcp

# Background Worker Settings
WORKER_POLL_INTERVAL=10
```

---

## 5. Quick Start (Local Execution)

### Prerequisites
- **Python 3.14.2** installed: `python --version`
- **Node.js 20+** and **npm** installed: `node --version`, `npm --version`

### Step 1: Start Flask Backend Server
Open **Windows PowerShell** in `backend/`:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
*Backend runs on `http://127.0.0.1:5000`.*

### Step 2: Start Background Worker (In a separate terminal)
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python worker.py
```
*Worker actively polls `ingestion_jobs` and executes background tasks.*

### Step 3: Start React Frontend (In a separate terminal)
```powershell
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:3000`.*

---

## 6. One-Click Demonstration Accounts

The platform includes pre-seeded demonstration accounts with role-based permissions:

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Admin** | `admin@legalupdate.ai` | `admin123` | Full access: Source management, monitors, users, review |
| **Senior Reviewer** | `senior.counsel@legalupdate.ai` | `review123` | Counsel sign-off, text editing, precedent indexing |
| **Compliance Reviewer** | `compliance.officer@legalupdate.ai` | `review123` | Compliance review verification and comments |
| **Analyst (Viewer)** | `analyst@legalupdate.ai` | `viewer123` | Read-only access to briefings, diffs, and search |

---

## 7. Cloud Deployment Guides

- **Render (Web Service + Background Worker):** Configured via [render.yaml](./render.yaml). See [DEPLOYMENT.md](./DEPLOYMENT.md).
- **Vercel (React Frontend):** Configured via [vercel.json](./frontend/vercel.json). See [DEPLOYMENT.md](./DEPLOYMENT.md).
- **Firebase Firestore Setup:** See [FIREBASE_SETUP.md](./FIREBASE_SETUP.md).
- **15-Minute Monitoring Setup:** See [MONITORING_SETUP.md](./MONITORING_SETUP.md).
- **REST API Reference:** See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md).
- **Automated Test Suite (15 Tests):** See [TESTING.md](./TESTING.md).

---

## 8. License & Compliance Disclaimer

*LegalUpdate AI is designed exclusively for legal and compliance decision support. AI-generated analyses do not constitute authoritative legal advice. All regulatory interpretations require verification by qualified legal counsel prior to formal reliance.*
