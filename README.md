# TriageGrid

An intelligent care-navigation and multilingual clinical triage platform built for the CareCompass challenge (IIIT-Delhi). TriageGrid bridges patient health inquiries with validated care categorization, urgency determination, proximity-based caregiver matching, and simulated emergency handover protocols.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Core Capabilities](#core-capabilities)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Machine Learning and Clinical Models](#machine-learning-and-clinical-models)
- [Local Setup and Installation](#local-setup-and-installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup (FastAPI)](#backend-setup-fastapi)
  - [Frontend Setup (React + Vite)](#frontend-setup-react--vite)
  - [Environment Configuration](#environment-configuration)
  - [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Testing and Verification](#testing-and-verification)
- [Clinical Disclaimer and Limitations](#clinical-disclaimer-and-limitations)
- [License](#license)

---

## Overview

TriageGrid addresses frontline healthcare access by transforming free-text patient requests (in English, Hindi, or Hinglish) into structured clinical pathways:
1. **Intake and Clarification:** Patient symptoms are captured through voice or text input, safety red flags are screened, and targeted follow-up clarifications are requested if context is missing.
2. **Clinical Decision Engine:** Machine-learned classification models infer appropriate care types (e.g., home visit, tele-consultation, nurse care) and urgency levels (routine, same-day, immediate emergency).
3. **Caregiver Matching and Slot Allocation:** An algorithm scores and ranks verified caregivers based on medical qualifications, language compatibility, travel distance, and availability windows.
4. **Emergency Escalation:** Red-flag presentations bypass routine scheduling and route directly to an urgent response interface with official hospital intelligence gathered via TinyFish and simulated hospital handovers.

---

## System Architecture

### Data Flow and Relational Schema

```text
       +------------------------+                    +-------------------------+
       |        PATIENTS        |                    |      CARE_TAXONOMY      |
       +------------------------+                    +-------------------------+
       | PK  patient_id         |                    | PK  care_type_code      |
       |     full_name          |                    |     display_name        |
       |     phone_number       |                    |     default_urgency     |
       |     lat                |                    |     red_flag_triggers   |
       |     lng                |                    |     min_qualification   |
       |     pref_language      |                    +------------+------------+
       +-----------+------------+                                 |
                   | 1                                            | 1
                   |                                              |
                   | N                                            | N
       +-----------v------------+                    +------------v------------+
       |    INTAKE_SESSIONS     | 1                1 |     TRIAGE_RECORDS      |
       +------------------------+--------------------+-------------------------+
       | PK  session_id         |                    | PK  triage_id           |
       | FK  patient_id         |                    | FK  session_id          |
       |     input_type (v/txt) |                    | FK  care_type_code      |
       |     raw_utterance      |                    |     urgency (rt/sd/imm) |
       |     symptom_slots      |                    |     is_red_flag (bool)  |
       |     turns_count        |                    |     clinical_reasoning  |
       |     created_at         |                    |     eval_confidence     |
       +------------------------+                    +------+- -----------+-----+
                                                            | 1          | 1
                                        +--------------------+            |
                                        | 1                               | N
                                        v                                 v
       +------------------------------------------------+   +---------------------------+
       |             TINYFISH_AGENT_RUNS                |   |     MATCHING_RECORDS      |
       +------------------------------------------------+   +---------------------------+
       | PK  run_id (TinyFish UUID)                     |   | PK  match_id              |
       | FK  triage_id                                  |   | FK  triage_id             |
       |     trigger_type (emergency_er / verification) |   | FK  caregiver_id          |
       |     target_url (e.g., Delhi ER portal)         |   |     match_score (0.00-1.0)|
       |     streaming_url                              |   |     rank_order            |
       |     agent_status (RUNNING / COMPLETED / FAILED)|   |     distance_km           |
       |     extracted_payload (JSON)                   |   |     justification_reason  |
       |     num_steps                                  |   |     booking_confirmed     |
       +------------------------------------------------+   +-------------^-------------+
                                                                          | N
                                                                          |
                                                                          | 1
                                                            +-------------+-------------+
                                                            |        CAREGIVERS         |
                                                            +---------------------------+
                                                            | PK  caregiver_id          |
                                                            |     full_name             |
                                                            |     role (paramedic/nurse)|
                                                            |     lat                   |
                                                            |     lng                   |
                                                            |     languages (JSON array)|
                                                            |     rating                |
                                                            |     is_active             |
                                                            +-------------+-------------+
                                                                          | 1
                                                                          |
                                                                          | N
                                                            +-------------+-------------+
                                                            |    AVAILABILITY_SLOTS     |
                                                            +---------------------------+
                                                            | PK  slot_id               |
                                                            | FK  caregiver_id          |
                                                            |     start_time            |
                                                            |     end_time              |
                                                            |     is_booked             |
                                                            +---------------------------+
```

---

## Core Capabilities

- **Multilingual Patient Intake:** Native support for English, Hindi, and Hinglish. Supports text typing and in-browser speech recognition with real-time audio transcript editing.
- **Conversational AI Assistant:** Stateful clinical assistant capable of tracking extracted facts, clarifying ambiguities without repetitive prompting, and preserving emergency flags across conversation turns.
- **Pluggable LLM Adapters:** Unified backend interface with interchangeable adapters for Google Gemini, xAI Grok, and a zero-dependency deterministic Mock adapter for local testing and CI environments.
- **Deterministic Red-Flag Safeguards:** Lexical and semantic validation rules scan for acute medical emergencies (chest pain, severe dyspnea, acute stroke indicators) and bypass non-urgent booking flows.
- **Multi-Factor Caregiver Matching:** Evaluates qualification constraints, geographical radius via Haversine calculation, active availability slots, spoken languages, and historical ratings.
- **Transactional Booking Protection:** Atomic SQLite transactions enforce slot idempotency and prevent double-booking across concurrent client sessions.
- **External Web Intelligence (TinyFish):** Web agent integration searches authorized public portals (e.g., AIIMS emergency departments) for published contact numbers, addresses, and operational notices without transmitting patient data.
- **Golden Bay Simulated Receiver:** Preview screen simulating hospital triage dashboard receiving structured patient handovers with explicit consent controls.
- **Session-Based Authentication:** Clean user authentication layer with registration, login, mock OTP verification, and isolated session contexts.

---

## Technology Stack

### Backend
- **Framework:** Python 3.10+, FastAPI, Uvicorn
- **Data Validation & Settings:** Pydantic v2, Pydantic-Settings
- **Machine Learning:** scikit-learn, joblib, numpy, pandas
- **Database:** SQLite with WAL mode and ACID transaction isolation; evaluated for AWS DynamoDB session storage
- **HTTP Client:** httpx (async requests with timeouts and bounded retries)

### Frontend
- **Framework:** React 19, TypeScript
- **Build Tool:** Vite 6
- **Styling:** Vanilla CSS with custom design system (custom tokens, responsive grid, light/blue clinical theme)
- **Icons & Typography:** Lucide React, Fontsource (Inter, Plus Jakarta Sans)

---

## Repository Structure

```text
TriageGrid-IIITD/
├── backend/
│   ├── Dockerfile                   # Backend container specification
│   ├── requirements.txt             # Production Python dependencies
│   ├── requirements-dev.txt         # Development and testing tools
│   ├── tests/                       # Pytest test suite (52 test cases)
│   └── triagegrid/
│       ├── main.py                  # FastAPI application entrypoint
│       ├── routes.py                # REST API endpoints
│       ├── schemas.py               # Pydantic request and response models
│       ├── storage.py               # SQLite persistence and database migrations
│       └── services/
│           ├── auth.py              # Authentication and credential validation
│           ├── matching.py          # Caregiver scoring and slot allocation
│           ├── safety.py            # Clinical red-flag lexical detectors
│           ├── tinyfish.py          # External hospital intelligence client
│           ├── triage.py            # ML pipeline inference orchestrator
│           ├── llm/                 # Gemini, Grok, and Mock LLM adapters
│           └── memory/              # Session memory providers (SQLite / AWS)
├── frontend/
│   ├── Dockerfile                   # Multi-stage Nginx container build
│   ├── package.json                 # Frontend package manifest
│   ├── vite.config.ts               # Vite configuration and backend API proxy
│   ├── index.html                   # HTML entrypoint
│   └── src/
│       ├── main.tsx                 # Root application component
│       ├── styles.css               # Clinical blue design system
│       ├── i18n.ts                  # Localization dictionaries (EN/HI/Hinglish)
│       ├── lib/api.ts               # Type-safe API client
│       └── components/
│           ├── AuthPages.tsx        # Login, Register, and OTP interfaces
│           ├── Brand.tsx            # Application branding and navigation header
│           └── Dialog.tsx           # Accessible modal dialog component
├── data/
│   └── provided/                    # Unaltered Sanocare synthetic datasets
├── models/
│   └── baseline/                    # Serialized TF-IDF classification pipelines
├── notebooks/
│   └── triagegrid_training.ipynb    # Reproducible model training workbook
├── scripts/
│   ├── audit_data.py                # Dataset integrity and checksum checks
│   ├── train_models.py              # Baseline pipeline training script
│   └── make_predictions_csv.py      # Batch evaluation inference CLI
├── docs/                            # Architecture, data audit, and security specs
├── reports/                         # Evaluation benchmarks and verification logs
├── compose.yaml                     # Docker Compose multi-service manifest
├── run_backend.py                   # Cross-platform backend server launcher
├── package.json                     # Monorepo root task runner
├── pytest.ini                       # Test suite runner settings
├── LICENSE                          # MIT License
└── README.md                        # Project documentation
```

---

## Machine Learning and Clinical Models

TriageGrid employs two specialized classification pipelines trained on the Sanocare synthetic triage dataset (340 annotated interactions, 65 distinct patient expressions):

1. **Care Type Classifier:** Evaluates n-gram token distributions to assign requests to appropriate services (`paramedic_home_visit`, `teleconsultation`, `nurse_visit`, `in_clinic`).
2. **Urgency Classifier:** Determines clinical urgency levels (`routine`, `same_day`, `emergency`).

### Performance Metrics (Grouped Cross-Validation)

- **Care Type Classification:** Macro-F1: 0.6466
- **Urgency Classification:** Macro-F1: 0.6116

Pipelines utilize TF-IDF word (1-3 n-grams) and character (3-5 n-grams) feature extraction combined with balanced Logistic Regression. Artifacts are stored under `models/baseline/` and loaded at runtime without unverified external network dependencies.

---

## Local Setup and Installation

### Prerequisites

- **Python:** Version 3.10 or higher
- **Node.js:** Version 18.0 or higher
- **Git:** Installed and available in terminal path

---

### Environment Configuration

Create a local environment file by copying the template:

```sh
cp .env.example .env
```

Available configuration keys:

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | None | Google Gemini API key for conversational AI |
| `GROK_API_KEY` | None | xAI Grok API key (alternative LLM adapter) |
| `LLM_PROVIDER` | `mock` | Active LLM adapter: `gemini`, `grok`, or `mock` |
| `TINYFISH_API_KEY` | None | API key for external emergency web research |
| `TRIAGEGRID_DATABASE_URL` | `sqlite:///./var/triagegrid.db` | Database connection string |
| `TRIAGEGRID_PORT` | `8000` | Port for FastAPI backend service |

---

### Backend Setup (FastAPI)

1. Navigate to the project root directory and create a Python virtual environment:

```sh
python -m venv .venv
```

2. Activate the virtual environment:

- **Linux / macOS:**
  ```sh
  source .venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```

3. Install required Python packages:

```sh
pip install -r backend/requirements.txt
```

4. Start the backend server:

```sh
python run_backend.py
```

The backend server initializes on `http://127.0.0.1:8000`. Interactive OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

---

### Frontend Setup (React + Vite)

From a separate terminal window:

1. Navigate to the frontend directory:

```sh
cd frontend
```

2. Install dependencies:

```sh
npm install
```

3. Start the development server:

```sh
npm run dev
```

4. Open `http://127.0.0.1:5173` in your browser. All requests to `/api` are automatically forwarded to the backend running on port 8000.

---

### Root-Level Convenience Scripts

If preferred, run standard lifecycle tasks directly from the repository root:

```sh
npm run dev        # Starts frontend Vite development server
npm run build      # Executes TypeScript validation and builds frontend assets
npm run backend    # Launches Python backend server launcher
```

---

### Docker Deployment

To build and run both the backend API and frontend Nginx proxy inside isolated containers:

```sh
docker compose up --build
```

- Web Application: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

---

## API Reference

### Core Endpoints

#### 1. System Health
- **Endpoint:** `GET /api/health`
- **Description:** Verifies service connectivity, active LLM adapter, and demo credentials.

#### 2. Triage Prediction
- **Endpoint:** `POST /api/triage/predict`
- **Request Body:**
  ```json
  {
    "user_input": "Mujhe 2 din se tez bukhar hai aur sar dard ho raha hai",
    "language": "auto",
    "location": { "lat": 28.54, "lng": 77.27 },
    "conversation_history": []
  }
  ```
- **Response Body:**
  ```json
  {
    "follow_up_question": null,
    "care_type": "paramedic_home_visit",
    "urgency": "same_day",
    "red_flags": [],
    "reasoning": "Reported persistent fever with headache, no acute respiratory distress.",
    "matched_caregivers": [
      {
        "caregiver_id": "CG_014",
        "full_name": "Rohan Verma",
        "score": 0.92,
        "distance_km": 3.2,
        "reason": "Hindi-speaking, within 5 km, available today"
      }
    ]
  }
  ```

#### 3. Conversational Assistant
- **Endpoint:** `POST /api/chat/message`
- **Description:** Multi-turn intake dialogue engine extracting symptom slots, assessing red flags, and producing conversational guidance.

#### 4. Booking Reservations
- **Endpoint:** `POST /api/bookings`
- **Description:** Secures a designated caregiver time slot with transactional conflict validation.

#### 5. Hospital Intelligence
- **Endpoint:** `POST /api/hospital/research`
- **Description:** Dispatches a scoped TinyFish web agent to extract publicly listed contact numbers and emergency desk locations.

---

## Testing and Verification

The test suite covers data integrity, model inference, safety red flags, booking concurrency, session ownership, and multi-turn conversational extraction.

Run the test suite from the project root:

```sh
# Run backend tests
PYTHONPATH=backend pytest backend/tests -v

# Verify dataset checksums and integrity
python scripts/audit_data.py

# Type-check and build frontend bundle
cd frontend && npm run build
```

---

## Clinical Disclaimer and Limitations

- **Educational & Prototype Use Only:** TriageGrid was developed as a competition prototype for the CareCompass challenge at IIIT-Delhi.
- **Not Medical Advice:** This software does not provide clinical diagnosis, medical triage, treatment recommendations, or drug prescription.
- **Synthetic Data:** The system operates exclusively on synthetic datasets provided by Sanocare Tech Innovations Pvt Ltd. No protected health information (PHI) or real patient records are utilized.
- **Simulated Emergency Handover:** Hospital communication screens (Golden Bay) and caregiver bookings are local mock simulations and do not dispatch medical personnel or alert emergency departments.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.
