from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query

from app.constants import SIMULATED_BANNER
from app.engine.sessions import seed_for, store
from app.models.ir import Observability
from app.models.runtime import (
    AdjudicateRequest,
    BindRequest,
    Observation,
    ReplayRequest,
    StartingBook,
    StartingBookRequest,
)

router = APIRouter()


def _world_or_404(world_id: str):
    try:
        return store.get(world_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown world {world_id}") from exc


def _book(world_id: str, starting_book: StartingBook | None) -> StartingBook:
    session = _world_or_404(world_id)
    return starting_book if starting_book is not None else session.starting_book


def _observations(world_id: str, bindings: list[Observation] | None) -> list[Observation]:
    session = _world_or_404(world_id)
    if bindings is None:
        return session.observations
    return [Observation.model_validate(o.model_dump()) for o in bindings]


def _upsert(observations: list[Observation], incoming: Observation) -> list[Observation]:
    next_obs = [Observation.model_validate(o.model_dump()) for o in observations]
    for i, existing in enumerate(next_obs):
        if existing.event_id == incoming.event_id:
            next_obs[i] = incoming.model_copy(
                update={"adjudicated": incoming.adjudicated or existing.adjudicated}
            )
            return next_obs
    next_obs.append(incoming)
    return next_obs


def _persist_if_local(world_id: str, observations: list[Observation], starting_book: StartingBook, client_tape: bool) -> None:
    if client_tape:
        return
    session = _world_or_404(world_id)
    session.observations = observations
    session.starting_book = starting_book


@router.get("/banner")
def banner() -> dict:
    return {"banner": SIMULATED_BANNER}


@router.get("/as-of")
def as_of() -> dict:
    a = store.model.as_of
    return {
        "date": a.date,
        "ticker": a.ticker,
        "price": a.price,
        "rating": a.rating,
        "conviction": a.conviction,
        "conviction_note": a.conviction_note,
        "position": a.position,
        "memo_date": a.memo_date,
        "document": a.document,
        "page": a.page,
        "fy2028": a.fy2028.model_dump(),
        "banner": SIMULATED_BANNER,
    }


@router.get("/world-model")
def world_model(world: str | None = Query(default=None)) -> dict:
    model = store.model
    lit: list[str] = []
    tilts: dict[str, str] = {}
    if world and world.upper() not in {"ASOF", "NONE"}:
        snap = store.snapshot(world)
        lit = snap.lit_node_ids
        tilts = snap.factor_tilts
    return {
        "banner": SIMULATED_BANNER,
        "as_of": model.as_of.model_dump(),
        "tickers": [t.model_dump() for t in model.tickers],
        "factors": [f.model_dump() for f in model.factors],
        "events": [e.model_dump() for e in model.events],
        "relationships": [r.model_dump() for r in model.relationships],
        "exposures": [x.model_dump() for x in model.exposures],
        "contracts": [c.model_dump() for c in model.contracts],
        "policies": [p.model_dump() for p in model.policies],
        "scenarios": [s.model_dump() for s in model.scenarios],
        "lit_node_ids": lit,
        "factor_tilts": tilts,
    }


@router.get("/calendar")
def calendar() -> dict:
    model = store.model
    events = {e.id: e for e in model.events}
    return {
        "banner": SIMULATED_BANNER,
        "items": [
            {
                **item.model_dump(),
                "event": events[item.event_id].model_dump(),
            }
            for item in model.calendar
        ],
    }


@router.get("/claims/{claim_id}")
def claim(claim_id: str) -> dict:
    for c in store.model.claims:
        if c.id == claim_id:
            return c.model_dump()
    raise HTTPException(status_code=404, detail="unknown claim")


@router.get("/thesis-state")
def thesis_state(world: str = Query(default="ASOF")) -> dict:
    if world.upper() == "ASOF":
        from app.engine.propagate import run_tape
        from app.models.runtime import StartingBook

        snap = run_tape(store.model, [], StartingBook.FLAT, "ASOF")
    else:
        _world_or_404(world)
        snap = store.snapshot(world)
    return {
        "banner": snap.banner,
        "thesis": snap.thesis.model_dump(),
        "factor_tilts": snap.factor_tilts,
        "lit_node_ids": snap.lit_node_ids,
        "awaiting_human": snap.awaiting_human,
        "tape_hash": snap.tape_hash,
    }


@router.get("/worlds/{world_id}")
def world(world_id: str) -> dict:
    _world_or_404(world_id)
    return store.snapshot(world_id).model_dump()


@router.get("/worlds/{world_id}/ledger")
def ledger(world_id: str) -> dict:
    _world_or_404(world_id)
    snap = store.snapshot(world_id)
    return {
        "banner": snap.banner,
        "world_id": snap.world_id,
        "tape_hash": snap.tape_hash,
        "ledger": [s.model_dump() for s in snap.ledger],
    }


@router.post("/worlds/{world_id}/bind")
def bind(world_id: str, body: BindRequest) -> dict:
    event = next((e for e in store.model.events if e.id == body.event_id), None)
    if event is None:
        raise HTTPException(status_code=404, detail="unknown event")
    if body.outcome not in event.possible_outcomes:
        raise HTTPException(status_code=400, detail="outcome not in possible_outcomes")
    observations = _observations(world_id, body.bindings)
    book = _book(world_id, body.starting_book)
    incoming = Observation(
        event_id=body.event_id,
        outcome=body.outcome,
        date=body.date or event.date,
        adjudicated=event.observability != Observability.HUMAN,
    )
    observations = _upsert(observations, incoming)
    _persist_if_local(world_id, observations, book, body.bindings is not None)
    return store.compute(world_id, observations, book).model_dump()


@router.post("/worlds/{world_id}/adjudicate")
def adjudicate(world_id: str, body: AdjudicateRequest) -> dict:
    event = next((e for e in store.model.events if e.id == body.event_id), None)
    if event is None:
        raise HTTPException(status_code=404, detail="unknown event")
    if body.outcome not in event.possible_outcomes:
        raise HTTPException(status_code=400, detail="outcome not in possible_outcomes")
    observations = _observations(world_id, body.bindings)
    book = _book(world_id, body.starting_book)
    incoming = Observation(event_id=body.event_id, outcome=body.outcome, adjudicated=True)
    observations = _upsert(observations, incoming)
    for i, existing in enumerate(observations):
        if existing.event_id == body.event_id:
            observations[i] = existing.model_copy(update={"outcome": body.outcome, "adjudicated": True})
    _persist_if_local(world_id, observations, book, body.bindings is not None)
    return store.compute(world_id, observations, book).model_dump()


@router.post("/worlds/{world_id}/starting-book")
def starting_book(world_id: str, body: StartingBookRequest) -> dict:
    observations = _observations(world_id, body.bindings)
    _persist_if_local(world_id, observations, body.starting_book, body.bindings is not None)
    return store.compute(world_id, observations, body.starting_book).model_dump()


@router.post("/worlds/{world_id}/replay")
def replay(world_id: str, body: ReplayRequest | None = Body(default=None)) -> dict:
    payload = body or ReplayRequest()
    observations = _observations(world_id, payload.bindings)
    book = _book(world_id, payload.starting_book)
    first = store.compute(world_id, observations, book)
    second = store.compute(world_id, observations, book)
    return {
        "banner": first.banner,
        "world_id": first.world_id,
        "tape_hash": first.tape_hash,
        "hashes_match": first.tape_hash == second.tape_hash,
        "thesis": first.thesis.model_dump(),
        "ledger": [s.model_dump() for s in first.ledger],
        "factor_tilts": first.factor_tilts,
        "lit_node_ids": first.lit_node_ids,
        "awaiting_human": first.awaiting_human,
        "bindings": [b.model_dump() for b in first.bindings],
        "starting_book": first.starting_book.value,
    }


@router.post("/worlds/{world_id}/reset")
def reset(world_id: str) -> dict:
    session = _world_or_404(world_id)
    session.reset()
    return store.compute(world_id, seed_for(world_id), StartingBook.FLAT).model_dump()
