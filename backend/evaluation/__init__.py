"""Evaluation & reliability framework for NeuroScan-XAI (Phase 3A).

Re-exports the pure metric functions and the programmatic evaluation entry
point so callers can simply ``from evaluation import ...``.

``run_evaluation`` is re-exported lazily (PEP 562): importing it eagerly here
would execute ``evaluation.evaluate`` at package-import time, which conflicts
with running the CLI as ``python -m evaluation.evaluate`` (RuntimeWarning).
"""

from .metrics import (
    binary_metrics,
    compute_brier,
    compute_ece,
    confidence_analysis,
    confusion_counts,
    confusion_matrix,
    per_class_metrics,
    reliability_bins,
)

# Alias so either naming convention works; both refer to the same pure function.
compute_binary_metrics = binary_metrics

__all__ = [
    "run_evaluation",
    "binary_metrics",
    "compute_binary_metrics",
    "compute_brier",
    "compute_ece",
    "confidence_analysis",
    "confusion_counts",
    "confusion_matrix",
    "per_class_metrics",
    "reliability_bins",
]


def __getattr__(name):
    if name == "run_evaluation":
        from .evaluate import run_evaluation

        return run_evaluation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
