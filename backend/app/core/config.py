import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "MAMAT AI"
    APP_URL: str = "http://localhost"
    API_URL: str = "http://localhost/api/v1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "supersecretjwtkey_change_me_in_production_32_chars_at_least"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "sqlite+aiosqlite:///jarvis.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Default to real LLM provider (OpenAI / OpenRouter)
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    STT_PROVIDER: str = "browser"
    TTS_PROVIDER: str = "browser"
    VISION_PROVIDER: str = "openai"

    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
