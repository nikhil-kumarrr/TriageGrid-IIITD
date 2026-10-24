"""
TriageGrid Backend Launcher
Works seamlessly across Windows, macOS, and Linux without needing manual PYTHONPATH configuration.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
backend_dir = ROOT / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    print("Starting TriageGrid FastAPI backend on http://127.0.0.1:8000 ...")
    uvicorn.run("triagegrid.main:app", host="127.0.0.1", port=8000, reload=True)
