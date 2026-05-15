import json
import logging
import time
from typing import Dict

from app.agents.prompts import ANOMALY_DETECTOR_SYSTEM, ANOMALY_DETECTOR_USER
from app.logging.db_logger import log_agent_result, log_trace_event, utc_now_iso
from app.orchestration.state import FraudState, append_trace, increment_retry, new_trace_event
from app.schemas.agent_report import AgentError, AgentReport
from app.services.gemini_client import GeminiClient


logger = logging.getLogger(__name__)


def run_anomaly_detector(state: FraudState) -> Dict[str, object]:
    claim = state.get("claim")
    if claim is None:
        raise ValueError("Missing claim input")

    request_id = state.get("request_id", "unknown")
    start_ts = utc_now_iso()
    start_perf = time.perf_counter()
    input_payload = _log_input_payload(claim)

    schema_json = json.dumps(AgentReport.model_json_schema(), separators=(",", ":"))
    features_json = json.dumps(_feature_payload(claim), separators=(",", ":"))
    baselines_json = json.dumps(_baseline_payload(claim), separators=(",", ":"))

    prompt = ANOMALY_DETECTOR_USER.format(
        features_json=features_json,
        baseline_json=baselines_json,
        schema_json=schema_json,
    )

    try:
        client = GeminiClient()
        report = client.generate_json(ANOMALY_DETECTOR_SYSTEM, prompt, AgentReport)
        report = _normalize_report(report)
        error_flag = False
    except Exception as exc:
        logger.exception("Anomaly detector failed")
        report = AgentReport(
            agent_name="AnomalyDetector",
            decision_label="medium",
            fraud_risk=0.5,
            confidence=0.0,
            evidence=[],
            flags=["agent_error"],
            uncertainties=[str(exc)],
            errors=AgentError(code="gemini_error", message=str(exc)),
        )
        error_flag = True

    end_ts = utc_now_iso()
    latency_ms = int((time.perf_counter() - start_perf) * 1000)
    log_agent_result(
        request_id=request_id,
        agent_name=report.agent_name,
        ts_start=start_ts,
        ts_end=end_ts,
        status="error" if error_flag else "ok",
        latency_ms=latency_ms,
        input_payload=input_payload,
        output_payload=report.model_dump(mode="json"),
        error_payload=report.errors.model_dump(mode="json") if report.errors else None,
    )

    return _wrap_result(state, report, error_flag, request_id)


def _feature_payload(claim) -> Dict[str, object]:
    return {
        "amount": claim.amount,
        "coverage_limit": claim.policy.coverage_limit,
        "deductible": claim.policy.deductible,
        "incident_type": claim.incident.type,
    }


def _baseline_payload(claim) -> Dict[str, object]:
    coverage_limit = claim.policy.coverage_limit
    utilization = None
    if coverage_limit:
        utilization = round(claim.amount / coverage_limit, 4)

    # Simple baseline metrics for MVP; replace with data-driven baselines later.
    return {"coverage_utilization": utilization}


def _wrap_result(
    state: FraudState,
    report: AgentReport,
    error_flag: bool,
    request_id: str,
) -> Dict[str, object]:
    reports = dict(state.get("agent_reports", {}))
    reports[report.agent_name] = report

    event = new_trace_event(
        node="anomaly_detector",
        event="completed",
        details={"decision_label": report.decision_label, "error": error_flag},
    )
    trace = append_trace(state, event)
    log_trace_event(request_id, event)

    retries = increment_retry(state, "anomaly_detector")

    return {"agent_reports": reports, "trace": trace, "retry_counters": retries}


def _normalize_report(report: AgentReport) -> AgentReport:
    if report.agent_name != "AnomalyDetector":
        report.agent_name = "AnomalyDetector"
    return report


def _log_input_payload(claim) -> Dict[str, object]:
    return {
        "claim_id": claim.claim_id,
        "amount": claim.amount,
        "coverage_limit": claim.policy.coverage_limit,
    }
