# Official Evaluation Snapshot (EVAL-001)
> Git commit evaluated: 58de4ed3ca1ae0fbd6ffecee901dfaa50751d284 (phase-3a; working tree
> contained only control-document/doc additions beyond this commit)
> Model: backend/model_weights.pt — SHA-256 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1
> Dataset: bundled Kaggle brain_tumor_dataset @ commit 4d0f5ed — APPROVED WITH DISCLOSURES 2026-09-25
> Dataset manifest SHA-256: ca502c2b8443b0d6d854578cf085caf02e54a2fffb9db02885abc6a17e343335
> Reproducibility: independently re-executed; all timestamp-free artifacts byte-identical
> Note: Phase 3A smoke-run figures are superseded by this run and were never citable.

# Evaluation Report

- Generated (UTC): 2026-09-24T22:09:16.128366+00:00
- Git commit: `58de4ed3ca1ae0fbd6ffecee901dfaa50751d284`
- Model: `model_weights.pt` (sha256 `5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1`)
- Device: cpu | img_size: 128

## Headline metrics

| Metric | Value |
| --- | --- |
| Accuracy | 0.6126 |
| Precision | 0.7664 |
| Recall (sensitivity) | 0.5290 |
| Specificity | 0.7449 |
| F1 | 0.6260 |
| Balanced accuracy | 0.6370 |
| ECE | 0.2907 |
| Brier score | 0.3129 |

## Confusion matrix (rows = true, cols = predicted; threshold 0.5)

counts = [[TN=73, FP=25], [FN=73, TP=82]] (labels [0, 1] = [no, yes]; positive class = tumour)

## Dataset info

- Dataset directory: `demo_data` (name: demo_data)
- Total samples: 253
- Class `no`: 98 images
- Class `yes`: 155 images
- Decision threshold: p >= 0.5 (positive = tumour)

## Calibration summary

- ECE: 0.2907 | Brier: 0.3129
- Binning procedure (exact): probabilities are partitioned into 10 equal-width bins over [0, 1]; bin i covers [i/10, (i+1)/10), i.e. [0.0,0.1), [0.1,0.2), ..., [0.9,1.0]. Each probability p is assigned to bin index min(int(p * 10), 9), so p = 1.0 falls into the last bin. For each non-empty bin B: conf_B = mean predicted probability in B, acc_B = mean true label (fraction of positives) in B, and ECE = sum over bins of (n_B / N) * |acc_B - conf_B|. The Brier score is (1/N) * sum((p_i - y_i)^2).

## Confidence analysis

- Correct predictions: 155 (mean confidence 0.9041)
- Incorrect predictions: 98 (mean confidence 0.8624)
- High-confidence errors (confidence >= 0.9): 55
- Uncertain predictions (0.4 <= p <= 0.6): 19

## Limitations

- Results depend on the chosen dataset and threshold; changing either changes every number in this report.
- The demo set is small and class-imbalanced, so all metrics carry high sampling uncertainty and wide confidence intervals.
- Images are resized to 128x128 grayscale, which discards detail and can change findings relative to full-resolution review.
- The CNN was trained on a small demo corpus; it may not generalize to other scanners, sequences, or populations, and no external validation has been performed.
- Calibration is measured, not corrected: no post-hoc recalibration (e.g. Platt scaling / isotonic) has been applied.

## Disclaimer

This evaluation is for academic demonstration only and is NOT a clinical tool. It must not be used for diagnosis, treatment decisions, or any medical purpose whatsoever.
