"""Scan-history persistence for NeuroScan-XAI (stdlib sqlite3 only).

The database is a single SQLite file whose location is taken from the
``SCAN_DB_PATH`` environment variable at call time (default:
``neuroscan.db`` in the working directory).  Every public function reads
``SCAN_DB_PATH`` dynamically so tests can point it at a temporary file.
"""

import sqlite3
import threading
import uuid
from datetime import datetime, timezone

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
