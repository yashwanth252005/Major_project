"""Numerical agreement metrics for model attribution maps.

These metrics compare explanation methods; they do not measure clinical
correctness or validate the model prediction.
"""

import numpy as np


def _normalize(values):
    arr = np.asarray(values, dtype=np.float32)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    arr = np.abs(arr)
    maximum = float(arr.max()) if arr.size else 0.0
    return arr / maximum if maximum > 0 else np.zeros_like(arr)


def _cosine(a, b):
    left = a.reshape(-1)
    right = b.reshape(-1)
    denom = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denom == 0:
        return 0.0
    return float(np.dot(left, right) / denom)


def _top_overlap(a, b, fraction=0.10):
    if not np.any(a) or not np.any(b):
        return 0.0

    left = a.reshape(-1)
    right = b.reshape(-1)
    count = max(1, int(left.size * fraction))
    left_idx = set(np.argpartition(left, -count)[-count:].tolist())
    right_idx = set(np.argpartition(right, -count)[-count:].tolist())
    union = left_idx | right_idx
    return float(len(left_idx & right_idx) / len(union)) if union else 0.0


def compute_xai_consistency(gradcam, integrated_gradients, shap):
    maps = {
        "gradcam": _normalize(gradcam),
        "integrated_gradients": _normalize(integrated_gradients),
        "shap": _normalize(shap),
    }

    shapes = {tuple(value.shape) for value in maps.values()}
    if len(shapes) != 1:
        raise ValueError(f"XAI maps must share one spatial shape, got: {sorted(shapes)}")

    pairs = [
        ("gradcam", "integrated_gradients"),
        ("gradcam", "shap"),
        ("integrated_gradients", "shap"),
    ]
    results = {}
    for left, right in pairs:
        key = f"{left}_vs_{right}"
        results[key] = {
            "cosine_similarity": round(_cosine(maps[left], maps[right]), 4),
            "top_10_percent_iou": round(_top_overlap(maps[left], maps[right]), 4),
        }

    return {
        "version": 1,
        "normalization": "absolute attribution scaled independently to [0,1]",
        "metrics": {
            "cosine_similarity": "Similarity of normalized attribution intensity patterns.",
            "top_10_percent_iou": "Intersection-over-union of each method's highest-attribution 10% pixels.",
        },
        "pairwise": results,
        "interpretation_guardrail": (
            "Agreement measures similarity between explanation maps only; "
            "it does not establish clinical correctness or prediction validity."
        ),
    }
