"""Upload-validation tests for the POST /predict endpoint.

Covers extension/size/empty-file rejection, the configurable upload cap,
the module-level inference lock, and that error details never leak
internal exception text.
"""

import base64
import io
import threading

import numpy as np
import pytest
from PIL import Image

from app import main as app_main


@pytest.fixture(scope="session")
def tiny_png_bytes():
    """A small valid PNG (128x128, mode "L") built in memory with PIL."""
    rng = np.random.default_rng(42)
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


def test_predict_unsupported_extension_returns_400(client, tiny_png_bytes):
    response = client.post(
        "/predict",
        files={"file": ("scan.txt", tiny_png_bytes, "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"].startswith("Unsupported file type")


def test_predict_no_extension_returns_400(client, tiny_png_bytes):
    response = client.post(
        "/predict",
        files={"file": ("scan", tiny_png_bytes, "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"].startswith("Unsupported file type")


def test_predict_oversize_returns_413(client):
    response = client.post(
        "/predict",
        files={
            "file": (
                "big.png",
                b"\x00" * (10 * 1024 * 1024 + 1),
                "image/png",
            )
        },
    )
    assert response.status_code == 413


def test_predict_oversize_limit_is_configurable(
    client, tiny_png_bytes, monkeypatch
):
    monkeypatch.setattr(app_main, "MAX_UPLOAD_BYTES", 16)
    response = client.post(
        "/predict",
        files={"file": ("tiny.png", tiny_png_bytes, "image/png")},
    )
    assert response.status_code == 413


def test_predict_empty_file_returns_400(client):
    response = client.post(
        "/predict",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file uploaded."


def test_predict_valid_png_still_200(client, tiny_png_bytes, mocked_xai):
    response = client.post(
        "/predict",
        files={"file": ("mri.png", tiny_png_bytes, "image/png")},
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
    for key in ("original_image", "gradcam", "lrp", "shap"):
        assert body[key]  # non-empty string
        assert base64.b64decode(body[key]).startswith(b"\x89PNG")


def test_inference_lock_exists_and_predict_works(
    client, tiny_png_bytes, mocked_xai
):
    # threading.Lock is a factory function, so isinstance needs its type.
    assert isinstance(app_main._inference_lock, type(threading.Lock()))
    response = client.post(
        "/predict",
        files={"file": ("mri.png", tiny_png_bytes, "image/png")},
    )
    assert response.status_code == 200


def test_predict_error_detail_does_not_leak_internals(client):
    response = client.post(
        "/predict",
        files={"file": ("corrupt.png", b"not an image", "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or unreadable image file."
