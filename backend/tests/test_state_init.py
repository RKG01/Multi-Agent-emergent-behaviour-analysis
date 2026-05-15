from app.orchestration.state import init_fraud_state
from app.schemas.claim import AnalyzeClaimRequest, ClaimantInput, IncidentInput, PolicyInput


def test_init_fraud_state_defaults() -> None:
    claim = AnalyzeClaimRequest(
        claim_id="C-1",
        claimant=ClaimantInput(name="Test", history_count=0),
        policy=PolicyInput(policy_id="P-1", coverage_limit=1000),
        incident=IncidentInput(date="2026-05-01", type="collision"),
        amount=100.0,
        documents=[],
    )
    state = init_fraud_state(claim)
    assert state["request_id"]
    assert state["conflicts"] == []
    assert state["redundancy"] is None
    assert state["emergence"] is None
    assert state["metrics"] is None
