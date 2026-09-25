/**
 * Horizontal confidence meter (0–100) with tick marks at the 50% decision
 * boundary and the 70% uncertain cutoff. Pure divs — html2canvas-safe.
 * `compact` drops the scale row (used inside table cells).
 */
export default function ConfidenceMeter({ value, compact = false }) {
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));

  return (
    <div
      className={`meter${compact ? " meter--compact" : ""}`}
      role="img"
      aria-label={`Model confidence ${clamped.toFixed(1)} percent of 100`}
    >
      <div className="meter__track">
        <div className="meter__fill" style={{ width: `${clamped}%` }} />
        <span className="meter__tick meter__tick--boundary" title="Decision boundary — 50%" />
        <span className="meter__tick meter__tick--uncertain" title="Uncertain cutoff — 70%" />
      </div>
      {!compact && (
        <div className="meter__scale" aria-hidden="true">
          <span>0%</span>
          <span>50% &middot; boundary</span>
          <span>70% &middot; cutoff</span>
          <span>100%</span>
        </div>
      )}
    </div>
  );
}
