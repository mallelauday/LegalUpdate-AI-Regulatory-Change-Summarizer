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
  Cpu,
  Activity,
  Play,
  Clock,
  ShieldCheck
} from 'lucide-react';
import api from '../services/api';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [monitoring, setMonitoring] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [hRes, mRes] = await Promise.all([
        api.get('/health'),
        api.get('/monitoring/status').catch(() => null)
      ]);
      if (hRes.success) setHealth(hRes.data);
      if (mRes?.success) setMonitoring(mRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTriggerMonitor = async (monitorId) => {
    try {
      setActionLoading(true);
      const res = await api.post('/monitoring/trigger', { monitor_id: monitorId });
      if (res.success) {
        alert(res.message || 'Monitor triggered successfully. Job queued for Background Worker.');
        fetchData();
      }
    } catch (err) {
      alert(err.message || 'Trigger failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleMonitor = async (monitorId, currentActive) => {
    try {
      setActionLoading(true);
      const res = await api.post(`/monitoring/${monitorId}/toggle`, { is_active: !currentActive });
      if (res.success) {
        fetchData();
      }
    } catch (err) {
      alert(err.message || 'Toggle failed');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>
            System Architecture, Monitoring & Integration Hub
          </h2>
          <div style={{ fontSize: '13px', color: '#64748b' }}>
            Real-time status of 15-minute Firecrawl monitors, Render Background Worker, Groq LLM, and hosted Memento MCP
          </div>
        </div>
        <button onClick={fetchData} className="btn btn-secondary" disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh Status
        </button>
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
            Mode: <strong>{health?.integrations?.firebase_firestore?.mode}</strong>. Persists 12 collections including updates, versions, summaries, and audit logs.
          </p>
        </div>

        {/* Groq LLM */}
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
              {health?.integrations?.groq_llm?.is_configured ? 'Active' : 'Fallback / Rule Engine'}
            </span>
          </div>
          <p style={{ fontSize: '12.5px', color: '#64748b', lineHeight: 1.5 }}>
            Model: <strong>{health?.integrations?.groq_llm?.model}</strong>. Zero-hallucination structured legal analysis with strict missing-data disclosure.
          </p>
        </div>

        {/* Firecrawl Scraper */}
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
              {health?.integrations?.firecrawl_scraper?.is_configured ? 'Cloud API + Webhook' : 'Resilient Fallback'}
            </span>
          </div>
          <p style={{ fontSize: '12.5px', color: '#64748b', lineHeight: 1.5 }}>
            Webhook: <code>/api/webhooks/firecrawl</code> with HMAC-SHA256 signature verification.
          </p>
        </div>

        {/* Memento Memory */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={20} color="#7c3aed" />
              <strong style={{ fontSize: '14px' }}>Memento AGI MCP</strong>
            </div>
            <span style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: '#ecfdf5',
              color: '#047857',
              fontWeight: 700
            }}>
              Hosted JSON-RPC Active
            </span>
          </div>
          <p style={{ fontSize: '12.5px', color: '#64748b', lineHeight: 1.5 }}>
            MCP Endpoint: <code>{health?.integrations?.memento_memory?.mcp_url || 'https://api.mementoagi.com/mcp'}</code>. Bitemporal tracking of regulatory precedents.
          </p>
        </div>
      </div>

      {/* Automated 15-Minute Regulatory Monitors Table */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
              Scheduled 15-Minute Regulatory Monitors (Firecrawl)
            </h3>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              Automated crawling schedules for RBI, SEBI, MCA, and IRDAI (Timezone: Asia/Kolkata)
            </div>
          </div>
          <button
            onClick={() => handleTriggerMonitor(null)}
            className="btn btn-primary"
            style={{ fontSize: '12px', padding: '6px 12px' }}
            disabled={actionLoading}
          >
            <Play size={13} /> Trigger All Monitors
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Regulator</th>
                <th>Monitor Name & Target URL</th>
                <th>Frequency</th>
                <th>Status</th>
                <th>Total Runs</th>
                <th>Last Checked</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {monitoring?.monitors?.length > 0 ? (
                monitoring.monitors.map((m) => (
                  <tr key={m.id || m.monitor_id}>
                    <td>
                      <span className="badge badge-regulator">
                        {m.source_code}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: '2px' }}>{m.name}</div>
                      <a href={m.crawl_url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: '#2563eb' }}>
                        {m.crawl_url.substring(0, 50)}...
                      </a>
                    </td>
                    <td style={{ fontSize: '12px', color: '#475569' }}>
                      <span className="badge" style={{ backgroundColor: '#f1f5f9', color: '#334155' }}>
                        <Clock size={11} style={{ marginRight: '4px' }} /> {m.schedule}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${m.is_active ? 'badge-approved' : 'badge-rejected'}`}>
                        {m.is_active ? 'Active' : 'Paused'}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px', color: '#475569' }}>
                      {m.total_runs || 0}
                    </td>
                    <td style={{ fontSize: '12px', color: '#64748b' }}>
                      {m.last_checked_at ? new Date(m.last_checked_at).toLocaleTimeString() : 'Pending'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          onClick={() => handleTriggerMonitor(m.monitor_id || m.id)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '11px' }}
                          disabled={actionLoading}
                          title="Enqueue immediate scrape job"
                        >
                          Trigger
                        </button>
                        <button
                          onClick={() => handleToggleMonitor(m.monitor_id || m.id, m.is_active)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '11px' }}
                          disabled={actionLoading}
                        >
                          {m.is_active ? 'Pause' : 'Resume'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>
                    Loading monitors...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Production Deployment Instructions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
        
        {/* Render Deployment */}
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
            Render Production Architecture
          </h3>
          <p style={{ fontSize: '12.5px', color: '#475569', lineHeight: 1.5, marginBottom: '12px' }}>
            Configured via <code>render.yaml</code> with two decoupled services:
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '12.5px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li><strong>Web Service:</strong> Gunicorn HTTP server running Flask API endpoints and webhooks.</li>
            <li><strong>Background Worker:</strong> Continuous daemon running <code>worker.py</code> to process ingestion queues without blocking API response times.</li>
          </ul>
        </div>

        {/* Vercel Deployment */}
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
            Vercel Frontend Hosting
          </h3>
          <p style={{ fontSize: '12.5px', color: '#475569', lineHeight: 1.5, marginBottom: '12px' }}>
            Configured via <code>frontend/vercel.json</code>:
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '12.5px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li>Single Page Application routing rewrites (<code>/* to /index.html</code>).</li>
            <li>Built using Vite + React with automated asset optimization.</li>
            <li>API proxying to live Render Web Service URL.</li>
          </ul>
        </div>

      </div>
    </div>
  );
}
