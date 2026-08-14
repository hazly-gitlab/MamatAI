import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "JARVIS"
    APP_URL: str = "http://localhost"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super_secret_jarvis_key_change_me_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Databases
    DATABASE_URL: str = "postgresql+asyncpg://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Providers (Configurable via UI or Admin panel, default to mock/openai)
    LLM_PROVIDER: str = "mock"  # mock, openai, ollama
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    STT_PROVIDER: str = "mock"  # mock, openai, local
    TTS_PROVIDER: str = "mock"  # mock, openai, local
    VISION_PROVIDER: str = "mock"  # mock, openai, local

    # Allowlist for SQL/HTTP requests
    ALLOWED_HTTP_DOMAINS: str = "api.weatherapi.com,wttr.in,api.github.com"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
