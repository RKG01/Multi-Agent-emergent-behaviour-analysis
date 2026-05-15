from __future__ import annotations

from typing import Dict

from langgraph.graph import END, StateGraph

from app.agents.anomaly_detector import run_anomaly_detector
from app.agents.behavioral_analyzer import run_behavioral_analyzer
from app.agents.claim_validator import run_claim_validator
from app.agents.coordinator import run_coordinator
from app.agents.document_verifier import run_document_verifier
from app.analysis.conflicts import analyze_conflicts
from app.analysis.emergence import analyze_emergence
from app.analysis.redundancy import analyze_redundancy
from app.logging.db_logger import (
    log_claim,
    log_conflicts,
    log_emergence_event,
    log_metrics,
    log_trace_event,
)
from app.orchestration.state import (
    FraudState,
    append_trace,
    init_fraud_state,
    new_trace_event,
)
from app.schemas.agent_report import FinalDecision


def build_graph() -> StateGraph:
    graph = StateGraph(FraudState)

    graph.add_node("ingest_request", ingest_request)
    graph.add_node("claim_validator", run_claim_validator)
    graph.add_node("document_verifier", run_document_verifier)
    graph.add_node("behavioral_analyzer", run_behavioral_analyzer)
    graph.add_node("anomaly_detector", run_anomaly_detector)
    graph.add_node("conflict_analyzer", conflict_analyzer)
    graph.add_node("redundancy_analyzer", redundancy_analyzer)
    graph.add_node("emergence_analyzer", emergence_analyzer)
    graph.add_node("coordinator", run_coordinator)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("ingest_request")
    # MVP flow is sequential to keep execution deterministic.
    graph.add_edge("ingest_request", "claim_validator")
    graph.add_edge("claim_validator", "document_verifier")
    graph.add_edge("document_verifier", "behavioral_analyzer")
    graph.add_edge("behavioral_analyzer", "anomaly_detector")
    graph.add_edge("anomaly_detector", "conflict_analyzer")
    graph.add_edge("conflict_analyzer", "redundancy_analyzer")
    graph.add_edge("redundancy_analyzer", "emergence_analyzer")
    graph.add_edge("emergence_analyzer", "coordinator")
    graph.add_edge("coordinator", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


def ingest_request(state: FraudState) -> FraudState:
    claim = state.get("claim")
    if claim is None:
        raise ValueError("Missing claim input")
    new_state = init_fraud_state(claim)
    request_id = new_state.get("request_id", "unknown")
    # Log the claim and the initial trace entry for auditability.
    log_claim(request_id, claim, status="received")
    if new_state.get("trace"):
        log_trace_event(request_id, new_state["trace"][0])
    return new_state


def conflict_analyzer(state: FraudState) -> Dict[str, object]:
    reports = state.get("agent_reports", {})
    conflicts = analyze_conflicts(reports)
    request_id = state.get("request_id", "unknown")

    event = new_trace_event(
        node="conflict_analyzer",
        event="completed",
        details={"conflict_count": len(conflicts)},
    )
    trace = append_trace(state, event)
    log_trace_event(request_id, event)
    log_conflicts(request_id, conflicts)

    return {"conflicts": conflicts, "trace": trace}


def redundancy_analyzer(state: FraudState) -> Dict[str, object]:
    reports = state.get("agent_reports", {})
    redundancy = analyze_redundancy(reports)
    request_id = state.get("request_id", "unknown")

    event = new_trace_event(
        node="redundancy_analyzer",
        event="completed",
        details={"overlap_score": redundancy.overlap_score},
    )
    trace = append_trace(state, event)
    log_trace_event(request_id, event)

    return {"redundancy": redundancy, "trace": trace}


def emergence_analyzer(state: FraudState) -> Dict[str, object]:
    reports = state.get("agent_reports", {})
    conflicts = state.get("conflicts", [])
    redundancy = state.get("redundancy")
    retry_counters = state.get("retry_counters", {})
    request_id = state.get("request_id", "unknown")

    # Compute emergence metrics for dashboards and logging.
    emergence, metrics, events = analyze_emergence(
        reports=reports,
        conflicts=conflicts,
        redundancy=redundancy,
        retry_counters=retry_counters,
        trace=state.get("trace", []),
    )

    log_metrics(request_id, metrics)
    for event in events:
        log_emergence_event(request_id, event)

    event = new_trace_event(
        node="emergence_analyzer",
        event="completed",
        details={
            "coordination_score": emergence.coordination_score,
            "conflict_rate": emergence.conflict_rate,
        },
    )
    trace = append_trace(state, event)
    log_trace_event(request_id, event)

    return {"emergence": emergence, "metrics": metrics, "trace": trace}


def finalize(state: FraudState) -> Dict[str, object]:
    decision = state.get("final_decision")
    fallback_used = False
    request_id = state.get("request_id", "unknown")

    if decision is None:
        reports = state.get("agent_reports", {})
        report = reports.get("ClaimValidator")

        final_score = report.fraud_risk if report else 0.5
        final_label = _label_from_score(final_score)
        decision = FinalDecision(
            final_label=final_label,
            final_score=final_score,
            rationale=["Fallback decision: coordinator unavailable."],
            dissenting_views=[],
        )
        fallback_used = True

    event = new_trace_event(
        node="finalize",
        event="completed",
        details={"final_label": decision.final_label, "fallback": fallback_used},
    )
    trace = append_trace(state, event)
    log_trace_event(request_id, event)

    return {"final_decision": decision, "trace": trace}


def _label_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"
