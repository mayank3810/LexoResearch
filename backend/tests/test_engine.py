from app.engine.propagate import run_tape, tape_hash
from app.models.runtime import Observation, StartingBook


def test_one_of_four_does_not_exit(model):
    snap = run_tape(
        model,
        [
            Observation(
                event_id="EVT-CAPEX-MSFT",
                outcome="flat_or_down",
                date="2027-01-28",
            )
        ],
        StartingBook.FLAT,
        "T",
    )
    assert snap.thesis.scenario == "BASE"
    assert snap.thesis.rating == "Hold"
    assert snap.thesis.position.value == "none"
    assert snap.thesis.position_action == "NONE"
    assert snap.factor_tilts["F-FY2028"] == "threatened"
    assert snap.factor_tilts["F-NVDA-DEMAND"] == "negative"
    assert not any(s.contracts_gated for s in snap.ledger if s.event_id == "EVT-CAPEX-MSFT")


def test_two_of_four_exits(model):
    snap = run_tape(
        model,
        [
            Observation(event_id="EVT-CAPEX-MSFT", outcome="flat_or_down", date="2027-01-28"),
            Observation(event_id="EVT-CAPEX-AMZN", outcome="flat_or_down", date="2027-01-30"),
        ],
        StartingBook.LONG,
        "T",
    )
    assert snap.thesis.scenario == "BEAR"
    assert snap.thesis.rating == "Sell"
    assert snap.thesis.position.value == "none"
    assert snap.thesis.position_action == "EXIT"
    assert any(
        any(c["contract_id"] == "CTR-TWO-OF-FOUR" for c in s.contracts_gated)
        for s in snap.ledger
    )
    assert any(s.third_party for s in snap.ledger)


def test_ambiguous_17_nov_does_not_move_state(model):
    snap = run_tape(
        model,
        [
            Observation(
                event_id="EVT-FY2028-COMMENTARY",
                outcome="ambiguous",
                date="2026-11-17",
                adjudicated=True,
            )
        ],
        StartingBook.FLAT,
        "T",
    )
    assert snap.thesis.scenario == "BASE"
    assert snap.thesis.rating == "Hold"
    assert snap.thesis.position.value == "none"
    assert snap.factor_tilts["F-FY2028"] == "neutral"
    assert snap.thesis.override_active is True


def test_confirmation_moves_to_bull_and_retires_override(model):
    snap = run_tape(
        model,
        [
            Observation(
                event_id="EVT-FY2028-COMMENTARY",
                outcome="confirmation_near_70_with_backlog",
                date="2026-11-17",
                adjudicated=True,
            )
        ],
        StartingBook.FLAT,
        "T",
    )
    assert snap.thesis.scenario == "BULL"
    assert snap.thesis.rating == "Buy"
    assert snap.thesis.override_active is False
    assert snap.thesis.position.value == "long"
    assert snap.thesis.position_action == "INITIATE"
    assert snap.factor_tilts["F-FY2028"] == "resolved_bull"


def test_softening_below_45_is_bear(model):
    snap = run_tape(
        model,
        [
            Observation(
                event_id="EVT-FY2028-COMMENTARY",
                outcome="softening_below_45",
                date="2026-11-17",
                adjudicated=True,
            )
        ],
        StartingBook.LONG,
        "T",
    )
    assert snap.thesis.scenario == "BEAR"
    assert snap.thesis.rating == "Sell"
    assert snap.thesis.position_action == "EXIT"


def test_stop_ignores_flat_book(model):
    snap = run_tape(
        model,
        [
            Observation(event_id="EVT-WEEKLY-CLOSE-1", outcome="below_195", date="2026-11-21"),
            Observation(event_id="EVT-WEEKLY-CLOSE-2", outcome="below_195", date="2026-11-28"),
        ],
        StartingBook.FLAT,
        "T",
    )
    assert snap.thesis.position.value == "none"
    assert snap.thesis.position_action == "NONE"
    assert snap.thesis.scenario == "BASE"
    assert any("flat book" in n.lower() or "ignores" in n.lower() for n in snap.thesis.notes)


def test_stop_exits_long_book(model):
    snap = run_tape(
        model,
        [
            Observation(event_id="EVT-WEEKLY-CLOSE-1", outcome="below_195", date="2026-11-21"),
            Observation(event_id="EVT-WEEKLY-CLOSE-2", outcome="below_195", date="2026-11-28"),
        ],
        StartingBook.LONG,
        "T",
    )
    assert snap.thesis.position.value == "none"
    assert snap.thesis.position_action == "STOP_EXIT"


def test_kill_switch_dominates_confirmation(model):
    snap = run_tape(
        model,
        [
            Observation(
                event_id="EVT-FY2028-COMMENTARY",
                outcome="confirmation_near_70_with_backlog",
                date="2026-11-17",
                adjudicated=True,
            ),
            Observation(
                event_id="EVT-KILL-TAIWAN",
                outcome="fired",
                date="2027-03-01",
                adjudicated=True,
            ),
        ],
        StartingBook.LONG,
        "T",
    )
    assert snap.thesis.kill_switch_up is True
    assert "CTR-KILL-TAIWAN" in snap.thesis.kill_switch_ids
    assert snap.thesis.scenario == "BEAR"
    assert snap.thesis.rating == "Sell"
    assert snap.thesis.position.value == "none"
    last = snap.ledger[-1]
    assert last.book_action == "EXIT"
    assert any(c["dominates"] for c in last.contracts_gated)


def test_human_observable_does_not_fire_until_adjudicated(model):
    bound_only = run_tape(
        model,
        [
            Observation(
                event_id="EVT-SUPPLY-LANGUAGE",
                outcome="language_disappears",
                adjudicated=False,
            )
        ],
        StartingBook.FLAT,
        "T",
    )
    assert bound_only.ledger[0].skipped is True
    assert bound_only.ledger[0].skip_reason == "AWAITING_HUMAN_OBSERVATION"
    assert bound_only.factor_tilts["F-19"] == "unresolved"

    adjudicated = run_tape(
        model,
        [
            Observation(
                event_id="EVT-SUPPLY-LANGUAGE",
                outcome="language_disappears",
                adjudicated=True,
            )
        ],
        StartingBook.FLAT,
        "T",
    )
    assert adjudicated.ledger[0].skipped is False
    assert adjudicated.factor_tilts["F-19"] == "negative"
    assert adjudicated.thesis.scenario == "BASE"


def test_identical_tapes_hash_identically(model):
    tape = [
        Observation(event_id="EVT-CAPEX-MSFT", outcome="flat_or_down", date="2027-01-28"),
        Observation(event_id="EVT-CAPEX-AMZN", outcome="flat_or_down", date="2027-01-30"),
    ]
    a = run_tape(model, tape, StartingBook.FLAT, "A")
    b = run_tape(model, tape, StartingBook.FLAT, "A")
    assert a.tape_hash == b.tape_hash
    assert a.tape_hash == tape_hash(a.bindings, StartingBook.FLAT, a.thesis, a.ledger)


def test_factor_weights_never_trade(model):
    snap = run_tape(
        model,
        [
            Observation(event_id="EVT-CAPEX-MSFT", outcome="flat_or_down", date="2027-01-28"),
        ],
        StartingBook.FLAT,
        "T",
    )
    weight_sum = sum(
        f.theme_weight or 0
        for f in model.factors
        if snap.factor_tilts.get(f.id) in {"negative", "threatened"}
    )
    assert weight_sum > 0
    assert snap.thesis.position_action == "NONE"
    assert snap.thesis.scenario == "BASE"


def test_print_is_not_the_catalyst(model):
    snap = run_tape(
        model,
        [Observation(event_id="EVT-Q3-PRINT", outcome="in_line", date="2026-11-17")],
        StartingBook.FLAT,
        "T",
    )
    assert snap.thesis.scenario == "BASE"
    assert snap.thesis.rating == "Hold"
    assert snap.factor_tilts["F-FY2028"] == "neutral"
