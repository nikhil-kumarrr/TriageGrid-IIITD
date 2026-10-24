"""Central paths and constants. Override via environment variables for deployment."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("TRIAGE_DATA_DIR", ROOT / "data"))
ART_DIR = Path(os.getenv("TRIAGE_ARTIFACT_DIR", ROOT / "artifacts"))

TRIAGE_CSV = DATA_DIR / "triage_dataset_flat.csv"
CAREGIVERS_CSV = Path(os.getenv("CAREGIVERS_CSV", DATA_DIR / "caregivers.csv"))

CARE_PIPE_PATH = ART_DIR / "care_type_pipeline.pkl"
URG_PIPE_PATH = ART_DIR / "urgency_pipeline.pkl"
META_PATH = ART_DIR / "model_meta.json"
CM_PATH = ART_DIR / "confusion_matrix.png"

SEED = 42
NEEDS_CLARIFICATION = "needs_clarification"
EMERGENCY = "emergency_112"
