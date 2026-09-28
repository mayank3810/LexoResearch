from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.models.ir import WorldModel


def _fixture_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "data" / "fixtures",
        Path.cwd() / "data" / "fixtures",
        Path(__file__).resolve().parents[2] / "data" / "fixtures",
    ]
    for path in candidates:
        if (path / "as_of.json").exists():
            return path
    raise FileNotFoundError("compiled fixtures not found")


FIXTURE_DIR = _fixture_dir()


def _read(name: str) -> object:
    path = FIXTURE_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def load_world_model() -> WorldModel:
    payload = {
        "as_of": _read("as_of.json"),
        "claims": _read("claims.json"),
        "factors": _read("factors.json"),
        "events": _read("events.json"),
        "relationships": _read("relationships.json"),
        "exposures": _read("exposures.json"),
        "scenarios": _read("scenarios.json"),
        "contracts": _read("contracts.json"),
        "policies": _read("policies.json"),
        "calendar": _read("calendar.json"),
        "tickers": _read("tickers.json"),
    }
    return WorldModel.model_validate(payload)


@lru_cache(maxsize=1)
def cached_world_model() -> WorldModel:
    return load_world_model()
