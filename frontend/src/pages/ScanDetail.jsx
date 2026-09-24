import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { API_BASE, fetchJson } from "../api";
import { XAI_METHODS } from "../xaiMethods";
import exportReportPdf from "../exportPdf";

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

  if (error) {
    return (
      <main className="detail-grid">
        <div className="error-box">⚠ {error}</div>
        <Link className="back-link" to="/history">&larr; Back to history</Link>
      </main>
    );
  }

  if (!record) {
    return (
      <main className="detail-grid">
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

  return (
    <main className="detail-grid">
      <div className="detail-toolbar">
        <Link className="back-link" to="/history">&larr; Back to history</Link>
        <button className="pdf-btn" onClick={downloadPdf} disabled={generating}>
          {generating ? "Generating PDF…" : "Download PDF"}
        </button>
      </div>

      {pdfError && <div className="error-box">⚠ {pdfError}</div>}

      <div className="report" ref={reportRef}>
        <section className="detail-section" data-pdf-section>
          <div className="panel-heading">
            <span className="panel-index">01</span> Scan Report
          </div>
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
                    <span key={c} className={`badge ${c === "Tumour Detected" ? "badge-alert" : "badge-safe"}`}>
                      {c}
                    </span>
                  ) : (
                    <span key={c} className="class-chip">{c}</span>
                  )
                )}
              </dd>
            </div>
            <div>
              <dt>Prediction</dt>
              <dd>
                <span className={record.prediction === "Tumour Detected" ? "pred-alert" : "pred-safe"}>
                  {record.prediction}
                </span>{" "}
                &middot; {record.confidence.toFixed(1)}% confidence &middot; raw
                probability {record.raw_probability} &middot; {record.processing_time_ms} ms
              </dd>
            </div>
          </dl>
        </section>

        <section className="detail-section" data-pdf-section>
          <div className="panel-heading">
            <span className="panel-index">02</span> Images &mdash; Original + XAI Overlays
          </div>
          <div className="xai-grid">
            <div className="xai-tile">
              <div className="xai-tile-header">
                <span className="xai-tile-label">Original</span>
                <span className="xai-tile-sub">Input scan</span>
              </div>
              <div className="xai-tile-image">
                <img
                  src={`data:image/png;base64,${record.original_image}`}
                  alt="Original MRI slice"
                />
              </div>
            </div>
            {XAI_METHODS.map((m) => (
              <div className="xai-tile" key={m.key}>
                <div className="xai-tile-header">
                  <span className="xai-tile-label">{m.label}</span>
                  <span className="xai-tile-sub">{m.sub}</span>
                </div>
                <div className="xai-tile-image">
                  {record[m.key] ? (
                    <img
                      src={`data:image/png;base64,${record[m.key]}`}
                      alt={`${m.label} heatmap`}
                    />
                  ) : (
                    <div className="xai-tile-placeholder">
                      <span className="xai-tile-placeholder-text">
                        {m.label} unavailable for this scan
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="detail-section" data-pdf-section>
          <div className="panel-heading">
            <span className="panel-index">03</span> Methods &amp; Disclaimer
          </div>
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
          <p className="disclaimer">
            This report was generated by NeuroScan-XAI for academic, research and
            educational use only. It is not a medical device and its output must not
            be used for clinical diagnosis of any kind. The XAI outputs (Grad-CAM,
            LRP, SHAP) explain the behaviour of the model — they are not tumour
            segmentations and carry no diagnostic validity.
          </p>
        </section>
      </div>
    </main>
  );
}
