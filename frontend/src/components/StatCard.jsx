/**
 * KPI chip: label over a large mono value with optional sub line.
 * tone shifts the value color: "default" | "accent" | "alert" | "safe".
 */
export default function StatCard({ label, value, sub, tone = "default", title }) {
  const toneClass = tone !== "default" ? ` stat-card--${tone}` : "";

  return (
    <div className={`stat-card${toneClass}`} title={title}>
      <span className="stat-card__label">{label}</span>
      <span className="stat-card__value">{value}</span>
      {sub && <span className="stat-card__sub">{sub}</span>}
    </div>
  );
}
