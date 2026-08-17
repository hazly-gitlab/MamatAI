# Configuration Reference

All environment settings are loaded from `.env`:
- `APP_NAME`: Assistant identifier (default: `JARVIS`)
- `LLM_PROVIDER`: `local_mock`, `openai`, `ollama`
- `SECRET_KEY`: Minimum 32-character secret string
- `DATABASE_URL`: Async SQLAlchemy connection string
