"""API tests for the /stats endpoint and the scan_stats aggregate."""

from datetime import datetime, timezone

from app import db as app_db

STATS_KEYS = {
    "total_scans",
    "count_by_prediction",
    "average_confidence_percent",
    "average_processing_time_ms",
    "latest_scan_created_at",
    "scans_last_7_days",
    "scans_last_30_days",
}

EXPECTED_EMPTY_STATS = {
    "total_scans": 0,
    "count_by_prediction": {"Tumour Detected": 0, "No Tumour Detected": 0},
    "average_confidence_percent": None,
    "average_processing_time_ms": None,
    "latest_scan_created_at": None,
    "scans_last_7_days": 0,
    "scans_last_30_days": 0,
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


def test_stats_empty_db_returns_zeros_and_nulls(client):
    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json() == EXPECTED_EMPTY_STATS


def test_stats_response_contains_exactly_expected_keys(client):
    _seed()
    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == STATS_KEYS


def test_stats_aggregates_seeded_dataset(client):
    _seed(
        filename="a.png",
        prediction="Tumour Detected",
        confidence=91.111,
        processing_time_ms=100.0,
        created_at="2026-01-01T10:00:00+00:00",
    )
    _seed(
        filename="b.png",
        prediction="Tumour Detected",
        confidence=82.222,
        processing_time_ms=200.0,
        created_at="2026-01-02T10:00:00+00:00",
    )
    _seed(
        filename="c.png",
        prediction="No Tumour Detected",
        confidence=73.333,
        processing_time_ms=300.0,
        created_at="2026-01-03T10:00:00+00:00",
    )

    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_scans"] == 3
    assert body["count_by_prediction"] == {
        "Tumour Detected": 2,
        "No Tumour Detected": 1,
    }
    assert body["average_confidence_percent"] == 82.22
    assert body["average_processing_time_ms"] == 200.0
    assert body["latest_scan_created_at"] == "2026-01-03T10:00:00+00:00"
    assert body["scans_last_7_days"] == 0
    assert body["scans_last_30_days"] == 0


def test_stats_includes_zero_count_for_absent_class(client):
    _seed(prediction="Tumour Detected")
    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["count_by_prediction"]["Tumour Detected"] == 1
    assert body["count_by_prediction"]["No Tumour Detected"] == 0


def test_stats_does_not_leak_image_payloads(client):
    _seed(original_image="orig-b64", gradcam="gradcam-b64", lrp="lrp-b64", shap="shap-b64")
    response = client.get("/stats")
    assert response.status_code == 200
    assert "orig-b64" not in response.text
    assert "gradcam-b64" not in response.text
    assert "lrp-b64" not in response.text
    assert "shap-b64" not in response.text
    body = response.json()
    for key in ("original_image", "gradcam", "lrp", "shap"):
        assert key not in body
        assert key not in body["count_by_prediction"]


def test_scan_stats_date_windows_with_fixed_now():
    _seed(created_at="2026-09-20T10:00:00+00:00")
    _seed(created_at="2026-09-01T10:00:00+00:00")
    _seed(created_at="2026-05-01T10:00:00+00:00")

    stats = app_db.scan_stats(now=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc))
    assert stats["total_scans"] == 3
    assert stats["scans_last_7_days"] == 1
    assert stats["scans_last_30_days"] == 2


def test_stats_db_failure_returns_500_sanitized(client, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("simulated db failure")

    monkeypatch.setattr(app_db, "scan_stats", _boom)
    response = client.get("/stats")
    assert response.status_code == 500
    assert response.json()["detail"] == "Stats storage error."
