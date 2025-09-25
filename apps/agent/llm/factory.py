from apps.agent.core.config import settings

def _make_llm():
    """Instanciate a LLM based on settings."""

    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", temperature=0)

    return None
