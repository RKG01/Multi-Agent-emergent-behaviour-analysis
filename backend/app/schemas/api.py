from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.agent_report import (
    AgentReport,
    ConflictRecord,
    EmergenceSummary,
    MetricsSnapshot,
    RedundancySummary,
)


class AnalyzeClaimResponse(BaseModel):
    request_id: str
    claim_id: str
    final_label: str
    final_score: float
    agent_reports: Dict[str, AgentReport] = Field(default_factory=dict)
    conflicts: List[ConflictRecord] = Field(default_factory=list)
    redundancy: Optional[RedundancySummary] = None
    emergence: Optional[EmergenceSummary] = None
    metrics: Optional[MetricsSnapshot] = None
