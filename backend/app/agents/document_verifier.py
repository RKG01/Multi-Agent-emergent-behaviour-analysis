import json
import logging
import time
from typing import Dict

from app.agents.prompts import DOCUMENT_VERIFIER_SYSTEM, DOCUMENT_VERIFIER_USER
from app.logging.db_logger import log_agent_result, log_trace_event, utc_now_iso
from app.orchestration.state import FraudState, append_trace, increment_retry, new_trace_event
from app.schemas.agent_report import AgentError, AgentReport
from app.services.gemini_client import GeminiClient


logger = logging.getLogger(__name__)


def run_document_verifier(state: FraudState) -> Dict[str, object]:
    claim = state.get("claim")
    if claim is None:
        raise ValueError("Missing claim input")

    request_id = state.get("request_id", "unknown")
    start_ts = utc_now_iso()
    start_perf = time.perf_counter()
    input_payload = _log_input_payload(claim)

    if not claim.documents:
        # Short-circuit when there are no documents to verify.
        report = AgentReport(
            agent_name="DocumentVerifier",
            decision_label="medium",
            fraud_risk=0.4,
            confidence=0.1,
            evidence=[],
            flags=["missing_documents"],
            uncertainties=["No documents were provided for verification."],
        )
        return _wrap_result(state, report, error_flag=False, log_meta=_log_meta(
            request_id,
            start_ts,
            start_perf,
            input_payload,
        ))

    schema_json = json.dumps(AgentReport.model_json_schema(), separators=(",", ":"))
    # Keep payloads minimal to reduce token usage.
    claim_json = json.dumps(
        {
            "claim_id": claim.claim_id,
            "incident": claim.incident.model_dump(mode="json"),
            "amount": claim.amount,
        },
        separators=(",", ":"),
    )
    documents_json = json.dumps(
        [doc.model_dump(mode="json") for doc in claim.documents],
        separators=(",", ":"),
    )

    prompt = DOCUMENT_VERIFIER_USER.format(
        claim_json=claim_json,
        documents_json=documents_json,
        schema_json=schema_json,
    )

    try:
        client = GeminiClient()
        report = client.generate_json(DOCUMENT_VERIFIER_SYSTEM, prompt, AgentReport)
        report = _normalize_report(report)
        error_flag = False
    except Exception as exc:
        logger.exception("Document verifier failed")
        report = AgentReport(
            agent_name="DocumentVerifier",
            decision_label="medium",
            fraud_risk=0.5,
            confidence=0.0,
            evidence=[],
            flags=["agent_error"],
            uncertainties=[str(exc)],
            errors=AgentError(code="gemini_error", message=str(exc)),
        )
        error_flag = True

    return _wrap_result(
        state,
        report,
        error_flag,
        log_meta=_log_meta(request_id, start_ts, start_perf, input_payload),
    )


def _wrap_result(
    state: FraudState,
    report: AgentReport,
    error_flag: bool,
    log_meta: Dict[str, object],
) -> Dict[str, object]:
    _log_agent(report, error_flag, log_meta)

    reports = dict(state.get("agent_reports", {}))
    reports[report.agent_name] = report

    event = new_trace_event(
        node="document_verifier",
        event="completed",
        details={"decision_label": report.decision_label, "error": error_flag},
    )
    trace = append_trace(state, event)
    log_trace_event(log_meta["request_id"], event)

    retries = increment_retry(state, "document_verifier")

    return {"agent_reports": reports, "trace": trace, "retry_counters": retries}


def _normalize_report(report: AgentReport) -> AgentReport:
    if report.agent_name != "DocumentVerifier":
        report.agent_name = "DocumentVerifier"
    return report


def _log_input_payload(claim) -> Dict[str, object]:
    return {
        "claim_id": claim.claim_id,
        "document_ids": [doc.document_id for doc in claim.documents],
        "document_count": len(claim.documents),
    }


def _log_meta(
    request_id: str,
    start_ts: str,
    start_perf: float,
    input_payload: Dict[str, object],
) -> Dict[str, object]:
    return {
        "request_id": request_id,
        "start_ts": start_ts,
        "start_perf": start_perf,
        "input_payload": input_payload,
    }


def _log_agent(report: AgentReport, error_flag: bool, log_meta: Dict[str, object]) -> None:
    end_ts = utc_now_iso()
    latency_ms = int((time.perf_counter() - log_meta["start_perf"]) * 1000)
    log_agent_result(
        request_id=log_meta["request_id"],
        agent_name=report.agent_name,
        ts_start=log_meta["start_ts"],
        ts_end=end_ts,
        status="error" if error_flag else "ok",
        latency_ms=latency_ms,
        input_payload=log_meta["input_payload"],
        output_payload=report.model_dump(mode="json"),
        error_payload=report.errors.model_dump(mode="json") if report.errors else None,
    )
