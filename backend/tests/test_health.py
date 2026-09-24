"""Tests for the GET /health endpoint."""

import torch

from app import main as app_main


def test_health_returns_200_with_expected_keys(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "model_loaded", "device"}
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["device"] == ("cuda" if torch.cuda.is_available() else "cpu")
