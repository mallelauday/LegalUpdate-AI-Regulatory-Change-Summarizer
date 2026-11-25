# LegalUpdate AI — Production Deployment Guide
**Regulatory Change Summarizer & Monitoring Suite**

This guide provides end-to-end production deployment instructions for LegalUpdate AI across **Render** (Web Service + Background Worker) and **Vercel** (React Frontend).

---

## Architecture Overview

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

## 1. Prerequisites

Before deploying, ensure you have:
1. **GitHub Repository:** The complete codebase pushed to GitHub.
2. **Render Account:** [https://render.com](https://render.com).
3. **Vercel Account:** [https://vercel.com](https://vercel.com).
4. **Firebase Account:** [https://console.firebase.google.com](https://console.firebase.google.com) with Firestore enabled.
5. **API Keys:**
   - Groq API Key (`your_groq_api_key`)
   - Firecrawl API Key (`your_firecrawl_api_key`)
   - Memento API Key (`your_memento_api_key`)

---

## 2. Deploying Backend to Render via Blueprint

The repository contains a native `render.yaml` Blueprint file that provisions both required backend services automatically:
1. **`legalupdate-ai-api`** (Web Service: Flask + Gunicorn)
2. **`legalupdate-ai-worker`** (Background Worker: `python worker.py`)

### Step-by-Step Render Deployment:
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** > **Blueprint**.
3. Connect your GitHub repository.
4. Render will parse `render.yaml` and display the two services.
5. Configure the secret environment variables in the prompt:
   - `GROQ_API_KEY`: Your Groq API key.
   - `FIRECRAWL_API_KEY`: Your Firecrawl API key.
   - `MEMENTO_API_KEY`: Your Memento API key.
   - `FIREBASE_PROJECT_ID`: e.g. `gen-ai-f7848`.
   - `FIREBASE_SERVICE_ACCOUNT_KEY`: Path or content of your service account.
6. Click **Apply**.
7. Render will build and deploy both services:
   - Web service will be available at: `https://legalupdate-ai-api.onrender.com`
   - Background worker will start listening to the queue.

### Manual Configuration on Render (Alternative):
If not using the Blueprint:
#### Web Service:
- **Name:** `legalupdate-ai-api`
- **Environment:** `Python 3`
- **Build Command:** `cd backend && pip install -r requirements.txt`
- **Start Command:** `cd backend && gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT app:app`

#### Background Worker:
- **Name:** `legalupdate-ai-worker`
- **Environment:** `Python 3`
- **Build Command:** `cd backend && pip install -r requirements.txt`
- **Start Command:** `cd backend && python worker.py`

---

## 3. Deploying Frontend to Vercel

The frontend is a Vite + React application configured for Vercel deployment with client-side SPA routing (`vercel.json`).

### Step-by-Step Vercel Deployment:
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** > **Project**.
3. Import your GitHub repository.
4. Set **Root Directory** to `frontend`.
5. Build settings will auto-detect:
   - **Framework Preset:** `Vite`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
6. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://legalupdate-ai-api.onrender.com/api`
7. Click **Deploy**.
8. Your frontend will be live at `https://legalupdate-ai.vercel.app`.

---

## 4. Configuring Firecrawl Webhooks

To receive automated crawl alerts from Firecrawl directly into your live Render Web Service:
1. Log in to [Firecrawl Dashboard](https://firecrawl.dev).
2. Navigate to **Webhooks** or **Monitors**.
3. Enter Webhook Target URL:
   ```
   https://legalupdate-ai-api.onrender.com/api/webhooks/firecrawl
   ```
4. Copy the Webhook Secret and set it as `FIRECRAWL_WEBHOOK_SECRET` in your Render Web Service environment variables.

---

## 5. Local Demonstration with Ngrok

To demonstrate the application locally or present to stakeholders:
1. **Start Backend Server:**
   ```powershell
   cd backend
   python app.py
   ```
2. **Start Background Worker (in separate terminal):**
   ```powershell
   cd backend
   python worker.py
   ```
3. **Start Frontend (in separate terminal):**
   ```powershell
   cd frontend
   npm run dev
   ```
4. **Expose Local Backend via Ngrok:**
   ```powershell
   ngrok http 5000
   ```
5. Use the forwarding HTTPS URL provided by Ngrok as the webhook target or API base.
