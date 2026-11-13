import React, { useState, useEffect } from 'react';
import { Users, Shield, UserCheck, AlertCircle, RefreshCw } from 'lucide-react';
import api from '../services/api';

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await api.get('/auth/users');
      if (res.success) {
        setUsers(res.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (uid, newRole) => {
    try {
      await api.put(`/auth/users/${uid}/role`, { role: newRole });
      fetchUsers();
    } catch (err) {
      alert('Error updating role: ' + err.message);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>
            User Access & Role-Based Authorization
          </h2>
          <div style={{ fontSize: '13px', color: '#64748b' }}>
            Enforce separation of duties between Administrators, Legal Reviewers, and Regulatory Intelligence Analysts
          </div>
        </div>

        <button onClick={fetchUsers} className="btn btn-outline btn-sm">
          <RefreshCw size={13} /> Refresh List
        </button>
      </div>

      <div className="card">
        {loading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
            Loading users...
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
                  <th style={{ padding: '12px 10px' }}>User</th>
                  <th style={{ padding: '12px 10px' }}>Department</th>
                  <th style={{ padding: '12px 10px' }}>Current Role</th>
                  <th style={{ padding: '12px 10px' }}>Last Sign In</th>
                  <th style={{ padding: '12px 10px' }}>Permissions</th>
                  <th style={{ padding: '12px 10px', textAlign: 'right' }}>Modify Role</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const uid = u.uid || u.id;
                  return (
                    <tr key={uid} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px 10px' }}>
                        <div style={{ fontWeight: 600, color: '#0f172a' }}>
                          {u.display_name || u.name || 'User'}
                        </div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>
                          {u.email}
                        </div>
                      </td>
                      <td style={{ padding: '12px 10px', color: '#475569' }}>
                        {u.department || 'Legal & Compliance'}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <span style={{
                          textTransform: 'capitalize',
                          fontWeight: 700,
                          fontSize: '12px',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          backgroundColor: u.role === 'admin' ? '#fef3c7' : u.role === 'reviewer' ? '#eff6ff' : '#f1f5f9',
                          color: u.role === 'admin' ? '#92400e' : u.role === 'reviewer' ? '#1e40af' : '#475569'
                        }}>
                          {u.role}
                        </span>
                      </td>
                      <td style={{ padding: '12px 10px', color: '#64748b', fontSize: '12px' }}>
                        {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#64748b', fontSize: '12px' }}>
                        {u.role === 'admin' && 'Full system configuration, source & user management'}
                        {u.role === 'reviewer' && 'Approve/reject AI output, edit interpretations, review queue'}
                        {u.role === 'viewer' && 'Read-only access to regulatory briefings and archives'}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                        <select
                          className="form-select"
                          style={{ width: 'auto', padding: '4px 8px', fontSize: '12px' }}
                          value={u.role}
                          onChange={(e) => handleRoleChange(uid, e.target.value)}
                        >
                          <option value="admin">Admin</option>
                          <option value="reviewer">Reviewer</option>
                          <option value="viewer">Viewer</option>
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

