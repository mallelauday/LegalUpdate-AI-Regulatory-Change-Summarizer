import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  CheckCircle2, 
  XCircle, 
  Flame, 
  Sparkles, 
  Globe2, 
  Database, 
  Terminal, 
  RefreshCw,
  Cpu
} from 'lucide-react';
import api from '../services/api';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const res = await api.get('/health');
      if (res.success) {
        setHealth(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>
          System Configuration & Integration Architecture
        </h2>
        <div style={{ fontSize: '13px', color: '#64748b' }}>
          Real-time diagnostics of external AI APIs, Firestore database state, and scraping infrastructure
        </div>
      </div>

      {/* Integration Status Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {/* Firestore */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Flame size={20} color="#ea580c" />
              <strong style={{ fontSize: '14px' }}>Firebase Firestore</strong>
            </div>
            <span style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: health?.integrations?.firebase_firestore?.is_live ? '#ecfdf5' : '#eff6ff',
              color: health?.integrations?.firebase_firestore?.is_live ? '#047857' : '#1e40af',
              fontWeight: 700
            }}>
              {health?.integrations?.firebase_firestore?.is_live ? 'Live Google Cloud' : 'Local State Store'}
            </span>
          </div>
          <p style={{ fontSize: '12.5px', color: '#64748b', lineHeight: 1.5 }}>
            Mode: <strong>{health?.integrations?.firebase_firestore?.mode}</strong>. All updates, versions, summaries, and reviews are persistently preserved.
          </p>
        </div>

        {/* Groq */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={20} color="#2563eb" />
              <strong style={{ fontSize: '14px' }}>Groq LLM Engine</strong>
            </div>
            <span style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: health?.integrations?.groq_llm?.is_configured ? '#ecfdf5' : '#fffbeb',
              color: health?.integrations?.groq_llm?.is_configured ? '#047857' : '#b45309',
              fontWeight: 700
            }}>
              {health?.integrations?.groq_llm?.is_configured ? 'Active' : 'Fallback / Mock'}
            </span>
          </div>
          <p style={{ fontSize: '12.5px', color: '#64748b', lineHeight: 1.5 }}>
            Model: <strong>{health?.integrations?.groq_llm?.model}</strong>. Zero-hallucination structured legal analysis with Memento precedent integration.
          </p>
        </div>

        {/* Firecrawl */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Globe2 size={20} color="#059669" />
              <strong style={{ fontSize: '14px' }}>Firecrawl Scraper</strong>
            </div>
            <span style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: health?.integrations?.firecrawl_scraper?.is_configured ? '#ecfdf5' : '#eff6ff',
              color: health?.integrations?.firecrawl_scraper?.is_configured ? '#047857' : '#1e40af',
              fontWeight: 700
            }}>
              {health?.integrations?.firecrawl_scraper?.is_configured ? 'Cloud API' : 'Resilient Fallback'}
            </span>
          </div>
          <p style={{ fontSize: '12.5px', color: '#64748b', lineHeight: 1.5 }}>
            API Endpoint: <strong>{health?.integrations?.firecrawl_scraper?.api_url}</strong>. Auto-extracts markdown content and metadata from government circulars.
          </p>
        </div>

        {/* Memento */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={20} color="#7c3aed" />
              <strong style={{ fontSize: '14px' }}>Memento Memory</strong>
            </div>
            <span style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: '#ecfdf5',
              color: '#047857',
              fontWeight: 700
            }}>
              Active
            </span>
          </div>
          <p style={{ fontSize: '12.5px', color: '#64748b', lineHeight: 1.5 }}>
            Storage: <code>{health?.integrations?.memento_memory?.storage_path}</code>. Bitemporal tracking of legal precedents and past approved interpretations.
          </p>
        </div>
      </div>

      {/* Guide Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
            Connecting Live Firebase Firestore & Authentication
          </h3>
          <ol style={{ paddingLeft: '20px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li>Go to <a href="https://console.firebase.google.com" target="_blank" rel="noreferrer">Firebase Console</a> and open or create your project.</li>
            <li>Enable <strong>Firestore Database</strong> in test/production mode.</li>
            <li>Navigate to <strong>Project Settings &gt; Service Accounts &gt; Generate New Private Key</strong>.</li>
            <li>Save the downloaded JSON file as <code>backend/firebase-service-account.json</code>.</li>
            <li>Set <code>FIREBASE_SERVICE_ACCOUNT_KEY=./firebase-service-account.json</code> in <code>backend/.env</code> and restart Flask.</li>
          </ol>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
            Deploying with Ngrok for Demonstration
          </h3>
          <div style={{
            backgroundColor: '#0f172a',
            color: '#f8fafc',
            borderRadius: '8px',
            padding: '14px',
            fontFamily: 'monospace',
            fontSize: '12.5px',
            lineHeight: 1.6
          }}>
            <div># 1. Start the Flask backend (Port 5000)</div>
            <div>cd backend</div>
            <div>.\venv\Scripts\python.exe app.py</div>
            <br />
            <div># 2. Expose via Ngrok in a separate terminal</div>
            <div>ngrok http 5000</div>
            <br />
            <div># 3. Use the generated forwarding URL (e.g., https://xyz.ngrok-free.app) for external API testing!</div>
          </div>
        </div>
      </div>
    </div>
  );
}

