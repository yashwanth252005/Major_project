export default function ReportImage({ title, base64, description }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
      <p className="mb-2 text-sm font-medium text-slate-200">{title}</p>
      {base64 ? (
        <img
          src={`data:image/png;base64,${base64}`}
          alt={title}
          className="w-full rounded-lg"
        />
      ) : (
        <div className="flex h-32 items-center justify-center text-xs text-slate-500">
          No image
        </div>
      )}
      {description && <p className="mt-2 text-xs text-slate-500">{description}</p>}
    </div>
  );
}
