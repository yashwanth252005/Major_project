import { useEffect, useState } from "react";
import { fetchStats } from "../api";

const DISTRIBUTION_CLASSES = [
  { label: "Tumour Detected", tone: "alert" },
  { label: "No Tumour Detected", tone: "safe" },
];

export default function Insights() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setStats(null);
    setError(null);
    (async () => {
      try {
        const data = await fetchStats();
        if (!cancelled) setStats(data);
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load insights.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <main className="insights-panel">
        <div className="panel-heading">
          <span className="panel-index">I</span> Insights
        </div>
        <div className="error-box">⚠ {error}</div>
      </main>
    );
  }

  if (!stats) {
    return (
      <main className="insights-panel">
        <p className="loading-line">Loading insights…</p>
      </main>
    );
  }

  if (stats.total_scans === 0) {
    return (
      <main className="insights-panel">
        <div className="panel-heading">
          <span className="panel-index">I</span> Insights
        </div>
        <p className="loading-line">
          No scans stored yet. Statistics will appear after the first analysis.
        </p>
      </main>
    );
  }

  const formatValue = (value, suffix, transform) =>
    value == null ? "—" : `${transform(value)}${suffix}`;

  const statCards = [
    { label: "Total scans", value: String(stats.total_scans) },
    {
      label: "Average model confidence",
      value: formatValue(stats.average_confidence_percent, "%", (v) => v.toFixed(2)),
    },
    {
      label: "Average processing time",
      value: formatValue(stats.average_processing_time_ms, " ms", (v) => v.toFixed(2)),
    },
    { label: "Scans last 7 days", value: String(stats.scans_last_7_days) },
    { label: "Scans last 30 days", value: String(stats.scans_last_30_days) },
    {
      label: "Latest scan",
      value:
        stats.latest_scan_created_at == null
          ? "—"
          : new Date(stats.latest_scan_created_at).toLocaleString(),
    },
  ];

  return (
    <main className="insights-panel">
      <div className="panel-heading">
        <span className="panel-index">I</span> Insights — Stored Scan Statistics
      </div>

      <p className="stats-caption">
        These are application-history statistics about scans stored in this browser
        deployment — not model performance metrics.
      </p>

      <div className="stats-grid">
        {statCards.map((c) => (
          <div className="stat-card" key={c.label}>
            <span className="stat-value">{c.value}</span>
            <span className="stat-label">{c.label}</span>
          </div>
        ))}
      </div>

      <section className="distribution">
        <h2 className="distribution-title">Stored prediction distribution</h2>
        {DISTRIBUTION_CLASSES.map((c) => {
          const count = stats.count_by_prediction?.[c.label] ?? 0;
          const widthPct = stats.total_scans > 0 ? (count / stats.total_scans) * 100 : 0;
          return (
            <div className="distribution-row" key={c.label}>
              <span className={c.tone === "alert" ? "pred-alert" : "pred-safe"}>
                {c.label}
              </span>
              <span className="distribution-count">{count}</span>
              <div className="distribution-bar">
                <div
                  className={`distribution-fill distribution-fill-${c.tone}`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </section>
    </main>
  );
}
