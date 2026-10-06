import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../auth';
import ReviewList from '../components/ReviewList';
import RatingBreakdown from '../components/RatingBreakdown';
import './ProfilePage.css';

function StatPill({ label, value, colorClass }) {
  if (!value && value !== 0) return null;
  return (
    <div className={`stat-pill ${colorClass}`}>
      <span className="stat-pill-value">★ {typeof value === 'number' ? value.toFixed(1) : value}</span>
      <span className="stat-pill-label">{label}</span>
    </div>
  );
}

export default function ProfilePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [profile, setProfile] = useState(null);
  const [breakdown, setBreakdown] = useState(null);
  const [myReview, setMyReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleteReviewId, setDeleteReviewId] = useState(null);

  // Determine if we're looking at /profile/me
  const isMePage = id === 'me';

  const load = useCallback(async () => {
    setLoading(true);
    setError('');

    let profileId = id;

    // Resolve "me" to actual profile id
    if (isMePage) {
      const { data, error: e } = await api.get('/me/profile');
      if (e) { setError('You don\'t have a profile yet. Create one!'); setLoading(false); return; }
      profileId = data.id;
    }

    const { data, error: err } = await api.get(`/profiles/${profileId}`);
    if (err) { setError(err); setLoading(false); return; }
    setProfile(data);

    // Fetch breakdown
    const { data: bd } = await api.get(`/profiles/${profileId}/rating-breakdown`);
    if (bd) setBreakdown(bd);

    // Fetch my review (if logged in and not own profile)
    if (user && data.user_id !== user.id) {
      const { data: mr } = await api.get(`/profiles/${profileId}/my-review`);
      if (mr) setMyReview(mr);
    }

    setLoading(false);
  }, [id, user, isMePage]);

  useEffect(() => { load(); }, [load]);

  async function handleDeleteProfile() {
    const { error: err } = await api.delete(`/profiles/${profile.id}`);
    if (err) return alert(err);
    navigate('/');
  }

  async function handleDeleteReview(reviewId) {
    const { error: err } = await api.delete(`/reviews/${reviewId}`);
    if (err) return alert(err);
    setDeleteReviewId(null);
    load(); // refresh
  }

  function handleEditReview(review) {
    navigate(`/profile/${profile.id}/review?edit=${review.id}`);
  }

  if (loading) {
    return (
      <div className="page-wrapper">
        <div className="page-loader">
          <div className="loader" />
          <p>Loading profile…</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="page-wrapper">
        <div className="container">
          <div className="alert alert-error" style={{ marginTop: '2rem' }}>{error || 'Profile not found'}</div>
          {isMePage && user && (
            <button
              className="btn btn-primary"
              style={{ marginTop: '1rem' }}
              onClick={() => navigate('/profile/create')}
            >
              Create My Profile
            </button>
          )}
        </div>
      </div>
    );
  }

  const isOwnProfile = user && profile.user_id === user.id;
  const defaultAvatar = `https://i.pravatar.cc/300?u=${profile.username}`;
  const hasReviewed = !!myReview;

  return (
    <div className="profile-page page-wrapper">
      <div className="container">
        {/* Hero Header */}
        <div className="profile-hero card animate-fade-up">
          <div className="profile-hero-bg" />
          <div className="profile-hero-content">
            <img
              src={profile.avatar_url || defaultAvatar}
              alt={`${profile.username} avatar`}
              className="avatar avatar-xl profile-hero-avatar"
              onError={(e) => { e.target.src = defaultAvatar; }}
            />
            <div className="profile-hero-info">
              <h1 className="profile-hero-username">@{profile.username}</h1>
              {profile.bio && <p className="profile-hero-bio">{profile.bio}</p>}

              {/* Ratings */}
              <div className="profile-hero-stats">
                <StatPill label="Looks"   value={profile.avg_looks}   colorClass="looks" />
                <StatPill label="Style"   value={profile.avg_style}   colorClass="style" />
                <StatPill label="Vibe"    value={profile.avg_vibe}    colorClass="vibe" />
                <StatPill label="Overall" value={profile.avg_overall} colorClass="overall" />
              </div>

              <p className="profile-review-count">
                {profile.review_count} {profile.review_count === 1 ? 'review' : 'reviews'}
              </p>
            </div>

            {/* Actions */}
            <div className="profile-hero-actions">
              {isOwnProfile && (
                <>
                  <button
                    id="edit-profile-btn"
                    className="btn btn-ghost btn-sm"
                    onClick={() => navigate(`/profile/${profile.id}/edit`)}
                  >
                    ✏️ Edit Profile
                  </button>
                  <button
                    id="delete-profile-btn"
                    className="btn btn-danger btn-sm"
                    onClick={() => setDeleteConfirm(true)}
                  >
                    🗑 Delete
                  </button>
                </>
              )}
              {!isOwnProfile && user && !hasReviewed && (
                <button
                  id="rate-profile-btn"
                  className="btn btn-primary"
                  onClick={() => navigate(`/profile/${profile.id}/review`)}
                >
                  ★ Rate This Profile
                </button>
              )}
              {!isOwnProfile && user && hasReviewed && (
                <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/profile/${profile.id}/review?edit=${myReview.id}`)}>
                  ✏️ Edit My Review
                </button>
              )}
              {!user && (
                <button className="btn btn-primary" onClick={() => navigate('/auth')}>
                  Login to Rate
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Delete Profile confirm */}
        {deleteConfirm && (
          <div className="alert alert-error animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <span>⚠️ Delete your profile? This cannot be undone.</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-danger btn-sm" onClick={handleDeleteProfile}>Yes, Delete</button>
              <button className="btn btn-ghost btn-sm" onClick={() => setDeleteConfirm(false)}>Cancel</button>
            </div>
          </div>
        )}

        {/* Rating breakdown */}
        {breakdown && profile.review_count > 0 && (
          <section className="profile-section animate-fade-up">
            <h2 className="section-title">Rating Breakdown</h2>
            <RatingBreakdown breakdown={breakdown} />
          </section>
        )}

        {/* Reviews */}
        <section className="profile-section animate-fade-up">
          <h2 className="section-title">
            Community Reviews
            <span style={{ color: 'var(--clr-text-3)', fontWeight: 400, fontSize: '0.9rem' }}>
              {profile.review_count}
            </span>
          </h2>
          <ReviewList
            reviews={profile.reviews}
            currentUserId={user?.id}
            onEdit={handleEditReview}
            onDelete={(reviewId) => {
              if (deleteReviewId === reviewId) {
                handleDeleteReview(reviewId);
              } else {
                setDeleteReviewId(reviewId);
              }
            }}
          />
          {deleteReviewId && (
            <div className="alert alert-error animate-fade-in" style={{ marginTop: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
              <span>Delete this review?</span>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-danger btn-sm" onClick={() => handleDeleteReview(deleteReviewId)}>Delete</button>
                <button className="btn btn-ghost btn-sm" onClick={() => setDeleteReviewId(null)}>Cancel</button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
