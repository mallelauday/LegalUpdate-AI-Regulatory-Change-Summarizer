import React, { useState } from 'react';
import { ShieldCheck, Lock, Mail, User, AlertCircle, ArrowRight, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function LoginPage() {
  const { login } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('admin@legalupdate.ai');
  const [password, setPassword] = useState('admin123');
  const [name, setName] = useState('');
  const [department, setDepartment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const demoAccounts = [
    { label: 'Admin (Sarah Jenkins)', email: 'admin@legalupdate.ai', pw: 'admin123', role: 'admin' },
    { label: 'Senior Counsel (Vikram Mehta)', email: 'senior.counsel@legalupdate.ai', pw: 'review123', role: 'reviewer' },
    { label: 'Compliance Officer (Ananya Sharma)', email: 'compliance.officer@legalupdate.ai', pw: 'review123', role: 'reviewer' },
    { label: 'Analyst (Rohan Gupta)', email: 'analyst@legalupdate.ai', pw: 'viewer123', role: 'viewer' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        const res = await api.post('/auth/register', {
          email,
          password,
          name,
          department,
          role: 'reviewer',
        });
        if (res.success) {
          await login(email, password);
        }
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDemo = (account) => {
    setEmail(account.email);
    setPassword(account.pw);
    setError(null);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#0f172a',
      padding: '24px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '480px',
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          backgroundColor: '#1e293b',
          padding: '28px 32px',
          color: '#ffffff',
          textAlign: 'center'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px',
            color: '#fff',
            fontSize: '24px',
            fontWeight: 800
          }}>
            L
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 800, letterSpacing: '-0.4px' }}>
            LegalUpdate AI
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
            Regulatory Change Summarizer & Monitoring Suite
          </p>
        </div>

        {/* Form Body */}
        <div style={{ padding: '32px' }}>
          {error && (
            <div style={{
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '13px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {isRegister && (
              <>
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    placeholder="Advocate Sarah Jenkins"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Department / Practice Area</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Capital Markets & Banking Regulatory"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                  />
                </div>
              </>
            )}

            <div className="form-group">
              <label className="form-label">Work Email</label>
              <input
                type="email"
                required
                className="form-input"
                placeholder="counsel@legalupdate.ai"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                required
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', padding: '11px', marginTop: '8px' }}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                isRegister ? 'Create Account' : 'Sign In to Workspace'
              )}
            </button>
          </form>

          {/* Quick Demo Logins */}
          <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '10px' }}>
              One-Click Demonstration Logins:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              {demoAccounts.map((acc, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSelectDemo(acc)}
                  className="btn btn-outline btn-sm"
                  style={{
                    fontSize: '11px',
                    justifyContent: 'flex-start',
                    textAlign: 'left',
                    padding: '6px 8px',
                    borderColor: email === acc.email ? '#2563eb' : '#e2e8f0',
                    backgroundColor: email === acc.email ? '#eff6ff' : '#ffffff'
                  }}
                >
                  <User size={12} />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {acc.label.split(' ')[0]} ({acc.role})
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '13px', color: '#64748b' }}>
            {isRegister ? 'Already have an account? ' : "Don't have an account? "}
            <button
              type="button"
              onClick={() => setIsRegister(!isRegister)}
              style={{
                background: 'none',
                border: 'none',
                color: '#2563eb',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {isRegister ? 'Sign In' : 'Register'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

