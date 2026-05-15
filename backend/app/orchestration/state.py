from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, TypedDict

from app.schemas.agent_report import (
    AgentReport,
    ConflictRecord,
    EmergenceSummary,
    FinalDecision,
    MetricsSnapshot,
    RedundancySummary,
)
from app.schemas.claim import AnalyzeClaimRequest


class TraceEvent(TypedDict):
    ts: str
    node: str
    event: str
    details: Dict[str, object]


class FraudState(TypedDict, total=False):
    request_id: str
    claim: AnalyzeClaimRequest
    agent_reports: Dict[str, AgentReport]
    conflicts: List[ConflictRecord]
    redundancy: Optional[RedundancySummary]
    emergence: Optional[EmergenceSummary]
    metrics: Optional[MetricsSnapshot]
    final_decision: Optional[FinalDecision]
    retry_counters: Dict[str, int]
    trace: List[TraceEvent]


def init_fraud_state(claim: AnalyzeClaimRequest) -> FraudState:
    return {
        "request_id": str(uuid.uuid4()),
        "claim": claim,
        "agent_reports": {},
        "conflicts": [],
        "redundancy": None,
        "emergence": None,
        "metrics": None,
        "final_decision": None,
        "retry_counters": {},
        "trace": [
            new_trace_event(
                node="ingest_request",
                event="initialized",
                details={"claim_id": claim.claim_id},
            )
        ],
    }


def new_trace_event(node: str, event: str, details: Dict[str, object]) -> TraceEvent:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "node": node,
        "event": event,
        "details": details,
    }


def append_trace(state: FraudState, event: TraceEvent) -> List[TraceEvent]:
    trace = list(state.get("trace", []))
    trace.append(event)
    return trace


def increment_retry(state: FraudState, key: str) -> Dict[str, int]:
    counters = dict(state.get("retry_counters", {}))
    counters[key] = counters.get(key, 0) + 1
    return counters
