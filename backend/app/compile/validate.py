from __future__ import annotations

from app.models.ir import KNOWN_DOCUMENTS, ProvenanceKind, WorldModel


class CompileError(ValueError):
    pass


def validate_world_model(model: WorldModel) -> None:
    errors: list[str] = []
    claim_ids = {c.id for c in model.claims}
    factor_ids = {f.id for f in model.factors}
    event_ids = {e.id for e in model.events}
    policy_ids = {p.id for p in model.policies}

    claims = {c.id: c for c in model.claims}

    def _check_source(label: str, document: str | None, page: int | None, claim_id: str | None = None) -> None:
        if not document or page is None:
            errors.append(f"{label}: missing PDF document/page")
            return
        if document not in KNOWN_DOCUMENTS:
            errors.append(f"{label}: unknown document {document}")
        if page < 1:
            errors.append(f"{label}: invalid page {page}")
        if claim_id:
            claim = claims.get(claim_id)
            if claim and (document != claim.document or page != claim.page):
                errors.append(
                    f"{label}: document/page {document} p.{page} does not match {claim_id}"
                )

    _check_source("as_of", model.as_of.document, model.as_of.page)
    _check_source(
        "as_of.fy2028",
        model.as_of.fy2028.document,
        model.as_of.fy2028.page,
        model.as_of.fy2028.claim_id,
    )
    for claim in model.claims:
        _check_source(claim.id, claim.document, claim.page)
    for factor in model.factors:
        _check_source(factor.id, factor.document, factor.page)
    for event in model.events:
        _check_source(event.id, event.document, event.page)
    for ticker in model.tickers:
        _check_source(ticker.symbol, ticker.document, ticker.page)

    for rel in model.relationships:
        if rel.event_id not in event_ids:
            errors.append(f"{rel.id}: unknown event {rel.event_id}")
        if rel.factor_id not in factor_ids:
            errors.append(f"{rel.id}: unknown factor {rel.factor_id}")
        if rel.provenance == ProvenanceKind.SOURCE_BACKED:
            if not rel.claim_id:
                errors.append(f"{rel.id}: source-backed edge missing claim")
            elif rel.claim_id not in claim_ids:
                errors.append(f"{rel.id}: unknown claim {rel.claim_id}")
            _check_source(rel.id, rel.document, rel.page, rel.claim_id)
        if rel.provenance == ProvenanceKind.OUR_POLICY:
            if not rel.policy_id:
                errors.append(f"{rel.id}: our_policy edge unlabeled")
            elif rel.policy_id not in policy_ids:
                errors.append(f"{rel.id}: unknown policy {rel.policy_id}")
        if rel.provenance == ProvenanceKind.OURS_NO_CLAIM:
            errors.append(f"{rel.id}: ours_no_claim is forbidden in this compile")

    for contract in model.contracts:
        if not contract.metric or not contract.threshold or not contract.timeframe:
            errors.append(f"{contract.id}: hard contract missing metric/threshold/timeframe")
        if not contract.claim_id or contract.claim_id not in claim_ids:
            errors.append(f"{contract.id}: hard contract must cite a claim")
        for factor_id in contract.related_factor_ids:
            if factor_id not in factor_ids:
                errors.append(f"{contract.id}: unknown related factor {factor_id}")
        for event_id in contract.related_event_ids:
            if event_id not in event_ids:
                errors.append(f"{contract.id}: unknown related event {event_id}")
        if contract.provenance == ProvenanceKind.OURS_NO_CLAIM:
            errors.append(f"{contract.id}: unlabeled ours_no_claim contract")
        _check_source(contract.id, contract.document, contract.page, contract.claim_id)

    for policy in model.policies:
        if policy.provenance not in {ProvenanceKind.OUR_POLICY}:
            errors.append(f"{policy.id}: policy must be painted our_policy")
        _check_source(policy.id, policy.document, policy.page, policy.claim_id)

    for exposure in model.exposures:
        if exposure.factor_id not in factor_ids:
            errors.append(f"{exposure.id}: unknown factor {exposure.factor_id}")
        if exposure.claim_id and exposure.claim_id not in claim_ids:
            errors.append(f"{exposure.id}: unknown claim {exposure.claim_id}")
        _check_source(exposure.id, exposure.document, exposure.page, exposure.claim_id)

    for scenario in model.scenarios:
        if scenario.claim_id not in claim_ids:
            errors.append(f"{scenario.id}: unknown claim {scenario.claim_id}")
        _check_source(scenario.id, scenario.document, scenario.page, scenario.claim_id)

    for item in model.calendar:
        if item.event_id not in event_ids:
            errors.append(f"{item.id}: unknown event {item.event_id}")
        else:
            event = next(e for e in model.events if e.id == item.event_id)
            _check_source(item.id, item.document, item.page)
            if item.document != event.document or item.page != event.page:
                errors.append(
                    f"{item.id}: document/page does not match event {item.event_id}"
                )

    if model.as_of.fy2028.claim_id not in claim_ids:
        errors.append("as_of FY2028 disagreement missing claim")

    if errors:
        raise CompileError("compile errors:\n" + "\n".join(errors))
