import { Link } from "react-router-dom";
import {
  Brain,
  Timer,
  BadgeCheck,
  ArrowRight,
} from "lucide-react";

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

  const confidence = Number(prediction?.confidence ?? 0);

  const isTumor =
    prediction?.class &&
    prediction.class.toLowerCase() !== "notumor";

  return (
    <div className="space-y-6 animate-fade">

      {/* Prediction */}

      <div
        className={`surface rounded-3xl p-6 border-l-4 ${
          isTumor
            ? "border-red-500"
            : "border-emerald-500"
        }`}
      >
        <div className="flex flex-wrap justify-between gap-6">

          <div>

            <p className="section-title">
              Prediction
            </p>

            <div className="mt-2 flex items-center gap-3">

              <Brain
                className={
                  isTumor
                    ? "text-red-400"
                    : "text-emerald-400"
                }
                size={30}
              />

              <h2 className="text-3xl font-bold capitalize">
                {prediction?.class}
              </h2>

            </div>

          </div>

          <div>

            <p className="section-title">
              Confidence
            </p>

            <h2 className="mt-2 text-3xl font-bold">
              {confidence}%
            </h2>

          </div>

          <div>

            <p className="section-title">
              Processing
            </p>

            <div className="mt-2 flex items-center gap-2">

              <Timer size={18} />

              <span className="text-2xl font-semibold">
                {processing_time}s
              </span>

            </div>

          </div>

        </div>

        {/* Progress */}

        <div className="mt-6">

          <div className="mb-2 flex justify-between text-sm text-slate-400">

            <span>Prediction Confidence</span>

            <span>{confidence}%</span>

          </div>

          <div className="h-3 rounded-full bg-slate-800 overflow-hidden">

            <div
              className={`h-full rounded-full transition-all duration-700 ${
                isTumor
                  ? "bg-gradient-to-r from-red-500 to-orange-400"
                  : "bg-gradient-to-r from-emerald-500 to-green-400"
              }`}
              style={{
                width: `${confidence}%`,
              }}
            />

          </div>

        </div>

      </div>

      {/* Summary */}

      {summary && (

        <div className="surface rounded-3xl p-6">

          <div className="flex items-center gap-2">

            <BadgeCheck
              className="text-brand-400"
            />

            <h3 className="font-semibold text-lg">
              AI Summary
            </h3>

          </div>

          <p className="mt-4 leading-7 text-slate-300">
            {summary}
          </p>

        </div>

      )}

      {/* Images */}

      <div className="grid gap-5 lg:grid-cols-3">

        <ReportImage
          title="Grad-CAM"
          base64={gradcam}
          description="Shows where the neural network focused."
        />

        <ReportImage
          title="Integrated Gradients"
          base64={integrated_gradients}
          description="Highlights pixel importance."
        />

        <ReportImage
          title="SHAP"
          base64={shap}
          description="Displays positive and negative feature contributions."
        />

      </div>

      {/* Footer */}

      {id && (

        <div className="flex justify-end">

          <Link
            to={`/history/${id}`}
            className="btn-primary"
          >

            View Full Report

            <ArrowRight size={18} />

          </Link>

        </div>

      )}

    </div>
  );
}