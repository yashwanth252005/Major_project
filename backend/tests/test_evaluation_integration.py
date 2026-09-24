"""End-to-end integration test for evaluation.evaluate.run_evaluation.

Marked slow: it loads the real checkpoint and runs real inference over a small
tmp dataset copied from demo_data. Assertions cover artifact existence and
bookkeeping only — deliberately NO assertion on any performance value.
"""

import csv
import json
import os
from pathlib import Path

import pytest

from evaluation.evaluate import run_evaluation

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEMO_DIR = BACKEND_DIR / "demo_data"
MODEL_PATH = BACKEND_DIR / "model_weights.pt"

EXPECTED_ARTIFACTS = [
    "run_metadata.json",
    "predictions.csv",
    "metrics.json",
    "per_class_metrics.csv",
    "confusion_matrix.json",
    "confusion_matrix_counts.png",
    "confusion_matrix_normalized.png",
    "confidence_analysis.csv",
    "misclassified_cases.csv",
    "calibration_data.csv",
    "reliability_diagram.png",
    "EVALUATION_REPORT.md",
]


def _copy_first_images(src_dir, dst_dir, count=2):
    """Copy the first `count` images (sorted) with an allowed extension."""
    copied = 0
    for name in sorted(os.listdir(src_dir)):
        path = src_dir / name
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            (dst_dir / name).write_bytes(path.read_bytes())
            copied += 1
            if copied == count:
                return


@pytest.mark.slow
def test_run_evaluation_end_to_end(tmp_path):
    data_dir = tmp_path / "mini_dataset"
    (data_dir / "yes").mkdir(parents=True)
    (data_dir / "no").mkdir(parents=True)
    _copy_first_images(DEMO_DIR / "yes", data_dir / "yes", count=2)
    _copy_first_images(DEMO_DIR / "no", data_dir / "no", count=2)

    output_dir = tmp_path / "evaluation_output"
    summary = run_evaluation(
        str(data_dir), str(output_dir), model_path=str(MODEL_PATH)
    )

    # All expected artifacts exist and are non-empty.
    for name in EXPECTED_ARTIFACTS:
        artifact = output_dir / name
        assert artifact.is_file(), f"missing artifact: {name}"
        assert artifact.stat().st_size > 0, f"empty artifact: {name}"

    # predictions.csv: header + exactly 4 rows (2 yes + 2 no).
    with open(output_dir / "predictions.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 4
    assert list(rows[0].keys()) == [
        "path", "true_label", "probability", "predicted_label", "correct"
    ]

    # run_metadata.json: class bookkeeping is exact.
    with open(output_dir / "run_metadata.json", encoding="utf-8") as fh:
        metadata = json.load(fh)
    assert metadata["class_counts"] == {"yes": 2, "no": 2}
    assert metadata["total_samples"] == 4

    # predictions.csv true_label column agrees with the folder layout.
    labels = {row["true_label"] for row in rows}
    assert labels == {"0", "1"}
