from fastapi import FastAPI

from apps.agent.api.routes import agent
from apps.agent.core.config import settings

app = FastAPI(title="LangChain Agent Service")
app.include_router(agent.router, prefix="/v1/agent", tags=["agent"])


@app.get("/health")
def health():
    return {
        "ok": True,
        "data_source": settings.AGENT_DATA_SOURCE,
        "agent_mode": settings.AGENT_MODE,
        "llm": settings.LLM_PROVIDER,
    }
