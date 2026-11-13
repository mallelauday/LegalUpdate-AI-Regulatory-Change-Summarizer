import React, { useState } from 'react';
import { X, Globe2, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import api from '../services/api';

export default function LiveScrapeModal({ isOpen, onClose, onSuccess }) {
  const [url, setUrl] = useState('');
  const [sourceCode, setSourceCode] = useState('RBI');
  const [customTitle, setCustomTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.post('/scrape/url', {
        url,
        source_code: sourceCode,
        custom_title: customTitle || undefined,
      });

      if (res.success) {
        setResult(res.data);
        if (onSuccess) onSuccess(res.data);
      }
    } catch (err) {
      setError(err.message || 'Failed to ingest URL');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setUrl('');
    setCustomTitle('');
    setError(null);
    setResult(null);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={handleReset}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe2 size={18} color="#2563eb" />
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
              Ingest Official Regulatory Circular
            </h2>
          </div>
          <button 
            onClick={handleReset} 
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div style={{
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                color: '#b91c1c',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '13px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <AlertTriangle size={16} />
                <span>{error}</span>
              </div>
            )}

            {result ? (
              <div style={{
                backgroundColor: '#f0fdf4',
                border: '1px solid #bbf7d0',
                padding: '16px',
                borderRadius: '8px',
                fontSize: '13px',
                color: '#166534'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, marginBottom: '6px' }}>
                  <CheckCircle2 size={18} />
                  <span>Document Processed Successfully</span>
                </div>
                <p>Status: <strong>{result.change_status}</strong></p>
                <p>Document ID: <strong>{result.document_id}</strong></p>
                <p style={{ marginTop: '8px', fontSize: '12px', color: '#15803d' }}>{result.message}</p>
              </div>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">Regulatory Authority</label>
                  <select 
                    className="form-select"
                    value={sourceCode}
                    onChange={(e) => setSourceCode(e.target.value)}
                  >
                    <option value="RBI">Reserve Bank of India (RBI)</option>
                    <option value="SEBI">Securities and Exchange Board of India (SEBI)</option>
                    <option value="MCA">Ministry of Corporate Affairs (MCA)</option>
                    <option value="IRDAI">Insurance Regulatory Authority (IRDAI)</option>
                    <option value="CUSTOM">Other Official Gazette / Regulator</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Official Circular URL *</label>
                  <input
                    type="url"
                    required
                    placeholder="https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx?Id=..."
                    className="form-input"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                  <span style={{ fontSize: '11px', color: '#64748b', marginTop: '4px', display: 'block' }}>
                    Extracted via Firecrawl API with domestic fallback parsing.
                  </span>
                </div>

                <div className="form-group">
                  <label className="form-label">Custom Document Title (Optional)</label>
                  <input
                    type="text"
                    placeholder="Leave blank to auto-extract from HTML metadata"
                    className="form-input"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                  />
                </div>
              </>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" onClick={handleReset} className="btn btn-outline">
              {result ? 'Close' : 'Cancel'}
            </button>
            {!result && (
              <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    <span>Extracting & Summarizing...</span>
                  </>
                ) : (
                  'Start Ingestion Pipeline'
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

