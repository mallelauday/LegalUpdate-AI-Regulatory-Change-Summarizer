import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Globe2, 
  ArrowUpRight, 
  Sparkles,
  ExternalLink,
  RefreshCw,
  Search
} from 'lucide-react';
import api from '../services/api';
import StatsCard from '../components/StatsCard';

export default function DashboardOverviewPage({ onSelectUpdate, onOpenScrapeModal }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await api.get('/updates/stats');
      if (res.success) {
        setStats(res.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'approved':
        return <span className="badge badge-approved"><CheckCircle2 size={12} /> Approved</span>;
      case 'rejected':
        return <span className="badge badge-rejected"><XCircle size={12} /> Rejected</span>;
      case 'needs_modification':
        return <span className="badge badge-needs-mod"><AlertCircle size={12} /> Modification</span>;
      default:
        return <span className="badge badge-pending"><Clock size={12} /> Pending Review</span>;
    }
  };

  return (
    <div>
      {/* Top Banner / Disclaimer */}
      <div className="disclaimer-banner">
        <Sparkles size={18} color="#2563eb" />
        <div>
          <strong>AI Regulatory Intelligence Active:</strong> Powered by Groq Llama-3, Firecrawl extraction, and Memento historical memory. Outputs are decision-support briefings for human legal verification.
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="stats-grid">
        <StatsCard
          label="Total Regulatory Updates"
          value={stats?.total_updates ?? '...'}
          icon={FileText}
          color="#2563eb"
          bg="#eff6ff"
          changeText="Across monitored official authorities"
        />
        <StatsCard
          label="Pending Human Review"
          value={stats?.pending_reviews ?? '...'}
          icon={Clock}
          color="#d97706"
          bg="#fffbeb"
          changeText="Requires legal counsel sign-off"
        />
        <StatsCard
          label="Approved Updates"
          value={stats?.approved_updates ?? '...'}
          icon={CheckCircle2}
          color="#059669"
          bg="#ecfdf5"
          changeText="Indexed into Memento memory"
        />
        <StatsCard
          label="Active Regulatory Sources"
          value={stats?.active_sources ?? '...'}
          icon={Globe2}
          color="#4f46e5"
          bg="#eef2ff"
          changeText="RBI, SEBI, MCA, IRDAI"
        />
      </div>

      {/* Regulators Overview Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
              Coverage by Regulatory Authority
            </h2>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Live Monitoring</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {['RBI', 'SEBI', 'MCA', 'IRDAI'].map((reg) => {
              const count = stats?.by_regulator?.[reg] || 0;
              const total = stats?.total_updates || 1;
              const pct = Math.round((count / total) * 100);
              return (
                <div key={reg} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="badge badge-regulator" style={{ width: '60px', justifyContent: 'center' }}>
                      {reg}
                    </span>
                    <span style={{ fontSize: '13px', fontWeight: 500, color: '#334155' }}>
                      {reg === 'RBI' && 'Reserve Bank of India'}
                      {reg === 'SEBI' && 'Securities & Exchange Board'}
                      {reg === 'MCA' && 'Ministry of Corporate Affairs'}
                      {reg === 'IRDAI' && 'Insurance Regulatory Authority'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '70px', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', backgroundColor: '#2563eb' }}></div>
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', width: '20px', textAlign: 'right' }}>
                      {count}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
              Instant Regulatory Ingestion
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Collect official notifications or press releases using Firecrawl extraction. Automatic hash-based change detection identifies modifications against prior circulars and recalls Memento historical context.
            </p>
          </div>

          <div style={{ marginTop: '18px', display: 'flex', gap: '10px' }}>
            <button 
              onClick={onOpenScrapeModal}
              className="btn btn-primary"
              style={{ flex: 1 }}
            >
              <RefreshCw size={14} /> Ingest Circular URL
            </button>
            <button 
              onClick={fetchStats}
              className="btn btn-outline"
              title="Refresh Stats"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Recent Regulatory Activity Table */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
              Recently Collected Regulatory Documents
            </h2>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              Live feed of newly scraped official notices, gazettes, and Master Directions
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
            Loading regulatory feed...
          </div>
        ) : !stats?.recent_activity?.length ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
            No regulatory updates collected yet. Click 'Ingest Regulatory URL' above to start.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 600 }}>
                  <th style={{ padding: '12px 10px' }}>Regulator</th>
                  <th style={{ padding: '12px 10px' }}>Document ID</th>
                  <th style={{ padding: '12px 10px' }}>Title & Scope</th>
                  <th style={{ padding: '12px 10px' }}>Published</th>
                  <th style={{ padding: '12px 10px' }}>Version</th>
                  <th style={{ padding: '12px 10px' }}>Status</th>
                  <th style={{ padding: '12px 10px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_activity.map((item) => (
                  <tr 
                    key={item.id} 
                    style={{ borderBottom: '1px solid #f1f5f9', transition: 'background-color 0.15s' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <td style={{ padding: '12px 10px' }}>
                      <span className="badge badge-regulator">{item.source_code}</span>
                    </td>
                    <td style={{ padding: '12px 10px', fontFamily: 'monospace', fontWeight: 600, color: '#1e3a8a' }}>
                      {item.document_id}
                    </td>
                    <td style={{ padding: '12px 10px', maxWidth: '380px' }}>
                      <div style={{ fontWeight: 600, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {item.title}
                      </div>
                      <a 
                        href={item.source_url} 
                        target="_blank" 
                        rel="noreferrer" 
                        style={{ fontSize: '11px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '3px' }}
                      >
                        Official Source <ExternalLink size={10} />
                      </a>
                    </td>
                    <td style={{ padding: '12px 10px', color: '#64748b', whiteSpace: 'nowrap' }}>
                      {item.published_date || item.collected_at?.slice(0, 10)}
                    </td>
                    <td style={{ padding: '12px 10px' }}>
                      <span style={{
                        fontSize: '11px',
                        backgroundColor: '#f1f5f9',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: 700,
                        color: '#475569'
                      }}>
                        v{item.version || 1}
                      </span>
                    </td>
                    <td style={{ padding: '12px 10px' }}>
                      {getStatusBadge(item.current_status)}
                    </td>
                    <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                      <button 
                        onClick={() => onSelectUpdate(item.id)}
                        className="btn btn-outline btn-sm"
                        style={{ padding: '4px 8px' }}
                      >
                        Inspect <ArrowUpRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

