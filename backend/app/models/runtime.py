from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class StartingBook(str, Enum):
    FLAT = "flat"
    LONG = "long"


class PositionState(str, Enum):
    NONE = "none"
    LONG = "long"


class ThesisState(BaseModel):
    world_id: str
    scenario: Literal["BULL", "BASE", "BEAR"]
    rating: Literal["Hold", "Buy", "Sell"]
    conviction: str
    unresolved_factors: list[str]
    position: PositionState
    position_action: str
    starting_book: StartingBook
    override_active: bool
    kill_switch_up: bool
    kill_switch_ids: list[str] = Field(default_factory=list)
    fy2028_row: dict
    notes: list[str] = Field(default_factory=list)


class LedgerStep(BaseModel):
    seq: int
    date: str
    event_id: str
    event_name: str
    outcome: str
    entity: str
    third_party: bool
    factors_tilted: list[dict]
    exposures_lit: list[dict]
    contracts_gated: list[dict]
    thesis_before: dict
    thesis_after: dict
    book_action: str
    provenance: list[dict]
    skipped: bool = False
    skip_reason: str | None = None


class Observation(BaseModel):
    event_id: str
    outcome: str
    date: str | None = None
    adjudicated: bool = False


class BindRequest(BaseModel):
    event_id: str
    outcome: str
    date: str | None = None
    bindings: list[Observation] | None = None
    starting_book: StartingBook | None = None


class AdjudicateRequest(BaseModel):
    event_id: str
    outcome: str
    bindings: list[Observation] | None = None
    starting_book: StartingBook | None = None


class StartingBookRequest(BaseModel):
    starting_book: StartingBook
    bindings: list[Observation] | None = None


class ReplayRequest(BaseModel):
    bindings: list[Observation] | None = None
    starting_book: StartingBook | None = None


class WorldSnapshot(BaseModel):
    world_id: str
    banner: str
    starting_book: StartingBook
    thesis: ThesisState
    factor_tilts: dict[str, str]
    lit_node_ids: list[str]
    awaiting_human: list[dict]
    ledger: list[LedgerStep]
    tape_hash: str
    bindings: list[Observation]
