import React, { useState } from 'react';
import { X, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function ReviewModal({ isOpen, onClose, update, currentSummary, onReviewed }) {
  const [decision, setDecision] = useState('approved');
  const [comments, setComments] = useState('');
  const [editedSummary, setEditedSummary] = useState(
    currentSummary?.human_edited_summary || currentSummary?.detailed_summary || ''
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !update) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.post(`/reviews/${update.id}`, {
        decision,
        comments,
        edited_summary: editedSummary !== currentSummary?.detailed_summary ? editedSummary : undefined,
      });

      if (res.success) {
        if (onReviewed) onReviewed(res.data);
        onClose();
      }
    } catch (err) {
      setError(err.message || 'Failed to submit review');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '720px' }}>
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
              Human Legal Review & Approval
            </h2>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              Doc ID: {update.document_id} | {update.source_code}
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
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
                marginBottom: '16px'
              }}>
                {error}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Review Decision *</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setDecision('approved')}
                  className="btn"
                  style={{
                    backgroundColor: decision === 'approved' ? '#ecfdf5' : '#ffffff',
                    border: `2px solid ${decision === 'approved' ? '#10b981' : '#e2e8f0'}`,
                    color: decision === 'approved' ? '#047857' : '#64748b',
                    fontWeight: 700
                  }}
                >
                  <CheckCircle size={16} /> Approved
                </button>

                <button
                  type="button"
                  onClick={() => setDecision('needs_modification')}
                  className="btn"
                  style={{
                    backgroundColor: decision === 'needs_modification' ? '#f3e8ff' : '#ffffff',
                    border: `2px solid ${decision === 'needs_modification' ? '#9333ea' : '#e2e8f0'}`,
                    color: decision === 'needs_modification' ? '#7e22ce' : '#64748b',
                    fontWeight: 700
                  }}
                >
                  <AlertCircle size={16} /> Modification
                </button>

                <button
                  type="button"
                  onClick={() => setDecision('rejected')}
                  className="btn"
                  style={{
                    backgroundColor: decision === 'rejected' ? '#fef2f2' : '#ffffff',
                    border: `2px solid ${decision === 'rejected' ? '#ef4444' : '#e2e8f0'}`,
                    color: decision === 'rejected' ? '#b91c1c' : '#64748b',
                    fontWeight: 700
                  }}
                >
                  <XCircle size={16} /> Rejected
                </button>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                Human Refined Interpretation (Editable)
              </label>
              <textarea
                className="form-textarea"
                rows={5}
                value={editedSummary}
                onChange={(e) => setEditedSummary(e.target.value)}
                placeholder="Review and polish the AI-generated interpretation. Preserved distinctly from raw AI output."
              />
              <span style={{ fontSize: '11px', color: '#64748b', marginTop: '4px', display: 'block' }}>
                Approved summaries will be indexed into Memento historical memory as authoritative organizational precedent.
              </span>
            </div>

            <div className="form-group">
              <label className="form-label">Internal Compliance Notes & Rationale *</label>
              <textarea
                className="form-textarea"
                rows={3}
                required
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="State statutory basis, cross-department impacts, or justification for this review decision..."
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-outline">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Submitting Review...</span>
                </>
              ) : (
                'Confirm Decision'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

