from app.analysis.conflicts import analyze_conflicts
from app.schemas.agent_report import AgentReport


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


def test_conflicts_when_labels_differ() -> None:
    reports = {
        "A": _report("A", "low", 0.1),
        "B": _report("B", "high", 0.9),
    }
    conflicts = analyze_conflicts(reports)
    assert len(conflicts) == 1
    record = conflicts[0]
    assert record.field == "decision_label"
    assert set(record.pair) == {"A", "B"}


def test_no_conflicts_when_labels_match() -> None:
    reports = {
        "A": _report("A", "low", 0.2),
        "B": _report("B", "low", 0.3),
    }
    conflicts = analyze_conflicts(reports)
    assert conflicts == []
