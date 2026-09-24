import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE, fetchJson } from "../api";

function formatBytes(n) {
  if (n == null) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function HistoryList() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setError(null);
    try {
      setRows(await fetchJson(`${API_BASE}/history`));
    } catch (e) {
      setError(e.message || "Failed to load scan history.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const deleteRow = async (id) => {
    if (!window.confirm("Delete this scan record?")) return;
    try {
      await fetchJson(`${API_BASE}/history/${id}`, { method: "DELETE" });
      await load();
    } catch (e) {
      setError(e.message || "Failed to delete scan record.");
    }
  };

  return (
    <main className="history-panel">
      <div className="panel-heading">
        <span className="panel-index">H</span> Scan History
      </div>

      {error && <div className="error-box">⚠ {error}</div>}

      {!error && rows === null && (
        <p className="loading-line">Loading scan history…</p>
      )}

      {!error && rows !== null && rows.length === 0 && (
        <p className="loading-line">
          No scans yet. Run an analysis on the Analyze page and it will appear here.
        </p>
      )}

      {!error && rows !== null && rows.length > 0 && (
        <table className="history-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Filename</th>
              <th>Prediction</th>
              <th>Confidence</th>
              <th>Dimensions</th>
              <th>Size</th>
              <th aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.id}
                className="history-row"
                onClick={() => navigate(`/history/${r.id}`)}
              >
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td>{r.filename || "—"}</td>
                <td>
                  <span className={r.prediction === "Tumour Detected" ? "pred-alert" : "pred-safe"}>
                    {r.prediction}
                  </span>
                </td>
                <td>{r.confidence.toFixed(1)}%</td>
                <td>
                  {r.source_dimensions.width} &times; {r.source_dimensions.height}
                </td>
                <td>{formatBytes(r.size_bytes)}</td>
                <td>
                  <button
                    className="history-delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteRow(r.id);
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
