# Care Triage & Caregiver Matching

Free-text request (English / हिंदी / Hinglish) → **triage** → **rule-based caregiver matching**, served through a Streamlit app (plus an optional REST API).

```
user text ──► triage.triage()  ──► care_type · urgency · red_flags · follow-up question
               ├─ safety rules (red flags → 112)
               └─ TF-IDF + Logistic Regression  (artifacts/*.pkl)
                         │  only if care_type is matchable
lat/lng/time ─────────► matcher.match_caregivers()  ──► ranked top-K caregivers
                         └─ rules over data/caregivers.csv  (no ML)
```

The `.pkl` files contain **only** the two sklearn pipelines. Matching is plain rules over the caregiver CSV; the two are connected in `app/streamlit_app.py` (and `api/main.py`).

## Layout

```
app/streamlit_app.py        Streamlit UI (Triage & Match · Caregivers · Model info)
api/main.py                 optional FastAPI wrapper over the same package
src/triage_matching/
    config.py               paths & constants (env-overridable)
    model.py                pipeline definition + load_models() (auto-retrain on missing/mismatched pkl)
    train.py                CLI: group-wise CV → tune C & threshold → save .pkl + metrics
    triage.py               inference: red-flag rules + model + follow-up/emergency messages
    matcher.py              hard filters + weighted ranking
artifacts/                  care_type_pipeline.pkl · urgency_pipeline.pkl · model_meta.json · confusion_matrix.png
data/                       triage_dataset_flat.csv · caregivers.csv
tests/                      27 tests (triage, matcher, Streamlit flows)
notebooks/                  exploratory end-to-end notebook
```

## Quick start

```bash
pip install -r requirements.txt
make train        # builds artifacts/*.pkl   (python -m triage_matching.train)
make test         # pytest
make app          # streamlit run app/streamlit_app.py  → http://localhost:8501
make api          # optional: uvicorn api.main:app → http://localhost:8000/docs
```
(`make` just sets `PYTHONPATH=src`; without make: `PYTHONPATH=src python -m triage_matching.train`.)

## How the `.pkl` is built, saved, and used

```python
# train.py (essence)
pipe = Pipeline([("tfidf", FeatureUnion([word_tfidf, char_tfidf])), ("clf", LogisticRegression(...))])
pipe.fit(texts, labels)
joblib.dump(pipe, "artifacts/care_type_pipeline.pkl", compress=3)

# anywhere else (inference)
pipe = joblib.load("artifacts/care_type_pipeline.pkl")
pipe.predict_proba(["papa ko insulin injection chahiye ghar pe"])
```

* Only built-in sklearn objects are used (no lambdas / custom classes), so the pickle loads in any process with the **same sklearn version** (pinned in `requirements.txt`, recorded in `model_meta.json`).
* **Deploy-safe:** `load_models()` retrains automatically if the pickles are missing or were built with a different sklearn version, so a version bump never crashes the app.
* Only load pickles you trained yourself.

## Matching rules (`matcher.py`)

| Stage | Rule |
|---|---|
| Role | teleconsultation → doctor · home_nursing / paramedic_home_visit → medic · lab_test_home → phlebotomist |
| Skill | injection → `injection_im` (IV/drip → `injection_iv`) · dressing/bedsore/post-op → `wound_dressing` · paramedic → `vitals_monitoring` · lab → `sample_collection` |
| Active / radius | `active == True`; home visits need haversine distance ≤ `max_radius_km` (teleconsult ignores radius) |
| Time (optional) | `free_from ≤ request_time ≤ free_until` |
| Score 0–1 | proximity .35 · rating .25 · experience .10 · preferred skills .10 · language .10 · tier .10 (medics) · gender pref .05 |

Validated against the reference dataset: every reference match is eligible under these filters, and "no match" rows agree 100%. Ranking weights are a design choice (the dataset does not define the formula).

## Deploy

**Streamlit Community Cloud** — push this repo to GitHub (commit `artifacts/` and `data/`), then New app → main file `app/streamlit_app.py`. No other config needed.

**Docker**
```bash
docker build -t care-triage .      # re-trains inside the image → pkl matches the image's sklearn
docker run -p 8501:8501 care-triage
```

**Config via env vars:** `TRIAGE_DATA_DIR`, `TRIAGE_ARTIFACT_DIR`, `CAREGIVERS_CSV`.

## Known limitations

* Only ~65 unique training sentences. Honest group-wise CV: **~71% accuracy / 0.65 macro-F1** (random split shows ~99% because of leakage). Weak spots: `needs_clarification` recall and `paramedic_home_visit` precision. Retrain on real logs (`make train`) — the biggest upgrade available.
* Safety nets: red-flag regexes (100% recall on dataset emergencies, 0 false alarms), emergency escalation at p ≥ 0.30, low-confidence → follow-up question. Keyword list needs clinical review before production use. **Decision-support only — not medical advice.**
* Red flags deliberately over-trigger on words like "bleeding".
* Availability is a same-day time-window check only (no booking calendar / conflicts).
