import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import './AuthPage.css';

const PASSWORD_RE = /^.{8,}$/;

function PasswordStrength({ password }) {
  const score = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ].filter(Boolean).length;

  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  const colors = ['', '#ef4444', '#f59e0b', '#22c55e', '#7c5cfc'];

  if (!password) return null;
  return (
    <div className="pw-strength">
      <div className="pw-bars">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="pw-bar"
            style={{ background: i <= score ? colors[score] : 'var(--clr-surface-3)' }}
          />
        ))}
      </div>
      <span style={{ color: colors[score], fontSize: '0.78rem' }}>{labels[score]}</span>
    </div>
  );
}

export default function AuthPage() {
  const [tab, setTab] = useState('login'); // 'login' | 'signup'
  const { signup, loginWithCredentials } = useAuth();
  const navigate = useNavigate();

  // Login state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPass, setLoginPass]   = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Signup state
  const [sigUsername, setSigUsername] = useState('');
  const [sigEmail, setSigEmail]       = useState('');
  const [sigPass, setSigPass]         = useState('');
  const [sigConfirm, setSigConfirm]   = useState('');
  const [sigErrors, setSigErrors]     = useState({});
  const [sigLoading, setSigLoading]   = useState(false);

  async function handleLogin(e) {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);
    const { error } = await loginWithCredentials(loginEmail, loginPass);
    setLoginLoading(false);
    if (error) return setLoginError(error);
    navigate('/');
  }

  async function handleSignup(e) {
    e.preventDefault();
    const errors = {};
    if (!sigUsername.trim()) errors.username = 'Username is required';
    if (!sigEmail.trim()) errors.email = 'Email is required';
    if (!PASSWORD_RE.test(sigPass)) errors.password = 'Password must be at least 8 characters';
    if (sigPass !== sigConfirm) errors.confirm = 'Passwords do not match';
    setSigErrors(errors);
    if (Object.keys(errors).length) return;

    setSigLoading(true);
    const { error } = await signup(sigUsername.trim(), sigEmail.trim(), sigPass);
    setSigLoading(false);
    if (error) return setSigErrors({ global: error });
    navigate('/');
  }

  return (
    <div className="auth-page page-wrapper">
      <div className="auth-card card animate-fade-up">
        {/* Header */}
        <div className="auth-header">
          <div className="auth-logo">✦</div>
          <h1 className="auth-title">LooksApp</h1>
          <p className="auth-subtitle">Rate profiles. Build community.</p>
        </div>

        {/* Tabs */}
        <div className="auth-tabs">
          <button
            id="tab-login"
            className={`auth-tab ${tab === 'login' ? 'active' : ''}`}
            onClick={() => { setTab('login'); setLoginError(''); }}
          >
            Login
          </button>
          <button
            id="tab-signup"
            className={`auth-tab ${tab === 'signup' ? 'active' : ''}`}
            onClick={() => { setTab('signup'); setSigErrors({}); }}
          >
            Sign Up
          </button>
        </div>

        {/* ── LOGIN ── */}
        {tab === 'login' && (
          <form className="auth-form animate-fade-in" onSubmit={handleLogin} id="login-form">
            {loginError && <div className="alert alert-error">{loginError}</div>}

            <div className="form-group">
              <label className="form-label" htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                className="form-input"
                placeholder="you@example.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={loginPass}
                onChange={(e) => setLoginPass(e.target.value)}
                required
              />
            </div>

            <button
              id="login-submit"
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={loginLoading}
              style={{ width: '100%' }}
            >
              {loginLoading ? 'Signing in…' : 'Sign In'}
            </button>

            <p className="auth-switch">
              No account?{' '}
              <button type="button" className="auth-link" onClick={() => setTab('signup')}>
                Create one
              </button>
            </p>
          </form>
        )}

        {/* ── SIGNUP ── */}
        {tab === 'signup' && (
          <form className="auth-form animate-fade-in" onSubmit={handleSignup} id="signup-form">
            {sigErrors.global && <div className="alert alert-error">{sigErrors.global}</div>}

            <div className="form-group">
              <label className="form-label" htmlFor="sig-username">Username</label>
              <input
                id="sig-username"
                type="text"
                className="form-input"
                placeholder="cool_username"
                value={sigUsername}
                onChange={(e) => setSigUsername(e.target.value)}
                autoFocus
              />
              {sigErrors.username && <p className="form-error">{sigErrors.username}</p>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="sig-email">Email</label>
              <input
                id="sig-email"
                type="email"
                className="form-input"
                placeholder="you@example.com"
                value={sigEmail}
                onChange={(e) => setSigEmail(e.target.value)}
              />
              {sigErrors.email && <p className="form-error">{sigErrors.email}</p>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="sig-password">Password</label>
              <input
                id="sig-password"
                type="password"
                className="form-input"
                placeholder="Min 8 characters"
                value={sigPass}
                onChange={(e) => setSigPass(e.target.value)}
              />
              <PasswordStrength password={sigPass} />
              {sigErrors.password && <p className="form-error">{sigErrors.password}</p>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="sig-confirm">Confirm Password</label>
              <input
                id="sig-confirm"
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={sigConfirm}
                onChange={(e) => setSigConfirm(e.target.value)}
              />
              {sigErrors.confirm && <p className="form-error">{sigErrors.confirm}</p>}
            </div>

            <button
              id="signup-submit"
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={sigLoading}
              style={{ width: '100%' }}
            >
              {sigLoading ? 'Creating account…' : 'Create Account'}
            </button>

            <p className="auth-switch">
              Already have an account?{' '}
              <button type="button" className="auth-link" onClick={() => setTab('login')}>
                Sign in
              </button>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
