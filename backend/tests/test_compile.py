from app.compile.loader import load_world_model
from app.compile.validate import CompileError, validate_world_model
from app.models.ir import ProvenanceKind, Relationship


def test_fixtures_load_and_validate():
    model = load_world_model()
    validate_world_model(model)
    assert model.as_of.price == 230.36
    assert model.as_of.rating == "Hold"
    assert model.as_of.conviction == "Low"
    assert len(model.factors) >= 28
    assert any(f.id == "F-FY2028" for f in model.factors)


def test_source_backed_edges_cite_claims(model):
    claim_ids = {c.id for c in model.claims}
    for rel in model.relationships:
        if rel.provenance == ProvenanceKind.SOURCE_BACKED:
            assert rel.claim_id in claim_ids


def test_hard_contracts_have_metric_threshold_timeframe_and_claim(model):
    claim_ids = {c.id for c in model.claims}
    for contract in model.contracts:
        assert contract.metric
        assert contract.threshold
        assert contract.timeframe
        assert contract.claim_id in claim_ids


def test_extracted_objects_cite_pdf_and_page(model):
    assert model.as_of.document == "NVDA-memo.pdf"
    assert model.as_of.page == 2
    assert model.as_of.fy2028.document == "NVDA-memo.pdf"
    assert model.as_of.fy2028.page == 3
    for collection in (
        model.claims,
        model.factors,
        model.events,
        model.relationships,
        model.exposures,
        model.scenarios,
        model.contracts,
        model.policies,
        model.calendar,
        model.tickers,
    ):
        for item in collection:
            assert item.document.endswith(".pdf")
            assert item.page >= 1


def test_policies_are_painted(model):
    for policy in model.policies:
        assert policy.provenance == ProvenanceKind.OUR_POLICY


def test_compile_rejects_source_backed_edge_without_claim(model):
    broken = model.model_copy(deep=True)
    broken.relationships.append(
        Relationship(
            id="REL-BAD",
            event_id="EVT-CAPEX-MSFT",
            outcome="flat_or_down",
            factor_id="F-11",
            direction="negative",
            provenance=ProvenanceKind.SOURCE_BACKED,
            claim_id=None,
        )
    )
    try:
        validate_world_model(broken)
        raise AssertionError("expected compile error")
    except CompileError as exc:
        assert "REL-BAD" in str(exc)
