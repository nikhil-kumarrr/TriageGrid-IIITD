# TriageGrid

A responsive care-navigation prototype for the CareCompass challenge. The supplied Stitch blue-theme design is implemented with React/TypeScript, local fonts, Lucide icons, a colourful care-kit illustration and a shared scalable care-and-navigation brand identity. Python FastAPI serves the actual trained model and supplied caregiver roster. Streamlit is not used by the new app.

## Implemented journeys

- Home, source dataset examples, text intake, microphone input with browser consent explanation, editable transcripts and request review.
- Language-specific clinical questions and main interface controls (English/Hindi/Hinglish), read-aloud, larger text and reduced motion. Source dataset fields and some detailed explanations remain English.
- Stateless conversation history, lexical safety checks, trained care/urgency pipelines and emergency matching bypass.
- Roster eligibility, factual reasons, detail cards, language filter and time-slot selection.
- Persistent prototype reservations, idempotency, transactional slot conflicts, session-owned booking lists and cancellation.
- Consent-gated Golden Bay handover, simulated receiver and explicit manual acknowledgement.
- Real TinyFish official-site extraction, background status, bounded timeout, labelled public-result cache and failure handling. No patient information is sent to TinyFish.
- Help, mentor model metrics, data-source documentation, strict API contracts, CSV prediction script and source regression tests.

Bookings and hospital handovers do not arrange real appointments, dispatch or hospital acceptance. Only provided synthetic data is permitted. This is not clinical advice or a production medical service. Admin portal is a separate later phase.

## Run locally

Python 3.12+ and Node 20+. From this project folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
.venv/bin/python scripts/train_models.py
PYTHONPATH=backend .venv/bin/python -m uvicorn triagegrid.main:app --host 127.0.0.1 --port 8000
```

Second terminal:

```sh
cd frontend
npm ci
npm run dev -- --port 5173
```

Open http://127.0.0.1:5173. Frontend `/api` requests are proxied to the Python service. API docs: http://127.0.0.1:8000/docs. Restart the development server if exported files or dependency changes are not reflected.

## Configuration

Copy `.env.example` to `.env` if missing. The backend loads `.env` at startup. Set `TINYFISH_API_KEY` only there; restart the backend after configuration changes. Never use a frontend `VITE_` variable for secrets. `.env` and local runtime state are ignored by Git/Docker build context.

The provided local key has not been copied into UI code, datasets, reports or examples. Do not share `.env`, `.venv` or `var/` when sharing the project.

## Tests and training

```sh
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q
.venv/bin/python scripts/audit_data.py
cd frontend
npm run build
```

Explicit training saves both complete TF-IDF pipelines to `models/baseline/`. No automatic startup retraining. Only load these trusted locally trained artifacts. `notebooks/triagegrid_training.ipynb` reproduces source inspection and training.

```sh
.venv/bin/python scripts/make_predictions_csv.py input.csv predictions.csv
```

The CSV script and API call the same `predict()` function. CSV input needs `user_input`; optional `id`, `lat`, `lng` are supported. Confirm final scorer column requirements with organizers. Do not use hidden-test labels for tuning.

## Data and architecture

- `data/provided/`: unchanged source data plus checksums.
- `models/baseline/`: trained artifacts and grouped model-selection results.
- `backend/triagegrid/`: inference, matching, schemas, session-owned persistence, booking and hospital services.
- `frontend/src/`: responsive UI and interactions.
- `docs/DATA_USAGE.md`: exact use of every file and scheduling assumptions.
- `reports/`: evaluation scope and live integration evidence, excluding credentials.
- Original Stitch exports and `triage_app/triage_app/`: preserved references. The old Streamlit app is not part of the new runtime.

## Deployment

`docker compose up --build` builds Python + Nginx frontend, proxies `/api` and persists SQLite through a named volume. Local ports are bound to loopback. Docker execution is not yet verified on this machine because Docker is unavailable.

This build is intended for local synthetic-data demonstration with one API worker. Before public multi-user deployment, add proper authentication/receiver roles, HTTPS, durable background jobs, data retention automation and infrastructure-level rate limits. Session tokens isolate local prototype records, but are not a substitute for production identity and access management. SQLite is not a clinical scheduling system.

## Evaluation and limitations

44 automated tests currently cover contracts, safety examples, supplied multi-turn conversations, data parity, booking ownership, cancellation, concurrent slot conflicts, handover consent and mocked TinyFish outcomes. Use the latest test output as authoritative if the suite changes.

Baseline grouped model-selection macro-F1: care type 0.6466; urgency 0.6116. These are not independent clinical validation. Lexical rules have limited language/context coverage. Some source emergency annotations are inconsistent. A successful TinyFish run returned published AIIMS information; that is not verification of bed status or real-time emergency capacity. Speech depends on browser/platform and may use remote recognition. Audio is not stored by this app.

Same-day care is restricted to today (IST); it cannot be postponed through the slot picker or API. The seven-day planning horizon applies to scheduled care only.
