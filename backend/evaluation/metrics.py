"""Pure evaluation metrics for the NeuroScan-XAI evaluator.

NumPy only — no torch, no model imports — so these functions are trivially
unit-testable against hand-derived known values.

Conventions (normative for this project):
  * Positive class = tumour (label 1).
  * Threshold rule: predicted positive iff p >= threshold (inclusive).
  * Confusion matrix (labels [0, 1], rows = true, cols = predicted):
        [[TN, FP],
         [FN, TP]]
  * Zero-division in a ratio metric resolves to 0.0.
"""

import numpy as np

CLASS_NAMES = {0: "no", 1: "yes"}


def _to_1d_int(*arrays):
    out = []
    for a in arrays:
        arr = np.asarray(a).reshape(-1)
        out.append(arr.astype(int))
    return out


def _to_1d_float(a):
    return np.asarray(a, dtype=float).reshape(-1)


def confusion_counts(y_true, y_pred):
    """Return (tn, fp, fn, tp) for binary labels {0, 1}."""
    t, p = _to_1d_int(y_true, y_pred)
    if t.size == 0:
        return 0, 0, 0, 0
    tn = int(np.sum((t == 0) & (p == 0)))
    fp = int(np.sum((t == 0) & (p == 1)))
    fn = int(np.sum((t == 1) & (p == 0)))
    tp = int(np.sum((t == 1) & (p == 1)))
    return tn, fp, fn, tp


def confusion_matrix(y_true, y_pred):
    """Confusion matrix as [[TN, FP], [FN, TP]] (rows = true, cols = predicted)."""
    tn, fp, fn, tp = confusion_counts(y_true, y_pred)
    return [[tn, fp], [fn, tp]]


def _safe_div(num, den):
    return float(num) / float(den) if den else 0.0


def binary_metrics(y_true, y_pred):
    """Binary classification metrics at a fixed threshold.

    Returns a dict with accuracy, precision, recall, specificity, f1 and
    balanced_accuracy. Zero-division resolves to 0.0.
    """
    tn, fp, fn, tp = confusion_counts(y_true, y_pred)
    n = tn + fp + fn + tp
    accuracy = (tp + tn) / n if n else 0.0
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)  # = sensitivity
    specificity = _safe_div(tn, tn + fp)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    balanced_accuracy = (recall + specificity) / 2
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "balanced_accuracy": balanced_accuracy,
        "counts": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def _one_vs_rest(y_true, y_pred, positive):
    """Precision/recall/F1 treating ``positive`` as the positive class."""
    t, p = _to_1d_int(y_true, y_pred)
    tp = int(np.sum((t == positive) & (p == positive)))
    fp = int(np.sum((t != positive) & (p == positive)))
    fn = int(np.sum((t == positive) & (p != positive)))
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return precision, recall, f1, tp + fn  # support = true occurrences


def per_class_metrics(y_true, y_pred):
    """One-vs-rest precision/recall/F1 for class 0 ("no") and class 1 ("yes"),
    plus macro (unweighted mean) and weighted (support-weighted) averages."""
    t, p = _to_1d_int(y_true, y_pred)
    n = t.size
    result = {}
    supports = {}
    for label in (0, 1):
        precision, recall, f1, support = _one_vs_rest(t, p, label)
        name = CLASS_NAMES[label]
        result[name] = {"precision": precision, "recall": recall, "f1": f1, "support": support}
        supports[label] = support
    macro = {}
    weighted = {}
    for metric in ("precision", "recall", "f1"):
        vals = [result[CLASS_NAMES[l]][metric] for l in (0, 1)]
        macro[metric] = float(sum(vals)) / 2.0
        weighted[metric] = (
            float(sum(v * supports[l] for v, l in zip(vals, (0, 1)))) / n if n else 0.0
        )
    result["macro"] = macro
    result["weighted"] = weighted
    return result


def bin_probabilities(p, n_bins=10):
    """Bin index for each probability: min(int(p * n_bins), n_bins - 1).

    With the default n_bins=10 this is the project-normative
    ``min(int(p * 10), 9)`` rule, so p = 1.0 falls into bin 9.
    """
    probs = _to_1d_float(p)
    if n_bins <= 0:
        raise ValueError("n_bins must be a positive integer")
    raw = (probs * n_bins).astype(int)
    return np.minimum(raw, n_bins - 1)


def compute_brier(y_true, y_score):
    """Brier score = (1/N) * sum((p_i - y_i)^2)."""
    t = _to_1d_int(y_true)[0]
    s = _to_1d_float(y_score)
    if t.size == 0:
        return 0.0
    return float(np.mean((s - t) ** 2))


def compute_ece(y_true, y_score, n_bins=10):
    """Expected Calibration Error over equal-width bins.

    ECE = sum over non-empty bins B of (n_B / N) * |acc_B - conf_B| where
    acc_B = mean y and conf_B = mean p within the bin.
    """
    t = _to_1d_int(y_true)[0]
    s = _to_1d_float(y_score)
    if t.size == 0:
        return 0.0
    bins = bin_probabilities(s, n_bins)
    ece = 0.0
    n = t.size
    for b in range(n_bins):
        mask = bins == b
        n_b = int(np.sum(mask))
        if n_b == 0:
            continue
        acc_b = float(np.mean(t[mask]))
        conf_b = float(np.mean(s[mask]))
        ece += (n_b / n) * abs(acc_b - conf_b)
    return float(ece)


def reliability_bins(y_true, y_score, n_bins=10):
    """Per-bin calibration data (for the reliability diagram / CSV).

    Returns one dict per bin (all n_bins bins, empty bins included):
      bin_index, range_start, range_end, count, mean_confidence,
      fraction_positive, weight (= count / N).
    """
    t = _to_1d_int(y_true)[0]
    s = _to_1d_float(y_score)
    n = t.size
    bins = bin_probabilities(s, n_bins) if n else np.empty(0, dtype=int)
    out = []
    for b in range(n_bins):
        mask = bins == b
        n_b = int(np.sum(mask))
        out.append(
            {
                "bin_index": b,
                "range_start": b / n_bins,
                "range_end": (b + 1) / n_bins,
                "count": n_b,
                "mean_confidence": float(np.mean(s[mask])) if n_b else 0.0,
                "fraction_positive": float(np.mean(t[mask])) if n_b else 0.0,
                "weight": (n_b / n) if n else 0.0,
            }
        )
    return out


def confidence_analysis(y_true, y_score, y_pred, high_conf=0.9, unc_low=0.4, unc_high=0.6):
    """Confidence stratification of correct vs incorrect predictions.

    Confidence per image = max(p, 1 - p). High-confidence error = incorrect
    AND confidence >= high_conf. Uncertain = unc_low <= p <= unc_high
    (inclusive). Empty correct/incorrect group -> count 0, mean 0.0.
    """
    t, _ = _to_1d_int(y_true, y_pred)
    s = _to_1d_float(y_score)
    p = _to_1d_int(y_pred)[0]
    correct = t == p
    incorrect = ~correct
    confidence = np.maximum(s, 1.0 - s)
    high_conf_errors = int(np.sum(incorrect & (confidence >= high_conf)))
    uncertain = int(np.sum((s >= unc_low) & (s <= unc_high)))

    def _group(mask):
        count = int(np.sum(mask))
        mean_conf = float(np.mean(confidence[mask])) if count else 0.0
        return count, mean_conf

    correct_count, correct_mean = _group(correct)
    incorrect_count, incorrect_mean = _group(incorrect)
    return {
        "correct_count": correct_count,
        "correct_mean_confidence": correct_mean,
        "incorrect_count": incorrect_count,
        "incorrect_mean_confidence": incorrect_mean,
        "high_confidence_errors": high_conf_errors,
        "high_confidence_threshold": float(high_conf),
        "uncertain_count": uncertain,
        "uncertain_low": float(unc_low),
        "uncertain_high": float(unc_high),
    }
