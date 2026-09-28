from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Observability(str, Enum):
    MACHINE = "machine_observable"
    HUMAN = "human_observable"
    NOT_YET = "not_yet_observable"


class ProvenanceKind(str, Enum):
    SOURCE_BACKED = "source_backed"
    OUR_POLICY = "our_policy"
    OURS_NO_CLAIM = "ours_no_claim"


class TiltDirection(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Circle(str, Enum):
    INTERNAL = "internal"
    SECTOR = "sector"
    MARKET = "market"


class ForceType(str, Enum):
    WAVE_PLUS = "wave_plus"
    WAVE_MINUS = "wave_minus"
    HEADWIND = "headwind"
    TAILWIND = "tailwind"
    EXISTENTIAL_THREAT = "existential_threat"
    MUD = "mud"


KNOWN_DOCUMENTS = {
    "NVDA-memo.pdf",
    "NVDA-factor-report.pdf",
    "NVDA-theme-report.pdf",
}


class Claim(BaseModel):
    id: str
    text: str
    document: str
    page: int
    section: str
    quote: str


class Fy2028Disagreement(BaseModel):
    workbook_revenue_m: float
    workbook_growth_pct: float
    management_guide_pct: float
    consensus_revenue_m: float
    note: str
    claim_id: str
    document: str
    page: int


class AsOf(BaseModel):
    date: str
    ticker: str
    price: float
    rating: str
    conviction: str
    conviction_note: str
    position: str
    memo_date: str
    fy2028: Fy2028Disagreement
    document: str
    page: int


class Factor(BaseModel):
    id: str
    name: str
    circle: Circle
    force_type: ForceType
    impact: float | None = None
    theme_weight: int | None = None
    description: str
    deep: bool = False
    initial_tilt: Literal["unresolved", "neutral"] = "unresolved"
    document: str
    page: int


class Event(BaseModel):
    id: str
    name: str
    entity: str
    event_type: str
    date: str | None
    window: str | None = None
    observability: Observability
    possible_outcomes: list[str]
    third_party: bool = False
    description: str
    watch_status: Literal["open", "awaiting_human", "inert"] | None = None
    document: str
    page: int


class Relationship(BaseModel):
    id: str
    event_id: str
    outcome: str
    factor_id: str
    direction: TiltDirection
    provenance: ProvenanceKind
    claim_id: str | None = None
    policy_id: str | None = None
    note: str = ""
    document: str | None = None
    page: int | None = None


class Exposure(BaseModel):
    id: str
    ticker: str
    factor_id: str
    has_position_policy: bool = False
    note: str = ""
    claim_id: str | None = None
    document: str
    page: int


class ScenarioSpec(BaseModel):
    id: str
    name: Literal["BULL", "BASE", "BEAR"]
    probability_pct: int
    region: str
    claim_id: str
    document: str
    page: int


class Contract(BaseModel):
    id: str
    name: str
    kind: Literal[
        "two_of_four",
        "fy2028_lt_45",
        "fy2028_near_70_with_backlog",
        "stop_195",
        "kill_switch",
    ]
    metric: str
    threshold: str
    timeframe: str
    gates: str
    provenance: ProvenanceKind
    claim_id: str
    kill_switch: bool = False
    holders_only: bool = False
    related_factor_ids: list[str] = Field(default_factory=list)
    related_event_ids: list[str] = Field(default_factory=list)
    document: str
    page: int


class OurPolicy(BaseModel):
    id: str
    name: str
    provenance: ProvenanceKind
    text: str
    retires_when: str | None = None
    claim_id: str | None = None
    document: str
    page: int


class CalendarItem(BaseModel):
    id: str
    event_id: str
    date: str
    label: str
    unresolved: bool = True
    document: str
    page: int


class Ticker(BaseModel):
    symbol: str
    name: str
    role: str
    document: str
    page: int


class WorldModel(BaseModel):
    as_of: AsOf
    claims: list[Claim]
    factors: list[Factor]
    events: list[Event]
    relationships: list[Relationship]
    exposures: list[Exposure]
    scenarios: list[ScenarioSpec]
    contracts: list[Contract]
    policies: list[OurPolicy]
    calendar: list[CalendarItem]
    tickers: list[Ticker]
