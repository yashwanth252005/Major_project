import { useState, useRef, useCallback, useEffect } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const XAI_METHODS = [
  {
    key: "gradcam",
    label: "Grad-CAM",
    sub: "Region-level",
    desc: "Highlights which spatial regions of the scan most influenced the prediction, via gradients flowing into the final convolutional layer.",
  },
  {
    key: "lrp",
    label: "LRP",
    sub: "Pixel-level",
    desc: "Layer-wise Relevance Propagation redistributes the prediction score back through every layer to each individual pixel.",
  },
  {
    key: "shap",
    label: "SHAP",
    sub: "Feature-level",
    desc: "Shapley Additive Explanations estimate each region's marginal contribution to the model's output, grounded in game theory.",
  },
];

function StatusDot({ ok }) {
  return <span className={`status-dot ${ok ? "status-ok" : "status-bad"}`} />;
}

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

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
    } catch (e) {
      setError(e.message || "Something went wrong while analyzing the scan.");
    } finally {
      setLoading(false);
    }
  };

  const isTumor = result?.prediction?.toLowerCase().includes("tumour detected");

  return (
    <div className="console">
      <header className="topbar">
        <div className="wordmark">
          <span className="wordmark-icon">◈</span>
          <div>
            <div className="wordmark-title">NEUROSCAN&nbsp;XAI</div>
            <div className="wordmark-sub">Unified Explainable AI Framework &mdash; Brain Tumour Detection</div>
          </div>
        </div>
        <div className="topbar-readouts">
          <div className="readout">
            <span className="readout-label">DATASET</span>
            <span className="readout-value">BraTS 2021 · FLAIR</span>
          </div>
          <div className="readout">
            <span className="readout-label">MODEL</span>
            <span className="readout-value">Custom CNN</span>
          </div>
          <div className="readout">
            <span className="readout-label">API</span>
            <span className="readout-value">
              <StatusDot ok={!error} /> {API_BASE.replace(/^https?:\/\//, "")}
            </span>
          </div>
        </div>
      </header>

      <main className="grid">
        {/* LEFT: scan intake */}
        <section className="panel intake-panel">
          <div className="panel-heading">
            <span className="panel-index">01</span> Scan Intake
          </div>

          <div
            className={`dropzone ${dragOver ? "dropzone-active" : ""} ${previewUrl ? "dropzone-filled" : ""}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              handleFile(e.dataTransfer.files?.[0]);
            }}
          >
            <span className="corner corner-tl" />
            <span className="corner corner-tr" />
            <span className="corner corner-bl" />
            <span className="corner corner-br" />

            {previewUrl ? (
              <img src={previewUrl} alt="MRI slice preview" className="preview-img" />
            ) : (
              <div className="dropzone-empty">
                <div className="dropzone-icon">＋</div>
                <div className="dropzone-text">Drop a FLAIR MRI slice</div>
                <div className="dropzone-subtext">PNG / JPG &middot; click to browse</div>
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

          <button className="run-btn" onClick={runAnalysis} disabled={!file || loading}>
            {loading ? "Analyzing…" : "Run Detection + XAI"}
          </button>

          {error && <div className="error-box">⚠ {error}</div>}
        </section>

        {/* RIGHT: verdict + XAI */}
        <section className="results-col">
          <div className={`verdict-bar ${result ? (isTumor ? "verdict-alert" : "verdict-safe") : ""}`}>
            <div className="verdict-left">
              <span className="panel-index">02</span>
              <div>
                <div className="verdict-label">Diagnostic Output</div>
                <div className="verdict-value">
                  {result ? result.prediction : loading ? "Scanning…" : "Awaiting scan"}
                </div>
              </div>
            </div>
            <div className="verdict-confidence">
              <span className="confidence-number">
                {result ? result.confidence.toFixed(1) : "—"}
              </span>
              <span className="confidence-unit">% confidence</span>
            </div>
          </div>

          <div className="panel-heading">
            <span className="panel-index">03</span> Explainability &mdash; Grad-CAM / LRP / SHAP
          </div>

          <div className="xai-grid">
            {XAI_METHODS.map((m) => (
              <div className="xai-tile" key={m.key}>
                <div className="xai-tile-header">
                  <span className="xai-tile-label">{m.label}</span>
                  <span className="xai-tile-sub">{m.sub}</span>
                </div>
                <div className="xai-tile-image">
                  {result && result[m.key] ? (
                    <img src={`data:image/png;base64,${result[m.key]}`} alt={`${m.label} heatmap`} />
                  ) : (
                    <div className="xai-tile-placeholder">
                      <span className="corner corner-tl" />
                      <span className="corner corner-br" />
                    </div>
                  )}
                </div>
                <p className="xai-tile-desc">{m.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="footbar">
        A Unified XAI Framework for Interpreting Deep Learning Models in Brain Tumour Detection
        &nbsp;&middot;&nbsp; Dept. of CS&amp;E &nbsp;&middot;&nbsp; Major Project, Phase 2
      </footer>
    </div>
  );
}
