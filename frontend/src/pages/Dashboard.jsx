import { useState } from "react";
import UploadCard from "../components/UploadCard.jsx";
import ResultPanel from "../components/ResultPanel.jsx";
import { predictScan } from "../api/client.js";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleAnalyze() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await predictScan(file);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.error || "Something went wrong while analyzing the scan.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">MRI Tumor Analysis</h1>
        <p className="mt-1 text-sm text-slate-400">
          Upload a FLAIR MRI slice to get a classification plus Grad-CAM, Integrated Gradients,
          and SHAP explanations.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <div className="space-y-4">
          <UploadCard onFileSelected={setFile} disabled={loading} />
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!file || loading}
            className="w-full rounded-xl bg-brand-500 py-3 font-medium text-white transition hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? "Analyzing…" : "Analyze Scan"}
          </button>
          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>

        <div>
          {loading && (
            <div className="flex h-64 items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/40 text-slate-400">
              Running CNN + Grad-CAM + SHAP + Integrated Gradients…
            </div>
          )}
          {!loading && !result && (
            <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-slate-800 text-slate-500">
              Results will appear here
            </div>
          )}
          <ResultPanel result={result} />
        </div>
      </div>
    </div>
  );
}
