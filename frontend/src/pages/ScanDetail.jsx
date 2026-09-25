import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { API_BASE, fetchJson } from "../api";
import { XAI_METHODS } from "../xaiMethods";
import exportReportPdf from "../exportPdf";
import Badge from "../components/Badge";
import Card from "../components/Card";
import ConfidenceMeter from "../components/ConfidenceMeter";
import DisclaimerBanner from "../components/DisclaimerBanner";
import ProbabilityGauge from "../components/ProbabilityGauge";

const CLASSES = ["Tumour Detected", "No Tumour Detected"];

function formatBytes(n) {
  if (n == null) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ScanDetail() {
  const { id } = useParams();
  const [record, setRecord] = useState(null);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [pdfError, setPdfError] = useState(null);
  const [showFullFingerprint, setShowFullFingerprint] = useState(false);
  const reportRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    setRecord(null);
    setError(null);
    (async () => {
      try {
        const data = await fetchJson(`${API_BASE}/history/${id}`);
        if (!cancelled) setRecord(data);
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load scan record.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const downloadPdf = async () => {
    if (!reportRef.current || !record) return;
    setGenerating(true);
    setPdfError(null);
    try {
      await exportReportPdf(reportRef.current, record.id);
    } catch (e) {
      setPdfError(e.message || "Failed to generate the PDF report.");
    } finally {
      setGenerating(false);
    }
  };

  // In-page jump for the anchor strip. Uses scrollIntoView (not href="#…")
  // because HashRouter owns the URL hash — a plain anchor would break routing.
  const scrollToSection = (sectionId) => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  if (error) {
    return (
      <main className="page detail">
        <div className="error-box">⚠ {error}</div>
        <Link className="back-link" to="/history">&larr; Back to history</Link>
      </main>
    );
  }

  if (!record) {
    return (
      <main className="page detail">
        <p className="loading-line">Loading scan record…</p>
      </main>
    );
  }

  const fp = record.model_fingerprint;
  const fingerprintDisplay = !fp
    ? "—"
    : showFullFingerprint
      ? fp
      : `${fp.slice(0, 8)}…${fp.slice(-8)}`;

  const verdictTone = record.prediction === "Tumour Detected" ? "alert" : "safe";

  return (
    <main className="page detail">
      <div className="detail-toolbar">
        <Link className="back-link" to="/history">&larr; Back to history</Link>
        <button className="btn btn--primary" onClick={downloadPdf} disabled={generating}>
          {generating ? "Generating PDF…" : "Download PDF"}
        </button>
      </div>

      {pdfError && <div className="error-box">⚠ {pdfError}</div>}

      <nav className="anchor-strip" aria-label="Report sections">
        <span className="anchor-strip__label">Jump to</span>
        <button
          type="button"
          className="anchor-strip__btn"
          onClick={() => scrollToSection("scan-report")}
        >
          Report
        </button>
        <button
          type="button"
          className="anchor-strip__btn"
          onClick={() => scrollToSection("scan-images")}
        >
          Images
        </button>
        <button
          type="button"
          className="anchor-strip__btn"
          onClick={() => scrollToSection("scan-methods")}
        >
          Methods
        </button>
      </nav>

      <div className="detail-layout">
        {/* LEFT: the exported report (3 PDF sections) */}
        <div className="detail-main">
          <div className="report" ref={reportRef}>
            <Card id="scan-report" index="01" title="Scan report" pdf>
              <dl className="detail-meta">
                <div>
                  <dt>Scan ID</dt>
                  <dd>{record.id}</dd>
                </div>
                <div>
                  <dt>Captured</dt>
                  <dd>{new Date(record.created_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Filename</dt>
                  <dd>{record.filename || "—"}</dd>
                </div>
                <div>
                  <dt>MIME type</dt>
                  <dd>{record.content_type || "—"}</dd>
                </div>
                <div>
                  <dt>Source dimensions</dt>
                  <dd>
                    {record.source_width} &times; {record.source_height} px
                  </dd>
                </div>
                <div>
                  <dt>File size</dt>
                  <dd>{formatBytes(record.size_bytes)}</dd>
                </div>
                <div>
                  <dt>Model</dt>
                  <dd>{record.model_name || "—"}</dd>
                </div>
                {fp && (
                  <div>
                    <dt>Model fingerprint</dt>
                    <dd>
                      <span
                        className="fingerprint"
                        title={fp}
                        onClick={() => setShowFullFingerprint((v) => !v)}
                      >
                        {fingerprintDisplay}
                      </span>
                    </dd>
                  </div>
                )}
                <div>
                  <dt>Classes</dt>
                  <dd>
                    {CLASSES.map((c) =>
                      c === record.prediction ? (
                        <Badge
                          key={c}
                          tone={c === "Tumour Detected" ? "alert" : "safe"}
                        >
                          {c}
                        </Badge>
                      ) : (
                        <span key={c} className="class-chip">{c}</span>
                      )
                    )}
                  </dd>
                </div>
                <div>
                  <dt>Prediction</dt>
                  <dd>
                    <Badge tone={verdictTone}>{record.prediction}</Badge> &middot;{" "}
                    {record.confidence != null ? `${record.confidence.toFixed(1)}%` : "—"}{" "}
                    confidence &middot; raw probability {record.raw_probability} &middot;{" "}
                    {record.processing_time_ms} ms
                  </dd>
                </div>
              </dl>
            </Card>

            <Card id="scan-images" index="02" title="Images — original + XAI overlays" pdf>
              <div className="xai-grid">
                <div className="xai-tile">
                  <div className="xai-tile__header">
                    <span className="xai-tile__label">Original</span>
                    <span className="xai-tile__sub">Input scan</span>
                  </div>
                  <div className="xai-tile__well">
                    <img
                      src={`data:image/png;base64,${record.original_image}`}
                      alt="Original MRI slice"
                    />
                  </div>
                </div>
                {XAI_METHODS.map((m) => (
                  <div className="xai-tile" key={m.key}>
                    <div className="xai-tile__header">
                      <span className="xai-tile__label">{m.label}</span>
                      <span className="xai-tile__sub">{m.sub}</span>
                    </div>
                    <div className="xai-tile__well">
                      {record[m.key] ? (
                        <img
                          src={`data:image/png;base64,${record[m.key]}`}
                          alt={`${m.label} heatmap`}
                        />
                      ) : (
                        <div className="xai-tile__placeholder">
                          <span className="xai-tile__placeholder-text">
                            {m.label} unavailable for this scan
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card id="scan-methods" index="03" title="Methods & disclaimer" pdf>
              <div className="methods-list">
                {XAI_METHODS.map((m) => (
                  <div className="method-item" key={m.key}>
                    <span className="method-name">
                      {m.label} &middot; {m.sub}
                    </span>
                    <p>{m.desc}</p>
                  </div>
                ))}
              </div>
              <DisclaimerBanner variant="inline" />
            </Card>
          </div>
        </div>

        {/* RIGHT: screen-only rail (outside the report root, never exported) */}
        <aside className="detail-rail">
          <Card title="Verdict at a glance">
            <div className="detail-rail__block">
              <Badge tone={verdictTone}>{record.prediction}</Badge>
            </div>
            {record.raw_probability != null && (
              <div className="detail-rail__block">
                <ProbabilityGauge value={record.raw_probability} />
              </div>
            )}
            <div className="detail-rail__block">
              <span className="detail-rail__label">Model confidence</span>
              <span className="detail-rail__value">
                {record.confidence != null ? `${record.confidence.toFixed(1)}%` : "—"}
              </span>
              <ConfidenceMeter value={record.confidence} />
            </div>
          </Card>

          <Card title="Run metrics">
            <dl className="detail-rail__metrics">
              <div>
                <dt>Scan ID</dt>
                <dd>{record.id}</dd>
              </div>
              <div>
                <dt>Captured</dt>
                <dd>{new Date(record.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt>Processing time</dt>
                <dd>{record.processing_time_ms} ms</dd>
              </div>
            </dl>
          </Card>

          <Link className="back-link" to="/history">&larr; Back to history</Link>
        </aside>
      </div>
    </main>
  );
}
