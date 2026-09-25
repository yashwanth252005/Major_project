export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function fetchJson(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function fetchStats() {
  return fetchJson(`${API_BASE}/stats`);
}

export async function fetchHistory() {
  return fetchJson(`${API_BASE}/history`);
}
