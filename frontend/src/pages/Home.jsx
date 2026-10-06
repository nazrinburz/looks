import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import ProfileCard from '../components/ProfileCard';
import './Home.css';

const SORT_OPTIONS = [
  { value: 'rating', label: '⭐ Top Rated' },
  { value: 'newest', label: '🕐 Newest' },
];

export default function Home() {
  const [profiles, setProfiles] = useState([]);
  const [total, setTotal] = useState(0);
  const [sort, setSort] = useState('rating');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError('');
      const { data, error: err } = await api.get(`/profiles?sort=${sort}&limit=50`);
      if (err) { setError(err); setLoading(false); return; }
      setProfiles(data.profiles || []);
      setTotal(data.total || 0);
      setLoading(false);
    }
    load();
  }, [sort]);

  return (
    <div className="home-page page-wrapper">
      <div className="container">
        {/* Hero */}
        <header className="home-hero animate-fade-up">
          <div className="home-hero-badge">✦ Community Reviews</div>
          <h1 className="home-hero-title">
            Rate. Review.<br />
            <span className="gradient-text">Be Rated.</span>
          </h1>
          <p className="home-hero-subtitle">
            Create your profile and let the community rate you across
            Looks, Style & Vibe. Anonymous, constructive, real.
          </p>
          <div className="home-hero-actions">
            <button
              className="btn btn-primary btn-lg"
              id="hero-get-started"
              onClick={() => navigate('/auth')}
            >
              Get Started
            </button>
            <div className="home-hero-stats">
              <span><strong>{total}</strong> profiles</span>
            </div>
          </div>
        </header>

        {/* Controls */}
        <div className="home-controls animate-fade-up">
          <h2 className="home-section-title">Community Profiles</h2>
          <div className="home-sort">
            {SORT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                id={`sort-${opt.value}`}
                className={`sort-btn ${sort === opt.value ? 'active' : ''}`}
                onClick={() => setSort(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Profiles grid */}
        {loading && (
          <div className="page-loader">
            <div className="loader" />
            <p>Loading profiles…</p>
          </div>
        )}

        {!loading && error && (
          <div className="alert alert-error" style={{ margin: '2rem 0' }}>{error}</div>
        )}

        {!loading && !error && profiles.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">👤</div>
            <h3>No profiles yet</h3>
            <p>Be the first to create a profile!</p>
          </div>
        )}

        {!loading && !error && (
          <div className="profiles-grid">
            {profiles.map((profile, i) => (
              <div key={profile.id} style={{ animationDelay: `${i * 0.05}s` }}>
                <ProfileCard profile={profile} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
