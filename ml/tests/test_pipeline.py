"""End-to-end training test on a small synthetic set.

Keeps the whole pipeline honest: data generation -> featurization (via the real
backend extractor) -> train two calibrated models -> evaluate -> save a loadable
artifact. Runs offline in a few seconds.
"""

from __future__ import annotations

import joblib

from catchy_ml.dataset import generate
from catchy_ml.featurize import FEATURE_NAMES, email_to_row
from catchy_ml.train import train_and_save


def test_featurization_reuses_backend_extractor() -> None:
    # A phishing-shaped email should light up structural features.
    text, numeric = email_to_row(generate(n=2, seed=1)[0][0])
    assert len(numeric) == len(FEATURE_NAMES)
    assert isinstance(text, str)


def test_train_saves_loadable_calibrated_model(tmp_path) -> None:
    model_path = tmp_path / "model.joblib"
    metrics_path = tmp_path / "metrics.json"
    samples = generate(n=200, seed=42)

    report = train_and_save(
        samples, model_path=model_path, metrics_path=metrics_path, seed=42
    )

    # Both models were evaluated and a winner chosen.
    assert set(report["models"]) == {"logistic_regression", "lightgbm"}
    assert report["chosen"] in report["models"]

    # On this clearly-separable synthetic data the model should be strong.
    best = report["models"][report["chosen"]]
    assert best["roc_auc"] >= 0.9
    assert best["recall"] >= 0.8

    # Artifact is self-contained and produces calibrated probabilities.
    bundle = joblib.load(model_path)
    assert set(bundle) >= {"tfidf", "scaler", "classifier", "feature_names", "model_type"}
    assert bundle["feature_names"] == FEATURE_NAMES
    assert metrics_path.exists()


def test_saved_model_scores_phish_above_legit(tmp_path) -> None:
    import scipy.sparse as sp

    from catchy_ml.dataset import _make_legit, _make_phish
    from catchy_ml.featurize import build_matrices

    model_path = tmp_path / "model.joblib"
    train_and_save(
        generate(n=200, seed=7),
        model_path=model_path,
        metrics_path=tmp_path / "m.json",
        seed=7,
    )
    bundle = joblib.load(model_path)

    import random

    rng = random.Random(0)
    phish_texts, phish_num = build_matrices([_make_phish(rng) for _ in range(10)])
    legit_texts, legit_num = build_matrices([_make_legit(rng) for _ in range(10)])

    def proba(texts, num):
        X = sp.hstack(
            [bundle["tfidf"].transform(texts), sp.csr_matrix(bundle["scaler"].transform(num))]
        ).tocsr()
        return bundle["classifier"].predict_proba(X)[:, 1].mean()

    # Mean phishing probability must clearly exceed mean legit probability.
    assert proba(phish_texts, phish_num) > proba(legit_texts, legit_num) + 0.3
