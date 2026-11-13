import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  XCircle, 
  FileText, 
  ArrowUpRight, 
  ExternalLink,
  Edit3
} from 'lucide-react';
import api from '../services/api';
import ReviewModal from '../components/ReviewModal';

export default function ReviewQueuePage({ onSelectUpdate }) {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUpdate, setSelectedUpdate] = useState(null);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [isReviewOpen, setIsReviewOpen] = useState(false);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const res = await api.get('/reviews/queue');
      if (res.success) {
        setQueue(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleOpenReview = async (item) => {
    setSelectedUpdate(item);
    try {
      const sumRes = await api.get(`/summaries/${item.id}`);
      if (sumRes.success) {
        setSelectedSummary(sumRes.data);
      }
    } catch (err) {
      setSelectedSummary(null);
    }
    setIsReviewOpen(true);
  };

  return (
    <div>
      {/* Banner */}
      <div className="disclaimer-banner">
        <CheckCircle2 size={18} color="#2563eb" />
        <div>
          <strong>Human Review Verification Workbench:</strong> In accordance with legal engineering ethics, AI outputs are decision-support materials. Authorised legal reviewers must approve, modify, or reject every regulatory analysis before it is treated as binding organizational precedent.
        </div>
      </div>

      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
              Pending Regulatory Review Queue ({queue.length})
            </h2>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              Items requiring human sign-off or requested modifications
            </div>
          </div>
          <button onClick={fetchQueue} className="btn btn-outline btn-sm">
            Refresh Queue
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
          Loading review queue...
        </div>
      ) : queue.length === 0 ? (
        <div className="card" style={{ padding: '50px', textAlign: 'center', color: '#059669' }}>
          <CheckCircle2 size={32} style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>All Caught Up!</h3>
          <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
            There are no regulatory circulars currently pending human review.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {queue.map((item) => (
            <div key={item.id} className="card">
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <span className="badge badge-regulator">{item.source_code}</span>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#1e3a8a', fontWeight: 700 }}>
                      {item.document_id}
                    </span>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>•</span>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      Published: {item.published_date}
                    </span>
                    <span className={item.current_status === 'needs_modification' ? 'badge badge-needs-mod' : 'badge badge-pending'}>
                      {item.current_status === 'needs_modification' ? 'Needs Modification' : 'Pending Review'}
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

                  <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
                    <a href={item.source_url} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#2563eb' }}>
                      Verify Official Source <ExternalLink size={11} />
                    </a>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '160px' }}>
                  <button 
                    onClick={() => handleOpenReview(item)}
                    className="btn btn-primary btn-sm"
                    style={{ width: '100%' }}
                  >
                    <Edit3 size={13} /> Review & Decision
                  </button>
                  <button 
                    onClick={() => onSelectUpdate(item.id)}
                    className="btn btn-outline btn-sm"
                    style={{ width: '100%' }}
                  >
                    Deep Analysis <ArrowUpRight size={13} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review Modal */}
      <ReviewModal
        isOpen={isReviewOpen}
        onClose={() => setIsReviewOpen(false)}
        update={selectedUpdate}
        currentSummary={selectedSummary}
        onReviewed={() => fetchQueue()}
      />
    </div>
  );
}

