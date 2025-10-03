from __future__ import annotations

import logging
from functools import lru_cache

from apps.agent.core.config import settings
from langfuse import Langfuse

logger = logging.getLogger(__name__)


class LangfuseClient:
    """Client to interact with Langfuse for prompt management."""

    def __init__(self) -> None:
        public_key = settings.LANGFUSE_PUBLIC_API_KEY
        secret_key = settings.LANGFUSE_SECRET_API_KEY
        host = settings.LANGFUSE_SERVER_URL

        self.enabled = bool(public_key and secret_key and host)
        self._client: Langfuse = None

        if not self.enabled:
            logger.warning("Langfuse disabled: missing credentials or host.")
            return

        try:
            self._client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )
        except Exception as error:
            self.enabled = False
            self._client = None
            logger.warning("Langfuse disabled (init error): %s", error)

    @property
    def client(self) -> Langfuse:
        return self._client


@lru_cache(maxsize=1)
def get_langfuse() -> LangfuseClient:
    """Singleton Langfuse client instance."""
    return LangfuseClient()
