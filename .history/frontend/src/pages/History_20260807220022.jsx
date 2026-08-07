import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  History as HistoryIcon,
  Brain,
  Calendar,
  ArrowRight,
} from "lucide-react";
import { motion } from "framer-motion";
import { fetchHistory } from "../api/client.js";

export default function History() {
  const [scans, setScans] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory()
      .then(setScans)
      .catch(() =>
        setError("Could not load history. Is the backend running?")
      );
  }, []);

  const totalScans = useMemo(() => scans?.length ?? 0, [scans]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">

      {/* Header */}

      <div className="mb-10 flex flex-wrap items-center justify-between gap-6">

        <div>

          <div className="badge mb-4">

            <HistoryIcon size={14} />

            Scan Archive

          </div>

          <h1 className="text-4xl font-bold gradient-text">
            Scan History
          </h1>

          <p className="mt-3 max-w-2xl text-slate-400 leading-7">
            Every analyzed MRI scan is securely stored here. Open any scan
            to view the explainability report and export it as a PDF.
          </p>

        </div>

        <div className="surface px-6 py-5">

          <p className="section-title">
            Total Scans
          </p>

          <h2 className="mt-2 text-4xl font-bold">
            {totalScans}
          </h2>

        </div>

      </div>

      {error && (
        <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-red-300">
          {error}
        </div>
      )}

      {!scans && !error && (
        <div className="surface flex h-60 items-center justify-center rounded-3xl">
          <p className="text-slate-400">
            Loading scan history...
          </p>
        </div>
      )}

      {scans && scans.length === 0 && (
        <div className="surface flex h-72 flex-col items-center justify-center rounded-3xl">

          <Brain
            size={60}
            className="mb-5 text-brand-400"
          />

          <h2 className="text-2xl font-semibold">
            No Scans Yet
          </h2>

          <p className="mt-3 text-center text-slate-400">
            Analyze your first MRI scan from the Dashboard.
          </p>

        </div>
      )}

      <div className="grid gap-7 md:grid-cols-2 xl:grid-cols-3">

        {scans?.map((scan, index) => {

          const confidence = Number(scan.confidence ?? 0);

          const isTumor =
            scan.predicted_class.toLowerCase() !== "notumor";

          return (

            <motion.div
              key={scan.id}
              initial={{
                opacity: 0,
                y: 18,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{
                delay: index * .05,
              }}
            >

              <Link
                to={`/history/${scan.id}`}
                className="group block overflow-hidden rounded-3xl border border-white/10 bg-[#131B2B] transition-all duration-300 hover:-translate-y-2 hover:border-brand-400 hover:shadow-[0_18px_45px_rgba(0,0,0,.45)]"
              >

                {/* Image */}

                <div className="relative overflow-hidden">

                  <img
                    src={`data:image/png;base64,${scan.original_image_b64}`}
                    alt={scan.predicted_class}
                    className="h-56 w-full object-cover transition duration-500 group-hover:scale-105"
                  />

                  <div
                    className={`absolute left-4 top-4 rounded-full px-3 py-1 text-xs font-semibold backdrop-blur
                    ${
                      isTumor
                        ? "bg-red-500/20 text-red-300"
                        : "bg-emerald-500/20 text-emerald-300"
                    }`}
                  >
                    {scan.predicted_class}
                  </div>

                </div>

                {/* Content */}

                <div className="p-5">

                  <div className="mb-5 flex items-center justify-between">

                    <div>

                      <p className="section-title">
                        Confidence
                      </p>

                      <h3 className="mt-1 text-2xl font-bold">
                        {confidence}%
                      </h3>

                    </div>

                    <ArrowRight
                      className="text-slate-500 transition group-hover:translate-x-1 group-hover:text-brand-400"
                    />

                  </div>

                  {/* Progress */}

                  <div className="mb-5">

                    <div className="h-2 overflow-hidden rounded-full bg-slate-800">

                      <div
                        className={`h-full rounded-full ${
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

                  <div className="flex items-center gap-2 text-sm text-slate-400">

                    <Calendar size={15} />

                    {new Date(scan.created_at).toLocaleString()}

                  </div>

                </div>

              </Link>

            </motion.div>

          );

        })}

      </div>

    </div>
  );
}