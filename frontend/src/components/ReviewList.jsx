import './ReviewList.css';

function formatDate(iso) {
  if (!iso) return '';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(iso));
}

function RatingPill({ label, value, colorClass }) {
  return (
    <span className={`review-pill ${colorClass}`}>
      ★ {value} {label}
    </span>
  );
}

export default function ReviewList({ reviews, currentUserId, onEdit, onDelete }) {
  if (!reviews || reviews.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">💬</div>
        <h3>No reviews yet</h3>
        <p>Be the first to leave feedback on this profile.</p>
      </div>
    );
  }

  return (
    <div className="review-list">
      {reviews.map((review) => {
        const isOwn = currentUserId && review.reviewer_user_id === currentUserId;
        const overall = ((review.looks_rating + review.style_rating + review.vibe_rating) / 3).toFixed(1);

        return (
          <article key={review.id} className={`review-card animate-fade-in ${isOwn ? 'review-card-own' : ''}`}>
            <div className="review-card-header">
              {/* Anonymous identity */}
              <div className="review-card-author">
                <div className="review-avatar-placeholder">
                  {isOwn ? '✦' : '◎'}
                </div>
                <div>
                  <p className="review-author-name">
                    {isOwn ? 'Your Review' : 'Community Review'}
                  </p>
                  <p className="review-date">{formatDate(review.created_at)}</p>
                </div>
              </div>

              {/* Overall */}
              <div className="review-overall">
                <span className="rating-star">★</span> {overall}
              </div>
            </div>

            {/* Dimension pills */}
            <div className="review-ratings">
              <RatingPill label="Looks" value={review.looks_rating} colorClass="looks" />
              <RatingPill label="Style" value={review.style_rating} colorClass="style" />
              <RatingPill label="Vibe"  value={review.vibe_rating}  colorClass="vibe"  />
            </div>

            {/* Feedback text */}
            {review.feedback_text && (
              <blockquote className="review-feedback">"{review.feedback_text}"</blockquote>
            )}

            {/* Own review actions */}
            {isOwn && (
              <div className="review-actions">
                <button className="btn btn-ghost btn-sm" onClick={() => onEdit(review)}>Edit</button>
                <button className="btn btn-danger btn-sm" onClick={() => onDelete(review.id)}>Delete</button>
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}
