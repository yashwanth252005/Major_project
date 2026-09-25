/**
 * Activity strip: flex row of div bars, height = count / peak * 100%.
 * Each bar carries a `title` tooltip ("Sep 12: 3 scans"); the day number is
 * repeated as a tiny caption under each bar.
 */
export default function MiniBars({ points, max, height = 56 }) {
  const safePoints = Array.isArray(points) ? points : [];

  if (safePoints.length === 0) {
    return <p className="muted-line">No activity data yet.</p>;
  }

  const peak = Math.max(
    1,
    Number(max) || Math.max(0, ...safePoints.map((p) => Number(p?.count) || 0))
  );

  return (
    <div
      className="minibars"
      role="img"
      aria-label={`Scans per day across the last ${safePoints.length} days, oldest to newest`}
    >
      <div className="minibars__bars" style={{ height }}>
        {safePoints.map((p) => {
          const count = Number(p?.count) || 0;
          return (
            <div
              key={p.label}
              className="minibars__slot"
              title={`${p.label}: ${count} scan${count === 1 ? "" : "s"}`}
            >
              <div
                className={`minibars__bar${count === 0 ? " minibars__bar--zero" : ""}`}
                style={{ height: `${(count / peak) * 100}%` }}
              />
            </div>
          );
        })}
      </div>
      <div className="minibars__labels" aria-hidden="true">
        {safePoints.map((p) => (
          <span key={p.label} className="minibars__label">
            {String(p.label).slice(-2)}
          </span>
        ))}
      </div>
    </div>
  );
}
