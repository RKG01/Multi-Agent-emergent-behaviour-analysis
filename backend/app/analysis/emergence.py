from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from app.schemas.agent_report import (
    AgentReport,
    ConflictRecord,
    EmergenceSummary,
    MetricsSnapshot,
    RedundancySummary,
)


POSITIVE_COORDINATION_THRESHOLD = 0.8
NEGATIVE_CONFLICT_THRESHOLD = 0.5
NEGATIVE_REDUNDANCY_THRESHOLD = 0.6
NEGATIVE_LOOP_THRESHOLD = 0.3


def analyze_emergence(
    reports: Dict[str, AgentReport],
    conflicts: List[ConflictRecord],
    redundancy: Optional[RedundancySummary],
    retry_counters: Dict[str, int],
    trace: Iterable[Dict[str, object]],
) -> Tuple[EmergenceSummary, MetricsSnapshot, List[Dict[str, object]]]:
    coordination_score = _coordination_score(reports)
    conflict_rate = _conflict_rate(conflicts, len(reports))
    redundancy_score = redundancy.overlap_score if redundancy else 0.0
    loop_risk = _loop_risk(retry_counters)

    emergence = EmergenceSummary(
        coordination_score=coordination_score,
        conflict_rate=conflict_rate,
        redundancy_score=redundancy_score,
        loop_risk=loop_risk,
    )

    metrics = MetricsSnapshot(
        latency_ms=_estimate_latency_ms(trace),
        model_calls=len(reports),
        token_usage={},
    )

    events = _build_emergence_events(emergence)
    return emergence, metrics, events


def _coordination_score(reports: Dict[str, AgentReport]) -> float:
    if not reports:
        return 0.0
    labels = [report.decision_label for report in reports.values()]
    counts = Counter(labels)
    top = max(counts.values())
    return round(top / len(labels), 4)


def _conflict_rate(conflicts: List[ConflictRecord], agent_count: int) -> float:
    if agent_count < 2:
        return 0.0
    pairs = agent_count * (agent_count - 1) / 2
    return round(len(conflicts) / pairs, 4)


def _loop_risk(retry_counters: Dict[str, int]) -> float:
    if not retry_counters:
        return 0.0
    max_retry = max(retry_counters.values())
    if max_retry <= 1:
        return 0.0
    return min(1.0, round((max_retry - 1) / 3, 4))


def _estimate_latency_ms(trace: Iterable[Dict[str, object]]) -> int:
    timestamps: List[datetime] = []
    for event in trace:
        ts = event.get("ts")
        if not isinstance(ts, str):
            continue
        try:
            timestamps.append(datetime.fromisoformat(ts))
        except ValueError:
            continue
    if len(timestamps) < 2:
        return 0
    delta = max(timestamps) - min(timestamps)
    return int(delta.total_seconds() * 1000)


def _build_emergence_events(summary: EmergenceSummary) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []

    if summary.coordination_score >= POSITIVE_COORDINATION_THRESHOLD:
        events.append(
            {
                "event_type": "positive_coordination",
                "severity": "low",
                "details": {"coordination_score": summary.coordination_score},
            }
        )

    if summary.conflict_rate >= NEGATIVE_CONFLICT_THRESHOLD:
        events.append(
            {
                "event_type": "high_conflict",
                "severity": "high",
                "details": {"conflict_rate": summary.conflict_rate},
            }
        )

    if summary.redundancy_score >= NEGATIVE_REDUNDANCY_THRESHOLD:
        events.append(
            {
                "event_type": "high_redundancy",
                "severity": "medium",
                "details": {"redundancy_score": summary.redundancy_score},
            }
        )

    if summary.loop_risk >= NEGATIVE_LOOP_THRESHOLD:
        events.append(
            {
                "event_type": "loop_risk",
                "severity": "medium",
                "details": {"loop_risk": summary.loop_risk},
            }
        )

    return events
