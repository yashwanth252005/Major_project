"""Tests for GET /model-info (transparency metadata) and GET /ready (readiness probe)."""

import hashlib
import re

import torch

from app import main as app_main


def _streamed_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---- GET /model-info ----


def test_model_info_returns_200_with_exact_schema(client):
    response = client.get("/model-info")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "model_name",
        "architecture",
        "classes",
        "num_outputs",
        "image_size",
        "channels",
        "normalization",
        "xai_methods",
        "decision_threshold",
        "model_fingerprint",
        "checkpoint_note",
        "training",
    }
    assert set(body["normalization"]) == {"mean", "std", "grayscale", "range_note"}
    assert set(body["training"]) == {"intended_dataset", "evaluation"}
    assert [m["key"] for m in body["xai_methods"]] == ["gradcam", "lrp", "shap"]


def test_model_info_metadata_values(client):
    response = client.get("/model-info")
    assert response.status_code == 200
    body = response.json()
    assert body["model_name"] == "BrainTumorCNN"
    assert body["classes"] == ["Tumour Detected", "No Tumour Detected"]
    assert body["num_outputs"] == 1
    assert body["image_size"] == 128
    assert body["channels"] == 1
    assert body["normalization"]["mean"] == 0.5
    assert body["normalization"]["std"] == 0.5
    assert body["normalization"]["grayscale"] is True
    assert body["decision_threshold"] == 0.5
    assert {m["label"] for m in body["xai_methods"]} == {"Grad-CAM", "LRP", "SHAP"}


def test_model_info_fingerprint_matches_checkpoint(client):
    response = client.get("/model-info")
    assert response.status_code == 200
    body = response.json()
    expected = _streamed_sha256("model_weights.pt")
    assert body["model_fingerprint"] == expected
    assert re.fullmatch(r"[0-9a-f]{64}", body["model_fingerprint"])


def test_model_info_no_path_leakage(client):
    response = client.get("/model-info")
    assert response.status_code == 200
    text = response.text
    assert "\\" not in text
    assert not re.search(r"[A-Za-z]:[\\/]", text)
    assert "model_weights.pt" not in text
    assert app_main.MODEL_PATH not in text


def test_model_info_no_performance_claims(client):
    response = client.get("/model-info")
    assert response.status_code == 200
    assert "accuracy" not in response.text.lower()
    assert "%" not in response.text
    assert "auc" not in response.text.lower()


# ---- GET /ready ----


def test_ready_ok_when_assets_present(client):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "status",
        "model_file_present",
        "model_loaded",
        "device",
        "model_fingerprint",
    }
    assert body["status"] == "ready"
    assert body["model_file_present"] is True
    assert body["model_loaded"] is True
    assert body["device"] == ("cuda" if torch.cuda.is_available() else "cpu")
    assert body["model_fingerprint"] == _streamed_sha256("model_weights.pt")


def test_ready_503_when_model_not_loaded(client, monkeypatch):
    monkeypatch.setattr(app_main, "model_loaded", False)
    response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert set(body) == {"status", "model_file_present", "model_loaded", "detail"}
    assert body["status"] == "not_ready"
    assert body["model_file_present"] is True
    assert body["model_loaded"] is False
    assert body["detail"] == "Model assets unavailable."


def test_ready_503_when_model_file_missing(client, monkeypatch):
    monkeypatch.setattr(app_main, "MODEL_PATH", "missing_weights__test.pt")
    response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["model_file_present"] is False
    assert body["model_loaded"] is True
