import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import jsPDF from "jspdf";

import {
  Activity,
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Download,
  FileText,
  Microscope,
  ScanLine,
  Sparkles,
  Trash2,
} from "lucide-react";

import ReportImage from "../components/ReportImage.jsx";
import ScanAssistant from "../components/ScanAssistant.jsx";
import { deleteScan, fetchScan } from "../api/client.js";

export default function ScanDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [scan, setScan] = useState(null);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const reportRef = useRef(null);

  useEffect(() => {
    setScan(null);
    setError(null);

    fetchScan(id)
      .then(setScan)
      .catch(() =>
        setError(
          "Could not load this scan. It may have been deleted or the backend may be unavailable."
        )
      );
  }, [id]);

  async function handleExportPdf() {
    setExporting(true);

    try {
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "pt",
        format: "a4",
      });

      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 42;
      const contentWidth = pageWidth - margin * 2;
      let y = 48;

      const ensureSpace = (height = 30) => {
        if (y + height > pageHeight - 48) {
          pdf.addPage();
          y = 48;
        }
      };

      const addWrappedText = (text, size = 10, gap = 15) => {
        pdf.setFontSize(size);
        const lines = pdf.splitTextToSize(String(text || ""), contentWidth);
        ensureSpace(lines.length * gap + 8);
        pdf.text(lines, margin, y);
        y += lines.length * gap;
      };

      const addSectionTitle = (title) => {
        ensureSpace(32);
        y += 8;
        pdf.setFont("helvetica", "bold");
        pdf.setFontSize(13);
        pdf.text(title, margin, y);
        y += 18;
        pdf.setFont("helvetica", "normal");
      };

      const imageItems = [
        ["Original MRI", scan.original_image_b64],
        ["Grad-CAM", scan.gradcam_b64],
        ["Integrated Gradients", scan.integrated_gradients_b64],
        ["SHAP", scan.shap_b64],
      ].filter(([, data]) => Boolean(data));

      const addImageGrid = () => {
        const gap = 16;
        const cellWidth = (contentWidth - gap) / 2;
        const maxImageHeight = 145;
        for (let i = 0; i < imageItems.length; i += 2) {
          const row = imageItems.slice(i, i + 2);
          const prepared = row.map(([label, raw]) => {
            const data = String(raw);
            const format = data.startsWith("/9j/") || data.startsWith("data:image/jpeg") ? "JPEG" : "PNG";
            const props = pdf.getImageProperties(data);
            const scale = Math.min(cellWidth / props.width, maxImageHeight / props.height);
            return { label, data, format, width: props.width * scale, height: props.height * scale };
          });
          const rowHeight = Math.max(...prepared.map((item) => item.height));
          ensureSpace(rowHeight + 43);
          prepared.forEach((item, column) => {
            const x = margin + column * (cellWidth + gap);
            pdf.setFont("helvetica", "bold");
            pdf.setFontSize(10);
            pdf.text(item.label, x, y);
            pdf.addImage(item.data, item.format, x + (cellWidth - item.width) / 2, y + 12, item.width, item.height, undefined, "FAST");
          });
          y += rowHeight + 38;
        }
        pdf.setFont("helvetica", "normal");
      };

      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(20);
      pdf.text("NeuroScan XAI Report", margin, y);
      y += 18;

      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(9);
      pdf.text("Explainable Brain MRI Analysis - Research Prototype", margin, y);
      y += 14;
      pdf.text(`Analysis Date: ${formatDate(scan.created_at)}`, margin, y);
      y += 13;
      pdf.text(`Report ID: ${id}`, margin, y);
      y += 22;

      addSectionTitle("Model Analysis");
      addWrappedText(`Prediction: ${className}`, 11, 15);
      addWrappedText(`Softmax confidence: ${confidence.toFixed(2)}%`, 11, 15);
      if (scan.processing_time != null) {
        addWrappedText(`Processing time: ${scan.processing_time} seconds`, 11, 15);
      }

      if (scan.summary) {
        addSectionTitle("Analysis Summary");
        addWrappedText(scan.summary, 10, 14);
      }

      addSectionTitle("Explainability Analysis");
      addWrappedText(
        "The following images are the original MRI and the three XAI outputs generated for this scan.",
        9,
        13
      );

      addImageGrid();

      // Keep the interpretation and safety disclaimer together on one page.
      const interpretation = "Grad-CAM shows spatial regions influencing the CNN output. Integrated Gradients provides input attribution. SHAP provides feature/input contribution evidence. These explanation methods do not provide tumor segmentation, lesion boundaries, tumor size, or a clinical diagnosis.";
      const disclaimer = "This report is generated by a research and educational prototype. Model predictions and explainability outputs must not be interpreted as an independent clinical diagnosis or treatment recommendation.";
      const interpretationLines = pdf.splitTextToSize(interpretation, contentWidth);
      const disclaimerLines = pdf.splitTextToSize(disclaimer, contentWidth);
      const closingHeight = 34 + interpretationLines.length * 13 + 36 + disclaimerLines.length * 12;
      ensureSpace(closingHeight);

      addSectionTitle("Interpretation Notes");
      addWrappedText(interpretation, 9, 13);

      y += 12;
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(9);
      pdf.text("Research-use disclaimer", margin, y);
      y += 14;
      pdf.setFont("helvetica", "normal");
      addWrappedText(disclaimer, 8, 12);

      const totalPages = pdf.internal.getNumberOfPages();
      for (let page = 1; page <= totalPages; page += 1) {
        pdf.setPage(page);
        pdf.setFont("helvetica", "normal");
        pdf.setFontSize(8);
        pdf.setTextColor(110, 120, 130);
        pdf.text("NeuroScan XAI | Research prototype", margin, pageHeight - 24);
        pdf.text(`Page ${page} of ${totalPages}`, pageWidth - margin, pageHeight - 24, { align: "right" });
      }

      pdf.save(`neuroscan-xai-report-${id}.pdf`);
    } catch (exportError) {
      console.error("PDF export failed:", exportError);
      window.alert("Could not export the PDF report.");
    } finally {
      setExporting(false);
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm(
      "Delete this scan permanently? This action cannot be undone."
    );

    if (!confirmed) return;

    setDeleting(true);

    try {
      await deleteScan(id);
      navigate("/history");
    } catch (deleteError) {
      console.error("Delete failed:", deleteError);
      window.alert("Could not delete this scan.");
      setDeleting(false);
    }
  }

  function formatDate(date) {
    if (!date) return "—";

    return new Date(date).toLocaleString(undefined, {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  /* ==========================================================
     ERROR STATE
     ========================================================== */

  if (error) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-10 md:px-8">

        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-sm text-slate-500 transition hover:text-brand-400"
        >
          <ArrowLeft size={15} />
          Back to history
        </Link>

        <div className="mt-8 rounded-2xl border border-red-400/15 bg-red-400/[0.04] p-6">

          <div className="flex items-start gap-4">

            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-400/10">
              <Activity
                size={18}
                className="text-red-300"
              />
            </div>

            <div>
              <h2 className="text-base font-semibold text-red-200">
                Unable to load analysis report
              </h2>

              <p className="mt-2 text-sm text-red-300/60">
                {error}
              </p>
            </div>

          </div>

        </div>

      </div>
    );
  }

  /* ==========================================================
     LOADING STATE
     ========================================================== */

  if (!scan) {
    return (
      <div className="mx-auto flex min-h-[500px] max-w-7xl items-center justify-center px-5">

        <div className="text-center">

          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-brand-400/15 bg-brand-500/[0.06]">
            <ScanLine
              size={20}
              className="animate-soft-pulse text-brand-400"
            />
          </div>

          <p className="mt-4 text-sm text-slate-400">
            Loading analysis report
          </p>

          <p className="mt-1 text-xs text-slate-600">
            Retrieving scan and XAI visualizations...
          </p>

        </div>

      </div>
    );
  }

  const confidence = Math.min(
    100,
    Math.max(0, Number(scan.confidence ?? 0))
  );

  const className = scan.predicted_class || "Unknown";

  const isTumor =
    scan.predicted_class &&
    scan.predicted_class.toLowerCase() !== "notumor";

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8 md:py-10">

      {/* ==================================================
          PAGE ACTION BAR
      ================================================== */}

      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">

        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-sm text-slate-500 transition hover:text-brand-400"
        >
          <ArrowLeft size={15} />
          Back to history
        </Link>


        <div className="flex items-center gap-2">

          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting || exporting}
            className="inline-flex items-center gap-2 rounded-xl border border-red-400/15 bg-red-400/[0.04] px-4 py-2.5 text-sm font-medium text-red-300 transition hover:bg-red-400/[0.08] disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Trash2 size={15} />

            {deleting ? "Deleting..." : "Delete"}
          </button>


          <button
            type="button"
            onClick={handleExportPdf}
            disabled={exporting || deleting}
            className="btn-primary"
          >
            <Download size={15} />

            {exporting ? "Generating PDF..." : "Export PDF"}
          </button>

        </div>

      </div>


      {/* ==================================================
          PDF REPORT AREA
      ================================================== */}

      <div
        ref={reportRef}
        className="space-y-5 rounded-3xl border border-white/[0.07] bg-[#070b0d] p-5 md:p-7"
      >

        {/* ================================================
            REPORT HEADER
        ================================================ */}

        <header className="flex flex-col justify-between gap-5 border-b border-white/[0.07] pb-6 md:flex-row md:items-start">

          <div className="flex items-start gap-4">

            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-brand-400/15 bg-brand-500/[0.07]">
              <BrainCircuit
                size={21}
                className="text-brand-400"
              />
            </div>


            <div>

              <div className="flex flex-wrap items-center gap-2">

                <h1 className="text-xl font-semibold text-slate-100 md:text-2xl">
                  NeuroScan XAI Report
                </h1>

                <span className="rounded-md border border-brand-400/15 bg-brand-500/[0.06] px-2 py-1 text-[9px] font-semibold tracking-[0.12em] text-brand-300">
                  RESEARCH
                </span>

              </div>

              <p className="mt-2 text-xs text-slate-500">
                Explainable Brain MRI Analysis
              </p>

            </div>

          </div>


          <div className="md:text-right">

            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-600">
              Analysis Date
            </p>

            <p className="mt-1.5 text-xs text-slate-400">
              {formatDate(scan.created_at)}
            </p>

            <p className="mt-1 text-[10px] text-slate-700">
              Report ID: {id}
            </p>

          </div>

        </header>


        {/* ================================================
            MODEL RESULT
        ================================================ */}

        <section className="overflow-hidden rounded-2xl border border-white/[0.07] bg-[#0d1416]">

          <div className="border-b border-white/[0.06] px-5 py-4">

            <div className="flex items-center gap-2">

              <Activity
                size={15}
                className="text-brand-400"
              />

              <h2 className="text-sm font-semibold text-slate-200">
                Model Analysis
              </h2>

            </div>

          </div>


          <div className="p-5 md:p-6">

            <div className="grid gap-6 md:grid-cols-3">

              {/* Prediction */}

              <div>

                <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-600">
                  Prediction
                </p>

                <div className="mt-3 flex items-center gap-3">

                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-xl border ${
                      isTumor
                        ? "border-red-400/15 bg-red-400/[0.06]"
                        : "border-emerald-400/15 bg-emerald-400/[0.06]"
                    }`}
                  >
                    <CheckCircle2
                      size={18}
                      className={
                        isTumor
                          ? "text-red-300"
                          : "text-emerald-300"
                      }
                    />
                  </div>

                  <div>

                    <p
                      className={`text-xl font-semibold capitalize ${
                        isTumor
                          ? "text-red-300"
                          : "text-emerald-300"
                      }`}
                    >
                      {className}
                    </p>

                    <p className="mt-0.5 text-[10px] text-slate-600">
                      CNN classification
                    </p>

                  </div>

                </div>

              </div>


              {/* Confidence */}

              <div className="md:border-l md:border-white/[0.07] md:pl-6">

                <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-600">
                  Confidence
                </p>

                <p className="mt-3 text-3xl font-semibold text-slate-100">
                  {confidence.toFixed(1)}
                  <span className="ml-1 text-base font-normal text-slate-600">
                    %
                  </span>
                </p>

                <p className="mt-1 text-[10px] text-slate-600">
                  Prediction probability
                </p>

              </div>


              {/* Processing */}

              <div className="md:border-l md:border-white/[0.07] md:pl-6">

                <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-600">
                  Processing Time
                </p>

                <div className="mt-3 flex items-center gap-2">

                  <Clock3
                    size={18}
                    className="text-brand-400"
                  />

                  <p className="text-2xl font-semibold text-slate-100">
                    {scan.processing_time != null
                      ? scan.processing_time
                      : "—"}

                    {scan.processing_time != null && (
                      <span className="ml-1 text-sm font-normal text-slate-600">
                        sec
                      </span>
                    )}
                  </p>

                </div>

                <p className="mt-1 text-[10px] text-slate-600">
                  End-to-end inference
                </p>

              </div>

            </div>


            {/* Confidence meter */}

            <div className="mt-6">

              <div className="mb-2 flex items-center justify-between">

                <span className="text-[10px] text-slate-600">
                  Model confidence
                </span>

                <span className="text-[10px] font-medium text-slate-400">
                  {confidence.toFixed(1)}%
                </span>

              </div>

              <div className="h-1 overflow-hidden rounded-full bg-white/[0.05]">

                <div
                  className={`h-full rounded-full ${
                    isTumor
                      ? "bg-red-400"
                      : "bg-emerald-400"
                  }`}
                  style={{
                    width: `${confidence}%`,
                  }}
                />

              </div>

            </div>

          </div>

        </section>


        {/* ================================================
            AI SUMMARY
        ================================================ */}

        {scan.summary && (
          <section className="rounded-2xl border border-white/[0.07] bg-[#0d1416] p-5 md:p-6">

            <div className="flex items-start gap-4">

              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-brand-400/15 bg-brand-500/[0.06]">

                <Sparkles
                  size={16}
                  className="text-brand-400"
                />

              </div>


              <div>

                <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-brand-400">
                  AI Interpretation
                </p>

                <h2 className="mt-1 text-sm font-semibold text-slate-200">
                  Analysis Summary
                </h2>

                <p className="mt-3 text-sm leading-7 text-slate-400">
                  {scan.summary}
                </p>

              </div>

            </div>

          </section>
        )}


        {/* ================================================
            VISUAL ANALYSIS
        ================================================ */}

        <section>

          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">

            <div>

              <div className="flex items-center gap-2">

                <Microscope
                  size={16}
                  className="text-brand-400"
                />

                <h2 className="text-sm font-semibold text-slate-200">
                  Explainability Analysis
                </h2>

              </div>

              <p className="mt-1.5 text-xs text-slate-600">
                Original MRI and model attribution visualizations
              </p>

            </div>


            <div className="flex items-center gap-2 text-[10px] text-slate-600">

              <FileText size={12} />

              Original + 3 XAI methods

            </div>

          </div>


          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

            <ReportImage
              title="Original MRI"
              base64={scan.original_image_b64}
              description="Input brain MRI used for model inference."
            />

            <ReportImage
              title="Grad-CAM"
              base64={scan.gradcam_b64}
              description="Spatial regions influencing the CNN prediction."
            />

            <ReportImage
              title="Integrated Gradients"
              base64={scan.integrated_gradients_b64}
              description="Pixel attribution relative to the model baseline."
            />

            <ReportImage
              title="SHAP"
              base64={scan.shap_b64}
              description="Feature contribution toward the model output."
            />

          </div>

        </section>


        {/* ================================================
            SCAN-AWARE ASSISTANT
        ================================================ */}

        <ScanAssistant scanId={id} />


        {/* ================================================
            REPORT FOOTER
        ================================================ */}

        <footer className="border-t border-white/[0.06] pt-5">

          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">

            <div className="flex items-center gap-2">

              <BrainCircuit
                size={13}
                className="text-brand-400"
              />

              <span className="text-[10px] font-medium text-slate-500">
                NeuroScan XAI
              </span>

            </div>


            <p className="max-w-2xl text-[9px] leading-4 text-slate-700 sm:text-right">
              Research prototype. Model predictions and explainability
              visualizations are intended for research and educational
              evaluation and should not be interpreted as independent
              clinical diagnoses.
            </p>

          </div>

        </footer>

      </div>

    </div>
  );
}