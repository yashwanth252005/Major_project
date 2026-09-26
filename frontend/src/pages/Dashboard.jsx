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

      // MRI validation passed
      setResult(data);
    } catch (err) {
      console.error("Scan analysis error:", err);

      const responseData = err?.response?.data;

      // ----------------------------------------------------
      // Gemini rejected the uploaded image
      // ----------------------------------------------------

      if (responseData?.valid_mri === false) {
        setError(
          responseData?.message ||
            "The uploaded image does not appear to be a brain MRI. Please upload a valid brain MRI image."
        );
      }

      // ----------------------------------------------------
      // Other backend errors
      // ----------------------------------------------------

      else {
        setError(
          responseData?.error ||
            "Something went wrong while analyzing the scan."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">

      {/* ==================================================
          PAGE HEADER
      ================================================== */}

      <div>
        <h1 className="text-2xl font-semibold">
          MRI Tumor Analysis
        </h1>

        <p className="mt-1 text-sm text-slate-400">
          Upload a FLAIR MRI slice to get a classification plus
          Grad-CAM, Integrated Gradients, and SHAP explanations.
        </p>
      </div>


      {/* ==================================================
          MAIN CONTENT
      ================================================== */}

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">

        {/* ==================================================
            LEFT SIDE — UPLOAD
        ================================================== */}

        <div className="space-y-4">

          <UploadCard
            onFileSelected={(selectedFile) => {
              setFile(selectedFile);
              setError(null);
              setResult(null);
            }}
            disabled={loading}
          />

          {/* Analyze Button */}

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!file || loading}
            className="w-full rounded-xl bg-brand-500 py-3 font-medium text-white transition hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? "Analyzing…" : "Analyze Scan"}
          </button>

        </div>


        {/* ==================================================
            RIGHT SIDE — RESULTS
        ================================================== */}

        <div>

          {/* ==================================================
              LOADING STATE
          ================================================== */}

          {loading && (
            <div className="flex h-64 items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/40 px-6 text-center text-slate-400">

              Running MRI validation + CNN + Grad-CAM + SHAP +
              Integrated Gradients…

            </div>
          )}


          {/* ==================================================
              MRI VALIDATION ERROR
          ================================================== */}

          {!loading && error && (
            <div className="flex min-h-64 items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/5 p-8">

              <div className="max-w-lg text-center">

                {/* Icon */}

                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10 text-3xl">
                  🧠
                </div>


                {/* Heading */}

                <h2 className="mt-5 text-xl font-semibold text-slate-100">
                  Invalid MRI Image
                </h2>


                {/* Message */}

                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-400">
                  {error}
                </p>


                {/* Helpful instruction */}

                <p className="mt-4 text-xs leading-5 text-slate-500">
                  Please upload a valid brain MRI scan and try again.
                </p>

              </div>

            </div>
          )}


          {/* ==================================================
              EMPTY STATE
          ================================================== */}

          {!loading && !error && !result && (
            <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-slate-800 text-slate-500">
              Results will appear here
            </div>
          )}


          {/* ==================================================
              SUCCESSFUL RESULT
          ================================================== */}

          {!loading && result && (
            <ResultPanel result={result} />
          )}

        </div>

      </div>
    </div>
  );
}