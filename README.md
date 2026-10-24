# TriageGrid

A responsive care-navigation prototype for the CareCompass challenge. The supplied Stitch blue-theme design is implemented with React/TypeScript, local fonts, Lucide icons, a colourful care-kit illustration and a shared scalable care-and-navigation brand identity. Python FastAPI serves the actual trained model and supplied caregiver roster. Streamlit is not used by the new app.

## Implemented journeys

- Home, source dataset examples, text intake, microphone input with browser consent explanation, editable transcripts and request review.
- Multilingual AI Care Assistant (English, Hindi, Hinglish) integrated directly into app navigation (`Home` | `AI Assistant` | `New Request` | `Bookings`).
- Purposeful conversational intake: safety red-flag scanning, extracted structured facts, clarification without repeated questions, expandable "What I understood" fact summaries, and user corrections.
- Integrated decision engine: conversation seamlessly hands off to the validated triage engine (`care_type`, `urgency_level`) and existing caregiver matching/booking without downgrading emergency classifications.
- Server-side interchangeable LLM adapters (Google Gemini, xAI Grok, and automated test mock) with strict error handling, bounded retries, and honest "Assistant not configured" state when credentials are not supplied.
- Structured session memory interface with local SQLite persistence and AWS DynamoDB evaluation (`docs/AWS_MEMORY_EVALUATION.md`).
- Language-specific clinical questions and main interface controls (English/Hindi/Hinglish), read-aloud, larger text and reduced motion. Source dataset fields and some detailed explanations remain English.
- Stateless conversation history, lexical safety checks, trained care/urgency pipelines and emergency matching bypass.
- Roster eligibility, factual reasons, detail cards, language filter and time-slot selection.
- Persistent prototype reservations, idempotency, transactional slot conflicts, session-owned booking lists and cancellation.
- Consent-gated Golden Bay handover, simulated receiver and explicit manual acknowledgement.
- Real TinyFish official-site extraction, background status, bounded timeout, labelled public-result cache and failure handling. No patient information is sent to TinyFish.
- Help, mentor model metrics, data-source documentation, strict API contracts, CSV prediction script and source regression tests.

Bookings, AI recommendations and hospital handovers do not arrange real appointments, dispatch or hospital acceptance. Only provided synthetic data is permitted. This is not clinical advice, medical diagnosis or a production medical service. The AI assistant does not prescribe drugs or guarantee safety. Admin portal is a separate later phase.

## Run locally

Python 3.10+ and Node 18+. From this project folder:

### Terminal 1: Backend (Python FastAPI)

```sh
# Setup virtual environment and dependencies
python3 -m venv .venv
source .venv/bin/activate  # On Windows (cmd/PowerShell): .venv\Scripts\activate
pip install -r backend/requirements.txt

# Run the backend server (starts on http://127.0.0.1:8000)
python run_backend.py
```
*(Alternative manual command: `PYTHONPATH=backend uvicorn triagegrid.main:app --host 127.0.0.1 --port 8000 --reload`)*

### Terminal 2: Frontend (React / Vite)

```sh
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173** (or http://localhost:5173). Frontend `/api` requests are automatically proxied to the Python backend on port 8000. API docs: http://127.0.0.1:8000/docs.

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

### Relational Schema & Data Flow

```text
       ┌────────────────────────┐                    ┌─────────────────────────┐
       │        PATIENTS        │                    │      CARE_TAXONOMY      │
       ├────────────────────────┤                    ├─────────────────────────┤
       │ PK  patient_id         │                    │ PK  care_type_code      │
       │     full_name          │                    │     display_name        │
       │     phone_number       │                    │     default_urgency     │
       │     lat                │                    │     red_flag_triggers   │
       │     lng                │                    │     min_qualification   │
       │     pref_language      │                    └────────────┬────────────┘
       └───────────┬────────────┘                                 │
                   │ 1                                            │ 1
                   │                                              │
                   │ N                                            │ N
       ┌───────────┴────────────┐                    ┌────────────┴────────────┐
       │    INTAKE_SESSIONS     │ 1                1 │     TRIAGE_RECORDS      │
       ├────────────────────────┼────────────────────┼─────────────────────────┤
       │ PK  session_id         │                    │ PK  triage_id           │
       │ FK  patient_id         │                    │ FK  session_id          │
       │     input_type (v/txt) │                    │ FK  care_type_code      │
       │     raw_utterance      │                    │     urgency (rt/sd/imm) │
       │     symptom_slots      │                    │     is_red_flag (bool)  │
       │     turns_count        │                    │     clinical_reasoning  │
       │     created_at         │                    │     eval_confidence     │
       └────────────────────────┘                    └──────┬────────────┬─────┘
                                                            │ 1          │ 1
                                       ┌────────────────────┘            │
                                       │ 1                               │ N
                                       ▼                                 ▼
       ┌────────────────────────────────────────────────┐   ┌───────────────────────────┐
       │             TINYFISH_AGENT_RUNS                │   │     MATCHING_RECORDS      │
       ├────────────────────────────────────────────────┤   ├───────────────────────────┤
       │ PK  run_id (TinyFish UUID)                     │   │ PK  match_id              │
       │ FK  triage_id                                  │   │ FK  triage_id             │
       │     trigger_type (emergency_er / verification) │   │ FK  caregiver_id          │
       │     target_url (e.g., Delhi ER portal)         │   │     match_score (0.00-1.0)│
       │     streaming_url                              │   │     rank_order            │
       │     agent_status (RUNNING / COMPLETED / FAILED)│   │     distance_km           │
       │     extracted_payload (JSON)                   │   │     justification_reason  │
       │     num_steps                                  │   │     booking_confirmed     │
       └────────────────────────────────────────────────┘   └─────────────▲─────────────┘
                                                                          │ N
                                                                          │
                                                                          │ 1
                                                            ┌─────────────┴─────────────┐
                                                            │        CAREGIVERS         │
                                                            ├───────────────────────────┤
                                                            │ PK  caregiver_id          │
                                                            │     full_name             │
                                                            │     role (paramedic/nurse)│
                                                            │     lat                   │
                                                            │     lng                   │
                                                            │     languages (JSON array)│
                                                            │     rating                │
                                                            │     is_active             │
                                                            └─────────────┬─────────────┘
                                                                          │ 1
                                                                          │
                                                                          │ N
                                                            ┌─────────────┴─────────────┐
                                                            │    AVAILABILITY_SLOTS     │
                                                            ├───────────────────────────┤
                                                            │ PK  slot_id               │
                                                            │ FK  caregiver_id          │
                                                            │     start_time            │
                                                            │     end_time              │
                                                            │     is_booked             │
                                                            └───────────────────────────┘
```

## Deployment

`docker compose up --build` builds Python + Nginx frontend, proxies `/api` and persists SQLite through a named volume. Local ports are bound to loopback. Docker execution is not yet verified on this machine because Docker is unavailable.

This build is intended for local synthetic-data demonstration with one API worker. Before public multi-user deployment, add proper authentication/receiver roles, HTTPS, durable background jobs, data retention automation and infrastructure-level rate limits. Session tokens isolate local prototype records, but are not a substitute for production identity and access management. SQLite is not a clinical scheduling system.

## Evaluation and limitations

52 automated tests currently cover contracts, safety examples, supplied multi-turn conversations, data parity, booking ownership, cancellation, concurrent slot conflicts, handover consent, AI assistant multi-turn facts extraction, multimodal image and prescription OCR analysis, emergency escalation midway, facts correction, session isolation, provider failure recovery, booking handoff, and mocked TinyFish outcomes. Use the latest test output as authoritative if the suite changes.

Baseline grouped model-selection macro-F1: care type 0.6466; urgency 0.6116. These are not independent clinical validation. Lexical rules have limited language/context coverage. Some source emergency annotations are inconsistent. A successful TinyFish run returned published AIIMS information; that is not verification of bed status or real-time emergency capacity. Speech depends on browser/platform and may use remote recognition. Audio is not stored by this app.

Same-day care is restricted to today (IST); it cannot be postponed through the slot picker or API. The seven-day planning horizon applies to scheduled care only.
