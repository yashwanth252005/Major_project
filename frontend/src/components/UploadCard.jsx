import { useRef, useState } from "react";

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
    <div
      className={`rounded-2xl border-2 border-dashed p-8 text-center transition ${
        dragOver ? "border-brand-400 bg-brand-500/10" : "border-slate-700 bg-slate-900/50"
      }`}
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
    >
      {previewUrl ? (
        <img
          src={previewUrl}
          alt="Selected MRI scan"
          className="mx-auto mb-4 h-48 w-48 rounded-xl object-cover"
        />
      ) : (
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-800 text-2xl">
          🧠
        </div>
      )}

      <p className="text-slate-300">
        Drag & drop an MRI (FLAIR) image here, or{" "}
        <button
          type="button"
          className="text-brand-400 underline underline-offset-2"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
        >
          browse
        </button>
      </p>
      <p className="mt-1 text-xs text-slate-500">JPG, JPEG, PNG, or BMP</p>

      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.bmp"
        className="hidden"
        disabled={disabled}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
    </div>
  );
}
