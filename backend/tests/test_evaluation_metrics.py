"""Known-value tests for evaluation/metrics.py.

Every expected number below is derived BY HAND from the project-normative
formulas (see the derivation comments in each test):

  * predicted positive (1) iff p >= threshold (inclusive); positive class = tumour
  * confusion matrix (labels [0,1], rows = true, cols = predicted): [[TN,FP],[FN,TP]]
  * accuracy=(TP+TN)/N; precision=TP/(TP+FP); recall=TP/(TP+FN);
    specificity=TN/(TN+FP); F1=2PR/(P+R); balanced_accuracy=(recall+specificity)/2;
    zero-division -> 0.0
  * per-class one-vs-rest for labels 0 ("no") and 1 ("yes"); macro = unweighted
    mean; weighted = sum((support_c/N) * metric_c)
  * Brier = (1/N) * sum((p_i - y_i)^2)
  * ECE: 10 equal-width bins, bin index = min(int(p*10), 9); per non-empty bin
    ECE += (n_B/N) * |acc_B - conf_B| with acc_B = mean y, conf_B = mean p
  * confidence per image = max(p, 1-p); high-confidence error = incorrect AND
    confidence >= 0.9; uncertain = 0.4 <= p <= 0.6 (inclusive)

Float note: bin index min(int(p*10), 9) was verified in the target venv for
every probability used below (0.05..0.95 all multiply to their exact integer
or half-integer; int() truncation then yields the mathematically intended bin),
so the decimal hand-derivations match the code exactly.
"""

import csv

import numpy as np
import pytest
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix as sklearn_confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from evaluation.evaluate import write_predictions_csv
from evaluation.metrics import (
    binary_metrics,
    bin_probabilities,
    compute_brier,
    compute_ece,
    confidence_analysis,
    confusion_counts,
    confusion_matrix,
    per_class_metrics,
    reliability_bins,
)

APPROX = dict(rel=1e-9)
APPROX_ABS = dict(abs=1e-9)  # for exact zeros, where rel=1e-9 is meaningless


# ---------------------------------------------------------------------------
# Case A: mixed predictions at threshold 0.5
# ---------------------------------------------------------------------------

CASE_A_TRUE = [1, 1, 1, 1, 0, 0, 0, 0]
CASE_A_SCORE = [0.9, 0.8, 0.7, 0.3, 0.2, 0.1, 0.6, 0.4]


def _case_a_pred(threshold=0.5):
    """p >= threshold (inclusive)."""
    return [1 if p >= threshold else 0 for p in CASE_A_SCORE]


def test_case_a_binary_metrics_and_confusion():
    # Derivation at t=0.5: y_pred = p>=0.5 -> [1,1,1,0,0,0,1,0].
    # Per sample (true,pred): (1,1)TP (1,1)TP (1,1)TP (1,0)FN
    #                         (0,0)TN (0,0)TN (0,1)FP (0,0)TN
    # => TP=3, FN=1, TN=3, FP=1;  N=8.
    y_pred = _case_a_pred(0.5)
    m = binary_metrics(CASE_A_TRUE, y_pred)
    assert m["counts"] == {"tn": 3, "fp": 1, "fn": 1, "tp": 3}
    # accuracy  = (TP+TN)/N   = (3+3)/8 = 0.75
    assert m["accuracy"] == pytest.approx(0.75, **APPROX)
    # precision = TP/(TP+FP)  = 3/(3+1)  = 0.75
    assert m["precision"] == pytest.approx(0.75, **APPROX)
    # recall    = TP/(TP+FN)  = 3/(3+1)  = 0.75
    assert m["recall"] == pytest.approx(0.75, **APPROX)
    # specificity = TN/(TN+FP) = 3/(3+1) = 0.75
    assert m["specificity"] == pytest.approx(0.75, **APPROX)
    # F1 = 2PR/(P+R) = 2*0.75*0.75/1.5 = 0.75
    assert m["f1"] == pytest.approx(0.75, **APPROX)
    # balanced  = (recall+specificity)/2 = (0.75+0.75)/2 = 0.75
    assert m["balanced_accuracy"] == pytest.approx(0.75, **APPROX)
    # Confusion matrix [[TN,FP],[FN,TP]] = [[3,1],[1,3]]
    assert confusion_matrix(CASE_A_TRUE, y_pred) == [[3, 1], [1, 3]]
    assert confusion_counts(CASE_A_TRUE, y_pred) == (3, 1, 1, 3)


def test_case_a_brier():
    # Brier = (1/8) * sum((p_i - y_i)^2):
    #   (0.9-1)^2=0.01  (0.8-1)^2=0.04  (0.7-1)^2=0.09  (0.3-1)^2=0.49
    #   (0.2-0)^2=0.04  (0.1-0)^2=0.01  (0.6-0)^2=0.36  (0.4-0)^2=0.16
    # sum = 1.20  ->  1.20 / 8 = 0.15
    assert compute_brier(CASE_A_TRUE, CASE_A_SCORE) == pytest.approx(0.15, **APPROX)


def test_case_a_ece():
    # Bins (index = min(int(p*10), 9)), one sample per bin (all distinct):
    #   p=0.9->9 (y=1)  p=0.8->8 (y=1)  p=0.7->7 (y=1)  p=0.3->3 (y=1)
    #   p=0.2->2 (y=0)  p=0.1->1 (y=0)  p=0.6->6 (y=0)  p=0.4->4 (y=0)
    # Single-sample bins: |acc_B - conf_B| = |y_i - p_i|.
    # gaps: 0.1 + 0.2 + 0.3 + 0.7 + 0.2 + 0.1 + 0.6 + 0.4 = 2.6
    # ECE = (1/8) * 2.6 = 0.325   (orchestrator-corrected value)
    assert compute_ece(CASE_A_TRUE, CASE_A_SCORE) == pytest.approx(0.325, **APPROX)


# ---------------------------------------------------------------------------
# Case B: all predictions correct (concrete values chosen by implementor)
# ---------------------------------------------------------------------------

CASE_B_TRUE = [1, 1, 1, 1, 0, 0, 0, 0]
CASE_B_SCORE = [0.9, 0.8, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1]


def _case_b_pred():
    return [1 if p >= 0.5 else 0 for p in CASE_B_SCORE]


def test_case_b_perfect_predictions_all_correct():
    # Derivation at t=0.5: y_pred = p>=0.5 -> [1,1,1,1,0,0,0,0], which equals
    # y_true exactly => TP=4, TN=4, FP=0, FN=0; N=8.
    y_pred = _case_b_pred()
    m = binary_metrics(CASE_B_TRUE, y_pred)
    # accuracy = 8/8 = 1.0; precision = 4/4 = 1.0; recall = 4/4 = 1.0;
    # specificity = 4/4 = 1.0; F1 = 2*1*1/2 = 1.0; balanced = (1+1)/2 = 1.0
    for key in ("accuracy", "precision", "recall", "specificity", "f1", "balanced_accuracy"):
        assert m[key] == pytest.approx(1.0, **APPROX), key
    assert confusion_matrix(CASE_B_TRUE, y_pred) == [[4, 0], [0, 4]]

    # Per-class one-vs-rest: class 1 as positive -> TP=4, FP=0, FN=0 -> all 1.0.
    # Class 0 as positive -> TP=4, FP=0, FN=0 -> all 1.0.
    # macro = (1+1)/2 = 1.0; weighted = (4/8)*1 + (4/8)*1 = 1.0
    pc = per_class_metrics(CASE_B_TRUE, y_pred)
    for name in ("no", "yes"):
        for key in ("precision", "recall", "f1"):
            assert pc[name][key] == pytest.approx(1.0, **APPROX), (name, key)
    for avg in ("macro", "weighted"):
        for key in ("precision", "recall", "f1"):
            assert pc[avg][key] == pytest.approx(1.0, **APPROX), (avg, key)


def test_case_b_brier_and_ece():
    # Brier = (1/8) * sum((p_i - y_i)^2):
    #   positives: (0.1)^2+(0.2)^2+(0.3)^2+(0.4)^2 = 0.01+0.04+0.09+0.16 = 0.30
    #   negatives: (0.4)^2+(0.3)^2+(0.2)^2+(0.1)^2 = 0.16+0.09+0.04+0.01 = 0.30
    # sum = 0.60 -> 0.60 / 8 = 0.075
    assert compute_brier(CASE_B_TRUE, CASE_B_SCORE) == pytest.approx(0.075, **APPROX)
    # ECE: bins 9,8,7,6,4,3,2,1 (all distinct, one sample each):
    #   |y-p| per sample: 0.1,0.2,0.3,0.4 (positives); 0.4,0.3,0.2,0.1 (negatives)
    #   sum of gaps = 2.0 -> ECE = 2.0/8 = 0.25
    assert compute_ece(CASE_B_TRUE, CASE_B_SCORE) == pytest.approx(0.25, **APPROX)


# ---------------------------------------------------------------------------
# Case C: zero-division paths (no negative predicted at t=0.5)
# ---------------------------------------------------------------------------

CASE_C_TRUE = [1, 1, 0, 0]
CASE_C_SCORE = [0.9, 0.8, 0.7, 0.6]


def test_case_c_zero_division_binary():
    # Derivation at t=0.5: y_pred = [1,1,1,1].
    # (1,1)TP (1,1)TP (0,1)FP (0,1)FP  =>  TP=2, FP=2, FN=0, TN=0; N=4.
    y_pred = [1 if p >= 0.5 else 0 for p in CASE_C_SCORE]
    m = binary_metrics(CASE_C_TRUE, y_pred)
    # accuracy  = (2+0)/4 = 0.5
    assert m["accuracy"] == pytest.approx(0.5, **APPROX)
    # precision = 2/(2+2) = 0.5
    assert m["precision"] == pytest.approx(0.5, **APPROX)
    # recall    = 2/(2+0) = 1.0
    assert m["recall"] == pytest.approx(1.0, **APPROX)
    # specificity = TN/(TN+FP) = 0/(0+2) -> zero-division -> 0.0
    assert m["specificity"] == pytest.approx(0.0, **APPROX_ABS)
    # F1 = 2*0.5*1.0/(0.5+1.0) = 1.0/1.5 = 2/3
    assert m["f1"] == pytest.approx(2.0 / 3.0, **APPROX)
    # balanced = (1.0 + 0.0)/2 = 0.5
    assert m["balanced_accuracy"] == pytest.approx(0.5, **APPROX)
    assert confusion_matrix(CASE_C_TRUE, y_pred) == [[0, 2], [0, 2]]


def test_case_c_zero_division_per_class():
    # y_pred = [1,1,1,1].
    # Class 1 ("yes") as positive: TP=2, FP=2, FN=0, support=2 ->
    #   precision 0.5, recall 1.0, F1 2/3.
    # Class 0 ("no") as positive: TP=0, FP=0, FN=2, support=2 ->
    #   precision 0/(0+0) -> zero-division -> 0.0; recall 0/(0+2) = 0.0;
    #   F1 2*0*0/(0+0) -> zero-division -> 0.0.
    # macro precision = (0.5+0.0)/2 = 0.25; macro recall = (1.0+0.0)/2 = 0.5;
    # macro F1 = (2/3 + 0)/2 = 1/3.
    # weighted (equal supports, 2/4 each) = same as macro.
    y_pred = [1 if p >= 0.5 else 0 for p in CASE_C_SCORE]
    pc = per_class_metrics(CASE_C_TRUE, y_pred)
    assert pc["no"]["precision"] == pytest.approx(0.0, **APPROX_ABS)
    assert pc["no"]["recall"] == pytest.approx(0.0, **APPROX)
    assert pc["no"]["f1"] == pytest.approx(0.0, **APPROX_ABS)
    assert pc["no"]["support"] == 2
    assert pc["yes"]["precision"] == pytest.approx(0.5, **APPROX)
    assert pc["yes"]["recall"] == pytest.approx(1.0, **APPROX)
    assert pc["yes"]["f1"] == pytest.approx(2.0 / 3.0, **APPROX)
    assert pc["macro"]["precision"] == pytest.approx(0.25, **APPROX)
    assert pc["macro"]["recall"] == pytest.approx(0.5, **APPROX)
    assert pc["macro"]["f1"] == pytest.approx(1.0 / 3.0, **APPROX)
    assert pc["weighted"]["precision"] == pytest.approx(0.25, **APPROX)
    assert pc["weighted"]["recall"] == pytest.approx(0.5, **APPROX)
    assert pc["weighted"]["f1"] == pytest.approx(1.0 / 3.0, **APPROX)


# ---------------------------------------------------------------------------
# Case D: ECE edge cases (p = 1.0 in last bin, small probabilities)
# ---------------------------------------------------------------------------

def test_case_d_ece_and_brier_edges():
    y_true = [1, 0, 0, 1]
    y_score = [1.0, 0.95, 0.05, 0.15]
    # Bins: 1.0 -> min(int(10), 9) = 9; 0.95 -> int(9.5) = 9;
    #       0.05 -> int(0.5) = 0; 0.15 -> int(1.5) = 1.
    # Bin 9: n=2, conf=(1.0+0.95)/2=0.975, acc=(1+0)/2=0.5, gap=0.475, w=2/4
    # Bin 0: n=1, conf=0.05, acc=0, gap=0.05,  w=1/4
    # Bin 1: n=1, conf=0.15, acc=1, gap=0.85,  w=1/4
    # ECE = 0.5*0.475 + 0.25*0.05 + 0.25*0.85
    #     = 0.2375 + 0.0125 + 0.2125 = 0.4625
    assert compute_ece(y_true, y_score) == pytest.approx(0.4625, **APPROX)
    # Brier = (1/4) * [ (1-1)^2 + (0-0.95)^2 + (0-0.05)^2 + (1-0.15)^2 ]
    #       = (0 + 0.9025 + 0.0025 + 0.7225) / 4 = 1.6275 / 4 = 0.406875
    assert compute_brier(y_true, y_score) == pytest.approx(0.406875, **APPROX)


def test_bin_probabilities_p_one_lands_in_bin_nine():
    # Normative rule: bin index = min(int(p*10), 9), so p = 1.0 -> bin 9
    # (int(1.0*10) = 10 would overflow; the min() clamps it).
    assert bin_probabilities([1.0]).tolist() == [9]
    # And for the full Case D vector: 1.0->9, 0.95->9, 0.05->0, 0.15->1.
    assert bin_probabilities([1.0, 0.95, 0.05, 0.15]).tolist() == [9, 9, 0, 1]
    assert bin_probabilities(np.array([1.0, 0.95, 0.05, 0.15])).tolist() == [9, 9, 0, 1]


# ---------------------------------------------------------------------------
# Threshold override: Case A at t = 0.65
# ---------------------------------------------------------------------------

def test_case_a_threshold_override_t_065():
    # Derivation at t=0.65: y_pred = p>=0.65 -> [1,1,1,0,0,0,0,0]
    # (0.7 >= 0.65 stays positive; 0.6 < 0.65 flips to negative).
    # (1,1)TP (1,1)TP (1,1)TP (1,0)FN (0,0)TN (0,0)TN (0,0)TN (0,0)TN
    # => TP=3, FN=1, TN=4, FP=0; N=8.
    y_pred = _case_a_pred(0.65)
    m = binary_metrics(CASE_A_TRUE, y_pred)
    # accuracy  = (3+4)/8 = 0.875
    assert m["accuracy"] == pytest.approx(0.875, **APPROX)
    # precision = 3/(3+0) = 1.0
    assert m["precision"] == pytest.approx(1.0, **APPROX)
    # recall    = 3/(3+1) = 0.75
    assert m["recall"] == pytest.approx(0.75, **APPROX)
    # specificity = 4/(4+0) = 1.0
    assert m["specificity"] == pytest.approx(1.0, **APPROX)
    # F1 = 2*1.0*0.75/(1.0+0.75) = 1.5/1.75 = 6/7
    assert m["f1"] == pytest.approx(6.0 / 7.0, **APPROX)
    # balanced = (0.75 + 1.0)/2 = 0.875
    assert m["balanced_accuracy"] == pytest.approx(0.875, **APPROX)
    # Confusion [[TN,FP],[FN,TP]] = [[4,0],[1,3]]
    assert confusion_matrix(CASE_A_TRUE, y_pred) == [[4, 0], [1, 3]]


# ---------------------------------------------------------------------------
# Case 7: confidence analysis, everything wrong
# ---------------------------------------------------------------------------

def test_case_7_confidence_analysis_all_incorrect():
    y_true = [1, 0, 1, 0]
    y_score = [0.05, 0.95, 0.45, 0.55]
    y_pred = [1 if p >= 0.5 else 0 for p in y_score]  # -> [0,1,0,1]
    # Every prediction disagrees with its label: all 4 incorrect.
    # Confidence = max(p, 1-p) = [0.95, 0.95, 0.55, 0.55].
    # mean incorrect confidence = (0.95+0.95+0.55+0.55)/4 = 3.0/4 = 0.75
    # high-confidence errors: incorrect AND confidence >= 0.9 -> 0.95, 0.95 -> 2
    # uncertain: 0.4 <= p <= 0.6 (inclusive) -> p=0.45 and p=0.55 -> 2
    result = confidence_analysis(y_true, y_score, y_pred)
    assert result["incorrect_count"] == 4
    assert result["incorrect_mean_confidence"] == pytest.approx(0.75, **APPROX)
    assert result["correct_count"] == 0
    # Empty correct group -> count 0, mean 0.0
    assert result["correct_mean_confidence"] == pytest.approx(0.0, **APPROX_ABS)
    assert result["high_confidence_errors"] == 2
    assert result["uncertain_count"] == 2


# ---------------------------------------------------------------------------
# Orientation lock: exact [[TN,FP],[FN,TP]] slot assignment
# ---------------------------------------------------------------------------

def test_confusion_orientation_locked_with_named_variables():
    # Named-variable case with all four cells distinct and asymmetric.
    # y_true/y_pred pair up as:
    #   i0 (1,1) -> tp   i1 (1,0) -> fn   i2 (1,0) -> fn
    #   i3 (0,1) -> fp   i4 (0,1) -> fp   i5 (0,1) -> fp
    #   i6..i9 (0,0)    -> tn x4
    tp, fp, fn, tn = 1, 3, 2, 4
    y_true = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    y_pred = [1, 0, 0, 1, 1, 1, 0, 0, 0, 0]
    assert confusion_counts(y_true, y_pred) == (tn, fp, fn, tp)
    matrix = confusion_matrix(y_true, y_pred)
    # Normative layout: rows = true, cols = predicted -> [[TN,FP],[FN,TP]].
    assert matrix == [[tn, fp], [fn, tp]]
    assert matrix == [[4, 3], [2, 1]]
    # The transposed (column= true) interpretation must NOT match, locking the
    # orientation against silent swaps.
    assert matrix != [[tn, fn], [fp, tp]]


# ---------------------------------------------------------------------------
# CSV round-trip through the evaluator's own writer
# ---------------------------------------------------------------------------

def test_predictions_csv_round_trip(tmp_path):
    rows = [
        {"path": "demo_data/yes/a.jpg", "true_label": 1, "probability": 0.912345,
         "predicted_label": 1, "correct": True},
        {"path": "demo_data/no/b.jpeg", "true_label": 0, "probability": 0.4,
         "predicted_label": 0, "correct": True},
        {"path": "demo_data/yes/c.png", "true_label": 1, "probability": 0.25,
         "predicted_label": 0, "correct": False},
    ]
    out = tmp_path / "predictions.csv"
    write_predictions_csv(str(out), rows)

    with open(out, newline="", encoding="utf-8") as fh:
        read_back = list(csv.DictReader(fh))

    # Writer contract: header path,true_label,probability,predicted_label,correct;
    # probability fixed to 6 decimals; correct serialized as "true"/"false".
    assert list(read_back[0].keys()) == [
        "path", "true_label", "probability", "predicted_label", "correct"
    ]
    expected = [
        {"path": "demo_data/yes/a.jpg", "true_label": "1", "probability": "0.912345",
         "predicted_label": "1", "correct": "true"},
        {"path": "demo_data/no/b.jpeg", "true_label": "0", "probability": "0.400000",
         "predicted_label": "0", "correct": "true"},
        {"path": "demo_data/yes/c.png", "true_label": "1", "probability": "0.250000",
         "predicted_label": "0", "correct": "false"},
    ]
    assert read_back == expected


# ---------------------------------------------------------------------------
# sklearn cross-check (sanity, independent implementation)
# ---------------------------------------------------------------------------

def test_sklearn_cross_check():
    cases = [
        # (y_true, y_pred, y_score)
        (CASE_A_TRUE, _case_a_pred(0.5), CASE_A_SCORE),
        (CASE_C_TRUE, [1, 1, 1, 1], CASE_C_SCORE),
    ]
    for y_true, y_pred, y_score in cases:
        m = binary_metrics(y_true, y_pred)
        assert m["accuracy"] == pytest.approx(accuracy_score(y_true, y_pred), **APPROX)
        assert m["precision"] == pytest.approx(
            precision_score(y_true, y_pred, zero_division=0), **APPROX)
        assert m["recall"] == pytest.approx(
            recall_score(y_true, y_pred, zero_division=0), **APPROX)
        assert m["f1"] == pytest.approx(
            f1_score(y_true, y_pred, zero_division=0), **APPROX)
        assert m["balanced_accuracy"] == pytest.approx(
            balanced_accuracy_score(y_true, y_pred), **APPROX)
        assert compute_brier(y_true, y_score) == pytest.approx(
            brier_score_loss(y_true, y_score), **APPROX)
        # sklearn labels=[0,1] also uses rows=true, cols=predicted.
        assert confusion_matrix(y_true, y_pred) == sklearn_confusion_matrix(
            y_true, y_pred, labels=[0, 1]
        ).tolist()


def test_reliability_bins_matches_ece_and_covers_all_bins():
    # reliability_bins must expose the same per-bin quantities compute_ece uses.
    y_true = CASE_A_TRUE
    y_score = CASE_A_SCORE
    bins = reliability_bins(y_true, y_score)
    assert [b["bin_index"] for b in bins] == list(range(10))
    n = len(y_true)
    ece_from_bins = sum(
        b["weight"] * abs(b["fraction_positive"] - b["mean_confidence"]) for b in bins
    )
    assert ece_from_bins == pytest.approx(compute_ece(y_true, y_score), **APPROX)
    assert sum(b["count"] for b in bins) == n
    assert sum(b["weight"] for b in bins) == pytest.approx(1.0, **APPROX)
    # Case A fills 8 distinct bins; bins 0 and 5 stay empty with zero weight.
    non_empty = [b for b in bins if b["count"] > 0]
    assert len(non_empty) == 8
    for b in bins:
        if b["count"] == 0:
            assert b["weight"] == pytest.approx(0.0, **APPROX_ABS)
            assert b["mean_confidence"] == pytest.approx(0.0, **APPROX_ABS)
            assert b["fraction_positive"] == pytest.approx(0.0, **APPROX_ABS)
