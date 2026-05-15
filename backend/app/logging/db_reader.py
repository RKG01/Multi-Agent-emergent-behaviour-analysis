import json
from typing import Any, Dict, List, Optional

from app.db.sqlite import get_connection


def fetch_agent_logs(
    request_id: Optional[str],
    agent_name: Optional[str],
    limit: int,
) -> List[Dict[str, Any]]:
    query = (
        "SELECT id, request_id, agent_name, ts_start, ts_end, status, latency_ms, "
        "input_hash, output_json, errors FROM agent_logs"
    )
    params: List[Any] = []
    where = []

    if request_id:
        where.append("request_id = ?")
        params.append(request_id)
    if agent_name:
        where.append("agent_name = ?")
        params.append(agent_name)

    if where:
        query += " WHERE " + " AND ".join(where)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = _fetch_rows(query, params)
    return [
        {
            **row,
            "output_json": _parse_json(row.get("output_json")),
            "errors": _parse_json(row.get("errors")),
        }
        for row in rows
    ]


def fetch_metrics(request_id: Optional[str], limit: int) -> List[Dict[str, Any]]:
    query = (
        "SELECT id, request_id, coordination_score, conflict_rate, "
        "redundancy_score, loop_risk, latency_ms, model_calls, token_usage_json "
        "FROM metrics"
    )
    params: List[Any] = []
    if request_id:
        query += " WHERE request_id = ?"
        params.append(request_id)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = _fetch_rows(query, params)
    return [
        {
            **row,
            "token_usage": _parse_json(row.get("token_usage_json")) or {},
        }
        for row in rows
    ]


def _fetch_rows(query: str, params: List[Any]) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [dict(row) for row in rows]


def _parse_json(value: Optional[str]) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None
