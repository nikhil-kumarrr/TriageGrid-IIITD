from dataclasses import dataclass
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
@dataclass(frozen=True)
class Settings:
    database_path: Path = ROOT / os.getenv("TRIAGE_DATABASE_PATH", "var/triagegrid.sqlite3")
    allowed_origins: tuple[str, ...] = tuple(x.strip() for x in os.getenv("TRIAGE_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip())
    data_dir: Path = ROOT / "data" / "provided"
    model_dir: Path = ROOT / "models" / "baseline"
    assistant_provider: str = os.getenv("ASSISTANT_PROVIDER", "gemini").lower()
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    grok_api_key: str = os.getenv("GROK_API_KEY", "") or os.getenv("XAI_API_KEY", "")
    memory_provider: str = os.getenv("MEMORY_PROVIDER", "sqlite").lower()
    aws_region: str = os.getenv("AWS_REGION", "ap-south-1")
    aws_dynamodb_table: str = os.getenv("AWS_DYNAMODB_TABLE", "triagegrid_memory")
settings = Settings()
