"""Model metadata helpers.

Two responsibilities:

* :func:`model_fingerprint` - sha256 digest of the model weights file
  (used by /predict persistence and the /model-info and /ready endpoints).
* :func:`get_model_info` - safe, machine-readable model metadata served by
  GET /model-info: no filesystem paths, no secrets, no performance claims.
"""

import hashlib
import os

_FINGERPRINT_CACHE: dict[str, str] = {}

_CHUNK_BYTES = 1024 * 1024  # 1 MiB


def model_fingerprint(path) -> str | None:
    """Return the hex sha256 of the file at ``path``, or None if it is missing.

    Successful digests are cached per path so the file is hashed only once.
    """
    if path in _FINGERPRINT_CACHE:
        return _FINGERPRINT_CACHE[path]

    if not os.path.isfile(path):
        return None

    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)

    hexdigest = digest.hexdigest()
    _FINGERPRINT_CACHE[path] = hexdigest
    return hexdigest


# Backend-owned copy of the XAI method registry. Display descriptions live in
# frontend/src/xaiMethods.js - the backend must not depend on the frontend.
_XAI_METHODS = [
    {"key": "gradcam", "label": "Grad-CAM"},
    {"key": "lrp", "label": "LRP"},
    {"key": "shap", "label": "SHAP"},
]


def get_model_info(fingerprint: str | None) -> dict:
    """Return the static model metadata payload served by GET /model-info.

    ``fingerprint`` is the SHA-256 hex digest of the model weights file
    (see :func:`model_fingerprint`), or None when the file is absent.
    The payload is safe to expose publicly: no paths, no secrets, no
    performance claims.
    """
    return {
        "model_name": "BrainTumorCNN",  # must match main.MODEL_NAME
        "architecture": "Custom 4-block CNN (Conv-ReLU-MaxPool x4, FC head, "
        "single-logit binary output)",
        "classes": ["Tumour Detected", "No Tumour Detected"],
        "num_outputs": 1,
        "image_size": 128,
        "channels": 1,
        "normalization": {
            "mean": 0.5,
            "std": 0.5,
            "grayscale": True,
            "range_note": "pixels scaled to [0,1] then normalized (x-0.5)/0.5",
        },
        "xai_methods": _XAI_METHODS,
        "decision_threshold": 0.5,
        "model_fingerprint": fingerprint,
        "checkpoint_note": "model_fingerprint is the SHA-256 hex digest of the "
        "model weights file; null when the file is absent",
        "training": {
            "intended_dataset": "BraTS 2021 FLAIR MRI slices (train_real.py)",
            "evaluation": "See docs/evaluation/EVALUATION_REPORT.md (EVAL-001)",
        },
    }
