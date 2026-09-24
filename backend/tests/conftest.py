"""Shared fixtures for the NeuroScan-XAI backend test suite.

Importing this module pins the process working directory to the backend
directory (so relative paths such as ``model_weights.pt`` and
``demo_data`` resolve) and puts ``backend`` on ``sys.path`` so that
``app`` is importable from the test modules.
"""

import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from app import main as app_main  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


@pytest.fixture(scope="session")
def client():
    return TestClient(app_main.app)


@pytest.fixture(scope="session")
def demo_image_bytes():
    """Bytes of the first (sorted) image file in backend/demo_data/yes."""
    demo_dir = BACKEND_DIR / "demo_data" / "yes"
    for name in sorted(os.listdir(demo_dir)):
        path = demo_dir / name
        if path.is_file() and path.suffix in IMAGE_SUFFIXES:
            return path.read_bytes()
    raise RuntimeError(f"No image with suffix in {IMAGE_SUFFIXES} found in {demo_dir}")


@pytest.fixture(autouse=True)
def isolated_scan_db(tmp_path, monkeypatch):
    from app import db as app_db
    monkeypatch.setattr(app_db, "SCAN_DB_PATH", str(tmp_path / "test_neuroscan.db"))
    monkeypatch.setattr(app_db, "_schema_ready", False)
