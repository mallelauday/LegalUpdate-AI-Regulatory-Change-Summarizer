import React from 'react';
import { RefreshCw, Shield, Bell, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ title, onOpenScrapeModal }) {
  const { user } = useAuth();

  return (
    <header className="navbar">
      <div className="navbar-left">
        <h1 className="page-title">{title}</h1>
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          color: '#10b981',
          backgroundColor: '#ecfdf5',
          padding: '3px 8px',
          borderRadius: '12px',
          fontWeight: 600
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }}></span>
          Monitoring Active
        </span>
      </div>

      <div className="navbar-right">
        <button 
          onClick={onOpenScrapeModal} 
          className="btn btn-primary btn-sm"
          style={{ gap: '6px' }}
        >
          <RefreshCw size={14} />
          <span>Ingest Regulatory URL</span>
        </button>

        <div style={{
          height: '24px',
          width: '1px',
          backgroundColor: '#e2e8f0',
          margin: '0 4px'
        }}></div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            backgroundColor: '#1e3a8a',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '13px',
            fontWeight: 700
          }}>
            {(user?.display_name || user?.email || 'U')[0].toUpperCase()}
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a' }}>
              {user?.display_name || user?.email?.split('@')[0]}
            </div>
            <div style={{ fontSize: '11px', color: '#64748b' }}>
              {user?.department || 'Legal & Compliance'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

