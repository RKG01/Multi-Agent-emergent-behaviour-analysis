from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClaimantInput(BaseModel):
    name: str
    history_count: int = Field(ge=0)


class PolicyInput(BaseModel):
    policy_id: str
    coverage_limit: float = Field(ge=0)
    deductible: Optional[float] = Field(default=None, ge=0)


class IncidentInput(BaseModel):
    date: str
    type: str
    description: Optional[str] = None


class DocumentInput(BaseModel):
    document_id: str
    filename: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyzeClaimRequest(BaseModel):
    claim_id: str
    claimant: ClaimantInput
    policy: PolicyInput
    incident: IncidentInput
    amount: float = Field(ge=0)
    documents: List[DocumentInput] = Field(default_factory=list)
