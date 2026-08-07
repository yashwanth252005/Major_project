import { useState } from "react";
import { motion } from "framer-motion";
import {
  Brain,
  Cpu,
  Sparkles,
  Activity,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

import UploadCard from "../components/UploadCard";
import ResultPanel from "../components/ResultPanel";
import { predictScan } from "../api/client";

function StatCard({ icon, title, value, color }) {
  return (
    <motion.div
      whileHover={{ y: -5 }}
      className="surface-hover p-5"
    >
      <div
        className={`mb-4 flex h-12 w-12 items-center justify-center rounded-2xl ${color}`}
      >
        {icon}
      </div>

      <p className="text-2xl font-bold">{value}</p>

      <p className="mt-1 text-sm text-slate-400">{title}</p>
    </motion.div>
  );
}

function EmptyState() {
  return (
    <div className="surface flex h-[520px] flex-col items-center justify-center rounded-3xl text-center p-10">

      <div className="mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-indigo-600 shadow-[0_20px_60px_rgba(91,124,255,.35)]">

        <Brain className="text-white" size={42} />

      </div>

      <h2 className="text-3xl font-bold gradient-text">
        AI Analysis Ready
      </h2>

      <p className="mt-5 max-w-md text-slate-400 leading-7">
        Upload a brain MRI scan to receive an AI prediction together with
        Grad-CAM, Integrated Gradients and SHAP visual explanations.
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-3">

        <span className="badge">Grad-CAM</span>
        <span className="badge">Integrated Gradients</span>
        <span className="badge">SHAP</span>

      </div>

    </div>
  );
}

function LoadingState() {
  const steps = [
    "Uploading MRI",
    "Pre-processing",
    "DenseNet121",
    "Grad-CAM",
    "Integrated Gradients",
    "SHAP",
    "Generating Report",
  ];

  return (
    <div className="surface rounded-3xl p-8">

      <h2 className="mb-8 text-2xl font-bold">
        AI Analysis Running
      </h2>

      <div className="space-y-5">

        {steps.map((step, index) => (
          <motion.div
            key={step}
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.2 }}
            className="flex items-center gap-4"
          >
            <div className="h-3 w-3 rounded-full bg-brand-500 animate-pulse" />

            <span className="flex-1 text-slate-300">{step}</span>

            <div className="h-2 w-32 rounded-full bg-slate-800 overflow-hidden">

              <motion.div
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                }}
                className="h-full bg-gradient-to-r from-brand-500 to-indigo-400"
              />

            </div>

          </motion.div>
        ))}

      </div>

    </div>
  );
}

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
      setError(
        err?.response?.data?.error ??
          "Something went wrong while analyzing the MRI."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-6 pb-12">

      {/* Hero */}

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mb-10"
      >

        <div className="flex items-center justify-between">

          <div>

            <div className="badge mb-5">

              <ShieldCheck size={14} />

              Explainable AI Enabled

            </div>

            <h1 className="text-5xl font-bold gradient-text">
              NeuroScan XAI
            </h1>

            <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-400">
              AI-powered brain MRI analysis using DenseNet121,
              Grad-CAM, Integrated Gradients and SHAP.
            </p>

          </div>

          <div className="hidden xl:flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-emerald-300">

            <Activity size={16} />

            Backend Online

          </div>

        </div>

        <div className="mt-10 grid gap-5 md:grid-cols-3">

          <StatCard
            icon={<Cpu />}
            title="AI Model"
            value="DenseNet121"
            color="bg-brand-500/20 text-brand-300"
          />

          <StatCard
            icon={<Sparkles />}
            title="Explainability"
            value="3 Methods"
            color="bg-purple-500/20 text-purple-300"
          />

          <StatCard
            icon={<Brain />}
            title="Average Runtime"
            value="< 3 sec"
            color="bg-emerald-500/20 text-emerald-300"
          />

        </div>
      </motion.div>
          {/* Main Content */}

      <div className="grid gap-8 xl:grid-cols-[400px_1fr]">

        {/* LEFT PANEL */}

        <div className="space-y-6">

          <UploadCard
            onFileSelected={setFile}
            disabled={loading}
          />

          <motion.button
            whileHover={{
              scale: 1.02,
              y: -2,
            }}
            whileTap={{
              scale: .98,
            }}
            disabled={!file || loading}
            onClick={handleAnalyze}
            className="btn-primary w-full py-4 text-base disabled:cursor-not-allowed disabled:opacity-40"
          >

            Analyze MRI Scan

            <ArrowRight size={18} />

          </motion.button>

          {error && (

            <motion.div

              initial={{
                opacity:0,
                y:10
              }}

              animate={{
                opacity:1,
                y:0
              }}

              className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4"

            >

              <p className="text-sm text-red-300">

                {error}

              </p>

            </motion.div>

          )}

          {/* AI Information */}

          <div className="surface p-6">

            <p className="section-title">

              Explainable AI Pipeline

            </p>

            <div className="mt-5 space-y-4">

              <PipelineItem
                title="DenseNet121"
                text="Deep CNN used for MRI classification."
              />

              <PipelineItem
                title="Grad-CAM"
                text="Highlights regions influencing prediction."
              />

              <PipelineItem
                title="Integrated Gradients"
                text="Shows pixel-level importance."
              />

              <PipelineItem
                title="SHAP"
                text="Explains positive and negative feature impact."
              />

            </div>

          </div>

        </div>

        {/* RIGHT PANEL */}

        <motion.div

          initial={{
            opacity:0,
            x:25
          }}

          animate={{
            opacity:1,
            x:0
          }}

        >

          {loading && <LoadingState />}

          {!loading && !result && <EmptyState />}

          {!loading && result && (

            <ResultPanel

              result={result}

            />

          )}

        </motion.div>

      </div>

    </div>

  );

}

/* ----------------------- */

function PipelineItem({

  title,

  text,

}) {

  return (

    <div className="flex items-start gap-4">

      <div className="mt-2 h-2.5 w-2.5 rounded-full bg-brand-500"/>

      <div>

        <p className="font-semibold">

          {title}

        </p>

        <p className="mt-1 text-sm leading-6 text-slate-400">

          {text}

        </p>

      </div>

    </div>

  );

}
