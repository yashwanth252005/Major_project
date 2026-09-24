"""Unit tests for app.main._preprocess and app.main._load_background."""

import io

import numpy as np
import pytest
import torch
from PIL import Image

from app import main as app_main


def _gradient_png_bytes() -> bytes:
    """Build a 128x128 gradient grayscale PNG entirely in memory."""
    arr = np.arange(128 * 128).reshape(128, 128) % 256
    img = Image.fromarray(arr.astype(np.uint8), mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_preprocess_shapes_dtypes_and_normalization():
    b = _gradient_png_bytes()
    tensor, display = app_main._preprocess(b)

    assert tuple(tensor.shape) == (1, 1, 128, 128)
    assert tensor.dtype == torch.float32
    assert tensor.min().item() >= -1.0
    assert tensor.max().item() <= 1.0
    assert display.shape == (128, 128)
    assert display.dtype == np.uint8

    # Independently recompute the expected normalization.
    arr = (
        np.array(Image.open(io.BytesIO(b)).convert("L").resize((128, 128)))
        .astype(np.float32)
        / 255.0
    )
    assert np.allclose(tensor.numpy()[0, 0], (arr - 0.5) / 0.5, atol=1e-6)
    assert np.array_equal(display, np.uint8(arr * 255))


def test_preprocess_is_deterministic():
    b = _gradient_png_bytes()
    t1, _ = app_main._preprocess(b)
    t2, _ = app_main._preprocess(b)
    assert torch.equal(t1, t2) is True


def test_load_background_returns_normalized_tensor(monkeypatch):
    monkeypatch.setattr(app_main, "background_cache", None)
    bg = app_main._load_background()
    assert isinstance(bg, torch.Tensor)
    assert tuple(bg.shape) == (16, 1, 128, 128)
    assert bg.dtype == torch.float32
    assert bg.min().item() >= -1.0
    assert bg.max().item() <= 1.0
    # Second call must return the cached object (identity, not a copy).
    assert app_main._load_background() is bg


def test_load_background_returns_none_without_demo_data(monkeypatch):
    monkeypatch.setattr(app_main, "background_cache", None)
    monkeypatch.setattr(app_main, "DEMO_DATA_DIR", "demo_data__missing__")
    assert app_main._load_background() is None
