/**
 * Semicircle probability gauge for the raw model probability (0–1).
 * Fill arc uses stroke-dasharray; a tick marks the decision threshold.
 * All labels are HTML siblings OUTSIDE the SVG (no <text> elements).
 * Stroke values are presentation attributes so the SVG renders identically
 * even when serialized (e.g. by html2canvas).
 */
const ARC_RADIUS = 90;
const ARC_LENGTH = Math.PI * ARC_RADIUS;

export default function ProbabilityGauge({ value, threshold = 0.5 }) {
  const v = Math.max(0, Math.min(1, Number(value) || 0));
  const t = Math.max(0, Math.min(1, Number(threshold) || 0.5));

  const angle = Math.PI * (1 - t);
  const inner = ARC_RADIUS - 9;
  const outer = ARC_RADIUS + 9;
  const x1 = 100 + inner * Math.cos(angle);
  const y1 = 102 - inner * Math.sin(angle);
  const x2 = 100 + outer * Math.cos(angle);
  const y2 = 102 - outer * Math.sin(angle);

  return (
    <figure className="gauge">
      <svg
        className="gauge__svg"
        viewBox="0 0 200 112"
        role="img"
        aria-label={`Raw model probability ${v.toFixed(3)} of 1, decision threshold ${t.toFixed(2)}`}
      >
        <path
          d="M 10 102 A 90 90 0 0 1 190 102"
          fill="none"
          stroke="#e6ebf0"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d="M 10 102 A 90 90 0 0 1 190 102"
          fill="none"
          stroke="#0e7490"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${ARC_LENGTH} ${ARC_LENGTH}`}
          strokeDashoffset={ARC_LENGTH * (1 - v)}
        />
        <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#3f4f5e" strokeWidth="2.5" />
      </svg>
      <figcaption className="gauge__caption">
        <span className="gauge__value">{v.toFixed(3)}</span>
        <span className="gauge__label">
          raw probability &middot; decision threshold {t.toFixed(2)}
        </span>
      </figcaption>
      <div className="gauge__ends" aria-hidden="true">
        <span>0</span>
        <span>1</span>
      </div>
    </figure>
  );
}
