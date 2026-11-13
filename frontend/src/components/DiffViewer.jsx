import React from 'react';
import { GitCompare, Plus, Minus } from 'lucide-react';

export default function DiffViewer({ diff, versionNumber }) {
  if (!diff || !diff.diff_lines || diff.diff_lines.length === 0) {
    return (
      <div style={{ padding: '16px', color: '#64748b', fontSize: '13px', fontStyle: 'italic' }}>
        No content differences detected (Initial Baseline Document).
      </div>
    );
  }

  return (
    <div style={{ marginTop: '12px' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '8px',
        fontSize: '12.5px',
        fontWeight: 600
      }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <GitCompare size={14} color="#2563eb" />
          Text Comparison (v{versionNumber} vs Prior Stored Version)
        </span>
        <div style={{ display: 'flex', gap: '12px', fontSize: '11.5px' }}>
          <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Plus size={12} /> {diff.additions || 0} additions
          </span>
          <span style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Minus size={12} /> {diff.deletions || 0} deletions
          </span>
        </div>
      </div>

      <div className="diff-container">
        {diff.diff_lines.map((line, idx) => {
          let lineClass = '';
          if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
            lineClass = 'diff-line-header';
          } else if (line.startsWith('+')) {
            lineClass = 'diff-line-added';
          } else if (line.startsWith('-')) {
            lineClass = 'diff-line-deleted';
          }
          return (
            <span key={idx} className={lineClass}>
              {line}
            </span>
          );
        })}
      </div>
    </div>
  );
}

