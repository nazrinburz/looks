import { useNavigate } from 'react-router-dom';
import './ProfileCard.css';

/** Star rating badge */
function RatingBadge({ label, value, colorClass }) {
  if (!value || value === 0) return null;
  return (
    <span className={`badge ${colorClass}`}>
      ★ {value.toFixed(1)} {label}
    </span>
  );
}

export default function ProfileCard({ profile }) {
  const navigate = useNavigate();
  const { id, username, bio, avatar_url, avg_looks, avg_style, avg_vibe, avg_overall, review_count } = profile;

  const defaultAvatar = `https://i.pravatar.cc/300?u=${username}`;

  return (
    <article
      className="profile-card card animate-fade-up"
      onClick={() => navigate(`/profile/${id}`)}
      id={`profile-card-${id}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/profile/${id}`)}
    >
      {/* Avatar + overall rating */}
      <div className="profile-card-header">
        <img
          src={avatar_url || defaultAvatar}
          alt={`${username} avatar`}
          className="avatar avatar-lg profile-card-avatar"
          onError={(e) => { e.target.src = defaultAvatar; }}
        />
        {avg_overall > 0 && (
          <div className="profile-card-overall">
            <span className="rating-star">★</span>
            {avg_overall.toFixed(1)}
          </div>
        )}
      </div>

      {/* Info */}
      <div className="profile-card-body">
        <h3 className="profile-card-username">@{username}</h3>
        {bio && <p className="profile-card-bio">{bio.length > 80 ? bio.slice(0, 80) + '…' : bio}</p>}

        {/* Ratings row */}
        <div className="ratings-row profile-card-ratings">
          <RatingBadge label="Looks" value={avg_looks} colorClass="badge-looks" />
          <RatingBadge label="Style" value={avg_style} colorClass="badge-style" />
          <RatingBadge label="Vibe"  value={avg_vibe}  colorClass="badge-vibe"  />
        </div>

        {/* Footer */}
        <div className="profile-card-footer">
          <span className="profile-card-reviews">
            {review_count} {review_count === 1 ? 'review' : 'reviews'}
          </span>
          <span className="profile-card-cta">View →</span>
        </div>
      </div>
    </article>
  );
}
