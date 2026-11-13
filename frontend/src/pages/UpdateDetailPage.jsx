import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  ExternalLink, 
  Sparkles, 
  FileText, 
  GitCompare, 
  History, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Clock, 
  Calendar, 
  Building2, 
  AlertTriangle, 
  CheckSquare, 
  RefreshCw,
  Share2
} from 'lucide-react';
import api from '../services/api';
import DiffViewer from '../components/DiffViewer';
import ReviewModal from '../components/ReviewModal';

export default function UpdateDetailPage({ updateId, onBack, onOpenReview }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const fetchDetail = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/updates/${updateId}`);
      if (res.success) {
        setData(res.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (updateId) fetchDetail();
  }, [updateId]);

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      const res = await api.post(`/summaries/${updateId}/regenerate`);
      if (res.success) {
        setData(prev => ({ ...prev, ai_summary: res.data }));
      }
    } catch (err) {
      alert('Error regenerating summary: ' + err.message);
    } finally {
      setRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        Retrieving document analysis from Firestore...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card" style={{ padding: '40px', textAlign: 'center', color: '#b91c1c' }}>
        <p>Failed to load update: {error}</p>
        <button onClick={onBack} className="btn btn-outline" style={{ marginTop: '12px' }}>
          Back to Updates
        </button>
      </div>
    );
  }

  const { update, ai_summary, versions, historical_context, reviews } = data;

  const getStatusBadge = (s) => {
    switch (s) {
      case 'approved':
        return <span className="badge badge-approved"><CheckCircle2 size={12} /> Approved</span>;
      case 'rejected':
        return <span className="badge badge-rejected"><XCircle size={12} /> Rejected</span>;
      case 'needs_modification':
        return <span className="badge badge-needs-mod"><AlertCircle size={12} /> Needs Modification</span>;
      default:
        return <span className="badge badge-pending"><Clock size={12} /> Pending Review</span>;
    }
  };

  return (
    <div>
      {/* Back Button and Actions Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <button onClick={onBack} className="btn btn-outline btn-sm">
          <ArrowLeft size={14} /> Back to Updates
        </button>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={handleRegenerate}
            disabled={regenerating}
            className="btn btn-outline btn-sm"
          >
            <RefreshCw size={13} className={regenerating ? 'animate-spin' : ''} />
            <span>{regenerating ? 'Re-running Llama...' : 'Regenerate Summary'}</span>
          </button>
          <button 
            onClick={() => setIsReviewOpen(true)}
            className="btn btn-primary btn-sm"
          >
            <CheckCircle2 size={14} /> Review & Approve
          </button>
        </div>
      </div>

      {/* Main Document Header Card */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
          <span className="badge badge-regulator">{update.source_code}</span>
          <span style={{ fontSize: '13px', fontFamily: 'monospace', fontWeight: 700, color: '#1e3a8a' }}>
            {update.document_id}
          </span>
          <span style={{ fontSize: '12px', color: '#64748b' }}>•</span>
          <span style={{ fontSize: '13px', color: '#64748b' }}>
            Published: {update.published_date || 'Date not marked'}
          </span>
          <span style={{
            fontSize: '11px',
            backgroundColor: '#f1f5f9',
            padding: '2px 8px',
            borderRadius: '4px',
            fontWeight: 700,
            color: '#475569'
          }}>
            Version {update.version || 1}
          </span>
          <div style={{ marginLeft: 'auto' }}>
            {getStatusBadge(update.current_status)}
          </div>
        </div>

        <h1 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', marginBottom: '12px', lineHeight: 1.3 }}>
          {update.title}
        </h1>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', fontSize: '12.5px', color: '#64748b' }}>
          <span>Collected: {update.collected_at ? new Date(update.collected_at).toLocaleString() : 'N/A'}</span>
          <span>Content SHA-256: <code>{update.content_hash?.slice(0, 16)}...</code></span>
          <a 
            href={update.source_url} 
            target="_blank" 
            rel="noreferrer" 
            style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#2563eb' }}
          >
            Official Gazette URL <ExternalLink size={12} />
          </a>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #e2e8f0',
        marginBottom: '20px',
        gap: '4px'
      }}>
        {[
          { id: 'summary', label: 'AI Regulatory Summary', icon: Sparkles },
          { id: 'original', label: 'Original Scraped Text', icon: FileText },
          { id: 'versions', label: `Version Diff (${versions?.length || 1})`, icon: GitCompare },
          { id: 'memory', label: 'Memento Historical Context', icon: History },
          { id: 'reviews', label: `Audit Trail (${reviews?.length || 0})`, icon: CheckCircle2 }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontSize: '13.5px',
                fontWeight: 600,
                color: isActive ? '#2563eb' : '#64748b',
                borderBottom: isActive ? '2px solid #2563eb' : '2px solid transparent',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === 'summary' && (
        <div>
          {/* Disclaimer */}
          <div className="disclaimer-banner">
            <Sparkles size={18} color="#2563eb" />
            <div>
              <strong>Human Verification Notice:</strong> {ai_summary?.disclaimer || "AI-generated regulatory analysis. Presented for human legal review. Does not constitute authoritative legal advice."}
              <div style={{ fontSize: '11px', color: '#1e40af', marginTop: '2px' }}>
                Generated using model: <strong>{ai_summary?.model_used || 'Groq Llama-3'}</strong> | Confidence Score: <strong>{ai_summary?.confidence_score || 0.94}</strong>
              </div>
            </div>
          </div>

          {ai_summary?.human_edited_summary && (
            <div className="card" style={{ marginBottom: '16px', backgroundColor: '#f0fdf4', borderColor: '#bbf7d0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534', fontWeight: 700, marginBottom: '6px' }}>
                <CheckCircle2 size={16} /> Human-Approved Interpretation (Authoritative Internal Precedent)
              </div>
              <p style={{ fontSize: '13.5px', color: '#14532d', lineHeight: 1.6 }}>
                {ai_summary.human_edited_summary}
              </p>
            </div>
          )}

          {/* Short Executive Summary */}
          <div className="card" style={{ marginBottom: '16px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#1e3a8a', textTransform: 'uppercase', marginBottom: '8px' }}>
              Executive Brief
            </h3>
            <p style={{ fontSize: '14.5px', color: '#0f172a', fontWeight: 500, lineHeight: 1.6 }}>
              {ai_summary?.short_summary}
            </p>
          </div>

          {/* Detailed Explanation */}
          <div className="card" style={{ marginBottom: '16px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#1e3a8a', textTransform: 'uppercase', marginBottom: '8px' }}>
              Detailed Legal Breakdown
            </h3>
            <p style={{ fontSize: '13.5px', color: '#334155', lineHeight: 1.7, whiteSpace: 'pre-line' }}>
              {ai_summary?.detailed_summary}
            </p>
          </div>

          {/* Key Changes & Important Requirements Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <GitCompare size={16} color="#2563eb" /> Key Regulatory Changes
              </h3>
              <ul style={{ paddingLeft: '18px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {ai_summary?.key_regulatory_changes?.map((item, idx) => (
                  <li key={idx} style={{ lineHeight: 1.5 }}>{item}</li>
                ))}
              </ul>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <CheckSquare size={16} color="#059669" /> Mandatory Compliance Requirements
              </h3>
              <ul style={{ paddingLeft: '18px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {ai_summary?.important_requirements?.map((item, idx) => (
                  <li key={idx} style={{ lineHeight: 1.5 }}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Affected Organizations & Potential Implications */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Building2 size={16} color="#4f46e5" /> Affected Organizations & Sectors
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {ai_summary?.affected_organizations?.map((org, idx) => (
                  <span key={idx} style={{
                    backgroundColor: '#eef2ff',
                    color: '#3730a3',
                    fontSize: '12.5px',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontWeight: 600
                  }}>
                    {org}
                  </span>
                ))}
              </div>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <AlertTriangle size={16} color="#d97706" /> Potential Compliance Implications
              </h3>
              <ul style={{ paddingLeft: '18px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {ai_summary?.potential_compliance_implications?.map((imp, idx) => (
                  <li key={idx} style={{ lineHeight: 1.5 }}>{imp}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Effective Date & Action Checklist */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <Calendar size={16} color="#2563eb" /> Effective Date & Implementation Timeline
              </h3>
              <div style={{
                fontSize: '14px',
                fontWeight: 700,
                color: '#1e3a8a',
                backgroundColor: '#eff6ff',
                padding: '12px 16px',
                borderRadius: '8px'
              }}>
                {ai_summary?.effective_date || "Not specified in the source document."}
              </div>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <CheckSquare size={16} color="#059669" /> Recommended Actions for Human Legal Review
              </h3>
              <ul style={{ paddingLeft: '18px', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {ai_summary?.recommended_actions?.map((act, idx) => (
                  <li key={idx}>{act}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Original Document Text */}
      {activeTab === 'original' && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
              Extracted Full Text (Extracted via Firecrawl)
            </h3>
            <a 
              href={update.source_url} 
              target="_blank" 
              rel="noreferrer"
              className="btn btn-outline btn-sm"
            >
              Verify on Regulatory Website <ExternalLink size={12} />
            </a>
          </div>

          <pre style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '18px',
            fontSize: '13px',
            color: '#1e293b',
            whiteSpace: 'pre-wrap',
            fontFamily: 'Consolas, Monaco, monospace',
            lineHeight: 1.6,
            maxHeight: '600px',
            overflowY: 'auto'
          }}>
            {update.content}
          </pre>
        </div>
      )}

      {/* Tab: Version History & Diff */}
      {activeTab === 'versions' && (
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
            Document Version History & Change Detection
          </h3>
          <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
            Whenever content modifications are detected across crawl cycles, a new immutable version is stored with cryptographic SHA-256 validation.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {versions?.map((v) => (
              <div key={v.id} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      backgroundColor: '#2563eb',
                      color: '#fff',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: 700
                    }}>
                      Version {v.version_number}
                    </span>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a' }}>
                      {v.title}
                    </span>
                  </div>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>
                    Recorded: {new Date(v.created_at).toLocaleString()}
                  </span>
                </div>

                <DiffViewer diff={v.diff} versionNumber={v.version_number} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Memento Historical Context */}
      {activeTab === 'memory' && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <History size={18} color="#2563eb" />
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
              Memento Bitemporal Memory Link
            </h3>
          </div>

          <div style={{ backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '13px' }}>
              <div>
                <span style={{ color: '#64748b', display: 'block', fontSize: '11px', textTransform: 'uppercase' }}>Memory Reference ID</span>
                <strong style={{ fontFamily: 'monospace', color: '#1e3a8a' }}>{historical_context?.memory_id || 'mem-init'}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block', fontSize: '11px', textTransform: 'uppercase' }}>Historical Precedent Circular</span>
                <strong>{historical_context?.precedent_ref || 'Baseline Standard'}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block', fontSize: '11px', textTransform: 'uppercase' }}>Precedent Valid Date</span>
                <strong>{historical_context?.precedent_date || 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block', fontSize: '11px', textTransform: 'uppercase' }}>Continuity Status</span>
                <span className="badge badge-regulator">{historical_context?.continuity_status || 'New Standard'}</span>
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>
              Recalled Regulatory Insight & Comparative Precedent:
            </h4>
            <p style={{ fontSize: '13px', color: '#334155', lineHeight: 1.6, backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              {historical_context?.recalled_context || 'No earlier circular in this series was found in memory.'}
            </p>
          </div>

          <div>
            <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
              Associated Legal & Entity Tags:
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {historical_context?.entity_tags?.map((t, idx) => (
                <span key={idx} style={{
                  fontSize: '11.5px',
                  backgroundColor: '#f1f5f9',
                  color: '#475569',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  fontWeight: 600
                }}>
                  #{t}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Reviews Audit Trail */}
      {activeTab === 'reviews' && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
              Human Legal Review Audit Trail
            </h3>
            <button onClick={() => setIsReviewOpen(true)} className="btn btn-primary btn-sm">
              <CheckCircle2 size={13} /> Add Review Decision
            </button>
          </div>

          {!reviews || reviews.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
              No review decisions recorded yet. Document is currently awaiting initial sign-off.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {reviews.map((rev) => (
                <div key={rev.id} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {getStatusBadge(rev.decision)}
                      <span style={{ fontSize: '13.5px', fontWeight: 700, color: '#0f172a' }}>
                        {rev.reviewer_name}
                      </span>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>
                        ({rev.reviewer_email})
                      </span>
                    </div>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      {new Date(rev.reviewed_at).toLocaleString()}
                    </span>
                  </div>

                  <p style={{ fontSize: '13px', color: '#334155', marginTop: '6px', lineHeight: 1.5 }}>
                    <strong>Reviewer Notes:</strong> {rev.comments}
                  </p>

                  {rev.edited_summary && (
                    <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f0fdf4', borderRadius: '6px', fontSize: '12.5px' }}>
                      <strong>Custom Edited Interpretation:</strong>
                      <p style={{ color: '#166534', marginTop: '4px' }}>{rev.edited_summary}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Review Modal */}
      <ReviewModal
        isOpen={isReviewOpen}
        onClose={() => setIsReviewOpen(false)}
        update={update}
        currentSummary={ai_summary}
        onReviewed={() => fetchDetail()}
      />
    </div>
  );
}

