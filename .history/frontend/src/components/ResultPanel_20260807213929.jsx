import { Link } from "react-router-dom";
import {
  Brain,
  Activity,
  Timer,
  Sparkles,
  ArrowRight
} from "lucide-react";
import { motion } from "framer-motion";
import ReportImage from "./ReportImage";

export default function ResultPanel({ result }) {
  if (!result) return null;

  const {
    id,
    prediction,
    summary,
    processing_time,
    gradcam,
    shap,
    integrated_gradients,
  } = result;

  const tumor = prediction?.class !== "notumor";

  const heroColor = tumor
    ? "from-red-500/15 to-red-900/5 border-red-500/30"
    : "from-emerald-500/15 to-emerald-900/5 border-emerald-500/30";

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* HERO */}

      <div
        className={`rounded-3xl border bg-gradient-to-br ${heroColor} p-7`}
      >
        <div className="flex items-start justify-between">

          <div>

            <span className="badge">

              <Sparkles size={14} />

              AI Analysis Complete

            </span>

            <h2 className="mt-4 text-4xl font-bold capitalize">
              {prediction?.class}
            </h2>

            <p className="mt-2 text-slate-400">
              High confidence prediction generated using Explainable AI.
            </p>

          </div>

          <div className="hidden md:block">

            <Brain
              size={70}
              className="text-brand-400 opacity-70"
            />

          </div>

        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">

          <StatCard
            icon={<Activity />}
            value={`${prediction?.confidence}%`}
            title="Confidence"
          />

          <StatCard
            icon={<Timer />}
            value={`${processing_time}s`}
            title="Processing"
          />

          <StatCard
            icon={<Sparkles />}
            value="3"
            title="XAI Methods"
          />

        </div>

        {summary && (
          <div className="mt-7 rounded-2xl bg-white/5 p-5">
            <p className="text-sm leading-7 text-slate-300">
              {summary}
            </p>
          </div>
        )}

        {id && (
          <Link
            to={`/history/${id}`}
            className="btn-primary mt-6 inline-flex"
          >
            View Full Report

            <ArrowRight size={18} />
          </Link>
        )}
      </div>

      {/* XAI IMAGES */}

      <div className="grid gap-5 lg:grid-cols-3">

        <ReportImage
          title="Grad-CAM"
          base64={gradcam}
          description="Shows where the CNN focused."
        />

        <ReportImage
          title="Integrated Gradients"
          base64={integrated_gradients}
          description="Pixel-level feature attribution."
        />

        <ReportImage
          title="SHAP"
          base64={shap}
          description="Positive & negative feature impact."
        />

      </div>
    </motion.div>
  );
}

function StatCard({ icon, value, title }) {
  return (
    <div className="surface-hover p-5">

      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-500/20 text-brand-300">
        {icon}
      </div>

      <p className="text-3xl font-bold">
        {value}
      </p>

      <p className="mt-1 text-sm text-slate-400">
        {title}
      </p>

    </div>
  );
}