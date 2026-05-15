from typing import Dict, List

from app.schemas.agent_report import AgentReport, EvidenceItem, RedundancySummary


def analyze_redundancy(reports: Dict[str, AgentReport]) -> RedundancySummary:
    evidence_sets: Dict[str, set[str]] = {}
    evidence_lookup: Dict[str, EvidenceItem] = {}
    evidence_counts: Dict[str, int] = {}

    for name, report in reports.items():
        keys: set[str] = set()
        for item in report.evidence:
            key = _evidence_key(item)
            keys.add(key)
            evidence_lookup.setdefault(key, item)
            evidence_counts[key] = evidence_counts.get(key, 0) + 1
        evidence_sets[name] = keys

    overlap_score = _average_jaccard(list(evidence_sets.values()))
    duplicated = [
        evidence_lookup[key]
        for key, count in evidence_counts.items()
        if count > 1
    ]

    return RedundancySummary(
        overlap_score=overlap_score,
        duplicated_evidence=duplicated,
    )


def _evidence_key(item: EvidenceItem) -> str:
    return f"{item.id}:{item.source_ref}"


def _average_jaccard(sets: List[set[str]]) -> float:
    # Pairwise Jaccard overlap across evidence sets.
    if len(sets) < 2:
        return 0.0

    total = 0.0
    count = 0
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            a = sets[i]
            b = sets[j]
            union = a | b
            score = len(a & b) / len(union) if union else 0.0
            total += score
            count += 1

    return total / count if count else 0.0
