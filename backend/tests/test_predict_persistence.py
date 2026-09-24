"""Tests that POST /predict persists a full scan-history record.

The three XAI functions are mocked (like test_predict_success.py) so the
real model forward pass runs but the heavy explanation steps stay cheap.
"""

import hashlib
import io
import re

import numpy as np
import pytest
from PIL import Image

from app import db as app_db
from app import main as app_main

ORIGINAL_KEYS = {
    "prediction",
    "raw_probability",
    "confidence",
    "original_image",
    "gradcam",
    "lrp",
    "shap",
}


@pytest.fixture(scope="session")
def tiny_png_bytes():
    """A small valid PNG (128x128, mode "L") built in memory with PIL."""
    rng = np.random.default_rng(7)
    arr = rng.integers(0, 256, size=(128, 128), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def mocked_xai(monkeypatch):
    hm = np.ones((128, 128), dtype=np.float32)
    monkeypatch.setattr(app_main, "grad_cam", lambda *a, **k: hm.copy())
    monkeypatch.setattr(app_main, "lrp", lambda *a, **k: hm.copy())
    monkeypatch.setattr(
        app_main, "shap_explanation", lambda *a, **k: (hm.copy(), hm.copy())
    )


def _predict(client, tiny_png_bytes):
    return client.post(
        "/predict",
        files={"file": ("mri.png", tiny_png_bytes, "image/png")},
    )


def test_predict_persists_row_with_metadata(client, tiny_png_bytes, mocked_xai):
    response = _predict(client, tiny_png_bytes)
    assert response.status_code == 200

    rows = app_db.list_scans()
    assert len(rows) == 1
    row = rows[0]

    assert row["filename"] == "mri.png"
    assert row["content_type"] == "image/png"
    assert row["size_bytes"] == len(tiny_png_bytes)
    assert row["source_width"] == 128
    assert row["source_height"] == 128
    assert row["model_name"] == "BrainTumorCNN"
    assert row["processing_time_ms"] > 0

    with open(app_main.MODEL_PATH, "rb") as f:
        expected_fingerprint = hashlib.sha256(f.read()).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", row["model_fingerprint"])
    assert row["model_fingerprint"] == expected_fingerprint


def test_predict_response_contains_original_and_additive_fields_matching_row(
    client, tiny_png_bytes, mocked_xai
):
    response = _predict(client, tiny_png_bytes)
    assert response.status_code == 200
    body = response.json()

    assert ORIGINAL_KEYS <= set(body)
    for key in (
        "id",
        "created_at",
        "filename",
        "content_type",
        "size_bytes",
        "source_dimensions",
        "processing_time_ms",
        "model_name",
        "model_fingerprint",
    ):
        assert key in body

    stored = app_db.get_scan(body["id"])
    assert stored is not None
    assert body["prediction"] == stored["prediction"]
    assert body["raw_probability"] == stored["raw_probability"]
    assert body["confidence"] == stored["confidence"]
    for key in ("original_image", "gradcam", "lrp", "shap"):
        assert body[key] == stored[key]
    assert body["filename"] == stored["filename"] == "mri.png"
    assert body["content_type"] == stored["content_type"]
    assert body["size_bytes"] == stored["size_bytes"]
    assert body["processing_time_ms"] == stored["processing_time_ms"]
    assert body["model_name"] == stored["model_name"]
    assert body["model_fingerprint"] == stored["model_fingerprint"]
    assert body["source_dimensions"] == {
        "width": stored["source_width"],
        "height": stored["source_height"],
    }


def test_predict_shap_null_persisted_as_null(
    client, tiny_png_bytes, mocked_xai, monkeypatch
):
    monkeypatch.setattr(app_main, "background_cache", None)
    monkeypatch.setattr(app_main, "DEMO_DATA_DIR", "demo_data__missing__")
    response = _predict(client, tiny_png_bytes)
    assert response.status_code == 200
    body = response.json()
    assert body["shap"] is None

    stored = app_db.get_scan(body["id"])
    assert stored is not None
    assert stored["shap"] is None


def test_predict_survives_db_insert_failure(
    client, tiny_png_bytes, mocked_xai, monkeypatch
):
    def _boom(*args, **kwargs):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(app_db, "insert_scan", _boom)
    response = _predict(client, tiny_png_bytes)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == ORIGINAL_KEYS
    assert "id" not in body
