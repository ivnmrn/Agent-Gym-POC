from functools import lru_cache

from apps.agent.core.config import settings
from apps.agent.llm.graph_agentic import build_agentic_graph
from apps.agent.llm.graph_deterministic import build_deterministic_agent_graph
from apps.agent.schemas.responses import SummaryRequest, SummaryResponse
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/agent", tags=["agent"])


@lru_cache(maxsize=1)
def _graph_det():
    """Cached graph instance."""
    return build_deterministic_agent_graph()


@lru_cache(maxsize=1)
def _graph_agentic():
    return build_agentic_graph()


def _select_graph():
    """Select the graph based on the settings"""
    if settings.AGENT_MODE.lower() == "agentic":
        return _graph_agentic()

    # Default to deterministic
    return _graph_det()


@router.post("/summary", response_model=SummaryResponse, status_code=200)
def summary(body: SummaryRequest):
    """Generate a summary based on user stats and KPIs."""

    thread_id = f"{body.user_id}:{body.start}:{body.end}"

    try:
        result = _select_graph().invoke(
            {
                "input": body.question,
                "user_id": body.user_id,
                "start": body.start,
                "end": body.end,
                "goal": body.goal,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
    except HTTPException:
        raise
    except Exception as exception:
        raise HTTPException(
            status_code=500, detail=f"Graph execution failed: {exception}"
        ) from exception

    return SummaryResponse(
        answer=result.get("answer", ""),
        evidence=result.get("kpis"),
        sources=[{"type": "api", "endpoint": "/stats"}],
        usage={"mode": "graph"},
    )
