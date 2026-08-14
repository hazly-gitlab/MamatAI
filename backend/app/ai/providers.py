import abc
import json
import asyncio
import os
from typing import AsyncGenerator, Dict, List, Any, Optional
import httpx
from backend.app.core.config import settings

class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate response tokens or tool calls from the LLM."""
        pass

class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "stream": stream
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            if not stream:
                try:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    yield {"type": "content", "data": data["choices"][0]["message"].get("content", "")}
                    if "tool_calls" in data["choices"][0]["message"]:
                        yield {"type": "tool_calls", "data": data["choices"][0]["message"]["tool_calls"]}
                except Exception as e:
                    yield {"type": "error", "data": f"OpenAI error: {str(e)}"}
            else:
                try:
                    async with client.stream("POST", url, headers=headers, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    break
                                chunk = json.loads(data_str)
                                if not chunk or "choices" not in chunk or len(chunk["choices"]) == 0:
                                    continue
                                delta = chunk["choices"][0]["delta"]
                                if "content" in delta and delta["content"]:
                                    yield {"type": "content", "data": delta["content"]}
                                if "tool_calls" in delta and delta["tool_calls"]:
                                    yield {"type": "tool_calls", "data": delta["tool_calls"]}
                except Exception as e:
                    yield {"type": "error", "data": f"OpenAI Stream error: {str(e)}"}

class OllamaLLMProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "stream": stream
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                if not stream:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    yield {"type": "content", "data": data["message"].get("content", "")}
                else:
                    async with client.stream("POST", url, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line:
                                continue
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield {"type": "content", "data": chunk["message"]["content"]}
            except Exception as e:
                yield {"type": "error", "data": f"Ollama error: {str(e)}"}

class MockLLMProvider(BaseLLMProvider):
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """A fully featured local mock LLM provider that simulates responses and tool triggering."""
        last_user_message = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_message = m["content"].lower()
                break

        # Simple intent matching for tool triggering
        triggered_tool = None
        tool_args = {}

        if "calculate" in last_user_message or "calculator" in last_user_message:
            triggered_tool = "calculator"
            tool_args = {"expression": "2 * 3.14159 * 5"}
        elif "weather" in last_user_message:
            triggered_tool = "get_weather"
            tool_args = {"city": "Kuala Lumpur"}
        elif "search" in last_user_message or "google" in last_user_message:
            triggered_tool = "web_search"
            tool_args = {"query": last_user_message}
        elif "system status" in last_user_message or "health status" in last_user_message or "health" in last_user_message:
            triggered_tool = "system_status"
            tool_args = {}
        elif "sql" in last_user_message or "database query" in last_user_message:
            triggered_tool = "safe_sql_query"
            tool_args = {"sql": "SELECT id, email, role FROM users LIMIT 5"}
        elif "http" in last_user_message or "request" in last_user_message:
            triggered_tool = "http_request"
            tool_args = {"url": "https://wttr.in/Kuala_Lumpur?format=j1"}

        if triggered_tool:
            # Generate fake tool call
            tool_calls = [{
                "id": f"call_{triggered_tool}",
                "type": "function",
                "function": {
                    "name": triggered_tool,
                    "arguments": json.dumps(tool_args)
                }
            }]
            yield {"type": "tool_calls", "data": tool_calls}
            return

        # Regular conversational text response
        response_text = f"Hello! I am {settings.APP_NAME}, your personal AI assistant. How can I help you today?"
        if "who are you" in last_user_message:
            response_text = f"I am {settings.APP_NAME}, a complete, highly-secure, production-ready AI control center assistant."
        elif "status" in last_user_message:
            response_text = "All systems (PostgreSQL, Redis, Voice services, Memory stores) are fully healthy and running smoothly."
        elif "malay" in last_user_message or "apa khabar" in last_user_message:
            response_text = f"Selamat datang! Saya {settings.APP_NAME}. Ada apa-apa yang boleh saya bantu anda hari ini?"

        if not stream:
            yield {"type": "content", "data": response_text}
        else:
            # Simulate real-time streaming
            words = response_text.split(" ")
            for i, word in enumerate(words):
                suffix = " " if i < len(words) - 1 else ""
                yield {"type": "content", "data": word + suffix}
                await asyncio.sleep(0.04)

def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai":
        # Check env for OpenAI key
        api_key = os.getenv("OPENAI_API_KEY", "mock_key")
        return OpenAILLMProvider(api_key=api_key)
    elif provider == "ollama":
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaLLMProvider(base_url=ollama_url)
    else:
        return MockLLMProvider()
