import { useRef, useState } from "react";
import {
  UploadCloud,
  Brain,
  ImageIcon,
  CheckCircle2,
} from "lucide-react";
import { motion } from "framer-motion";

export default function UploadCard({ onFileSelected, disabled }) {
  const inputRef = useRef(null);

  const [dragOver, setDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [fileName, setFileName] = useState("");

  function handleFile(file) {
    if (!file) return;

    setPreviewUrl(URL.createObjectURL(file));
    setFileName(file.name);
    onFileSelected(file);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
      className={`relative overflow-hidden rounded-3xl border transition-all duration-300
      ${
        dragOver
          ? "border-brand-400 shadow-[0_0_45px_rgba(91,124,255,.25)]"
          : "border-white/10"
      } bg-[#131B2B]`}
    >
      {/* Decorative Glow */}

      <div className="absolute -top-24 -right-24 h-56 w-56 rounded-full bg-brand-500/10 blur-3xl" />

      <div className="absolute -bottom-24 -left-24 h-56 w-56 rounded-full bg-indigo-500/10 blur-3xl" />

      <div className="relative p-6">

        {/* Preview */}

        {previewUrl ? (
          <div className="rounded-2xl border border-white/10 bg-black/20 p-3">

            <img
              src={previewUrl}
              alt="MRI Preview"
              className="h-48 w-full rounded-xl object-contain"
            />

          </div>
        ) : (
          <div className="flex justify-center">

            <motion.div
              animate={{
                y: [0, -6, 0],
              }}
              transition={{
                repeat: Infinity,
                duration: 3,
              }}
              className="flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-indigo-500 shadow-[0_18px_45px_rgba(91,124,255,.35)]"
            >
              <Brain size={38} className="text-white" />
            </motion.div>

          </div>
        )}

        {/* Title */}

        <h2 className="mt-6 text-center text-2xl font-bold">
          Upload MRI Scan
        </h2>

        <p className="mt-2 text-center text-sm leading-6 text-slate-400">
          Upload a FLAIR MRI image to receive AI-powered prediction with
          Grad-CAM, Integrated Gradients and SHAP explanations.
        </p>

        {/* Tags */}

        <div className="mt-5 flex flex-wrap justify-center gap-2">

          <span className="badge">Grad-CAM</span>

          <span className="badge">Integrated Gradients</span>

          <span className="badge">SHAP</span>

        </div>

        {/* Selected File */}

        {fileName && (
          <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3">

            <div className="flex items-center gap-2">

              <CheckCircle2
                size={18}
                className="text-emerald-400"
              />

              <div>

                <p className="text-sm font-medium">
                  Ready for Analysis
                </p>

                <p className="truncate text-xs text-slate-400">
                  {fileName}
                </p>

              </div>

            </div>

          </div>
        )}

        {/* Upload Button */}

        <button
          type="button"
          disabled={disabled}
          onClick={() => inputRef.current?.click()}
          className="btn-primary mt-6 w-full"
        >
          <UploadCloud size={18} />

          Browse MRI Image
        </button>

        {/* Drag & Drop */}

        <div className="mt-5 flex items-center justify-center gap-2 text-sm text-slate-500">

          <ImageIcon size={16} />

          or drag & drop your MRI image here

        </div>

        <p className="mt-2 text-center text-xs text-slate-600">
          Supported formats • JPG • JPEG • PNG • BMP
        </p>

        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.bmp"
          className="hidden"
          disabled={disabled}
          onChange={(e) => handleFile(e.target.files?.[0])}
        />

      </div>
    </motion.div>
  );
}