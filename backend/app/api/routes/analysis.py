from fastapi import APIRouter, HTTPException

from app.orchestration.graph import build_graph
from app.schemas.api import AnalyzeClaimResponse
from app.schemas.claim import AnalyzeClaimRequest

router = APIRouter()

# Compile the graph once for reuse across requests.
_graph = build_graph()


@router.post("/analyze-claim", response_model=AnalyzeClaimResponse)
async def analyze_claim(payload: AnalyzeClaimRequest) -> AnalyzeClaimResponse:
    result = _graph.invoke({"claim": payload})
    decision = result.get("final_decision")
    if decision is None:
        raise HTTPException(status_code=500, detail="Missing final decision")

    return AnalyzeClaimResponse(
        request_id=result.get("request_id", ""),
        claim_id=payload.claim_id,
        final_label=decision.final_label,
        final_score=decision.final_score,
        agent_reports=result.get("agent_reports", {}),
        conflicts=result.get("conflicts", []),
        redundancy=result.get("redundancy"),
        emergence=result.get("emergence"),
        metrics=result.get("metrics"),
    )
