import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE, fetchJson } from "../api";

const PREDICTION_LABELS = ["Tumour Detected", "No Tumour Detected"];

const SORT_MODES = [
  { value: "newest", label: "Newest first" },
  { value: "oldest", label: "Oldest first" },
  { value: "highest", label: "Highest confidence" },
  { value: "lowest", label: "Lowest confidence" },
];

function formatBytes(n) {
  if (n == null) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

// Local calendar date (YYYY-MM-DD) of a Date — matches <input type="date"> values.
function localDateKey(d) {
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

// Pure client-side filtering: search substring over filename/prediction/id,
// optional exact prediction, optional minimum confidence, optional inclusive
// local date range on the row's calendar date.
function applyFilters(rows, filters) {
  const search = filters.search.trim().toLowerCase();
  const minConfidence = Number.parseFloat(filters.minConfidence);
  const hasMinConfidence =
    filters.minConfidence !== "" && Number.isFinite(minConfidence);

  return rows.filter((r) => {
    if (search) {
      const haystack = `${r.filename || ""} ${r.prediction || ""} ${r.id || ""}`.toLowerCase();
      if (!haystack.includes(search)) return false;
    }
    if (filters.prediction && r.prediction !== filters.prediction) return false;
    if (hasMinConfidence && !(r.confidence >= minConfidence)) return false;
    if (filters.fromDate || filters.toDate) {
      const key = localDateKey(new Date(r.created_at));
      if (filters.fromDate && key < filters.fromDate) return false;
      if (filters.toDate && key > filters.toDate) return false;
    }
    return true;
  });
}

// Stable sort on a copied array; default is newest first.
function sortRows(rows, mode) {
  const sorted = [...rows];
  const byCreatedAsc = (a, b) => Date.parse(a.created_at) - Date.parse(b.created_at);
  switch (mode) {
    case "oldest":
      sorted.sort(byCreatedAsc);
      break;
    case "highest":
      sorted.sort((a, b) => b.confidence - a.confidence);
      break;
    case "lowest":
      sorted.sort((a, b) => a.confidence - b.confidence);
      break;
    case "newest":
    default:
      sorted.sort((a, b) => byCreatedAsc(b, a));
      break;
  }
  return sorted;
}

export default function HistoryList() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [prediction, setPrediction] = useState("");
  const [minConfidence, setMinConfidence] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [sortMode, setSortMode] = useState("newest");
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

  const filtered = useMemo(
    () =>
      rows
        ? sortRows(
            applyFilters(rows, { search, prediction, minConfidence, fromDate, toDate }),
            sortMode
          )
        : [],
    [rows, search, prediction, minConfidence, fromDate, toDate, sortMode]
  );

  const clearFilters = () => {
    setSearch("");
    setPrediction("");
    setMinConfidence("");
    setFromDate("");
    setToDate("");
    setSortMode("newest");
  };

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
        <>
          <div className="history-filters">
            <div className="filter-field filter-field-grow">
              <label className="filter-label" htmlFor="history-filter-search">
                Search
              </label>
              <input
                id="history-filter-search"
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search filename, prediction or scan ID…"
              />
            </div>
            <div className="filter-field">
              <label className="filter-label" htmlFor="history-filter-class">
                Class
              </label>
              <select
                id="history-filter-class"
                value={prediction}
                onChange={(e) => setPrediction(e.target.value)}
              >
                <option value="">All classes</option>
                {PREDICTION_LABELS.map((label) => (
                  <option key={label} value={label}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="filter-field">
              <label className="filter-label" htmlFor="history-filter-min-confidence">
                Min confidence
              </label>
              <input
                id="history-filter-min-confidence"
                type="number"
                min={0}
                max={100}
                step={1}
                value={minConfidence}
                onChange={(e) => setMinConfidence(e.target.value)}
                placeholder="Any"
              />
            </div>
            <div className="filter-field">
              <label className="filter-label" htmlFor="history-filter-from">
                From
              </label>
              <input
                id="history-filter-from"
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>
            <div className="filter-field">
              <label className="filter-label" htmlFor="history-filter-to">
                To
              </label>
              <input
                id="history-filter-to"
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
            </div>
            <div className="filter-field">
              <label className="filter-label" htmlFor="history-filter-sort">
                Sort
              </label>
              <select
                id="history-filter-sort"
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value)}
              >
                {SORT_MODES.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="filter-field">
              <button type="button" className="filter-clear" onClick={clearFilters}>
                Clear filters
              </button>
            </div>
          </div>

          <p className="filter-count">
            Showing {filtered.length} of {rows.length} scans
          </p>

          {filtered.length === 0 ? (
            <p className="history-empty-filter">No scans match the selected filters.</p>
          ) : (
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
                {filtered.map((r) => (
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
        </>
      )}
    </main>
  );
}
