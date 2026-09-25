import { useState, useRef, useCallback, useEffect } from "react";
import { Link } from "react-router-dom";
import { API_BASE } from "../api";
import { XAI_METHODS } from "../xaiMethods";
import Badge from "../components/Badge";
import Card from "../components/Card";
import ConfidenceMeter from "../components/ConfidenceMeter";
import DisclaimerBanner from "../components/DisclaimerBanner";
import EmptyState from "../components/EmptyState";
import ProbabilityGauge from "../components/ProbabilityGauge";
import useHistoryData from "../hooks/useHistoryData";

const HOW_STEPS = [
  {
    num: "1",
    title: "Drop a FLAIR MRI slice",
    text: "Drag a PNG or JPG onto the dark intake well, or click it to browse.",
  },
  {
    num: "2",
    title: "Run detection + XAI",
    text: "The model classifies the slice and Grad-CAM, LRP and SHAP explain its output.",
  },
  {
    num: "3",
    title: "Review the verdict",
    text: "Check the probability gauge, confidence meter and explanation tiles.",
  },
];

// Relative time for recent scans; falls back to the local date string
// when the scan is older than a day.
function formatWhen(iso) {
  const ts = Date.parse(iso);
  if (!Number.isFinite(ts)) return "—";
  const diffMs = Date.now() - ts;
  if (diffMs < 60_000) return "just now";
  if (diffMs < 3_600_000) return `${Math.floor(diffMs / 60_000)} min ago`;
  if (diffMs < 86_400_000) return `${Math.floor(diffMs / 3_600_000)} h ago`;
  return new Date(ts).toLocaleString();
}

function RecentScans({ rows, loading }) {
  const recent = (rows || []).slice(0, 5);

  if (loading) {
    return <p className="loading-line">Loading recent scans…</p>;
  }

  if (recent.length === 0) {
    return (
      <p className="muted-line">No scans stored yet — analyses you run will appear here.</p>
    );
  }

  return (
    <ul className="recent-list">
      {recent.map((r) => (
        <li key={r.id} className="recent-item">
          <Link className="recent-item__name" to={`/history/${r.id}`}>
            {r.filename || r.id.slice(0, 8)}
          </Link>
          <Badge tone={r.prediction === "Tumour Detected" ? "alert" : "safe"}>
            {r.prediction}
          </Badge>
          <span className="recent-item__conf">
            {r.confidence != null && Number.isFinite(Number(r.confidence))
              ? `${Number(r.confidence).toFixed(1)}%`
              : "—"}
          </span>
          <span className="recent-item__time">{formatWhen(r.created_at)}</span>
        </li>
      ))}
    </ul>
  );
}

export default function Home() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);
  const {
    rows: historyRows,
    loading: historyLoading,
    error: historyError,
    refresh: refreshHistory,
  } = useHistoryData();

  // Revoke the blob URL when it is replaced or the component unmounts.
  useEffect(() => {
    if (!previewUrl) return;
    return () => URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  const handleFile = useCallback((f) => {
    if (!f) return;
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  }, []);

  const runAnalysis = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/predict`, { method: "POST", body: form });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setResult(data);
      refreshHistory();
    } catch (e) {
      setError(e.message || "Something went wrong while analyzing the scan.");
    } finally {
      setLoading(false);
    }
  };

  const isTumor = result?.prediction?.toLowerCase().includes("tumour detected");
  const verdictTone = isTumor ? "alert" : "safe";

  return (
    <main className="page home">
      <DisclaimerBanner variant="banner" />

      <div className="home-grid">
        {/* LEFT: scan intake */}
        <Card index="01" title="Scan intake">
          <div
            className={`dropzone ${dragOver ? "dropzone--active" : ""} ${previewUrl ? "dropzone--filled" : ""}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              handleFile(e.dataTransfer.files?.[0]);
            }}
          >
            <span className="corner corner--tl" />
            <span className="corner corner--tr" />
            <span className="corner corner--bl" />
            <span className="corner corner--br" />

            {previewUrl ? (
              <img src={previewUrl} alt="MRI slice preview" className="preview-img" />
            ) : (
              <div className="dropzone__empty">
                <div className="dropzone__icon">＋</div>
                <div className="dropzone__text">Drop a FLAIR MRI slice</div>
                <div className="dropzone__subtext">PNG / JPG &middot; click to browse</div>
              </div>
            )}
            {loading && <div className="scan-sweep" />}
          </div>

          <input
            ref={inputRef}
            type="file"
            accept="image/png,image/jpeg"
            hidden
            onChange={(e) => handleFile(e.target.files?.[0])}
          />

          <dl className="meta-strip">
            <div><dt>Modality</dt><dd>MRI &middot; FLAIR</dd></div>
            <div><dt>Input size</dt><dd>128 &times; 128</dd></div>
            <div><dt>Channels</dt><dd>Grayscale (1)</dd></div>
          </dl>

          <button
            className="btn btn--primary btn--block run-btn"
            onClick={runAnalysis}
            disabled={!file || loading}
          >
            {loading ? "Analyzing…" : "Run Detection + XAI"}
          </button>

          {error && <div className="error-box">⚠ {error}</div>}
        </Card>

        {/* RIGHT: verdict + XAI */}
        <div className="results-col">
          {result ? (
            <>
              <Card index="02" title="Verdict">
                <div className="verdict">
                  <div className="verdict__head">
                    <Badge tone={verdictTone}>{result.prediction}</Badge>
                    <p className="verdict__text">
                      Model-predicted class for this slice &mdash; not a medical
                      diagnosis.
                    </p>
                  </div>

                  <div className="verdict__meters">
                    {result.raw_probability != null ? (
                      <ProbabilityGauge value={result.raw_probability} />
                    ) : (
                      <p className="muted-line">Raw probability not recorded for this scan.</p>
                    )}
                    <div className="verdict__meter-block">
                      <span className="verdict__meter-label">Model confidence</span>
                      <span className="verdict__meter-value">
                        {result.confidence != null ? `${result.confidence.toFixed(1)}%` : "—"}
                      </span>
                      <ConfidenceMeter value={result.confidence} />
                    </div>
                  </div>

                  <ul className="verdict__chips">
                    <li className="chip">{result.model_name || "—"}</li>
                    <li className="chip">
                      {result.model_fingerprint ? result.model_fingerprint.slice(0, 8) : "—"}
                    </li>
                    <li className="chip">
                      {result.processing_time_ms != null
                        ? `${result.processing_time_ms} ms`
                        : "—"}
                    </li>
                    {result.id && (
                      <li>
                        <Link className="chip chip--link" to={`/history/${result.id}`}>
                          Saved to history — open scan report →
                        </Link>
                      </li>
                    )}
                  </ul>
                </div>
              </Card>

              <Card index="03" title="Explainability — Grad-CAM / LRP / SHAP">
                <div className="xai-grid">
                  {XAI_METHODS.map((m) => (
                    <div className="xai-tile" key={m.key}>
                      <div className="xai-tile__header">
                        <span className="xai-tile__label">{m.label}</span>
                        <span className="xai-tile__sub">{m.sub}</span>
                      </div>
                      <div className="xai-tile__well">
                        {result && result[m.key] ? (
                          <img
                            src={`data:image/png;base64,${result[m.key]}`}
                            alt={`${m.label} heatmap`}
                          />
                        ) : (
                          <div className="xai-tile__placeholder">
                            <span className="corner corner--tl" />
                            <span className="corner corner--br" />
                          </div>
                        )}
                      </div>
                      <p className="xai-tile__desc">{m.desc}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          ) : (
            <Card title="Analysis output">
              {loading ? (
                <p className="loading-line">Scanning…</p>
              ) : (
                <EmptyState
                  title="No scan analyzed yet"
                  hint="Drop a FLAIR MRI slice in the intake well and run detection to see the verdict, probability and explanations here."
                />
              )}
              <div className="how-strip">
                {HOW_STEPS.map((s) => (
                  <div className="how-step" key={s.num}>
                    <span className="how-step__num">Step {s.num}</span>
                    <span className="how-step__title">{s.title}</span>
                    <span className="how-step__text">{s.text}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>

      {!historyError && (
        <Card
          title="Recent scans"
          actions={<Link className="link" to="/history">Open history →</Link>}
        >
          <RecentScans rows={historyRows} loading={historyLoading} />
        </Card>
      )}
    </main>
  );
}
