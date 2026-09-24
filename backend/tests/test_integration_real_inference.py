"""End-to-end test: real model inference and the full XAI pipeline (no mocks)."""

import base64

import pytest

EXPECTED_KEYS = {
    "prediction",
    "raw_probability",
    "confidence",
    "original_image",
    "gradcam",
    "lrp",
    "shap",
}


@pytest.mark.slow
def test_predict_end_to_end_real_model_and_xai(client, demo_image_bytes):
    response = client.post(
        "/predict",
        files={"file": ("mri.jpg", demo_image_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == EXPECTED_KEYS
    for key in ("original_image", "gradcam", "lrp", "shap"):
        assert body[key]  # non-null, non-empty
        assert base64.b64decode(body[key]).startswith(b"\x89PNG")
    assert body["prediction"] in {"Tumour Detected", "No Tumour Detected"}
    assert 0.0 <= body["raw_probability"] <= 1.0
    assert 0.0 <= body["confidence"] <= 100.0
