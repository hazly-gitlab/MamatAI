import pytest
from unittest.mock import AsyncMock, patch
from app.ai.local_first_manager import LocalFirstLLMManager, check_sensitive_data

@pytest.mark.asyncio
async def test_privacy_detector():
    assert check_sensitive_data("Standard hello world request") == False
    assert check_sensitive_data("Here is my secret sk-1234567890abcdef1234567890 key") == True
    assert check_sensitive_data("User password=SuperSecretPassword123!") == True
    assert check_sensitive_data("This document is [CONFIDENTIAL] internal policy.") == True

@pytest.mark.asyncio
async def test_ollama_success():
    manager = LocalFirstLLMManager()

    with patch.object(manager, '_call_ollama_with_retry', new_callable=AsyncMock) as mock_ollama:
        mock_ollama.return_value = (True, "Ollama Local Output")

        res = await manager.generate_response("Tell me a joke", "System Prompt", [])
        assert res == "Ollama Local Output"
        mock_ollama.assert_called_once()

@pytest.mark.asyncio
async def test_ollama_unavailable_openrouter_fallback():
    manager = LocalFirstLLMManager()

    with patch.object(manager, '_call_ollama_with_retry', new_callable=AsyncMock) as mock_ollama, \
         patch.object(manager, '_call_openrouter', new_callable=AsyncMock) as mock_openrouter:

        mock_ollama.return_value = (False, "Ollama unavailable: Connection refused")
        mock_openrouter.return_value = (True, "OpenRouter Cloud Fallback Output")

        res = await manager.generate_response("General non-sensitive request", "System Prompt", [])
        assert res == "OpenRouter Cloud Fallback Output"
        mock_ollama.assert_called_once()
        mock_openrouter.assert_called_once()

@pytest.mark.asyncio
async def test_ollama_timeout_openrouter_fallback():
    manager = LocalFirstLLMManager()

    with patch.object(manager, '_call_ollama_with_retry', new_callable=AsyncMock) as mock_ollama, \
         patch.object(manager, '_call_openrouter', new_callable=AsyncMock) as mock_openrouter:

        mock_ollama.return_value = (False, "Ollama ping timeout")
        mock_openrouter.return_value = (True, "OpenRouter Cloud Fallback Output")

        res = await manager.generate_response("What is the capital of Malaysia?", "System", [])
        assert res == "OpenRouter Cloud Fallback Output"
        mock_openrouter.assert_called_once()

@pytest.mark.asyncio
async def test_ollama_model_missing_openrouter_fallback():
    manager = LocalFirstLLMManager()

    with patch.object(manager, '_call_ollama_with_retry', new_callable=AsyncMock) as mock_ollama, \
         patch.object(manager, '_call_openrouter', new_callable=AsyncMock) as mock_openrouter:

        mock_ollama.return_value = (False, "Ollama model missing: 'llama3.2' not found")
        mock_openrouter.return_value = (True, "OpenRouter Cloud Fallback Output")

        res = await manager.generate_response("Simple math formula", "System", [])
        assert res == "OpenRouter Cloud Fallback Output"
        mock_openrouter.assert_called_once()

@pytest.mark.asyncio
async def test_sensitive_request_local_failure_no_cloud_fallback():
    manager = LocalFirstLLMManager()

    with patch.object(manager, '_call_ollama_with_retry', new_callable=AsyncMock) as mock_ollama, \
         patch.object(manager, '_call_openrouter', new_callable=AsyncMock) as mock_openrouter:

        mock_ollama.return_value = (False, "Ollama unavailable: Connection refused")

        # Prompt contains sensitive API KEY
        sensitive_prompt = "Process user secret sk-abcdef1234567890abcdef1234567890"

        res = await manager.generate_response(sensitive_prompt, "System", [])
        assert "PRIVACY_PROTECTION" in res
        assert "Safe Error" in res

        # Verify OpenRouter was NOT called!
        mock_openrouter.assert_not_called()

@pytest.mark.asyncio
async def test_both_providers_fail():
    manager = LocalFirstLLMManager()

    with patch.object(manager, '_call_ollama_with_retry', new_callable=AsyncMock) as mock_ollama, \
         patch.object(manager, '_call_openrouter', new_callable=AsyncMock) as mock_openrouter:

        mock_ollama.return_value = (False, "Ollama connection timeout")
        mock_openrouter.return_value = (False, "OpenRouter API Key invalid")

        res = await manager.generate_response("Non-sensitive query", "System", [])
        assert "LLM Service Unavailable" in res
        assert "Both local Ollama and OpenRouter fallback failed" in res
