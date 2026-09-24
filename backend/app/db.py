"""Scan-history persistence for NeuroScan-XAI (stdlib sqlite3 only).

The database is a single SQLite file whose location is taken from the
``SCAN_DB_PATH`` environment variable at call time (default:
``neuroscan.db`` in the working directory).  Every public function reads
``SCAN_DB_PATH`` dynamically so tests can point it at a temporary file.
"""

import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone

import os

SCAN_DB_PATH = os.environ.get("SCAN_DB_PATH", "neuroscan.db")

_db_write_lock = threading.Lock()
_schema_ready = False

_DDL = """CREATE TABLE IF NOT EXISTS scans (
  id TEXT PRIMARY KEY, created_at TEXT NOT NULL, filename TEXT, content_type TEXT,
  size_bytes INTEGER, source_width INTEGER, source_height INTEGER,
  prediction TEXT NOT NULL, confidence REAL NOT NULL, raw_probability REAL NOT NULL,
  processing_time_ms REAL, model_name TEXT, model_fingerprint TEXT,
  original_image TEXT, gradcam TEXT, lrp TEXT, shap TEXT)"""

_SCAN_COLUMNS = (
    "id",
    "created_at",
    "filename",
    "content_type",
    "size_bytes",
    "source_width",
    "source_height",
    "prediction",
    "confidence",
    "raw_probability",
    "processing_time_ms",
    "model_name",
    "model_fingerprint",
    "original_image",
    "gradcam",
    "lrp",
    "shap",
)
_EXPECTED_COLUMNS = frozenset(_SCAN_COLUMNS)

# Columns returned by the lightweight list view (no base64 image payloads).
_LIST_COLUMNS = tuple(
    c for c in _SCAN_COLUMNS if c not in ("original_image", "gradcam", "lrp", "shap")
)


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(SCAN_DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _ensure_schema() -> None:
    """Create the scans table once per process; validate an existing one."""
    global _schema_ready
    if _schema_ready:
        return
    with _db_write_lock:
        if _schema_ready:
            return
        con = _connect()
        try:
            con.execute(_DDL)
            con.commit()
            columns = {row["name"] for row in con.execute("PRAGMA table_info(scans)")}
        finally:
            con.close()
        if columns != _EXPECTED_COLUMNS:
            raise RuntimeError(
                "neuroscan.db contains an incompatible existing 'scans' table; "
                "migration is out of scope — move or delete the file"
            )
        _schema_ready = True


def insert_scan(record: dict, created_at: str | None = None) -> dict:
    """Persist one scan record; returns the full stored row incl. id/created_at."""
    _ensure_schema()
    values = {
        "id": uuid.uuid4().hex,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
    }
    for col in _SCAN_COLUMNS:
        if col not in ("id", "created_at"):
            values[col] = record.get(col)

    columns_sql = ", ".join(_SCAN_COLUMNS)
    placeholders = ", ".join(f":{c}" for c in _SCAN_COLUMNS)
    with _db_write_lock:
        con = _connect()
        try:
            con.execute(
                f"INSERT INTO scans ({columns_sql}) VALUES ({placeholders})",
                values,
            )
            con.commit()
        finally:
            con.close()
    return values


def list_scans() -> list[dict]:
    """All scan records (metadata only — no image payloads), newest first."""
    _ensure_schema()
    columns_sql = ", ".join(_LIST_COLUMNS)
    con = _connect()
    try:
        rows = con.execute(
            f"SELECT {columns_sql} FROM scans ORDER BY created_at DESC, rowid DESC"
        ).fetchall()
    finally:
        con.close()
    return [dict(row) for row in rows]


def get_scan(scan_id: str) -> dict | None:
    """Full record (incl. base64 images) for one scan, or None."""
    _ensure_schema()
    columns_sql = ", ".join(_SCAN_COLUMNS)
    con = _connect()
    try:
        row = con.execute(
            f"SELECT {columns_sql} FROM scans WHERE id = ?", (scan_id,)
        ).fetchone()
    finally:
        con.close()
    return dict(row) if row is not None else None


def delete_scan(scan_id: str) -> bool:
    """Delete one scan record; True if a row was removed."""
    _ensure_schema()
    with _db_write_lock:
        con = _connect()
        try:
            cursor = con.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            con.commit()
            return cursor.rowcount > 0
        finally:
            con.close()


def scan_stats(now: datetime | None = None) -> dict:
    """Application-history statistics over stored scans (single aggregate query, no blobs)."""
    _ensure_schema()
    now = now or datetime.now(timezone.utc)
    # created_at is compared as ISO strings: insert_scan is the only writer and
    # always stores datetime.now(timezone.utc).isoformat(), so lexicographic
    # order == chronological order for these values.
    week_cutoff = (now - timedelta(days=7)).isoformat()
    month_cutoff = (now - timedelta(days=30)).isoformat()
    con = _connect()
    try:
        row = con.execute(
            """
            SELECT
              COUNT(*) AS total_scans,
              AVG(confidence) AS avg_confidence,
              AVG(processing_time_ms) AS avg_processing_time_ms,
              MAX(created_at) AS latest_scan_created_at,
              SUM(CASE WHEN prediction = 'Tumour Detected' THEN 1 ELSE 0 END) AS tumour_count,
              SUM(CASE WHEN prediction = 'No Tumour Detected' THEN 1 ELSE 0 END) AS no_tumour_count,
              COALESCE(SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END), 0) AS scans_last_7_days,
              COALESCE(SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END), 0) AS scans_last_30_days
            FROM scans
            """,
            (week_cutoff, month_cutoff),
        ).fetchone()
        by_prediction = {
            r["prediction"]: r["count"]
            for r in con.execute(
                "SELECT prediction, COUNT(*) AS count FROM scans GROUP BY prediction"
            ).fetchall()
        }
    finally:
        con.close()

    count_by_prediction = {"Tumour Detected": 0, "No Tumour Detected": 0}
    count_by_prediction.update(by_prediction)

    return {
        "total_scans": row["total_scans"],
        "count_by_prediction": count_by_prediction,
        "average_confidence_percent": (
            round(row["avg_confidence"], 2) if row["avg_confidence"] is not None else None
        ),
        "average_processing_time_ms": (
            round(row["avg_processing_time_ms"], 2)
            if row["avg_processing_time_ms"] is not None
            else None
        ),
        "latest_scan_created_at": row["latest_scan_created_at"],
        "scans_last_7_days": row["scans_last_7_days"],
        "scans_last_30_days": row["scans_last_30_days"],
    }
