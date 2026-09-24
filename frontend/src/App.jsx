import { useEffect, useState } from "react";
import { HashRouter, Routes, Route, NavLink, Navigate, useLocation } from "react-router-dom";
import "./App.css";
import { API_BASE, fetchJson } from "./api";
import Home from "./pages/Home";
import HistoryList from "./pages/HistoryList";
import ScanDetail from "./pages/ScanDetail";
import Insights from "./pages/Insights";

function StatusDot({ ok }) {
  return <span className={`status-dot ${ok ? "status-ok" : "status-bad"}`} />;
}

function ApiReadout() {
  const [ok, setOk] = useState(null);
  const location = useLocation();

  // Probe /health on load and on every route change so the readout
  // reflects real backend reachability.
  useEffect(() => {
    const controller = new AbortController();
    fetchJson(`${API_BASE}/health`, { signal: controller.signal })
      .then(() => setOk(true))
      .catch(() => setOk(false));
    return () => controller.abort();
  }, [location.pathname]);

  return (
    <div className="readout">
      <span className="readout-label">API</span>
      <span className="readout-value">
        <StatusDot ok={!!ok} /> {API_BASE.replace(/^https?:\/\//, "")}
      </span>
    </div>
  );
}

export default function App() {
  return (
    <HashRouter>
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
            <ApiReadout />
            <nav className="topbar-nav">
              <NavLink
                to="/"
                end
                className={({ isActive }) => `nav-link${isActive ? " nav-link-active" : ""}`}
              >
                Analyze
              </NavLink>
              <NavLink
                to="/history"
                className={({ isActive }) => `nav-link${isActive ? " nav-link-active" : ""}`}
              >
                History
              </NavLink>
              <NavLink
                to="/insights"
                className={({ isActive }) => `nav-link${isActive ? " nav-link-active" : ""}`}
              >
                Insights
              </NavLink>
            </nav>
          </div>
        </header>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/history" element={<HistoryList />} />
          <Route path="/history/:id" element={<ScanDetail />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        <footer className="footbar">
          A Unified XAI Framework for Interpreting Deep Learning Models in Brain Tumour Detection
          &nbsp;&middot;&nbsp; Dept. of CS&amp;E &nbsp;&middot;&nbsp; Major Project, Phase 2
        </footer>
      </div>
    </HashRouter>
  );
}
