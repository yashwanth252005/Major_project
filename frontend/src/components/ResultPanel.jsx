import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Sparkles,
} from "lucide-react";

import ScanAssistant from "./ScanAssistant.jsx";

function XAIImage({ title, description, image }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-sky-400/10 bg-[#061018]/80">
      <div className="border-b border-sky-400/10 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-200">
          {title}
        </h3>

        <p className="mt-1 text-xs leading-5 text-slate-500">
          {description}
        </p>
      </div>

      <div className="flex min-h-[250px] items-center justify-center p-4">
        {image ? (
          <img
            src={`data:image/png;base64,${image}`}
            alt={title}
            className="max-h-[320px] w-full rounded-xl object-contain"
          />
        ) : (
          <div className="flex min-h-[220px] items-center justify-center text-sm text-slate-600">
            Visualization unavailable
          </div>
        )}
      </div>
    </div>
  );
}

export default function ResultPanel({ result }) {
  if (!result) {
    return null;
  }

  const prediction = result?.prediction || {};

  const predictedClass =
    prediction?.class || "Unavailable";

  const rawConfidence = prediction?.confidence;

  const confidence =
    rawConfidence !== undefined && rawConfidence !== null
      ? Number(rawConfidence)
      : null;

  const processingTime =
    result?.processing_time !== undefined &&
    result?.processing_time !== null
      ? Number(result.processing_time)
      : null;

  const originalImage = result?.original_image;
  const gradcam = result?.gradcam;
  const integratedGradients =
    result?.integrated_gradients;
  const shap = result?.shap;

  const summary = result?.summary;

  return (
    <div className="space-y-5">

      {/* SUCCESS HEADER */}

      <section className="rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.035] p-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">

          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.07]">
              <CheckCircle2
                size={22}
                className="text-emerald-300"
              />
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-300">
                Analysis Complete
              </p>

              <h2 className="mt-1 text-xl font-semibold text-slate-100">
                MRI Analysis Result
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                CNN classification and explainability analysis completed.
              </p>
            </div>
          </div>

          {result?.valid_mri && (
            <div className="rounded-full border border-emerald-400/15 bg-emerald-400/[0.05] px-3 py-1.5 text-xs font-medium text-emerald-300">
              MRI Input Accepted
            </div>
          )}
        </div>
      </section>


      {/* PREDICTION METRICS */}

      <section className="grid gap-3 sm:grid-cols-3">

        <div className="rounded-2xl border border-sky-400/10 bg-[#07131c]/80 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
            <BrainCircuit
              size={15}
              className="text-brand-400"
            />
            Prediction
          </div>

          <p className="mt-3 text-xl font-semibold capitalize text-slate-100">
            {predictedClass}
          </p>
        </div>


        <div className="rounded-2xl border border-sky-400/10 bg-[#07131c]/80 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
            <Activity
              size={15}
              className="text-brand-400"
            />
            Confidence
          </div>

          <p className="mt-3 text-xl font-semibold text-slate-100">
            {confidence !== null && !Number.isNaN(confidence)
              ? `${confidence.toFixed(2)}%`
              : "Unavailable"}
          </p>
        </div>


        <div className="rounded-2xl border border-sky-400/10 bg-[#07131c]/80 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
            <Clock3
              size={15}
              className="text-brand-400"
            />
            Processing
          </div>

          <p className="mt-3 text-xl font-semibold text-slate-100">
            {processingTime !== null &&
            !Number.isNaN(processingTime)
              ? `${processingTime.toFixed(2)} s`
              : "Unavailable"}
          </p>
        </div>

      </section>


      {/* SUMMARY */}

      {summary && (
        <section className="rounded-2xl border border-brand-400/10 bg-brand-500/[0.025] p-5">

          <div className="flex items-center gap-2">
            <Sparkles
              size={17}
              className="text-brand-400"
            />

            <h3 className="text-sm font-semibold text-slate-200">
              Analysis Summary
            </h3>
          </div>

          <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-400">
            {summary}
          </p>

        </section>
      )}


      {/* XAI HEADING */}

      <section>
        <div className="mb-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-400">
            Explainability
          </p>

          <h2 className="mt-1 text-lg font-semibold text-slate-100">
            Visual Explanation Results
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Compare the original MRI with three complementary XAI methods.
          </p>
        </div>


        {/* ORIGINAL + GRAD-CAM */}

        <div className="grid gap-4 md:grid-cols-2">

          <XAIImage
            title="Original MRI"
            description="MRI image supplied to the analysis pipeline."
            image={originalImage}
          />

          <XAIImage
            title="Grad-CAM"
            description="Highlights spatial regions influencing the CNN prediction."
            image={gradcam}
          />

        </div>


        {/* IG + SHAP */}

        <div className="mt-4 grid gap-4 md:grid-cols-2">

          <XAIImage
            title="Integrated Gradients"
            description="Shows input attribution relative to a baseline."
            image={integratedGradients}
          />

          <XAIImage
            title="SHAP"
            description="Visualizes feature contributions toward the model output."
            image={shap}
          />

        </div>
      </section>


      {/* SCAN-AWARE ASSISTANT */}

      <ScanAssistant scanId={result?.id} />


      {/* DISCLAIMER */}

      <section className="rounded-xl border border-sky-400/[0.08] bg-sky-400/[0.02] px-4 py-3">
        <p className="text-xs leading-5 text-slate-600">
          Research and educational prototype. The prediction and
          explainability outputs are not intended to be interpreted
          as an independent clinical diagnosis.
        </p>
      </section>

    </div>
  );
}