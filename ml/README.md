# Catchy ML

Trains the phishing classifier that complements the M2 rule engine. The model's
calibrated probability becomes one weighted input to the fused risk score in M4 —
it never replaces the transparent rules.

## Design

**One extractor, no skew.** Featurization reuses the *production* parser and
`FeatureExtractor` from `backend/` (see `catchy_ml/_backend.py`). The numbers the
model trains on are byte-for-byte the numbers it scores in production.

**Two signals.** Each email becomes:
- **TF-IDF(text)** — subject + visible body, capturing lure wording the fixed
  rule lexicons miss.
- **numeric FeatureVector** — the M2 structural features (link mismatch, IP
  links, auth failures, entropy, urgency, …), scaled.

These are hstacked into one matrix.

**Two models, keep the winner.** A Logistic Regression baseline (interpretable —
if it can't be beaten we don't ship complexity) and LightGBM (non-linear, handles
the mixed sparse/dense space). Both are wrapped in `CalibratedClassifierCV` so
`predict_proba` is *calibrated* — critical because M4 blends this probability with
the rule and LLM scores, and a miscalibrated 0.9 would distort the mix. The higher
ROC-AUC model is saved.

**Portable artifact.** `models/catchy_model.joblib` holds only standard
sklearn/scipy objects (vectorizer, scaler, classifier) — no custom classes — so
the backend loads it at serving time (M4) with just sklearn installed, never
importing this training package.

## Run

```bash
cd ml
pip install -r requirements.txt          # backend/ is imported as a sibling
python -m catchy_ml.train                # -> models/catchy_model.joblib + metrics.json
pytest                                    # end-to-end pipeline test (offline)
```

## Data

`catchy_ml/dataset.load_dataset` prefers `ml/data/emails.csv` (columns
`raw_email,label`; 1 = phish, 0 = legit) and otherwise falls back to a **seeded
synthetic generator** so everything runs with zero downloads.

> ⚠️ **On the metrics:** the bundled synthetic data is *separable by
> construction* (phishing and legit draw from disjoint brand/vocabulary sets), so
> both models score ~1.0. Those numbers validate that the **pipeline works**
> (featurization → calibration → evaluation → a loadable artifact) — they are
> **not** a real-world accuracy claim. For meaningful metrics, drop a real corpus
> into `data/emails.csv` and retrain.

### Public corpora to plug in
- **Nazario phishing corpus** — real phishing emails (raw RFC-822).
- **SpamAssassin public corpus** / **Enron** — legitimate ("ham") mail.
- **Kaggle "Phishing Email Detection"** sets — mixed, already labelled.

Convert each to the `raw_email,label` CSV shape and concatenate. Because
featurization is identical, no code changes are needed — just retrain.
