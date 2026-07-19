"""Evaluation metrics.

For phishing detection, accuracy alone is misleading (classes are often
imbalanced and the costs are asymmetric). We report precision, recall, F1, and
ROC-AUC together: recall is "what fraction of phish did we catch", precision is
"when we cry phish, how often are we right", and ROC-AUC is threshold-independent
ranking quality — the fairest single number for comparing models.
"""

from __future__ import annotations

from collections.abc import Sequence

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)


def compute_metrics(
    y_true: Sequence[int], y_prob: Sequence[float], threshold: float = 0.5
) -> dict:
    y_pred = [1 if p >= threshold else 0 for p in y_prob]
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except ValueError:  # only one class present in y_true
        auc = float("nan")
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(auc, 4),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "threshold": threshold,
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "support": len(y_true),
    }
