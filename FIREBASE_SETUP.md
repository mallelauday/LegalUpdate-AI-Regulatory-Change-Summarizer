# LegalUpdate AI — Firebase & Firestore Setup Guide
**Regulatory Change Summarizer & Monitoring Suite**

LegalUpdate AI supports both **Live Google Cloud Firestore** (via `firebase-admin` SDK) and a **Zero-Config Local Firestore State Store** for development and offline testing.

---

## 1. The 12 Production Firestore Collections

The application establishes and manages 12 collections:

1. **`users`**: User profiles with 4-tier roles (`admin`, `senior_reviewer`, `compliance_reviewer`, `viewer`).
2. **`regulatory_sources`**: Registered authorities (RBI, SEBI, MCA, IRDAI) and official crawl URLs.
3. **`monitor_configs`**: 15-minute scheduling configurations, cron strings, and timezone (`Asia/Kolkata`).
4. **`ingestion_jobs`**: Decoupled queue processed by the Render Background Worker (`pending`, `processing`, `completed`, `failed`).
5. **`webhook_events`**: Audit trail of incoming Firecrawl webhook payloads for idempotency.
6. **`regulatory_updates`**: Canonical regulatory circulars, normalized hashes, and metadata.
7. **`document_versions`**: Historical versions and computed unified text diffs.
8. **`ai_summaries`**: 10-point structured Groq LLM analyses with mandatory disclaimers.
9. **`historical_context`**: Bitemporal Memento memory records and legal precedents.
10. **`review_history`**: Immutable human legal review decisions and audit comments.
11. **`notifications`**: Compliance alerts for newly discovered circulars and review tasks.
12. **`system_logs`**: Operational health logs, worker heartbeats, and scraper diagnostics.

---

## 2. Enabling Live Cloud Firestore in Firebase Console

If you see the warning:
> `403 Cloud Firestore API has not been used in project gen-ai-f7848 before or it is disabled`

Follow these simple steps:
1. Open [Firebase Console](https://console.firebase.google.com/project/gen-ai-f7848/firestore).
2. Click **Create database**.
3. Select Database location: **asia-south1 (Mumbai)** or **nam5 (United States)**.
4. Select Security Rules mode: **Start in test mode** (allows read/write during development) or **Production mode**.
5. Click **Enable**.
6. Cloud Firestore is now live! The backend will automatically detect the enabled API and transition from Local Firestore to Live Cloud Firestore with zero code changes.

---

## 3. Configuring Service Account Credentials

1. In Firebase Console, go to **Project Settings** > **Service accounts**.
2. Click **Generate new private key** and download the JSON file.
3. Save it into `backend/` (e.g. `backend/gen-ai-f7848-firebase-adminsdk-fbsvc-f734bc9909.json`).
4. In `backend/.env`, set:
   ```env
   FIREBASE_PROJECT_ID=gen-ai-f7848
   FIREBASE_SERVICE_ACCOUNT_KEY=./gen-ai-f7848-firebase-adminsdk-fbsvc-f734bc9909.json
   ```

---

## 4. Local Firestore Fallback Mode

If the Firebase Admin SDK credentials are missing or the Cloud Firestore API is currently propagating:
- `FirestoreManager` automatically falls back to `LocalFirestoreClient`.
- Data is persisted to `backend/data/local_firestore_db.json`.
- All queries, filters (`where`), sorting (`order_by`), batch operations, and limits run with identical semantics.
- No data is lost, and the application remains 100% functional.
