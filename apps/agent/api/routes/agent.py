from functools import lru_cache

from apps.agent.llm.graph import build_agent_graph
from apps.agent.schemas.responses import SummaryRequest, SummaryResponse
from fastapi import APIRouter

router = APIRouter(prefix="/v1/agent", tags=["agent"])


@lru_cache
def _graph():
    """Cached graph instance."""
    return build_agent_graph()


@router.post("/summary", response_model=SummaryResponse, status_code=200)
def summary(body: SummaryRequest):
    """Generate a summary based on user stats and KPIs."""

    thread_id = f"{body.user_id}:{body.start}:{body.end}"
    result = _graph().invoke(
        {
            "input": body.question,
            "user_id": body.user_id,
            "start": body.start,
            "end": body.end,
            "goal": body.goal,
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    return SummaryResponse(
        answer=result.get("answer", ""),
        evidence=result.get("kpis"),
        sources=[{"type": "api", "endpoint": "/stats"}],
        usage={"mode": "graph"},
    )
