import { useRef, useState } from "react";
import { UploadCloud, ImagePlus, Brain } from "lucide-react";
import { motion } from "framer-motion";

export default function UploadCard({ onFileSelected, disabled }) {
  const inputRef = useRef(null);

  const [dragOver, setDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);

  function handleFile(file) {
    if (!file) return;

    setPreviewUrl(URL.createObjectURL(file));
    onFileSelected(file);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
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
      className={`relative overflow-hidden rounded-[30px] border transition-all duration-300
      ${
        dragOver
          ? "border-brand-400 bg-brand-500/10 scale-[1.01]"
          : "border-white/10 bg-white/[0.04]"
      }`}
    >
      {/* background glow */}

      <div className="absolute inset-0 bg-gradient-to-br from-brand-500/10 via-transparent to-transparent pointer-events-none" />

      <div className="relative p-8">

        {previewUrl ? (
          <img
            src={previewUrl}
            alt=""
            className="mx-auto h-64 rounded-2xl shadow-2xl object-contain"
          />
        ) : (
          <div className="flex justify-center">

            <div className="flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-indigo-500 shadow-[0_20px_50px_rgba(79,107,255,.45)]">

              <Brain size={42} className="text-white" />

            </div>

          </div>
        )}

        <h2 className="mt-7 text-center text-2xl font-bold">
          Upload MRI Scan
        </h2>

        <p className="mx-auto mt-3 max-w-md text-center text-slate-400">
          Upload a FLAIR MRI image and receive an AI prediction with
          Grad-CAM, Integrated Gradients and SHAP explanations.
        </p>

        <div className="mt-6 flex flex-wrap justify-center gap-2">

          <span className="badge">Grad-CAM</span>

          <span className="badge">Integrated Gradients</span>

          <span className="badge">SHAP</span>

        </div>

        <button
          type="button"
          disabled={disabled}
          onClick={() => inputRef.current?.click()}
          className="btn-primary mt-8 w-full"
        >
          <UploadCloud size={20} />

          Browse MRI Image
        </button>

        <div className="mt-5 flex justify-center gap-2 text-xs text-slate-500">

          <ImagePlus size={15} />

          JPG

          •

          PNG

          •

          JPEG

          •

          BMP

        </div>

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