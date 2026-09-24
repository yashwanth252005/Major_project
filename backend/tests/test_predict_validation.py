"""Validation tests for the POST /predict endpoint."""

import os

from app import main as app_main


def test_predict_without_file_returns_422(client):
    response = client.post("/predict")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert any(
        entry.get("type") == "missing" and entry.get("loc") == ["body", "file"]
        for entry in detail
    )


def test_predict_corrupt_bytes_returns_400(client):
    response = client.post(
        "/predict",
        files={"file": ("corrupt.png", b"this is not an image")},
    )
    assert response.status_code == 400
    assert response.json()["detail"].startswith("Could not read image")


def test_predict_garbage_with_valid_extension_returns_400(client):
    garbage = b"\x89PNG\r\n\x1a\n" + os.urandom(64)
    response = client.post(
        "/predict",
        files={"file": ("scan.png", garbage, "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"].startswith("Could not read image")


def test_predict_returns_503_when_model_not_loaded(client, demo_image_bytes, monkeypatch):
    monkeypatch.setattr(app_main, "model_loaded", False)
    response = client.post(
        "/predict",
        files={"file": ("mri.jpg", demo_image_bytes, "image/jpeg")},
    )
    assert response.status_code == 503
    assert "No trained model found" in response.json()["detail"]
