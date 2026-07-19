"""Training pipeline: data -> features -> compare models -> save the winner.

Model input = TF-IDF(text)  hstacked with  scaled numeric FeatureVector. We train
two calibrated classifiers and keep the better by ROC-AUC:

  * Logistic Regression — the interpretable linear baseline. Fast, and its
    coefficients are readable; if a fancier model can't beat it, we don't ship
    complexity we can't justify.
  * LightGBM — gradient-boosted trees. Handles the mixed sparse-text / dense-
    numeric space and non-linear interactions well, and trains quickly.

Both are wrapped in CalibratedClassifierCV so `predict_proba` returns a
*calibrated* probability — essential because M4 fuses this number with the rule
and (later) LLM scores, and a miscalibrated 0.9 would distort the blend.

The saved artifact holds only standard sklearn/scipy objects (vectorizer, scaler,
classifier) — no custom classes — so the backend can load it at serving time with
just sklearn installed, without importing this training package.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import joblib
import scipy.sparse as sp
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from catchy_ml import config
from catchy_ml.dataset import load_dataset
from catchy_ml.evaluate import compute_metrics
from catchy_ml.featurize import FEATURE_NAMES, build_matrices


def _build_X(tfidf, scaler, texts, numeric, *, fit: bool):
    if fit:
        text_mat = tfidf.fit_transform(texts)
        num_mat = scaler.fit_transform(numeric)
    else:
        text_mat = tfidf.transform(texts)
        num_mat = scaler.transform(numeric)
    return sp.hstack([text_mat, sp.csr_matrix(num_mat)]).tocsr()


def _make_models(seed: int) -> dict:
    return {
        "logistic_regression": CalibratedClassifierCV(
            LogisticRegression(max_iter=1000, class_weight="balanced"),
            method="sigmoid",
            cv=3,
        ),
        "lightgbm": CalibratedClassifierCV(
            LGBMClassifier(
                n_estimators=200,
                learning_rate=0.05,
                num_leaves=31,
                class_weight="balanced",
                random_state=seed,
                verbosity=-1,
            ),
            method="sigmoid",
            cv=3,
        ),
    }


def train_and_save(
    samples: list[tuple[str, int]],
    *,
    model_path=config.MODEL_PATH,
    metrics_path=config.METRICS_PATH,
    seed: int = config.RANDOM_SEED,
    threshold: float = config.DEFAULT_THRESHOLD,
) -> dict:
    raws = [s[0] for s in samples]
    labels = [s[1] for s in samples]

    raw_tr, raw_te, y_tr, y_te = train_test_split(
        raws, labels, test_size=config.TEST_SIZE, stratify=labels, random_state=seed
    )

    tr_texts, tr_num = build_matrices(raw_tr)
    te_texts, te_num = build_matrices(raw_te)

    tfidf = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=2,
        max_features=5000,
        sublinear_tf=True,
        strip_accents="unicode",
    )
    scaler = StandardScaler()
    X_tr = _build_X(tfidf, scaler, tr_texts, tr_num, fit=True)
    X_te = _build_X(tfidf, scaler, te_texts, te_num, fit=False)

    fitted: dict = {}
    results: dict = {}
    for name, model in _make_models(seed).items():
        model.fit(X_tr, y_tr)
        prob = model.predict_proba(X_te)[:, 1]
        fitted[name] = model
        results[name] = compute_metrics(y_te, prob, threshold)

    chosen = max(results, key=lambda k: results[k]["roc_auc"])

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "tfidf": tfidf,
            "scaler": scaler,
            "classifier": fitted[chosen],
            "feature_names": FEATURE_NAMES,
            "model_type": chosen,
            "threshold": threshold,
            "trained_at": datetime.now(UTC).isoformat(),
        },
        model_path,
    )

    report = {
        "chosen": chosen,
        "threshold": threshold,
        "n_train": len(y_tr),
        "n_test": len(y_te),
        "n_features_text": len(tfidf.vocabulary_),
        "n_features_numeric": len(FEATURE_NAMES),
        "models": results,
        "trained_at": datetime.now(UTC).isoformat(),
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    samples = load_dataset(csv_path=config.DATA_DIR / "emails.csv")
    report = train_and_save(samples)
    chosen = report["chosen"]
    print(f"Trained on {report['n_train']} / tested on {report['n_test']} emails")
    print(f"Chosen model: {chosen}")
    for name, res in report["models"].items():
        mark = " *" if name == chosen else "  "
        print(
            f"{mark} {name:20} "
            f"P={res['precision']:.3f} R={res['recall']:.3f} "
            f"F1={res['f1']:.3f} AUC={res['roc_auc']:.3f}"
        )
    print(f"Saved model -> {config.MODEL_PATH}")
    print(f"Saved metrics -> {config.METRICS_PATH}")


if __name__ == "__main__":
    main()
