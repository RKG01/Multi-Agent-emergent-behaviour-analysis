from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    id: str
    type: str
    summary: str
    source_ref: str


class AgentError(BaseModel):
    code: str
    message: str


class AgentReport(BaseModel):
    agent_name: str
    decision_label: str
    fraud_risk: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    errors: Optional[AgentError] = None


class ConflictRecord(BaseModel):
    pair: List[str]
    field: str
    severity: str
    description: str


class RedundancySummary(BaseModel):
    overlap_score: float = Field(ge=0, le=1)
    duplicated_evidence: List[EvidenceItem] = Field(default_factory=list)


class EmergenceSummary(BaseModel):
    coordination_score: float = Field(ge=0, le=1)
    conflict_rate: float = Field(ge=0, le=1)
    redundancy_score: float = Field(ge=0, le=1)
    loop_risk: float = Field(ge=0, le=1)


class MetricsSnapshot(BaseModel):
    latency_ms: int = Field(ge=0)
    model_calls: int = Field(ge=0)
    token_usage: Dict[str, int] = Field(default_factory=dict)


class FinalDecision(BaseModel):
    final_label: str
    final_score: float = Field(ge=0, le=1)
    rationale: List[str] = Field(default_factory=list)
    dissenting_views: List[str] = Field(default_factory=list)
