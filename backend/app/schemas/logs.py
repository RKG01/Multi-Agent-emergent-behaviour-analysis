from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AgentLogEntry(BaseModel):
    id: int
    request_id: str
    agent_name: str
    ts_start: str
    ts_end: str
    status: str
    latency_ms: int
    input_hash: str
    output_json: Dict[str, Any] = Field(default_factory=dict)
    errors: Optional[Dict[str, Any]] = None


class MetricsEntry(BaseModel):
    id: int
    request_id: str
    coordination_score: Optional[float] = None
    conflict_rate: Optional[float] = None
    redundancy_score: Optional[float] = None
    loop_risk: Optional[float] = None
    latency_ms: Optional[int] = None
    model_calls: Optional[int] = None
    token_usage: Dict[str, int] = Field(default_factory=dict)
