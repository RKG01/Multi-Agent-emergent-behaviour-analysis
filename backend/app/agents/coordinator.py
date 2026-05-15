import json
import logging
import time
from typing import Dict

from app.agents.prompts import COORDINATOR_SYSTEM, COORDINATOR_USER
from app.logging.db_logger import log_agent_result, log_trace_event, utc_now_iso
from app.orchestration.state import FraudState, append_trace, increment_retry, new_trace_event
from app.schemas.agent_report import FinalDecision
from app.services.gemini_client import GeminiClient


logger = logging.getLogger(__name__)


def run_coordinator(state: FraudState) -> Dict[str, object]:
    reports = state.get("agent_reports", {})
    conflicts = state.get("conflicts", [])
    redundancy = state.get("redundancy")

    request_id = state.get("request_id", "unknown")
    start_ts = utc_now_iso()
    start_perf = time.perf_counter()
    input_payload = _log_input_payload(reports, conflicts, redundancy)

    schema_json = json.dumps(FinalDecision.model_json_schema(), separators=(",", ":"))
    reports_json = json.dumps(
        {name: report.model_dump(mode="json") for name, report in reports.items()},
        separators=(",", ":"),
    )
    conflicts_json = json.dumps(
        [record.model_dump(mode="json") for record in conflicts],
        separators=(",", ":"),
    )
    redundancy_json = json.dumps(
        redundancy.model_dump(mode="json") if redundancy else {},
        separators=(",", ":"),
    )

    prompt = COORDINATOR_USER.format(
        reports_json=reports_json,
        conflicts_json=conflicts_json,
        redundancy_json=redundancy_json,
        schema_json=schema_json,
    )

    try:
        client = GeminiClient()
        decision = client.generate_json(COORDINATOR_SYSTEM, prompt, FinalDecision)
        error_flag = False
    except Exception as exc:
        logger.exception("Coordinator failed")
        # Fallback ensures the pipeline returns a decision.
        decision = _fallback_decision(reports)
        error_flag = True

    end_ts = utc_now_iso()
    latency_ms = int((time.perf_counter() - start_perf) * 1000)
    log_agent_result(
        request_id=request_id,
        agent_name="Coordinator",
        ts_start=start_ts,
        ts_end=end_ts,
        status="error" if error_flag else "ok",
        latency_ms=latency_ms,
        input_payload=input_payload,
        output_payload=decision.model_dump(mode="json"),
        error_payload=None,
    )

    event = new_trace_event(
        node="coordinator",
        event="completed",
        details={"final_label": decision.final_label, "error": error_flag},
    )
    trace = append_trace(state, event)
    log_trace_event(request_id, event)

    retries = increment_retry(state, "coordinator")

    return {"final_decision": decision, "trace": trace, "retry_counters": retries}


def _fallback_decision(reports: Dict[str, object]) -> FinalDecision:
    max_score = 0.5
    if reports:
        max_score = max(report.fraud_risk for report in reports.values())

    label = _label_from_score(max_score)
    return FinalDecision(
        final_label=label,
        final_score=max_score,
        rationale=["Fallback decision: coordinator unavailable."],
        dissenting_views=[],
    )


def _label_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _log_input_payload(reports, conflicts, redundancy) -> Dict[str, object]:
    return {
        "report_count": len(reports),
        "conflict_count": len(conflicts),
        "redundancy_overlap": redundancy.overlap_score if redundancy else None,
    }
