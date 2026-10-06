import './RatingBreakdown.css';

/**
 * RatingBreakdown – shows a bar chart of rating distribution for
 * one dimension (looks / style / vibe) from value 10 down to 1.
 */
function DimensionBreakdown({ label, data, colorClass }) {
  const max = Math.max(...Object.values(data), 1);

  return (
    <div className="breakdown-dimension">
      <h4 className={`breakdown-label ${colorClass}`}>{label}</h4>
      <div className="breakdown-bars">
        {Array.from({ length: 10 }, (_, i) => 10 - i).map((score) => {
          const count = data[score] || 0;
          const pct = (count / max) * 100;
          return (
            <div key={score} className="breakdown-row">
              <span className="breakdown-score">{score}</span>
              <div className="breakdown-track">
                <div
                  className={`breakdown-fill ${colorClass}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="breakdown-count">{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function RatingBreakdown({ breakdown }) {
  if (!breakdown) return null;

  return (
    <div className="rating-breakdown">
      <DimensionBreakdown label="Looks"  data={breakdown.looks} colorClass="looks"  />
      <DimensionBreakdown label="Style"  data={breakdown.style} colorClass="style"  />
      <DimensionBreakdown label="Vibe"   data={breakdown.vibe}  colorClass="vibe"   />
    </div>
  );
}
