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

    # AI Providers (Configurable via UI or Admin panel, default to mock/hybrid/openai/ollama/openrouter)
    LLM_PROVIDER: str = "hybrid"  # mock, hybrid, openai, ollama, openrouter
    LLM_MODEL: str = "gpt-4o"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_AUDIO_MODEL: str = "gemini-2.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    STT_PROVIDER: str = "gemini"  # mock, gemini, openai, local
    TTS_PROVIDER: str = "gemini"  # mock, gemini, openai, local
    VISION_PROVIDER: str = "mock"  # mock, gemini, openai, local

    # Allowlist for SQL/HTTP requests
    ALLOWED_HTTP_DOMAINS: str = "api.weatherapi.com,wttr.in,api.github.com"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
