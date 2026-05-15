from typing import Dict, List

from app.schemas.agent_report import AgentReport, ConflictRecord


def analyze_conflicts(reports: Dict[str, AgentReport]) -> List[ConflictRecord]:
    # MVP heuristic: conflict exists when labels diverge.
    names = list(reports.keys())
    conflicts: List[ConflictRecord] = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name_a = names[i]
            name_b = names[j]
            report_a = reports[name_a]
            report_b = reports[name_b]

            if report_a.decision_label == report_b.decision_label:
                continue

            score_gap = abs(report_a.fraud_risk - report_b.fraud_risk)
            conflicts.append(
                ConflictRecord(
                    pair=[name_a, name_b],
                    field="decision_label",
                    severity=_severity_from_gap(score_gap),
                    description=(
                        f"Label mismatch: {name_a}={report_a.decision_label}, "
                        f"{name_b}={report_b.decision_label}"
                    ),
                )
            )

    return conflicts


def _severity_from_gap(score_gap: float) -> str:
    if score_gap >= 0.4:
        return "high"
    if score_gap >= 0.2:
        return "medium"
    return "low"
