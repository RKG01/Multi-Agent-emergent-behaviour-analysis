from app.analysis.emergence import analyze_emergence
from app.schemas.agent_report import AgentReport, ConflictRecord, RedundancySummary


def _report(name: str, label: str, risk: float) -> AgentReport:
    return AgentReport(
        agent_name=name,
        decision_label=label,
        fraud_risk=risk,
        confidence=0.9,
        evidence=[],
        flags=[],
        uncertainties=[],
    )


def test_emergence_metrics_and_events() -> None:
    reports = {
        "A": _report("A", "high", 0.9),
        "B": _report("B", "low", 0.1),
    }
    conflicts = [
        ConflictRecord(
            pair=["A", "B"],
            field="decision_label",
            severity="high",
            description="Mismatch",
        )
    ]
    redundancy = RedundancySummary(overlap_score=0.7, duplicated_evidence=[])
    emergence, metrics, events = analyze_emergence(
        reports=reports,
        conflicts=conflicts,
        redundancy=redundancy,
        retry_counters={"claim_validator": 2},
        trace=[],
    )

    assert 0.0 <= emergence.coordination_score <= 1.0
    assert metrics.model_calls == len(reports)
    assert events
