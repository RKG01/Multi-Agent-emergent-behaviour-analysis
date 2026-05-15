import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from app.db.sqlite import get_connection


logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_claim(request_id: str, claim: object, status: str) -> None:
    payload = _serialize(claim)
    _execute(
        """
        INSERT INTO claims (request_id, claim_id, received_at, claim_json, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            request_id,
            payload.get("claim_id") if isinstance(payload, dict) else None,
            utc_now_iso(),
            _json_dumps(payload),
            status,
        ),
    )


def log_agent_result(
    request_id: str,
    agent_name: str,
    ts_start: str,
    ts_end: str,
    status: str,
    latency_ms: int,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    error_payload: Optional[Dict[str, Any]],
) -> None:
    _execute(
        """
        INSERT INTO agent_logs (
            request_id, agent_name, ts_start, ts_end, status,
            latency_ms, input_hash, output_json, errors
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            agent_name,
            ts_start,
            ts_end,
            status,
            latency_ms,
            _hash_json(input_payload),
            _json_dumps(output_payload),
            _json_dumps(error_payload),
        ),
    )


def log_trace_event(request_id: str, event: Dict[str, Any]) -> None:
    _execute(
        """
        INSERT INTO trace_events (request_id, ts, node, event, details_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            request_id,
            event.get("ts"),
            event.get("node"),
            event.get("event"),
            _json_dumps(event.get("details", {})),
        ),
    )


def log_conflicts(request_id: str, conflicts: Iterable[object]) -> None:
    rows = []
    for record in conflicts:
        payload = _serialize(record)
        if not isinstance(payload, dict):
            continue
        pair = payload.get("pair", [None, None])
        rows.append(
            (
                request_id,
                pair[0],
                pair[1],
                payload.get("field"),
                payload.get("severity"),
                payload.get("description"),
            )
        )

    if not rows:
        return

    _executemany(
        """
        INSERT INTO conflict_logs (request_id, agent_a, agent_b, field, severity, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def log_metrics(request_id: str, metrics: object) -> None:
    payload = _serialize(metrics)
    if not isinstance(payload, dict):
        return

    _execute(
        """
        INSERT INTO metrics (
            request_id, coordination_score, conflict_rate, redundancy_score,
            loop_risk, latency_ms, model_calls, token_usage_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            payload.get("coordination_score"),
            payload.get("conflict_rate"),
            payload.get("redundancy_score"),
            payload.get("loop_risk"),
            payload.get("latency_ms"),
            payload.get("model_calls"),
            _json_dumps(payload.get("token_usage")),
        ),
    )


def log_emergence_event(request_id: str, event: Dict[str, Any]) -> None:
    _execute(
        """
        INSERT INTO emergence_events (request_id, ts, event_type, severity, details_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            request_id,
            utc_now_iso(),
            event.get("event_type"),
            event.get("severity"),
            _json_dumps(event.get("details", {})),
        ),
    )


def _execute(query: str, params: tuple) -> None:
    try:
        conn = get_connection()
        try:
            conn.execute(query, params)
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("Logging failed: %s", exc)


def _executemany(query: str, rows: Iterable[tuple]) -> None:
    try:
        conn = get_connection()
        try:
            conn.executemany(query, rows)
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("Logging failed: %s", exc)


def _serialize(data: object) -> Any:
    if data is None:
        return None
    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")
    if isinstance(data, (dict, list, str, int, float, bool)):
        return data
    return str(data)


def _json_dumps(data: Any) -> Optional[str]:
    if data is None:
        return None
    return json.dumps(data, separators=(",", ":"), ensure_ascii=True, default=str)


def _hash_json(data: Any) -> str:
    raw = _json_dumps(data) or ""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
