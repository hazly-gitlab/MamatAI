import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.ai.providers import get_llm_provider, MockLLMProvider
from app.ai.orchestrator import get_system_prompt, build_messages_with_context

@pytest.mark.asyncio
async def test_mock_provider_text():
    provider = MockLLMProvider()
    messages = [{"role": "user", "content": "Who are you?"}]
    responses = []
    async for chunk in provider.chat_completion(messages, stream=False):
        responses.append(chunk)

    assert len(responses) > 0
    assert responses[0]["type"] == "content"
    assert "assistant" in responses[0]["data"].lower() or "jarvis" in responses[0]["data"].lower()

@pytest.mark.asyncio
async def test_mock_provider_tool():
    provider = MockLLMProvider()
    messages = [{"role": "user", "content": "Please calculate something"}]
    responses = []
    async for chunk in provider.chat_completion(messages, stream=False):
        responses.append(chunk)

    assert len(responses) > 0
    assert responses[0]["type"] == "tool_calls"
    assert responses[0]["data"][0]["function"]["name"] == "calculator"

def test_system_prompt_builder():
    prompt = get_system_prompt()
    assert "JARVIS" in prompt or "assistant" in prompt

    messages = build_messages_with_context(
        [{"role": "user", "content": "hello"}],
        rag_context="RAG doc text details",
        vision_context="Screenshot has error details"
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "RAG doc" in messages[0]["content"]
    assert "Screenshot" in messages[0]["content"]
    assert messages[1]["role"] == "user"
