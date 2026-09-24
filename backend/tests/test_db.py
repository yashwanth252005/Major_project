"""Unit tests for the scan-history SQLite store (app.db)."""

import sqlite3

import pytest

from app import db as app_db

ALL_COLUMNS = {
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
}


def _record(**overrides):
    record = {
        "filename": "scan.png",
        "content_type": "image/png",
        "size_bytes": 1024,
        "source_width": 128,
        "source_height": 128,
        "prediction": "Tumour Detected",
        "confidence": 87.5,
        "raw_probability": 0.875,
        "processing_time_ms": 12.34,
        "model_name": "BrainTumorCNN",
        "model_fingerprint": "a" * 64,
        "original_image": "orig-b64",
        "gradcam": "gradcam-b64",
        "lrp": "lrp-b64",
        "shap": "shap-b64",
    }
    record.update(overrides)
    return record


def test_schema_creation_is_idempotent():
    app_db._ensure_schema()
    app_db._ensure_schema()  # repeated calls must be a no-op
    app_db.insert_scan(_record())
    app_db.insert_scan(_record(filename="second.png"))
    assert len(app_db.list_scans()) == 2


def test_insert_and_get_roundtrip_all_fields():
    rec = app_db.insert_scan(_record(shap=None))
    assert rec["id"]
    assert rec["created_at"]

    stored = app_db.get_scan(rec["id"])
    assert stored is not None
    assert set(stored) == ALL_COLUMNS
    assert stored["filename"] == "scan.png"
    assert stored["content_type"] == "image/png"
    assert stored["size_bytes"] == 1024
    assert stored["source_width"] == 128
    assert stored["source_height"] == 128
    assert stored["prediction"] == "Tumour Detected"
    assert stored["confidence"] == 87.5
    assert stored["raw_probability"] == 0.875
    assert stored["processing_time_ms"] == 12.34
    assert stored["model_name"] == "BrainTumorCNN"
    assert stored["model_fingerprint"] == "a" * 64
    # images round-trip byte-identical (as stored base64 strings)
    assert stored["original_image"] == "orig-b64"
    assert stored["gradcam"] == "gradcam-b64"
    assert stored["lrp"] == "lrp-b64"
    assert stored["shap"] is None  # None preserved, not coerced


def test_get_missing_returns_none_and_delete_missing_returns_false():
    assert app_db.get_scan("no-such-id") is None
    assert app_db.delete_scan("no-such-id") is False


def test_incompatible_existing_scans_table_raises(tmp_path, monkeypatch):
    db_path = str(tmp_path / "incompatible.db")
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE scans (id TEXT)")
    con.commit()
    con.close()

    monkeypatch.setattr(app_db, "SCAN_DB_PATH", db_path)
    monkeypatch.setattr(app_db, "_schema_ready", False)

    with pytest.raises(RuntimeError, match="incompatible"):
        app_db.list_scans()


def test_list_scans_orders_newest_first():
    app_db.insert_scan(_record(filename="old.png"), created_at="2026-01-01T00:00:00+00:00")
    app_db.insert_scan(_record(filename="newest.png"), created_at="2026-03-01T00:00:00+00:00")
    app_db.insert_scan(_record(filename="middle.png"), created_at="2026-02-01T00:00:00+00:00")

    rows = app_db.list_scans()
    assert [r["filename"] for r in rows] == ["newest.png", "middle.png", "old.png"]
