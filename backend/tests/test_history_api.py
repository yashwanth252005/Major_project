"""API tests for the /history endpoints."""

from app import db as app_db

LIGHTWEIGHT_KEYS = {
    "id",
    "created_at",
    "filename",
    "content_type",
    "size_bytes",
    "source_dimensions",
    "prediction",
    "confidence",
    "raw_probability",
    "processing_time_ms",
    "model_name",
}


def _seed(created_at=None, **overrides):
    record = {
        "filename": "scan.png",
        "content_type": "image/png",
        "size_bytes": 2048,
        "source_width": 256,
        "source_height": 256,
        "prediction": "Tumour Detected",
        "confidence": 91.23,
        "raw_probability": 0.9123,
        "processing_time_ms": 42.5,
        "model_name": "BrainTumorCNN",
        "model_fingerprint": "f" * 64,
        "original_image": "orig-b64",
        "gradcam": "gradcam-b64",
        "lrp": "lrp-b64",
        "shap": "shap-b64",
    }
    record.update(overrides)
    return app_db.insert_scan(record, created_at=created_at)


def test_history_empty_returns_empty_list(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == []


def test_history_lists_newest_first(client):
    _seed(filename="old.png", created_at="2026-01-01T00:00:00+00:00")
    _seed(filename="new.png", created_at="2026-02-01T00:00:00+00:00")

    response = client.get("/history")
    assert response.status_code == 200
    rows = response.json()
    assert [r["filename"] for r in rows] == ["new.png", "old.png"]


def test_history_list_excludes_image_payloads(client):
    _seed()
    response = client.get("/history")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    row = rows[0]
    assert set(row) == LIGHTWEIGHT_KEYS
    for key in ("original_image", "gradcam", "lrp", "shap", "model_fingerprint"):
        assert key not in row
    assert row["source_dimensions"] == {"width": 256, "height": 256}


def test_history_detail_returns_images_and_shap_none_roundtrips(client):
    rec = _seed(shap=None)
    response = client.get(f"/history/{rec['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == rec["id"]
    assert body["original_image"] == "orig-b64"
    assert body["gradcam"] == "gradcam-b64"
    assert body["lrp"] == "lrp-b64"
    assert body["shap"] is None


def test_history_detail_missing_returns_404(client):
    response = client.get("/history/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Scan record not found."


def test_history_delete_removes_record(client):
    rec = _seed()
    response = client.delete(f"/history/{rec['id']}")
    assert response.status_code == 204
    assert client.get(f"/history/{rec['id']}").status_code == 404


def test_history_delete_missing_returns_404(client):
    response = client.delete("/history/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Scan record not found."


def _boom(*_args, **_kwargs):
    raise RuntimeError("simulated db failure")


def test_history_list_db_failure_returns_500_sanitized(client, monkeypatch):
    monkeypatch.setattr(app_db, "list_scans", _boom)
    response = client.get("/history")
    assert response.status_code == 500
    assert response.json()["detail"] == "History storage error."


def test_history_detail_db_failure_returns_500_sanitized(client, monkeypatch):
    monkeypatch.setattr(app_db, "get_scan", _boom)
    response = client.get("/history/some-id")
    assert response.status_code == 500
    assert response.json()["detail"] == "History storage error."


def test_history_delete_db_failure_returns_500_sanitized(client, monkeypatch):
    monkeypatch.setattr(app_db, "delete_scan", _boom)
    response = client.delete("/history/some-id")
    assert response.status_code == 500
    assert response.json()["detail"] == "History storage error."
