import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  FileText, 
  ExternalLink, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  ArrowUpRight,
  RefreshCw,
  GitCompare
} from 'lucide-react';
import api from '../services/api';

export default function RegulatoryUpdatesPage({ onSelectUpdate, onOpenScrapeModal }) {
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [regulator, setRegulator] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState(null);

  const fetchUpdates = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (regulator) params.append('regulator', regulator);
      if (status) params.append('status', status);
      params.append('page', page);
      params.append('limit', 15);

      const res = await api.get(`/updates?${params.toString()}`);
      if (res.success) {
        setUpdates(res.data);
        setMeta(res.meta);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUpdates();
  }, [regulator, status, page]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchUpdates();
  };

  const getStatusBadge = (s) => {
    switch (s) {
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
      {/* Header and Controls */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        marginBottom: '20px'
      }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px', flex: 1, minWidth: '280px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            <input
              type="text"
              placeholder="Search circulars, document numbers, or legal subject matter..."
              className="form-input"
              style={{ paddingLeft: '36px' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-outline">
            Search
          </button>
        </form>

        <div style={{ display: 'flex', gap: '10px' }}>
          <select 
            className="form-select"
            style={{ width: 'auto' }}
            value={regulator}
            onChange={(e) => { setRegulator(e.target.value); setPage(1); }}
          >
            <option value="">All Regulators</option>
            <option value="RBI">Reserve Bank of India (RBI)</option>
            <option value="SEBI">SEBI</option>
            <option value="MCA">Ministry of Corporate Affairs</option>
            <option value="IRDAI">IRDAI</option>
          </select>

          <select 
            className="form-select"
            style={{ width: 'auto' }}
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          >
            <option value="">All Statuses</option>
            <option value="pending_review">Pending Review</option>
            <option value="approved">Approved</option>
            <option value="needs_modification">Needs Modification</option>
            <option value="rejected">Rejected</option>
          </select>

          <button onClick={onOpenScrapeModal} className="btn btn-primary">
            + New Ingestion
          </button>
        </div>
      </div>

      {/* Updates Cards List */}
      {loading ? (
        <div className="card" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
          Querying Firestore regulatory repository...
        </div>
      ) : updates.length === 0 ? (
        <div className="card" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
          No regulatory updates match your query. Try resetting filters or ingesting a new circular URL.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {updates.map((item) => (
            <div 
              key={item.id} 
              className="card"
              style={{
                transition: 'all 0.15s ease',
                cursor: 'pointer',
                borderColor: '#e2e8f0'
              }}
              onClick={() => onSelectUpdate(item.id)}
              onMouseEnter={(e) => e.currentTarget.style.borderColor = '#2563eb'}
              onMouseLeave={(e) => e.currentTarget.style.borderColor = '#e2e8f0'}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <span className="badge badge-regulator">{item.source_code}</span>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#1e3a8a', fontWeight: 700 }}>
                      {item.document_id}
                    </span>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>•</span>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      Date: {item.published_date || item.collected_at?.slice(0, 10)}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      backgroundColor: '#f1f5f9',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontWeight: 700,
                      color: '#475569',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '3px'
                    }}>
                      {item.version > 1 && <GitCompare size={10} color="#2563eb" />}
                      v{item.version || 1}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', marginBottom: '8px', lineHeight: 1.3 }}>
                    {item.title}
                  </h3>

                  <p style={{
                    fontSize: '13px',
                    color: '#475569',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    lineHeight: 1.5,
                    marginBottom: '12px'
                  }}>
                    {item.content}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px', color: '#64748b' }}>
                    <span>SHA-256 Hash: <code style={{ fontSize: '11px' }}>{item.content_hash?.slice(0, 12)}...</code></span>
                    <a 
                      href={item.source_url} 
                      target="_blank" 
                      rel="noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#2563eb' }}
                    >
                      Official Source Link <ExternalLink size={11} />
                    </a>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px' }}>
                  {getStatusBadge(item.current_status)}
                  <button 
                    onClick={(e) => { e.stopPropagation(); onSelectUpdate(item.id); }}
                    className="btn btn-outline btn-sm"
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    View Analysis <ArrowUpRight size={13} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination Footer */}
      {meta && meta.total_pages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginTop: '24px' }}>
          <button 
            disabled={page <= 1}
            onClick={() => setPage(p => p - 1)}
            className="btn btn-outline btn-sm"
          >
            Previous
          </button>
          <span style={{ fontSize: '13px', color: '#64748b' }}>
            Page {page} of {meta.total_pages} ({meta.total_count} records)
          </span>
          <button 
            disabled={page >= meta.total_pages}
            onClick={() => setPage(p => p + 1)}
            className="btn btn-outline btn-sm"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

