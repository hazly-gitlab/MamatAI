from app.core.config import settings
from app.ai.base_provider import BaseLLMProvider
from app.ai.cloud_providers import OpenAIProvider, OllamaProvider
from app.ai.mock_provider import LocalMockProvider

def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    provider = provider_name or settings.LLM_PROVIDER
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "ollama":
        return OllamaProvider()
    else:
        return LocalMockProvider()
