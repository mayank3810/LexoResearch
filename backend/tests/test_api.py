from fastapi.testclient import TestClient

from app.constants import SIMULATED_BANNER
from app.main import app

client = TestClient(app)


def test_health_and_as_of():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["banner"] == SIMULATED_BANNER
    as_of = client.get("/as-of")
    body = as_of.json()
    assert body["price"] == 230.36
    assert body["rating"] == "Hold"
    assert body["position"] == "no position initiated"
    assert body["document"] == "NVDA-memo.pdf"
    assert body["page"] == 2
    assert body["fy2028"]["document"] == "NVDA-memo.pdf"
    assert body["fy2028"]["page"] == 3


def test_world_a_default_is_confirmation():
    body = client.get("/thesis-state", params={"world": "A"}).json()
    assert body["thesis"]["scenario"] == "BULL"
    assert body["thesis"]["rating"] == "Buy"
    assert body["thesis"]["override_active"] is False


def test_world_b_default_is_two_of_four_third_party():
    body = client.get("/worlds/B").json()
    assert body["thesis"]["scenario"] == "BEAR"
    assert any(step["third_party"] for step in body["ledger"])
    assert any(
        any(c["contract_id"] == "CTR-TWO-OF-FOUR" for c in step["contracts_gated"])
        for step in body["ledger"]
    )


def test_replay_hash_stable():
    first = client.post("/worlds/A/replay").json()
    second = client.post("/worlds/A/replay").json()
    assert first["tape_hash"] == second["tape_hash"]
    assert first["hashes_match"] is True


def test_world_model_and_calendar():
    graph = client.get("/world-model", params={"world": "B"}).json()
    assert len(graph["factors"]) >= 28
    assert graph["lit_node_ids"]
    cal = client.get("/calendar").json()
    assert any(item["event_id"] == "EVT-CAPEX-MSFT" for item in cal["items"])


def test_adjudicate_human_node():
    before = client.get("/worlds/B").json()
    assert any(n["event_id"] == "EVT-SUPPLY-LANGUAGE" for n in before["awaiting_human"])
    after = client.post(
        "/worlds/B/adjudicate",
        json={"event_id": "EVT-SUPPLY-LANGUAGE", "outcome": "language_disappears"},
    ).json()
    assert after["factor_tilts"]["F-19"] == "negative"
    assert not any(
        n["event_id"] == "EVT-SUPPLY-LANGUAGE" for n in after["awaiting_human"]
    )


def test_claim_click_through():
    body = client.get("/claims/CLM-005").json()
    assert body["page"] == 47
    assert "Buy" in body["quote"]


def test_asof_thesis_is_the_memo_conclusion():
    body = client.get("/thesis-state", params={"world": "ASOF"}).json()
    assert body["thesis"]["scenario"] == "BASE"
    assert body["thesis"]["rating"] == "Hold"
    assert body["thesis"]["position"] == "none"
    assert body["thesis"]["override_active"] is True


def test_starting_book_parameter():
    client.post("/worlds/B/starting-book", json={"starting_book": "long"})
    body = client.get("/worlds/B").json()
    assert body["starting_book"] == "long"
    assert body["thesis"]["position_action"] == "EXIT"


def test_client_tape_does_not_need_server_memory():
    seed = client.get("/worlds/A").json()
    after = client.post(
        "/worlds/A/bind",
        json={
            "event_id": "EVT-CAPEX-MSFT",
            "outcome": "flat_or_down",
            "bindings": seed["bindings"],
            "starting_book": seed["starting_book"],
        },
    ).json()
    assert after["thesis"]["scenario"] == "BULL"
    assert any(b["event_id"] == "EVT-CAPEX-MSFT" for b in after["bindings"])
