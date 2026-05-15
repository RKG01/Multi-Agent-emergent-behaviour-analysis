from typing import List, Optional

from fastapi import APIRouter, Query

from app.logging.db_reader import fetch_agent_logs, fetch_metrics
from app.schemas.logs import AgentLogEntry, MetricsEntry

router = APIRouter()


@router.get("/logs", response_model=List[AgentLogEntry])
async def get_logs(
    request_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
) -> List[AgentLogEntry]:
    return fetch_agent_logs(request_id=request_id, agent_name=agent_name, limit=limit)


@router.get("/metrics", response_model=List[MetricsEntry])
async def get_metrics(
    request_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
) -> List[MetricsEntry]:
    return fetch_metrics(request_id=request_id, limit=limit)
