import React, { useState, useEffect } from 'react';
import { 
  History, 
  Search, 
  Filter, 
  Clock, 
  Tag, 
  CheckCircle2, 
  ArrowUpRight, 
  Sparkles,
  Layers
} from 'lucide-react';
import api from '../services/api';

export default function HistoricalContextPage({ onSelectUpdate }) {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [regulator, setRegulator] = useState('');

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.append('q', search);
      if (regulator) params.append('regulator', regulator);

      const res = await api.get(`/memory/search?${params.toString()}`);
      if (res.success) {
        setMemories(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [regulator]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchMemories();
  };

  return (
    <div>
      {/* Banner */}
      <div className="disclaimer-banner">
        <History size={18} color="#2563eb" />
        <div>
          <strong>Memento Historical Memory Layer:</strong> Bitemporal tracking of regulatory evolution. Links current notifications to earlier circulars, historical amendments, and previous human-approved interpretations to maintain consistent institutional knowledge.
        </div>
      </div>

      {/* Search and Filters */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', flex: 1, minWidth: '280px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            <input
              type="text"
              placeholder="Search historical precedents, circular citations, or recalled insights..."
              className="form-input"
              style={{ paddingLeft: '36px' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-outline">Search</button>
        </form>

        <select
          className="form-select"
          style={{ width: 'auto' }}
          value={regulator}
          onChange={(e) => setRegulator(e.target.value)}
        >
          <option value="">All Regulatory Authorities</option>
          <option value="RBI">Reserve Bank of India (RBI)</option>
          <option value="SEBI">Securities & Exchange Board (SEBI)</option>
          <option value="MCA">Ministry of Corporate Affairs (MCA)</option>
          <option value="IRDAI">IRDAI</option>
        </select>
      </div>

      {/* Memories Timeline Grid */}
      {loading ? (
        <div className="card" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
          Querying Memento memory repository...
        </div>
      ) : memories.length === 0 ? (
        <div className="card" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
          No historical memory entries match your search query.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {memories.map((mem) => (
            <div key={mem.id || mem.memory_id} className="card" style={{ borderLeft: '4px solid #2563eb' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', marginBottom: '10px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span className="badge badge-regulator">{mem.regulator}</span>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#1e3a8a', fontWeight: 700 }}>
                      Memory: {mem.memory_id}
                    </span>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>•</span>
                    <span style={{ fontSize: '12px', color: '#047857', fontWeight: 600 }}>
                      {mem.continuity_status || 'Precedent Connection'}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
                    Precedent Reference: {mem.precedent_ref || mem.document_id}
                  </h3>
                </div>

                {mem.update_id && (
                  <button 
                    onClick={() => onSelectUpdate(mem.update_id)}
                    className="btn btn-outline btn-sm"
                  >
                    View Associated Update <ArrowUpRight size={12} />
                  </button>
                )}
              </div>

              {/* Recalled Insight Body */}
              <div style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '14px',
                fontSize: '13px',
                color: '#334155',
                lineHeight: 1.6,
                marginBottom: '12px'
              }}>
                <strong>Historical Context & Evolution:</strong>
                <p style={{ marginTop: '4px' }}>{mem.recalled_context}</p>
              </div>

              {/* Bitemporal Timestamps & Tags */}
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '12px', fontSize: '12px', color: '#64748b' }}>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <span>Valid Law Time: <strong>{mem.valid_time || mem.precedent_date || 'N/A'}</strong></span>
                  <span>Transaction Time: <strong>{mem.transaction_time ? new Date(mem.transaction_time).toLocaleString() : 'N/A'}</strong></span>
                </div>

                <div style={{ display: 'flex', gap: '6px' }}>
                  {mem.entity_tags?.map((tag, idx) => (
                    <span key={idx} style={{
                      backgroundColor: '#eff6ff',
                      color: '#1e40af',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 600
                    }}>
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

