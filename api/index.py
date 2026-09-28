import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app as engine
from fastapi import FastAPI

app = FastAPI(title="Lexo")
app.mount("/api", engine)
