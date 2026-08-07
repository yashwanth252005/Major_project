import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import ReportImage from "../components/ReportImage.jsx";
import { deleteScan, fetchScan } from "../api/client.js";

export default function ScanDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [scan, setScan] = useState(null);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const reportRef = useRef(null);

  useEffect(() => {
    setScan(null);
    setError(null);
    fetchScan(id)
      .then(setScan)
      .catch(() => setError("Could not load this scan. It may have been deleted."));
  }, [id]);

  async function handleExportPdf() {
    if (!reportRef.current) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(reportRef.current, {
        backgroundColor: "#020617",
        scale: 2,
        useCORS: true,
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({ orientation: "portrait", unit: "pt", format: "a4" });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const imgHeight = (canvas.height * pageWidth) / canvas.width;
      pdf.addImage(imgData, "PNG", 0, 0, pageWidth, imgHeight);
      pdf.save(`scan-report-${id}.pdf`);
    } finally {
      setExporting(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this scan permanently?")) return;
    await deleteScan(id);
    navigate("/history");
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Link to="/history" className="text-sm text-brand-400 hover:underline">
          ← Back to history
        </Link>
        <p className="text-sm text-red-400">{error}</p>
      </div>
    );
  }

  if (!scan) return <p className="text-sm text-slate-400">Loading…</p>;

  const isTumor = scan.predicted_class && scan.predicted_class !== "notumor";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to="/history" className="text-sm text-brand-400 hover:underline">
          ← Back to history
        </Link>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleDelete}
            className="rounded-lg border border-red-500/40 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/10"
          >
            Delete
          </button>
          <button
            type="button"
            onClick={handleExportPdf}
            disabled={exporting}
            className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-40"
          >
            {exporting ? "Exporting…" : "Export PDF"}
          </button>
        </div>
      </div>

      {/* Everything inside this div is what gets captured into the PDF */}
      <div ref={reportRef} className="space-y-6 rounded-2xl bg-slate-950 p-6">
        <div>
          <h1 className="text-xl font-semibold">Brain Tumor XAI Report</h1>
          <p className="text-xs text-slate-500">{new Date(scan.created_at).toLocaleString()}</p>
        </div>

        <div
          className={`rounded-2xl border p-6 ${
            isTumor ? "border-red-500/40 bg-red-500/5" : "border-emerald-500/40 bg-emerald-500/5"
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">Prediction</p>
              <p className="text-2xl font-semibold capitalize">{scan.predicted_class}</p>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-wide text-slate-400">Confidence</p>
              <p className="text-2xl font-semibold">{scan.confidence}%</p>
            </div>
            {scan.processing_time != null && (
              <div className="text-right">
                <p className="text-xs uppercase tracking-wide text-slate-400">Processing time</p>
                <p className="text-2xl font-semibold">{scan.processing_time}s</p>
              </div>
            )}
          </div>
          {scan.summary && <p className="mt-4 text-sm text-slate-300">{scan.summary}</p>}
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ReportImage title="Original MRI" base64={scan.original_image_b64} />
          <ReportImage title="Grad-CAM" base64={scan.gradcam_b64} />
          <ReportImage title="Integrated Gradients" base64={scan.integrated_gradients_b64} />
          <ReportImage title="SHAP" base64={scan.shap_b64} />
        </div>
      </div>
    </div>
  );
}
