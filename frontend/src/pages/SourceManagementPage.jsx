import React, { useState, useEffect } from 'react';
import { 
  Globe2, 
  Plus, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  ExternalLink, 
  Clock, 
  Shield, 
  AlertCircle,
  Loader2
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function SourceManagementPage() {
  const { isAdmin } = useAuth();
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [crawlingId, setCrawlingId] = useState(null);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newSource, setNewSource] = useState({
    source_code: '',
    name: '',
    jurisdiction: 'India',
    regulator_type: 'Central Statutory Regulator',
    base_url: '',
    crawl_url: '',
    category: 'Banking & Securities',
    crawl_frequency_minutes: 60,
    description: ''
  });
  const [error, setError] = useState(null);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const res = await api.get('/sources');
      if (res.success) {
        setSources(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleTriggerCrawl = async (sourceId) => {
    setCrawlingId(sourceId);
    try {
      const res = await api.post(`/sources/${sourceId}/crawl`);
      alert(res.message || 'Crawl initiated successfully!');
      fetchSources();
    } catch (err) {
      alert('Crawl error: ' + err.message);
    } finally {
      setCrawlingId(null);
    }
  };

  const handleToggleActive = async (source) => {
    if (!isAdmin) return;
    try {
      await api.put(`/sources/${source.source_id || source.id}`, {
        is_active: !source.is_active
      });
      fetchSources();
    } catch (err) {
      alert('Error updating source: ' + err.message);
    }
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/sources', newSource);
      if (res.success) {
        setIsAddOpen(false);
        setNewSource({
          source_code: '',
          name: '',
          jurisdiction: 'India',
          regulator_type: 'Central Statutory Regulator',
          base_url: '',
          crawl_url: '',
          category: 'Banking & Securities',
          crawl_frequency_minutes: 60,
          description: ''
        });
        fetchSources();
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>
            Official Regulatory Authorities & Sources
          </h2>
          <div style={{ fontSize: '13px', color: '#64748b' }}>
            Manage crawled endpoints, frequency parameters, and Firecrawl scraping rules
          </div>
        </div>

        {isAdmin && (
          <button onClick={() => setIsAddOpen(true)} className="btn btn-primary">
            <Plus size={16} /> Add Regulatory Source
          </button>
        )}
      </div>

      {loading ? (
        <div className="card" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
          Loading regulatory sources...
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '18px' }}>
          {sources.map((src) => (
            <div key={src.source_id || src.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="badge badge-regulator" style={{ fontSize: '13px', padding: '3px 10px' }}>
                      {src.source_code}
                    </span>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      {src.jurisdiction}
                    </span>
                  </div>

                  <span 
                    onClick={() => handleToggleActive(src)}
                    style={{
                      cursor: isAdmin ? 'pointer' : 'default',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '12px',
                      backgroundColor: src.is_active ? '#ecfdf5' : '#f1f5f9',
                      color: src.is_active ? '#047857' : '#64748b'
                    }}
                    title={isAdmin ? 'Click to toggle active state' : ''}
                  >
                    {src.is_active ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                    {src.is_active ? 'Active' : 'Paused'}
                  </span>
                </div>

                <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>
                  {src.name}
                </h3>
                <p style={{ fontSize: '12.5px', color: '#64748b', marginBottom: '12px', lineHeight: 1.5 }}>
                  {src.description || 'Statutory authority monitoring circulars and directions.'}
                </p>

                <div style={{
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  padding: '10px 12px',
                  fontSize: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  marginBottom: '14px'
                }}>
                  <div>
                    <span style={{ color: '#64748b' }}>Crawl URL: </span>
                    <a href={src.crawl_url} target="_blank" rel="noreferrer" style={{ wordBreak: 'break-all' }}>
                      {src.crawl_url} <ExternalLink size={10} style={{ display: 'inline' }} />
                    </a>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', marginTop: '4px' }}>
                    <span>Frequency: <strong>{src.crawl_frequency_minutes} mins</strong></span>
                    <span>Last Crawled: <strong>{src.last_crawled_at ? new Date(src.last_crawled_at).toLocaleTimeString() : 'Never'}</strong></span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={() => handleTriggerCrawl(src.source_id || src.id)}
                  disabled={crawlingId === (src.source_id || src.id) || !src.is_active}
                  className="btn btn-outline btn-sm"
                  style={{ flex: 1 }}
                >
                  {crawlingId === (src.source_id || src.id) ? (
                    <>
                      <Loader2 size={13} className="animate-spin" />
                      <span>Crawling...</span>
                    </>
                  ) : (
                    <>
                      <RefreshCw size={13} />
                      <span>Crawl Now</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Source Modal */}
      {isAddOpen && (
        <div className="modal-overlay" onClick={() => setIsAddOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 style={{ fontSize: '16px', fontWeight: 700 }}>Add Regulatory Source</h2>
              <button onClick={() => setIsAddOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                &times;
              </button>
            </div>
            <form onSubmit={handleAddSubmit}>
              <div className="modal-body">
                {error && (
                  <div style={{ padding: '10px', backgroundColor: '#fef2f2', color: '#b91c1c', borderRadius: '6px', fontSize: '13px', marginBottom: '12px' }}>
                    {error}
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label">Regulator Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. TRAI, CCI, IBBI"
                    className="form-input"
                    value={newSource.source_code}
                    onChange={(e) => setNewSource({ ...newSource, source_code: e.target.value.toUpperCase() })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Full Authority Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Competition Commission of India"
                    className="form-input"
                    value={newSource.name}
                    onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Crawl Index URL *</label>
                  <input
                    type="url"
                    required
                    placeholder="https://.../circulars-index"
                    className="form-input"
                    value={newSource.crawl_url}
                    onChange={(e) => setNewSource({ ...newSource, crawl_url: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <input
                    type="text"
                    placeholder="Antitrust, Corporate Restructuring"
                    className="form-input"
                    value={newSource.category}
                    onChange={(e) => setNewSource({ ...newSource, category: e.target.value })}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setIsAddOpen(false)} className="btn btn-outline">Cancel</button>
                <button type="submit" className="btn btn-primary">Save Source</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

