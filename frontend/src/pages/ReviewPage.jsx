import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../auth';
import './ReviewPage.css';

/** Interactive 1-10 rating slider + display */
function RatingInput({ label, value, onChange, colorClass, id }) {
  return (
    <div className={`rating-input-group ${colorClass}`}>
      <div className="rating-input-header">
        <label htmlFor={id} className="rating-input-label">{label}</label>
        <span className="rating-input-value">{value}</span>
      </div>
      <input
        id={id}
        type="range"
        min={1} max={10} step={1}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        className={`rating-slider ${colorClass}`}
      />
      <div className="rating-slider-ticks">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
          <span key={n} className={`tick ${n <= value ? 'active' : ''}`}>{n}</span>
        ))}
      </div>
    </div>
  );
}

export default function ReviewPage() {
  const { id: profileId } = useParams();
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit');
  const navigate = useNavigate();
  const { user } = useAuth();

  const [profile, setProfile] = useState(null);
  const [looks, setLooks] = useState(7);
  const [style, setStyle] = useState(7);
  const [vibe, setVibe]  = useState(7);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const MAX_CHARS = 500;
  const overall = ((looks + style + vibe) / 3).toFixed(1);

  // Redirect if not logged in
  useEffect(() => {
    if (!user) navigate('/auth');
  }, [user, navigate]);

  // Load profile + existing review if editing
  useEffect(() => {
    async function load() {
      setLoading(true);
      const { data, error: err } = await api.get(`/profiles/${profileId}`);
      if (err) { setError(err); setLoading(false); return; }
      setProfile(data);

      if (editId) {
        const { data: rv } = await api.get(`/profiles/${profileId}/my-review`);
        if (rv) {
          setLooks(rv.looks_rating);
          setStyle(rv.style_rating);
          setVibe(rv.vibe_rating);
          setFeedback(rv.feedback_text || '');
        }
      }
      setLoading(false);
    }
    load();
  }, [profileId, editId]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    const payload = {
      looks_rating: looks,
      style_rating: style,
      vibe_rating: vibe,
      feedback_text: feedback.trim(),
    };

    let result;
    if (editId) {
      result = await api.patch(`/reviews/${editId}`, payload);
    } else {
      result = await api.post(`/profiles/${profileId}/reviews`, payload);
    }

    setSubmitting(false);
    if (result.error) return setError(result.error);
    navigate(`/profile/${profileId}`);
  }

  if (loading || !profile) {
    return (
      <div className="page-wrapper">
        <div className="page-loader"><div className="loader" /></div>
      </div>
    );
  }

  const defaultAvatar = `https://i.pravatar.cc/300?u=${profile.username}`;

  return (
    <div className="review-page page-wrapper">
      <div className="container review-container">
        {/* Mini profile header */}
        <div className="review-profile-mini card animate-fade-up">
          <img
            src={profile.avatar_url || defaultAvatar}
            alt={profile.username}
            className="avatar avatar-md"
            onError={(e) => { e.target.src = defaultAvatar; }}
          />
          <div>
            <p className="review-profile-mini-name">@{profile.username}</p>
            <p className="review-profile-mini-bio">
              {profile.bio ? (profile.bio.length > 60 ? profile.bio.slice(0, 60) + '…' : profile.bio) : ''}
            </p>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            style={{ marginLeft: 'auto' }}
            onClick={() => navigate(`/profile/${profileId}`)}
          >
            ← Back
          </button>
        </div>

        {/* Review form */}
        <div className="card review-form-card animate-fade-up">
          <h2 className="review-form-title">
            {editId ? '✏️ Edit Your Review' : '★ Rate This Profile'}
          </h2>

          {error && <div className="alert alert-error">{error}</div>}

          <form id="review-form" onSubmit={handleSubmit}>
            {/* Rating sliders */}
            <div className="review-sliders">
              <RatingInput
                id="slider-looks"
                label="👀 Looks"
                value={looks}
                onChange={setLooks}
                colorClass="looks"
              />
              <RatingInput
                id="slider-style"
                label="✨ Style"
                value={style}
                onChange={setStyle}
                colorClass="style"
              />
              <RatingInput
                id="slider-vibe"
                label="⚡ Vibe"
                value={vibe}
                onChange={setVibe}
                colorClass="vibe"
              />
            </div>

            {/* Overall (read-only) */}
            <div className="review-overall-display">
              <span>Overall Score</span>
              <span className="review-overall-value">★ {overall}</span>
            </div>

            {/* Feedback */}
            <div className="form-group" style={{ marginTop: 'var(--space-5)' }}>
              <label className="form-label" htmlFor="feedback-text">
                Feedback <span style={{ color: 'var(--clr-text-3)', fontWeight: 400 }}>(optional)</span>
              </label>
              <textarea
                id="feedback-text"
                className="form-textarea"
                placeholder="Share constructive feedback…"
                value={feedback}
                onChange={(e) => {
                  if (e.target.value.length <= MAX_CHARS) setFeedback(e.target.value);
                }}
                rows={4}
              />
              <p className={`form-hint ${feedback.length > MAX_CHARS * 0.9 ? 'form-error' : ''}`}>
                {feedback.length} / {MAX_CHARS}
              </p>
            </div>

            {/* Actions */}
            <div className="review-form-actions">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => navigate(`/profile/${profileId}`)}
              >
                Cancel
              </button>
              <button
                id="review-submit"
                type="submit"
                className="btn btn-primary"
                disabled={submitting}
              >
                {submitting ? 'Submitting…' : editId ? 'Update Review' : 'Submit Review'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
