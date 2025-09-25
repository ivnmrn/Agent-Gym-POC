from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    AGENT_DATA_SOURCE: str
    AGENT_MODE: str
    LLM_PROVIDER: str
    OPENAI_API_KEY: str = None
    API_V1: str = "/api/v1"


settings = Settings()
