from app.analysis.redundancy import analyze_redundancy
from app.schemas.agent_report import AgentReport, EvidenceItem


def _report(name: str, evidence) -> AgentReport:
    return AgentReport(
        agent_name=name,
        decision_label="low",
        fraud_risk=0.1,
        confidence=0.9,
        evidence=evidence,
        flags=[],
        uncertainties=[],
    )


def test_redundancy_detects_overlap() -> None:
    shared = EvidenceItem(
        id="claim_id",
        type="field",
        summary="Claim id present.",
        source_ref="C-1",
    )
    reports = {
        "A": _report("A", [shared]),
        "B": _report("B", [shared]),
    }
    summary = analyze_redundancy(reports)
    assert summary.overlap_score > 0
    assert len(summary.duplicated_evidence) == 1
