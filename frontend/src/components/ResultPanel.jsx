import { Link } from "react-router-dom";
import ReportImage from "./ReportImage.jsx";

export default function ResultPanel({ result }) {
  if (!result) return null;

  const { id, prediction, summary, processing_time, gradcam, shap, integrated_gradients } = result;
  const isTumor = prediction?.class && prediction.class !== "notumor";

  return (
    <div className="space-y-6">
      <div
        className={`rounded-2xl border p-6 ${
          isTumor ? "border-red-500/40 bg-red-500/5" : "border-emerald-500/40 bg-emerald-500/5"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Prediction</p>
            <p className="text-2xl font-semibold capitalize">{prediction?.class}</p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-slate-400">Confidence</p>
            <p className="text-2xl font-semibold">{prediction?.confidence}%</p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-slate-400">Processing time</p>
            <p className="text-2xl font-semibold">{processing_time}s</p>
          </div>
        </div>
        {summary && <p className="mt-4 text-sm text-slate-300">{summary}</p>}
        {id && (
          <Link
            to={`/history/${id}`}
            className="mt-4 inline-block text-sm text-brand-400 underline underline-offset-2"
          >
            View full report & export PDF →
          </Link>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <ReportImage title="Grad-CAM" base64={gradcam} description="Region-level: where the network focused." />
        <ReportImage
          title="Integrated Gradients"
          base64={integrated_gradients}
          description="Pixel-level: fine-grained attribution."
        />
        <ReportImage
          title="SHAP"
          base64={shap}
          description="Feature-level: positive vs. negative contributions."
        />
      </div>
    </div>
  );
}
