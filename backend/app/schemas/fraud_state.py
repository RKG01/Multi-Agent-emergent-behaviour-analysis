from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.agent_report import (
    AgentReport,
    ConflictRecord,
    EmergenceSummary,
    FinalDecision,
    MetricsSnapshot,
    RedundancySummary,
)
from app.schemas.claim import AnalyzeClaimRequest


class TraceEvent(BaseModel):
    ts: str
    node: str
    event: str
    details: Dict[str, object] = Field(default_factory=dict)


class FraudStateModel(BaseModel):
    request_id: str
    claim: AnalyzeClaimRequest
    agent_reports: Dict[str, AgentReport] = Field(default_factory=dict)
    conflicts: List[ConflictRecord] = Field(default_factory=list)
    redundancy: Optional[RedundancySummary] = None
    emergence: Optional[EmergenceSummary] = None
    metrics: Optional[MetricsSnapshot] = None
    final_decision: Optional[FinalDecision] = None
    retry_counters: Dict[str, int] = Field(default_factory=dict)
    trace: List[TraceEvent] = Field(default_factory=list)
