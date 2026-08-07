import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchHistory } from "../api/client.js";

export default function History() {
  const [scans, setScans] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory()
      .then(setScans)
      .catch(() => setError("Could not load history. Is the backend running?"));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Scan History</h1>
        <p className="mt-1 text-sm text-slate-400">
          Every analyzed scan is saved automatically. Click one to view the full report and
          export a PDF.
        </p>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {!scans && !error && <p className="text-sm text-slate-400">Loading…</p>}
      {scans && scans.length === 0 && (
        <p className="text-sm text-slate-500">No scans yet — analyze one from the Dashboard.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {scans?.map((scan) => {
          const isTumor = scan.predicted_class !== "notumor";
          return (
            <Link
              key={scan.id}
              to={`/history/${scan.id}`}
              className="group overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 transition hover:border-brand-500"
            >
              <img
                src={`data:image/png;base64,${scan.original_image_b64}`}
                alt={scan.predicted_class}
                className="h-40 w-full object-cover opacity-90 transition group-hover:opacity-100"
              />
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-sm font-semibold capitalize ${
                      isTumor ? "text-red-400" : "text-emerald-400"
                    }`}
                  >
                    {scan.predicted_class}
                  </span>
                  <span className="text-sm text-slate-400">{scan.confidence}%</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {new Date(scan.created_at).toLocaleString()}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
