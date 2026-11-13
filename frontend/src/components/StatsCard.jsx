import React from 'react';

export default function StatsCard({ label, value, icon: Icon, color = '#2563eb', bg = '#eff6ff', changeText }) {
  return (
    <div className="stat-card">
      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
        {changeText && (
          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
            {changeText}
          </div>
        )}
      </div>
      <div className="stat-icon-wrapper" style={{ backgroundColor: bg, color }}>
        <Icon size={22} />
      </div>
    </div>
  );
}

