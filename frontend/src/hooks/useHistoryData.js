import { useCallback, useEffect, useRef, useState } from "react";
import { fetchHistory } from "../api";

/**
 * Fetches GET /history once on mount and exposes the stored rows.
 * The `cancelled` flag guards against setState after unmount (and against
 * the double-invoked effects React StrictMode runs in development).
 * Returns { rows, loading, error, refresh } — refresh() re-fetches.
 */
export default function useHistoryData() {
  const [rows, setRows] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchHistory();
        if (!cancelled) setRows(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load scan history.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      mountedRef.current = false;
    };
  }, []);

  const refresh = useCallback(async () => {
    if (!mountedRef.current) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHistory();
      if (mountedRef.current) setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      if (mountedRef.current) setError(e.message || "Failed to load scan history.");
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  return { rows, loading, error, refresh };
}
