"""Tests for POST /predict with the three XAI functions mocked.

Only ``grad_cam``, ``lrp`` and ``shap_explanation`` are replaced, and only
in the ``app.main`` namespace (they were imported there). The real model
forward pass is kept.
"""

import base64

import numpy as np
import pytest

from app import main as app_main


@pytest.fixture()
def mocked_xai(monkeypatch):
    hm = np.ones((128, 128), dtype=np.float32)
    monkeypatch.setattr(app_main, "grad_cam", lambda *a, **k: hm.copy())
    monkeypatch.setattr(app_main, "lrp", lambda *a, **k: hm.copy())
    monkeypatch.setattr(
        app_main, "shap_explanation", lambda *a, **k: (hm.copy(), hm.copy())
    )


def test_predict_happy_path_response_shape(client, demo_image_bytes, mocked_xai):
    response = client.post(
        "/predict",
        files={"file": ("mri.jpg", demo_image_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    # Phase 4 adds history metadata fields
    assert {
        "prediction",
        "raw_probability",
        "confidence",
        "original_image",
        "gradcam",
        "lrp",
        "shap",
    } <= set(body)
    assert body["prediction"] in {"Tumour Detected", "No Tumour Detected"}
    assert isinstance(body["raw_probability"], float)
    assert 0.0 <= body["raw_probability"] <= 1.0
    assert 0 <= body["confidence"] <= 100
    for key in ("original_image", "gradcam", "lrp", "shap"):
        assert body[key]  # non-empty string
        assert base64.b64decode(body[key]).startswith(b"\x89PNG")
    assert body["shap"] is not None


def test_predict_label_and_confidence_consistency(client, demo_image_bytes, mocked_xai):
    response = client.post(
        "/predict",
        files={"file": ("mri.jpg", demo_image_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    rp = body["raw_probability"]
    expected_label = "Tumour Detected" if rp >= 0.5 else "No Tumour Detected"
    assert body["prediction"] == expected_label
    expected_confidence = round((rp if rp >= 0.5 else 1 - rp) * 100, 2)
    assert body["confidence"] == expected_confidence


def test_predict_shap_null_when_demo_data_missing(
    client, demo_image_bytes, mocked_xai, monkeypatch
):
    monkeypatch.setattr(app_main, "background_cache", None)
    monkeypatch.setattr(app_main, "DEMO_DATA_DIR", "demo_data__missing__")
    response = client.post(
        "/predict",
        files={"file": ("mri.jpg", demo_image_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["shap"] is None
    for key in ("original_image", "gradcam", "lrp"):
        assert body[key]  # non-empty string
        assert base64.b64decode(body[key]).startswith(b"\x89PNG")
