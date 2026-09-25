/**
 * Dashed placeholder panel for empty / loading / no-match states.
 * `action` is an optional rendered node (link or button).
 */
export default function EmptyState({ title, hint, action }) {
  return (
    <div className="empty-state">
      <svg
        className="empty-state__art"
        width="34"
        height="34"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="6.5" />
        <path d="M16 16l4.5 4.5" strokeLinecap="round" />
      </svg>
      <p className="empty-state__title">{title}</p>
      {hint && <p className="empty-state__hint">{hint}</p>}
      {action && <div className="empty-state__action">{action}</div>}
    </div>
  );
}
