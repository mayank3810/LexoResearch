from __future__ import annotations

import hashlib
import json
from app.constants import SIMULATED_BANNER
from app.models.ir import Event, Observability, WorldModel
from app.models.runtime import (
    LedgerStep,
    Observation,
    PositionState,
    StartingBook,
    ThesisState,
    WorldSnapshot,
)

HYPERSCALER_EVENTS = {
    "EVT-CAPEX-MSFT",
    "EVT-CAPEX-AMZN",
    "EVT-CAPEX-GOOGL",
    "EVT-CAPEX-META",
}

KILL_EVENTS = {
    "EVT-KILL-TAIWAN": "CTR-KILL-TAIWAN",
    "EVT-KILL-TRAINING": "CTR-KILL-TRAINING",
    "EVT-KILL-NETWORKING": "CTR-KILL-NETWORKING",
    "EVT-KILL-CASH": "CTR-KILL-CASH",
}


def _event_map(model: WorldModel) -> dict[str, Event]:
    return {e.id: e for e in model.events}


def _sort_key(obs: Observation, events: dict[str, Event]) -> tuple[str, str]:
    event = events[obs.event_id]
    date = obs.date or event.date or "9999-12-31"
    return (date, obs.event_id)


def _initial_position(book: StartingBook) -> PositionState:
    return PositionState.LONG if book == StartingBook.LONG else PositionState.NONE


def _thesis_dict(t: ThesisState) -> dict:
    return t.model_dump()


def tape_hash(
    observations: list[Observation],
    starting_book: StartingBook,
    thesis: ThesisState,
    ledger: list[LedgerStep],
) -> str:
    payload = {
        "starting_book": starting_book.value,
        "observations": [o.model_dump() for o in observations],
        "thesis": thesis.model_dump(),
        "ledger": [s.model_dump() for s in ledger],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run_tape(
    model: WorldModel,
    observations: list[Observation],
    starting_book: StartingBook,
    world_id: str,
) -> WorldSnapshot:
    events = _event_map(model)
    claims = {c.id: c for c in model.claims}
    factors = {f.id: f for f in model.factors}
    contracts = {c.id: c for c in model.contracts}

    tilts: dict[str, str] = {f.id: f.initial_tilt for f in model.factors}
    lit: set[str] = set()
    hyperscaler_down: list[str] = []
    weekly_below: list[str] = []
    kills: list[str] = []
    override_active = True
    scenario: str = "BASE"
    rating: str = "Hold"
    position = _initial_position(starting_book)
    notes: list[str] = []
    ledger: list[LedgerStep] = []

    ordered = sorted(observations, key=lambda o: _sort_key(o, events))

    def snapshot_thesis(action: str) -> ThesisState:
        unresolved = [
            fid
            for fid, tilt in tilts.items()
            if tilt == "unresolved" and factors[fid].deep
        ]
        return ThesisState(
            world_id=world_id,
            scenario=scenario,  # type: ignore[arg-type]
            rating=rating,  # type: ignore[arg-type]
            conviction=model.as_of.conviction,
            unresolved_factors=unresolved,
            position=position,
            position_action=action,
            starting_book=starting_book,
            override_active=override_active,
            kill_switch_up=bool(kills),
            kill_switch_ids=list(kills),
            fy2028_row=model.as_of.fy2028.model_dump(),
            notes=list(notes),
        )

    for seq, obs in enumerate(ordered, start=1):
        event = events[obs.event_id]
        before = snapshot_thesis("HOLD")
        tilted: list[dict] = []
        exposures_lit: list[dict] = []
        gated: list[dict] = []
        provenance: list[dict] = []
        skipped = False
        skip_reason = None
        action = "NONE"

        if event.observability == Observability.HUMAN and not obs.adjudicated:
            skipped = True
            skip_reason = "AWAITING_HUMAN_OBSERVATION"
        elif event.observability == Observability.NOT_YET:
            skipped = True
            skip_reason = "NOT_YET_OBSERVABLE"
        else:
            matching = [
                r
                for r in model.relationships
                if r.event_id == obs.event_id and r.outcome == obs.outcome
            ]
            for rel in matching:
                if rel.direction.value == "neutral":
                    tilts[rel.factor_id] = "neutral"
                elif rel.direction.value == "positive":
                    tilts[rel.factor_id] = "positive"
                else:
                    if rel.factor_id == "F-FY2028" and obs.event_id in HYPERSCALER_EVENTS:
                        if tilts[rel.factor_id] not in {"positive", "resolved_bull", "resolved_bear"}:
                            tilts[rel.factor_id] = "threatened"
                    else:
                        tilts[rel.factor_id] = "negative"
                lit.add(rel.id)
                lit.add(rel.factor_id)
                lit.add(obs.event_id)
                claim = claims.get(rel.claim_id) if rel.claim_id else None
                tilted.append(
                    {
                        "relationship_id": rel.id,
                        "factor_id": rel.factor_id,
                        "factor_name": factors[rel.factor_id].name,
                        "direction": rel.direction.value,
                        "tilt": tilts[rel.factor_id],
                    }
                )
                provenance.append(
                    {
                        "kind": rel.provenance.value,
                        "claim_id": rel.claim_id,
                        "policy_id": rel.policy_id,
                        "document": claim.document if claim else None,
                        "page": claim.page if claim else None,
                        "section": claim.section if claim else None,
                        "quote": claim.quote if claim else None,
                    }
                )
                for exp in model.exposures:
                    if exp.factor_id == rel.factor_id:
                        lit.add(exp.id)
                        lit.add(exp.ticker)
                        exposures_lit.append(
                            {
                                "exposure_id": exp.id,
                                "ticker": exp.ticker,
                                "factor_id": exp.factor_id,
                                "has_position_policy": exp.has_position_policy,
                            }
                        )

            if obs.event_id in HYPERSCALER_EVENTS and obs.outcome == "flat_or_down":
                if obs.event_id not in hyperscaler_down:
                    hyperscaler_down.append(obs.event_id)

            if event.event_type == "weekly_close":
                weekly_below.append(obs.event_id if obs.outcome == "below_195" else "")

            if obs.event_id in KILL_EVENTS and obs.outcome == "fired":
                kills.append(KILL_EVENTS[obs.event_id])

            if kills:
                scenario = "BEAR"
                rating = "Sell"
                override_active = False
                for kid in kills:
                    ctr = contracts[kid]
                    lit.add(ctr.id)
                    gated.append(
                        {
                            "contract_id": ctr.id,
                            "name": ctr.name,
                            "kind": ctr.kind,
                            "dominates": True,
                        }
                    )
                if position == PositionState.LONG:
                    action = "EXIT"
                    position = PositionState.NONE
                else:
                    action = "NONE"
                    notes.append("Kill switch up; flat book stays flat.")
            else:
                confirm = (
                    obs.event_id == "EVT-FY2028-COMMENTARY"
                    and obs.outcome == "confirmation_near_70_with_backlog"
                )
                bear_45 = (
                    (
                        obs.event_id == "EVT-FY2028-COMMENTARY"
                        and obs.outcome == "softening_below_45"
                    )
                    or (
                        obs.event_id == "EVT-FY2028-FORMAL-GUIDE"
                        and obs.outcome == "below_45"
                    )
                )
                two_of_four = len(hyperscaler_down) >= 2
                one_of_four = len(hyperscaler_down) == 1
                consecutive_stop = (
                    len(weekly_below) >= 2
                    and weekly_below[-1] != ""
                    and weekly_below[-2] != ""
                )
                ambiguous = (
                    obs.event_id == "EVT-FY2028-COMMENTARY"
                    and obs.outcome == "ambiguous"
                )

                if confirm:
                    tilts["F-FY2028"] = "resolved_bull"
                    scenario = "BULL"
                    rating = "Buy"
                    override_active = False
                    ctr = contracts["CTR-FY2028-CONFIRM"]
                    lit.add(ctr.id)
                    gated.append(
                        {
                            "contract_id": ctr.id,
                            "name": ctr.name,
                            "kind": ctr.kind,
                            "dominates": False,
                        }
                    )
                    notes.append("Neutral-spring override retired.")
                    if position == PositionState.NONE:
                        action = "INITIATE"
                        position = PositionState.LONG
                    else:
                        action = "HOLD"
                elif bear_45:
                    tilts["F-FY2028"] = "resolved_bear"
                    scenario = "BEAR"
                    rating = "Sell"
                    override_active = False
                    ctr = contracts["CTR-FY2028-LT-45"]
                    lit.add(ctr.id)
                    gated.append(
                        {
                            "contract_id": ctr.id,
                            "name": ctr.name,
                            "kind": ctr.kind,
                            "dominates": False,
                        }
                    )
                    if position == PositionState.LONG:
                        action = "EXIT"
                        position = PositionState.NONE
                    else:
                        action = "NONE"
                elif two_of_four and obs.event_id in HYPERSCALER_EVENTS:
                    tilts["F-FY2028"] = "resolved_bear"
                    scenario = "BEAR"
                    rating = "Sell"
                    override_active = False
                    ctr = contracts["CTR-TWO-OF-FOUR"]
                    lit.add(ctr.id)
                    gated.append(
                        {
                            "contract_id": ctr.id,
                            "name": ctr.name,
                            "kind": ctr.kind,
                            "dominates": False,
                        }
                    )
                    if position == PositionState.LONG:
                        action = "EXIT"
                        position = PositionState.NONE
                    else:
                        action = "NONE"
                elif one_of_four and obs.event_id in HYPERSCALER_EVENTS:
                    notes.append(
                        "One of four flat-or-down threatens FY2028; contract requires two."
                    )
                    action = "NONE"
                elif ambiguous:
                    notes.append("Ambiguous 17 Nov language resolves nothing. Stay BASE.")
                    action = "NONE"
                elif consecutive_stop:
                    ctr = contracts["CTR-STOP-195"]
                    lit.add(ctr.id)
                    if position == PositionState.LONG:
                        gated.append(
                            {
                                "contract_id": ctr.id,
                                "name": ctr.name,
                                "kind": ctr.kind,
                                "dominates": False,
                            }
                        )
                        action = "STOP_EXIT"
                        position = PositionState.NONE
                        notes.append("Stop honoured for existing holder.")
                    else:
                        notes.append("Stop ignores a flat book.")
                        action = "NONE"
                else:
                    action = "NONE"

        after = snapshot_thesis(action)
        ledger.append(
            LedgerStep(
                seq=seq,
                date=_sort_key(obs, events)[0],
                event_id=obs.event_id,
                event_name=event.name,
                outcome=obs.outcome,
                entity=event.entity,
                third_party=event.third_party,
                factors_tilted=tilted,
                exposures_lit=exposures_lit,
                contracts_gated=gated,
                thesis_before=_thesis_dict(before),
                thesis_after=_thesis_dict(after),
                book_action=action,
                provenance=provenance,
                skipped=skipped,
                skip_reason=skip_reason,
            )
        )

    final = snapshot_thesis(ledger[-1].book_action if ledger else "NONE")
    awaiting = []
    bound_ids = {o.event_id for o in observations}
    adjudicated_ids = {o.event_id for o in observations if o.adjudicated}
    for event in model.events:
        if event.observability == Observability.HUMAN and event.id not in adjudicated_ids:
            awaiting.append(
                {
                    "event_id": event.id,
                    "name": event.name,
                    "status": "AWAITING_HUMAN_OBSERVATION",
                    "bound": event.id in bound_ids,
                }
            )

    return WorldSnapshot(
        world_id=world_id,
        banner=SIMULATED_BANNER,
        starting_book=starting_book,
        thesis=final,
        factor_tilts=tilts,
        lit_node_ids=sorted(lit),
        awaiting_human=awaiting,
        ledger=ledger,
        tape_hash=tape_hash(ordered, starting_book, final, ledger),
        bindings=ordered,
    )


def clone_observations(observations: list[Observation]) -> list[Observation]:
    return [Observation.model_validate(o.model_dump()) for o in observations]
