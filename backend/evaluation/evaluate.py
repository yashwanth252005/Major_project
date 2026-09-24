"""Standalone evaluation CLI for the NeuroScan-XAI backend.

Runs the trained model over a labelled image directory, computes pure-metric
evaluation numbers (see evaluation/metrics.py) and writes a full set of
artifacts (metrics.json, predictions.csv, plots, EVALUATION_REPORT.md, ...).

Fresh-command reference:

    cd backend && venv/Scripts/python.exe -m evaluation.evaluate \
        --data-dir demo_data --output-dir evaluation_output

Programmatic entry point: :func:`run_evaluation`.

The model is loaded and the images are preprocessed EXACTLY like the FastAPI
app does (BrainTumorCNN + app.preprocessing.preprocess_bytes), so the numbers
here describe the deployed inference path, not a separate one.
"""

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")  # must run before pyplot import: no display available

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import sklearn  # noqa: E402
import torch  # noqa: E402

from app.config import ALLOWED_IMAGE_EXTENSIONS, IMG_SIZE  # noqa: E402
from app.model import BrainTumorCNN  # noqa: E402
from app.preprocessing import preprocess_bytes  # noqa: E402

from .metrics import (  # noqa: E402
    binary_metrics,
    compute_brier,
    compute_ece,
    confidence_analysis,
    confusion_matrix,
    per_class_metrics,
    reliability_bins,
)

# Immediate child directories of --data-dir are mapped to classes by name.
# Any other subdirectory (e.g. demo_data/brain_tumor_dataset) is ignored by
# construction: it is not in this mapping.
CLASS_DIR_TO_LABEL = {"yes": 1, "tumor": 1, "no": 0, "notumor": 0}
LABEL_NAMES = {0: "no", 1: "yes"}

PREDICTIONS_COLUMNS = ["path", "true_label", "probability", "predicted_label", "correct"]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _git_commit():
    """Current git commit hash, or "unknown" when git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _sha256_of_file(path):
    """SHA-256 of a file, streamed so large checkpoints don't blow memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_dataset(data_dir):
    """Scan immediate child directories of ``data_dir`` (non-recursive).

    Returns (samples, class_counts) where samples is a sorted list of
    (image_path, label) tuples and class_counts maps directory name -> file
    count. Subdirectories not in CLASS_DIR_TO_LABEL are ignored; files whose
    extension is not in ALLOWED_IMAGE_EXTENSIONS (case-insensitive) are
    skipped.
    """
    samples = []
    class_counts = {}
    for entry in sorted(os.listdir(data_dir)):
        cls_dir = os.path.join(data_dir, entry)
        if not os.path.isdir(cls_dir):
            continue
        label = CLASS_DIR_TO_LABEL.get(entry.lower())
        if label is None:
            continue
        files = sorted(
            name
            for name in os.listdir(cls_dir)
            if os.path.isfile(os.path.join(cls_dir, name))
            and os.path.splitext(name)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
        )
        class_counts[entry] = len(files)
        samples.extend((os.path.join(cls_dir, name), label) for name in files)
    return samples, class_counts


def load_model(model_path):
    """Load BrainTumorCNN exactly like app/main.py._load_model does."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = BrainTumorCNN(in_channels=1, input_size=IMG_SIZE).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model, device


def predict_probabilities(model, samples, device, batch_size=16):
    """Run batched inference; returns the tumour probability of each sample."""
    probabilities = []
    for start in range(0, len(samples), batch_size):
        chunk = samples[start : start + batch_size]
        tensors = []
        for path, _label in chunk:
            with open(path, "rb") as fh:
                tensor, _display = preprocess_bytes(fh.read())
            tensors.append(tensor)
        batch = torch.cat(tensors, dim=0).to(device)
        with torch.no_grad():
            logits = model(batch)
        probabilities.extend(torch.sigmoid(logits).reshape(-1).tolist())
    return [float(p) for p in probabilities]


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------

def _normalize_confusion(counts):
    normalized = []
    for row in counts:
        row_sum = sum(row)
        normalized.append([value / row_sum if row_sum else 0.0 for value in row])
    return normalized


def write_predictions_csv(path, rows):
    """Write predictions.csv / misclassified_cases.csv.

    ``rows`` is a list of dicts with keys path, true_label, probability,
    predicted_label, correct (bool). ``correct`` is serialized as the literal
    string "true"/"false" and probability with 6 decimals.
    """
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(PREDICTIONS_COLUMNS)
        for row in rows:
            writer.writerow(
                [
                    row["path"],
                    int(row["true_label"]),
                    f"{float(row['probability']):.6f}",
                    int(row["predicted_label"]),
                    "true" if row["correct"] else "false",
                ]
            )


def _write_per_class_csv(path, per_class, total):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["class", "precision", "recall", "f1", "support"])
        for name in ("no", "yes"):
            entry = per_class[name]
            writer.writerow([name, f"{entry['precision']:.6f}", f"{entry['recall']:.6f}",
                             f"{entry['f1']:.6f}", entry["support"]])
        for avg in ("macro", "weighted"):
            entry = per_class[avg]
            writer.writerow([avg, f"{entry['precision']:.6f}", f"{entry['recall']:.6f}",
                             f"{entry['f1']:.6f}", total])


def _write_confidence_csv(path, analysis):
    rows = [
        ("correct_count", analysis["correct_count"]),
        ("correct_mean_confidence", f"{analysis['correct_mean_confidence']:.6f}"),
        ("incorrect_count", analysis["incorrect_count"]),
        ("incorrect_mean_confidence", f"{analysis['incorrect_mean_confidence']:.6f}"),
        ("high_confidence_errors", analysis["high_confidence_errors"]),
        ("uncertain_count", analysis["uncertain_count"]),
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "value"])
        writer.writerows(rows)


def _write_calibration_csv(path, bins):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["bin_index", "range", "count", "mean_confidence",
                         "fraction_positive", "weight"])
        for b in bins:
            writer.writerow(
                [
                    b["bin_index"],
                    f"{b['range_start']:.1f}-{b['range_end']:.1f}",
                    b["count"],
                    f"{b['mean_confidence']:.6f}",
                    f"{b['fraction_positive']:.6f}",
                    f"{b['weight']:.6f}",
                ]
            )


def _plot_confusion_matrix(counts, normalized, out_path, title, annotate_normalized):
    fig, ax = plt.subplots(figsize=(5.0, 4.2))
    image = ax.imshow(np.array(counts, dtype=float), cmap="Blues", vmin=0)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels([LABEL_NAMES[0], LABEL_NAMES[1]])
    ax.set_yticklabels([LABEL_NAMES[0], LABEL_NAMES[1]])
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title(title)
    for i in range(2):
        for j in range(2):
            color = "white" if normalized[i][j] > 0.5 else "black"
            if annotate_normalized:
                text = f"{normalized[i][j]:.3f}\n(n={counts[i][j]})"
            else:
                text = f"{counts[i][j]}\n({normalized[i][j]:.3f})"
            ax.text(j, i, text, ha="center", va="center", color=color, fontsize=11)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_reliability_diagram(bins, out_path):
    non_empty = [b for b in bins if b["count"] > 0]
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Perfect calibration")
    if non_empty:
        xs = [b["mean_confidence"] for b in non_empty]
        ys = [b["fraction_positive"] for b in non_empty]
        ax.bar(xs, ys, width=0.1, align="center", edgecolor="black",
               alpha=0.6, label="Observed positive fraction")
        ax.plot(xs, ys, "o-", color="tab:blue", label="Calibration curve")
    ax.set_xlabel("Mean model confidence in bin")
    ax.set_ylabel("Fraction positive in bin")
    ax.set_title("Reliability diagram (calibration curve)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


BINNING_PROCEDURE_TEXT = (
    "Binning procedure (exact): probabilities are partitioned into 10 "
    "equal-width bins over [0, 1]; bin i covers [i/10, (i+1)/10), i.e. "
    "[0.0,0.1), [0.1,0.2), ..., [0.9,1.0]. Each probability p is assigned to "
    "bin index min(int(p * 10), 9), so p = 1.0 falls into the last bin. For "
    "each non-empty bin B: conf_B = mean predicted probability in B, acc_B = "
    "mean true label (fraction of positives) in B, and ECE = sum over bins of "
    "(n_B / N) * |acc_B - conf_B|. The Brier score is (1/N) * sum((p_i - y_i)^2)."
)


def _write_report(path, context):
    m = context["metrics"]
    cm = context["confusion"]
    lines = []
    lines.append("# Evaluation Report")
    lines.append("")
    lines.append(f"- Generated (UTC): {context['generated_at']}")
    lines.append(f"- Git commit: `{context['commit']}`")
    lines.append(f"- Model: `{context['model_path']}` (sha256 `{context['model_sha256']}`)")
    lines.append(f"- Device: {context['device']} | img_size: {context['img_size']}")
    lines.append("")
    lines.append("## Headline metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    for name, key in [("Accuracy", "accuracy"), ("Precision", "precision"),
                      ("Recall (sensitivity)", "recall"), ("Specificity", "specificity"),
                      ("F1", "f1"), ("Balanced accuracy", "balanced_accuracy"),
                      ("ECE", "ece"), ("Brier score", "brier")]:
        lines.append(f"| {name} | {m[key]:.4f} |")
    lines.append("")
    lines.append("## Confusion matrix (rows = true, cols = predicted; threshold "
                 f"{context['threshold']})")
    lines.append("")
    lines.append(f"counts = [[TN={cm['counts'][0][0]}, FP={cm['counts'][0][1]}], "
                 f"[FN={cm['counts'][1][0]}, TP={cm['counts'][1][1]}]] "
                 "(labels [0, 1] = [no, yes]; positive class = tumour)")
    lines.append("")
    lines.append("## Dataset info")
    lines.append("")
    lines.append(f"- Dataset directory: `{context['dataset_dir']}` (name: "
                 f"{context['dataset_name']})")
    lines.append(f"- Total samples: {context['total_samples']}")
    for name, count in context["class_counts"].items():
        lines.append(f"- Class `{name}`: {count} images")
    lines.append(f"- Decision threshold: p >= {context['threshold']} (positive = tumour)")
    lines.append("")
    lines.append("## Calibration summary")
    lines.append("")
    lines.append(f"- ECE: {m['ece']:.4f} | Brier: {m['brier']:.4f}")
    lines.append(f"- {BINNING_PROCEDURE_TEXT}")
    lines.append("")
    lines.append("## Confidence analysis")
    lines.append("")
    ca = m["confidence_analysis"]
    lines.append(f"- Correct predictions: {ca['correct_count']} "
                 f"(mean confidence {ca['correct_mean_confidence']:.4f})")
    lines.append(f"- Incorrect predictions: {ca['incorrect_count']} "
                 f"(mean confidence {ca['incorrect_mean_confidence']:.4f})")
    lines.append(f"- High-confidence errors (confidence >= {ca['high_confidence_threshold']}): "
                 f"{ca['high_confidence_errors']}")
    lines.append(f"- Uncertain predictions ({ca['uncertain_low']} <= p <= "
                 f"{ca['uncertain_high']}): {ca['uncertain_count']}")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- Results depend on the chosen dataset and threshold; changing either "
                 "changes every number in this report.")
    lines.append("- The demo set is small and class-imbalanced, so all metrics carry "
                 "high sampling uncertainty and wide confidence intervals.")
    lines.append("- Images are resized to 128x128 grayscale, which discards detail and "
                 "can change findings relative to full-resolution review.")
    lines.append("- The CNN was trained on a small demo corpus; it may not generalize "
                 "to other scanners, sequences, or populations, and no external "
                 "validation has been performed.")
    lines.append("- Calibration is measured, not corrected: no post-hoc recalibration "
                 "(e.g. Platt scaling / isotonic) has been applied.")
    lines.append("")
    lines.append("## Disclaimer")
    lines.append("")
    lines.append("This evaluation is for academic demonstration only and is NOT a "
                 "clinical tool. It must not be used for diagnosis, treatment "
                 "decisions, or any medical purpose whatsoever.")
    lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def run_evaluation(data_dir, output_dir="evaluation_output", threshold=0.5, batch=16,
                   high_confidence=0.9, uncertain_low=0.4, uncertain_high=0.6,
                   model_path="model_weights.pt"):
    """Evaluate the model over ``data_dir`` and write all artifacts.

    Returns a summary dict with the output directory, headline metrics and
    the list of artifact file names.
    """
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model weights not found: {model_path}")

    samples, class_counts = scan_dataset(data_dir)
    if not samples:
        raise ValueError(
            f"No labelled images found under {data_dir}. Expected immediate "
            "subdirectories named yes/tumor (label 1) or no/notumor (label 0) "
            f"containing {sorted(ALLOWED_IMAGE_EXTENSIONS)} files."
        )

    os.makedirs(output_dir, exist_ok=True)

    model, device = load_model(model_path)
    probabilities = predict_probabilities(model, samples, device, batch_size=batch)

    y_true = [label for _path, label in samples]
    y_score = probabilities
    y_pred = [1 if p >= threshold else 0 for p in y_score]

    binary = binary_metrics(y_true, y_pred)
    per_class = per_class_metrics(y_true, y_pred)
    ece = compute_ece(y_true, y_score)
    brier = compute_brier(y_true, y_score)
    analysis = confidence_analysis(
        y_true, y_score, y_pred,
        high_conf=high_confidence, unc_low=uncertain_low, unc_high=uncertain_high,
    )
    cm_counts = confusion_matrix(y_true, y_pred)
    cm_normalized = _normalize_confusion(cm_counts)
    bins = reliability_bins(y_true, y_score)

    total = len(samples)

    # ---- predictions.csv / misclassified_cases.csv ----
    rows = [
        {
            "path": path,
            "true_label": y_true[i],
            "probability": y_score[i],
            "predicted_label": y_pred[i],
            "correct": y_pred[i] == y_true[i],
        }
        for i, (path, _label) in enumerate(samples)
    ]
    predictions_path = os.path.join(output_dir, "predictions.csv")
    write_predictions_csv(predictions_path, rows)
    write_predictions_csv(
        os.path.join(output_dir, "misclassified_cases.csv"),
        [row for row in rows if not row["correct"]],
    )

    # ---- per_class_metrics.csv ----
    _write_per_class_csv(os.path.join(output_dir, "per_class_metrics.csv"), per_class, total)

    # ---- confidence_analysis.csv / calibration_data.csv ----
    _write_confidence_csv(os.path.join(output_dir, "confidence_analysis.csv"), analysis)
    _write_calibration_csv(os.path.join(output_dir, "calibration_data.csv"), bins)

    # ---- confusion_matrix.json + plots ----
    confusion = {
        "labels": [0, 1],
        "label_names": [LABEL_NAMES[0], LABEL_NAMES[1]],
        "counts": cm_counts,
        "normalized": cm_normalized,
    }
    with open(os.path.join(output_dir, "confusion_matrix.json"), "w", encoding="utf-8") as fh:
        json.dump(confusion, fh, indent=2)

    _plot_confusion_matrix(
        cm_counts, cm_normalized,
        os.path.join(output_dir, "confusion_matrix_counts.png"),
        f"Confusion matrix (counts) - threshold {threshold}",
        annotate_normalized=False,
    )
    _plot_confusion_matrix(
        cm_counts, cm_normalized,
        os.path.join(output_dir, "confusion_matrix_normalized.png"),
        f"Confusion matrix (row-normalized) - threshold {threshold}",
        annotate_normalized=True,
    )
    _plot_reliability_diagram(bins, os.path.join(output_dir, "reliability_diagram.png"))

    # ---- metrics.json ----
    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "dir": data_dir,
            "name": os.path.basename(os.path.normpath(data_dir)),
            "total_samples": total,
            "class_counts": class_counts,
        },
        "threshold": threshold,
        "img_size": IMG_SIZE,
        "device": str(device),
        "confusion_matrix": confusion,
        "accuracy": binary["accuracy"],
        "precision": binary["precision"],
        "recall": binary["recall"],
        "specificity": binary["specificity"],
        "f1": binary["f1"],
        "balanced_accuracy": binary["balanced_accuracy"],
        "counts": binary["counts"],
        "per_class": per_class,
        "ece": ece,
        "brier": brier,
        "confidence_analysis": analysis,
    }
    with open(os.path.join(output_dir, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    # ---- run_metadata.json ----
    metadata = {
        "git_commit": _git_commit(),
        "model_path": model_path,
        "model_sha256": _sha256_of_file(model_path),
        "dataset_dir": data_dir,
        "dataset_name": os.path.basename(os.path.normpath(data_dir)),
        "class_counts": class_counts,
        "total_samples": total,
        "threshold": threshold,
        "high_conf": high_confidence,
        "uncertain_band": {"low": uncertain_low, "high": uncertain_high},
        "device": str(device),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "img_size": IMG_SIZE,
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
        },
    }
    with open(os.path.join(output_dir, "run_metadata.json"), "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    # ---- EVALUATION_REPORT.md ----
    _write_report(
        os.path.join(output_dir, "EVALUATION_REPORT.md"),
        {
            "metrics": {
                "accuracy": binary["accuracy"], "precision": binary["precision"],
                "recall": binary["recall"], "specificity": binary["specificity"],
                "f1": binary["f1"], "balanced_accuracy": binary["balanced_accuracy"],
                "ece": ece, "brier": brier,
                "confidence_analysis": analysis,
            },
            "confusion": confusion,
            "threshold": threshold,
            "generated_at": metadata["generated_at_utc"],
            "commit": metadata["git_commit"],
            "model_path": model_path,
            "model_sha256": metadata["model_sha256"],
            "device": str(device),
            "img_size": IMG_SIZE,
            "dataset_dir": data_dir,
            "dataset_name": metadata["dataset_name"],
            "total_samples": total,
            "class_counts": class_counts,
        },
    )

    artifacts = [
        "run_metadata.json", "predictions.csv", "metrics.json", "per_class_metrics.csv",
        "confusion_matrix.json", "confusion_matrix_counts.png",
        "confusion_matrix_normalized.png", "confidence_analysis.csv",
        "misclassified_cases.csv", "calibration_data.csv", "reliability_diagram.png",
        "EVALUATION_REPORT.md",
    ]
    return {
        "output_dir": output_dir,
        "total_samples": total,
        "class_counts": class_counts,
        "metrics": metrics,
        "artifacts": artifacts,
    }


def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Evaluate the NeuroScan-XAI model over a labelled image directory."
    )
    parser.add_argument("--data-dir", required=True,
                        help="Directory whose immediate child dirs are class folders "
                             "(yes/tumor -> 1, no/notumor -> 0; others ignored).")
    parser.add_argument("--output-dir", default="evaluation_output",
                        help="Where to write artifacts (default: evaluation_output).")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Decision threshold; positive iff p >= threshold.")
    parser.add_argument("--batch", type=int, default=16, help="Inference batch size.")
    parser.add_argument("--high-confidence", type=float, default=0.9,
                        help="Confidence at or above which an error counts as "
                             "high-confidence.")
    parser.add_argument("--uncertain-low", type=float, default=0.4,
                        help="Lower edge (inclusive) of the uncertain band.")
    parser.add_argument("--uncertain-high", type=float, default=0.6,
                        help="Upper edge (inclusive) of the uncertain band.")
    parser.add_argument("--model-path", default="model_weights.pt",
                        help="Path to the trained model_weights.pt checkpoint.")
    return parser


def main(argv=None):
    args = _build_arg_parser().parse_args(argv)
    summary = run_evaluation(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        threshold=args.threshold,
        batch=args.batch,
        high_confidence=args.high_confidence,
        uncertain_low=args.uncertain_low,
        uncertain_high=args.uncertain_high,
        model_path=args.model_path,
    )
    m = summary["metrics"]
    print(f"Evaluated {summary['total_samples']} images "
          f"({summary['class_counts']}) from {args.data_dir}")
    print(f"  accuracy={m['accuracy']:.4f}  precision={m['precision']:.4f}  "
          f"recall={m['recall']:.4f}  specificity={m['specificity']:.4f}")
    print(f"  f1={m['f1']:.4f}  balanced_accuracy={m['balanced_accuracy']:.4f}  "
          f"ECE={m['ece']:.4f}  Brier={m['brier']:.4f}")
    print(f"Artifacts written to: {os.path.abspath(summary['output_dir'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
