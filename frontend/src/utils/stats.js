/**
 * Pure helpers for deriving application-usage statistics from the rows
 * returned by GET /history. Every function accepts an empty (or null)
 * row list and returns a well-defined empty result:
 *   - counts are 0, lists are []
 *   - averages / medians are null when there is nothing to average
 */

/**
 * Collects the finite numeric `confidence` values (0–100) from rows.
 * @param {Array<{confidence: number}>} rows
 * @returns {number[]}
 */
function collectConfidences(rows) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((r) => Number(r?.confidence))
    .filter((c) => Number.isFinite(c));
}

/**
 * Local calendar date key (YYYY-MM-DD) of a Date — matches the
 * <input type="date"> string format used by the history filters.
 * @param {Date} d
 * @returns {string}
 */
function localDateKey(d) {
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

/**
 * Short day label like "Sep 12" (locale pinned to en-US so the
 * day-number extraction in MiniBars stays stable).
 * @param {Date} d
 * @returns {string}
 */
function formatDayLabel(d) {
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/**
 * Median of the `confidence` field (0–100) across rows.
 * @param {Array<{confidence: number}>} rows
 * @returns {number|null} median confidence, or null when rows is empty
 */
export function medianConfidence(rows) {
  const values = collectConfidences(rows);
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
}

/**
 * Bins stored scans by model confidence into `binCount` equal-width bins.
 *
 * Domain note: the backend stores confidence as max(p, 1 - p) * 100, so every
 * value lies in [50, 100]; the default lo/hi match that assumption. Bins are
 * inclusive of their lower edge, and the final bin is also inclusive of its
 * upper edge so the maximum possible value (100) is never dropped.
 *
 * @param {Array<{confidence: number}>} rows
 * @param {number} [binCount=10] number of equal-width bins
 * @param {number} [lo=50] lower edge of the binning domain
 * @param {number} [hi=100] upper edge of the binning domain
 * @returns {Array<{from: number, to: number, count: number}>}
 */
export function binConfidence(rows, binCount = 10, lo = 50, hi = 100) {
  if (!Array.isArray(rows) || !Number.isFinite(binCount) || binCount <= 0) return [];
  if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo) return [];

  const width = (hi - lo) / binCount;
  const bins = Array.from({ length: binCount }, (_, i) => ({
    from: lo + i * width,
    to: lo + (i + 1) * width,
    count: 0,
  }));

  for (const value of collectConfidences(rows)) {
    let idx = Math.floor((value - lo) / width);
    if (idx < 0) idx = 0;
    if (idx >= binCount) idx = binCount - 1;
    bins[idx].count += 1;
  }

  return bins;
}

/**
 * Scan counts per local calendar day for the last `days` days, ordered
 * oldest → newest. "Today" is the final bucket; days without scans count 0.
 * @param {Array<{created_at: string}>} rows
 * @param {number} [days=14]
 * @returns {Array<{label: string, count: number}>} label is a short local day like "Sep 12"
 */
export function countsByDay(rows, days = 14) {
  const list = Array.isArray(rows) ? rows : [];
  const n = Math.max(1, Math.floor(days));

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const buckets = [];
  for (let i = n - 1; i >= 0; i -= 1) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    buckets.push({ key: localDateKey(d), label: formatDayLabel(d), count: 0 });
  }

  const byKey = new Map(buckets.map((b) => [b.key, b]));
  for (const row of list) {
    const ts = Date.parse(row?.created_at);
    if (!Number.isFinite(ts)) continue;
    const day = new Date(ts);
    day.setHours(0, 0, 0, 0);
    const bucket = byKey.get(localDateKey(day));
    if (bucket) bucket.count += 1;
  }

  return buckets.map(({ label, count }) => ({ label, count }));
}

/**
 * Headline numbers for the history KPI chips.
 * @param {Array<{confidence: number, prediction: string}>} rows
 * @returns {{count: number, avgConfidence: number|null, tumour: number,
 *            noTumour: number, uncertain70: number}}
 *   avgConfidence is rounded to 2 decimal places (null when empty);
 *   uncertain70 counts rows whose confidence is below 70 — a low-certainty
 *   model output, not a mistake.
 */
export function summarizeRows(rows) {
  const list = Array.isArray(rows) ? rows : [];
  const values = collectConfidences(rows);
  const avg =
    values.length === 0
      ? null
      : values.reduce((sum, v) => sum + v, 0) / values.length;

  return {
    count: list.length,
    avgConfidence: avg === null ? null : Math.round(avg * 100) / 100,
    tumour: list.filter((r) => r?.prediction === "Tumour Detected").length,
    noTumour: list.filter((r) => r?.prediction === "No Tumour Detected").length,
    uncertain70: values.filter((c) => c < 70).length,
  };
}

/**
 * Count of rows captured today (local calendar date).
 * @param {Array<{created_at: string}>} rows
 * @returns {number}
 */
export function scansToday(rows) {
  const list = Array.isArray(rows) ? rows : [];
  const todayKey = localDateKey(new Date());
  return list.filter((r) => {
    const ts = Date.parse(r?.created_at);
    if (!Number.isFinite(ts)) return false;
    return localDateKey(new Date(ts)) === todayKey;
  }).length;
}
