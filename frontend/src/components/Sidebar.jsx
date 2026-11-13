import React from 'react';
import { 
  LayoutDashboard, 
  FileText, 
  Sparkles, 
  History, 
  CheckCircle2, 
  Globe2, 
  Users, 
  Settings, 
  ShieldAlert,
  LogOut
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({ currentPage, setCurrentPage }) {
  const { user, logout, isAdmin, isReviewer } = useAuth();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard Overview', icon: LayoutDashboard },
    { id: 'updates', label: 'Regulatory Updates', icon: FileText },
    { id: 'summary', label: 'AI Summaries', icon: Sparkles },
    { id: 'history', label: 'Historical Context', icon: History },
    { id: 'review', label: 'Review & Approval', icon: CheckCircle2, badge: 'Queue' },
    { id: 'sources', label: 'Source Management', icon: Globe2 },
    ...(isAdmin ? [{ id: 'users', label: 'User Management', icon: Users }] : []),
    { id: 'settings', label: 'System Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo-icon">L</div>
        <div>
          <div className="sidebar-title">LegalUpdate AI</div>
          <div className="sidebar-sub">Regulatory Summarizer</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <div
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} />
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge && (
                <span style={{
                  fontSize: '10px',
                  backgroundColor: 'rgba(255,255,255,0.2)',
                  padding: '2px 6px',
                  borderRadius: '10px'
                }}>
                  {item.badge}
                </span>
              )}
            </div>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>
              {user?.display_name || user?.email?.split('@')[0] || 'Legal Counsel'}
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'capitalize' }}>
              Role: {user?.role || 'Reviewer'}
            </div>
          </div>
          <button 
            onClick={logout} 
            title="Log Out"
            style={{ 
              background: 'none', 
              border: 'none', 
              color: '#ef4444', 
              cursor: 'pointer', 
              display: 'flex', 
              padding: '6px' 
            }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}

