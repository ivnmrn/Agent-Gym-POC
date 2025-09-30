from apps.agent.api.routes import agent
from apps.agent.core.config import settings
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="LangChain Agent Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend.domain.com",
    ],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-Id"],
    max_age=600,
)
app.include_router(agent.router, prefix="/v1/agent", tags=["agent"])


@app.get("/health")
def health():
    return {
        "ok": True,
        "data_source": settings.AGENT_DATA_SOURCE,
        "agent_mode": settings.AGENT_MODE,
        "llm": settings.LLM_PROVIDER,
    }
