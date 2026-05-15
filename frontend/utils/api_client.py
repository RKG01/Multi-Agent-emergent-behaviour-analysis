from typing import Any, Dict, List, Optional, Tuple

import requests


def analyze_claim(base_url: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    return _request_json("post", f"{base_url}/analyze-claim", json=payload)


def fetch_logs(
    base_url: str,
    request_id: Optional[str],
    agent_name: Optional[str],
    limit: int,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    params: Dict[str, Any] = {"limit": limit}
    if request_id:
        params["request_id"] = request_id
    if agent_name:
        params["agent_name"] = agent_name

    return _request_json("get", f"{base_url}/logs", params=params)


def fetch_metrics(
    base_url: str,
    request_id: Optional[str],
    limit: int,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    params: Dict[str, Any] = {"limit": limit}
    if request_id:
        params["request_id"] = request_id

    return _request_json("get", f"{base_url}/metrics", params=params)


def health_check(base_url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    return _request_json("get", f"{base_url}/health")


def _request_json(
    method: str,
    url: str,
    **kwargs: Any,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, f"Request failed: {exc}"
    except ValueError:
        return None, "Invalid JSON response"
