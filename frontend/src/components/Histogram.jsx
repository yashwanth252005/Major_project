/**
 * Confidence histogram: pure div columns, one per bin
 * ({ from, to, count }), height = count / peak * 100%.
 * Falls back to an empty state when `total` is 0 or no bins are given.
 */
import EmptyState from "./EmptyState";

export default function Histogram({ bins, total, axisNote }) {
  const safeBins = Array.isArray(bins) ? bins : [];

  if (!total || safeBins.length === 0) {
    return (
      <EmptyState
        title="No scans to plot yet"
        hint="The confidence distribution appears after the first analysis."
      />
    );
  }

  const peak = Math.max(1, ...safeBins.map((b) => Number(b?.count) || 0));

  return (
    <div
      className="histogram"
      role="img"
      aria-label="Number of stored scans per model-confidence band"
    >
      <div className="histogram__cols">
        {safeBins.map((b) => {
          const count = Number(b?.count) || 0;
          return (
            <div
              key={`${b.from}-${b.to}`}
              className="histogram__col"
              title={`${b.from}–${b.to}%: ${count} scan${count === 1 ? "" : "s"}`}
            >
              <span className="histogram__count">{count > 0 ? count : ""}</span>
              <div className="histogram__bar-wrap">
                <div
                  className={`histogram__bar${count === 0 ? " histogram__bar--zero" : ""}`}
                  style={{ height: `${Math.max(2, (count / peak) * 100)}%` }}
                />
              </div>
              <span className="histogram__tick">{Math.round(b.from)}%</span>
            </div>
          );
        })}
      </div>
      {axisNote && <p className="histogram__axis-note">{axisNote}</p>}
    </div>
  );
}
