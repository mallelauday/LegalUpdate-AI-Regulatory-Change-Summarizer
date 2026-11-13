import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  FileText, 
  Copy, 
  Check, 
  ArrowUpRight, 
  Building2, 
  Calendar, 
  AlertTriangle,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';
import api from '../services/api';

export default function AISummaryPage({ onSelectUpdate }) {
  const [updates, setUpdates] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [selectedUpdate, setSelectedUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchList = async () => {
      try {
        setLoading(true);
        const res = await api.get('/updates?limit=30');
        if (res.success && res.data.length > 0) {
          setUpdates(res.data);
          loadSummaryForUpdate(res.data[0]);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchList();
  }, []);

  const loadSummaryForUpdate = async (upd) => {
    setSelectedId(upd.id);
    setSelectedUpdate(upd);
    try {
      const res = await api.get(`/summaries/${upd.id}`);
      if (res.success) {
        setSelectedSummary(res.data);
      }
    } catch (err) {
      setSelectedSummary(null);
    }
  };

  const handleCopy = () => {
    if (!selectedSummary) return;
    const text = `LEGAL BRIEFING: ${selectedUpdate?.title}\nDocument ID: ${selectedUpdate?.document_id}\n\nEXECUTIVE SUMMARY:\n${selectedSummary.short_summary}\n\nDETAILED BREAKDOWN:\n${selectedSummary.detailed_summary}\n\nEFFECTIVE DATE:\n${selectedSummary.effective_date}\n\nDISCLAIMER:\n${selectedSummary.disclaimer}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className="disclaimer-banner">
        <Sparkles size={18} color="#2563eb" />
        <div>
          <strong>AI Regulatory Summaries Engine:</strong> Generating 10-point structured compliance breakdowns using Groq API (Llama-3.3-70B) with zero factual hallucinations and strict missing-information disclosures.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
        {/* Left Side: Updates Selector List */}
        <div className="card" style={{ padding: '16px', maxHeight: '80vh', overflowY: 'auto' }}>
          <h2 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginBottom: '12px' }}>
            Available Regulatory Briefings
          </h2>

          {loading ? (
            <div style={{ padding: '20px', textAlign: 'center', fontSize: '13px', color: '#64748b' }}>
              Loading briefings...
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {updates.map((u) => {
                const isSelected = selectedId === u.id;
                return (
                  <div
                    key={u.id}
                    onClick={() => loadSummaryForUpdate(u)}
                    style={{
                      padding: '12px',
                      borderRadius: '8px',
                      border: `1px solid ${isSelected ? '#2563eb' : '#e2e8f0'}`,
                      backgroundColor: isSelected ? '#eff6ff' : '#ffffff',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                      <span className="badge badge-regulator" style={{ fontSize: '10px', padding: '2px 6px' }}>
                        {u.source_code}
                      </span>
                      <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#1e3a8a', fontWeight: 700 }}>
                        {u.document_id}
                      </span>
                    </div>
                    <div style={{
                      fontSize: '13px',
                      fontWeight: 600,
                      color: '#0f172a',
                      lineHeight: 1.3,
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden'
                    }}>
                      {u.title}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Side: Full 10-Point AI Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {selectedSummary ? (
            <>
              {/* Header */}
              <div className="card">
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span className="badge badge-regulator">{selectedUpdate?.source_code}</span>
                      <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#1e3a8a', fontWeight: 700 }}>
                        {selectedUpdate?.document_id}
                      </span>
                    </div>
                    <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', lineHeight: 1.3 }}>
                      {selectedUpdate?.title}
                    </h2>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button onClick={handleCopy} className="btn btn-outline btn-sm">
                      {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                      <span>{copied ? 'Copied' : 'Copy Brief'}</span>
                    </button>
                    <button 
                      onClick={() => onSelectUpdate(selectedId)}
                      className="btn btn-primary btn-sm"
                    >
                      Full Details <ArrowUpRight size={13} />
                    </button>
                  </div>
                </div>

                <div style={{
                  marginTop: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  fontSize: '12px',
                  color: '#64748b',
                  borderTop: '1px solid #f1f5f9',
                  paddingTop: '10px'
                }}>
                  <span>Model: <strong>{selectedSummary.model_used}</strong></span>
                  <span>Confidence: <strong>{selectedSummary.confidence_score}</strong></span>
                  <a href={selectedUpdate?.source_url} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Source URL <ExternalLink size={10} />
                  </a>
                </div>
              </div>

              {/* Short Summary Card */}
              <div className="card">
                <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#1e3a8a', textTransform: 'uppercase', marginBottom: '8px' }}>
                  1. Executive Briefing
                </h3>
                <p style={{ fontSize: '14px', color: '#0f172a', lineHeight: 1.6, fontWeight: 500 }}>
                  {selectedSummary.short_summary}
                </p>
              </div>

              {/* Detailed Breakdown */}
              <div className="card">
                <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#1e3a8a', textTransform: 'uppercase', marginBottom: '8px' }}>
                  2. Detailed Regulatory Explanation
                </h3>
                <p style={{ fontSize: '13.5px', color: '#334155', lineHeight: 1.7, whiteSpace: 'pre-line' }}>
                  {selectedSummary.detailed_summary}
                </p>
              </div>

              {/* Key Changes & Mandatory Requirements */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                <div className="card">
                  <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '10px' }}>
                    3. Key Regulatory Changes
                  </h3>
                  <ul style={{ paddingLeft: '16px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selectedSummary.key_regulatory_changes?.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div className="card">
                  <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '10px' }}>
                    4. Important Compliance Mandates
                  </h3>
                  <ul style={{ paddingLeft: '16px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selectedSummary.important_requirements?.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Affected Organizations & Compliance Implications */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                <div className="card">
                  <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '10px' }}>
                    5. Affected Business Categories
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {selectedSummary.affected_organizations?.map((org, i) => (
                      <span key={i} style={{ backgroundColor: '#eef2ff', color: '#3730a3', fontSize: '12px', padding: '3px 8px', borderRadius: '4px', fontWeight: 600 }}>
                        {org}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="card">
                  <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '10px' }}>
                    6. Potential Risk & Enforcement Implications
                  </h3>
                  <ul style={{ paddingLeft: '16px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selectedSummary.potential_compliance_implications?.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Effective Date & Recommendations */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                <div className="card">
                  <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                    7. Effective Statutory Date
                  </h3>
                  <div style={{ backgroundColor: '#eff6ff', color: '#1e3a8a', padding: '10px 14px', borderRadius: '8px', fontWeight: 700, fontSize: '13.5px' }}>
                    {selectedSummary.effective_date}
                  </div>
                </div>

                <div className="card">
                  <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                    8. Recommended Actions for Legal Review
                  </h3>
                  <ul style={{ paddingLeft: '16px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {selectedSummary.recommended_actions?.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          ) : (
            <div className="card" style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
              Select a regulatory circular on the left to inspect its AI summary.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

