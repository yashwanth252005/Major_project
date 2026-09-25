/**
 * Verdict/status pill. tone: "neutral" | "alert" | "safe" | "accent".
 */
export default function Badge({ tone = "neutral", children }) {
  return <span className={`badge badge--${tone}`}>{children}</span>;
}
