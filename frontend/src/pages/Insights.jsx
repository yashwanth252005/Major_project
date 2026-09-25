import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchStats } from "../api";
import { binConfidence, countsByDay, medianConfidence, scansToday, summarizeRows } from "../utils/stats";
import Badge from "../components/Badge";
import Card from "../components/Card";
import DisclaimerBanner from "../components/DisclaimerBanner";
import EmptyState from "../components/EmptyState";
import Histogram from "../components/Histogram";
import MiniBars from "../components/MiniBars";
import PageHeader from "../components/PageHeader";
import StatCard from "../components/StatCard";
import useHistoryData from "../hooks/useHistoryData";

const DISTRIBUTION_CLASSES = [
  { label: "Tumour Detected", tone: "alert" },
  { label: "No Tumour Detected", tone: "safe" },
];

// Rows without a usable confidence value sort last.
const confidenceOf = (r) => {
  const c = Number(r?.confidence);
  return Number.isFinite(c) ? c : Number.POSITIVE_INFINITY;
};

export default function Insights() {
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState(null);
  const { rows, loading: rowsLoading, error: rowsError } = useHistoryData();

  useEffect(() => {
    let cancelled = false;
    setStats(null);
    setStatsError(null);
    (async () => {
      try {
        const data = await fetchStats();
        if (!cancelled) setStats(data);
      } catch (e) {
        if (!cancelled) setStatsError(e.message || "Failed to load insights.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const summary = summarizeRows(rows || []);
  const bins = binConfidence(rows || []);
  const activity = countsByDay(rows || [], 14);
  const lowest = [...(rows || [])]
    .sort((a, b) => confidenceOf(a) - confidenceOf(b))
    .slice(0, 5);

  // Row-derived card values degrade to "—" while the list loads.
  const rowValue = (compute) => (rowsLoading ? "—" : compute());

  const statCards = stats
    ? [
        { label: "Total scans", value: String(stats.total_scans) },
        {
          label: "Scans today (local time)",
          value: rowValue(() => String(scansToday(rows || []))),
        },
        { label: "Scans last 7 days", value: String(stats.scans_last_7_days) },
        { label: "Scans last 30 days", value: String(stats.scans_last_30_days) },
        {
          label: "Verdict split",
          value: `${stats.count_by_prediction?.["Tumour Detected"] ?? 0} / ${
            stats.count_by_prediction?.["No Tumour Detected"] ?? 0
          }`,
          sub: "tumour / no tumour",
        },
        {
          label: "Avg model confidence",
          value:
            stats.average_confidence_percent == null
              ? "—"
              : `${stats.average_confidence_percent.toFixed(2)}%`,
          sub: "not a diagnostic score",
        },
        {
          label: "Median confidence",
          value: rowValue(() => {
            const m = medianConfidence(rows || []);
            return m == null ? "—" : `${m.toFixed(2)}%`;
          }),
        },
        {
          label: "Avg processing time",
          value:
            stats.average_processing_time_ms == null
              ? "—"
              : `${stats.average_processing_time_ms.toFixed(2)} ms`,
        },
        {
          label: "Uncertain calls <70%",
          value: rowValue(() => String(summary.uncertain70)),
          sub: "low-certainty outputs — not errors",
        },
      ]
    : [];

  return (
    <main className="page insights">
      <PageHeader title="Insights" />

      <DisclaimerBanner variant="banner" />

      <p className="insights-caption">
        Application-usage and model-confidence statistics about scans stored in this
        deployment — not model performance metrics.
      </p>

      {statsError && <div className="error-box">⚠ {statsError}</div>}

      {!statsError && !stats && (
        <EmptyState
          title="Loading insights…"
          hint="Fetching stored-scan statistics."
        />
      )}

      {stats && stats.total_scans === 0 && (
        <EmptyState
          title="No scans stored yet"
          hint="Statistics will appear after the first analysis."
          action={<Link to="/" className="btn btn--primary">Analyze a scan</Link>}
        />
      )}

      {stats && stats.total_scans > 0 && (
        <>
          <div className="stat-grid stat-grid--3">
            {statCards.map((c) => (
              <StatCard key={c.label} label={c.label} value={c.value} sub={c.sub} />
            ))}
          </div>

          {rowsError ? (
            <EmptyState
              title="Stored-scan list unavailable"
              hint="These sections need the stored-scan list, which could not be loaded. The summary cards above still reflect stored totals."
            />
          ) : rowsLoading ? (
            <EmptyState title="Loading scan data…" />
          ) : (
            <>
              <Card title="Confidence distribution">
                <p className="section-hint">
                  Number of scans per model-confidence band. Stored confidences are
                  max(p, 1 &minus; p) &times; 100, so every scan sits between 50% and 100%.
                </p>
                <Histogram bins={bins} total={summary.count} />
              </Card>

              <Card title="Scan activity — last 14 days">
                <p className="section-hint">
                  Scans per local calendar day, oldest &rarr; newest.
                </p>
                <MiniBars points={activity} />
              </Card>

              <Card title="Stored verdict distribution">
                {DISTRIBUTION_CLASSES.map((c) => {
                  const count = stats.count_by_prediction?.[c.label] ?? 0;
                  const widthPct = stats.total_scans > 0 ? (count / stats.total_scans) * 100 : 0;
                  return (
                    <div className="dist-row" key={c.label}>
                      <span className="dist-row__label">{c.label}</span>
                      <span className="dist-row__count">{count}</span>
                      <div className="dist-bar">
                        <div
                          className={`dist-fill dist-fill--${c.tone}`}
                          style={{ width: `${widthPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </Card>

              <Card title="Lowest-confidence scans">
                <p className="section-hint">
                  The model&apos;s least certain calls — low confidence is not an error
                  verdict.
                </p>
                {lowest.length === 0 ? (
                  <p className="muted-line">No scans to list yet.</p>
                ) : (
                  <ol className="lowconf-list">
                    {lowest.map((r, i) => (
                      <li key={r.id} className="lowconf-item">
                        <span className="lowconf-item__num">{i + 1}</span>
                        <Link className="lowconf-item__name" to={`/history/${r.id}`}>
                          {r.filename || r.id.slice(0, 8)}
                        </Link>
                        <Badge tone={r.prediction === "Tumour Detected" ? "alert" : "safe"}>
                          {r.prediction}
                        </Badge>
                        <span className="lowconf-item__conf">
                          {r.confidence != null && Number.isFinite(Number(r.confidence))
                            ? `${Number(r.confidence).toFixed(1)}%`
                            : "—"}
                        </span>
                      </li>
                    ))}
                  </ol>
                )}
              </Card>
            </>
          )}
        </>
      )}
    </main>
  );
}
