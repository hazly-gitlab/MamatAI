import httpx
import json
import logging
from typing import AsyncGenerator, List, Dict, Any
from app.ai.base_provider import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger("jarvis.ai.cloud")

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL
        if settings.OPENROUTER_API_KEY:
            self.url = "https://openrouter.ai/api/v1/chat/completions"
        else:
            self.url = "https://api.openai.com/v1/chat/completions"

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> str:
        if not self.api_key or self.api_key.startswith("mock-"):
            return (
                "Real LLM Notice: OPENAI_API_KEY or OPENROUTER_API_KEY is not configured or contains placeholder value. "
                "Please set a valid API key in your .env file to enable real LLM generation, or switch to local_mock mode in Settings."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as err:
            logger.error(f"OpenAI API status error: {err.response.status_code} - {err.response.text}")
            return f"Real LLM API Error ({err.response.status_code}): {err.response.text}"
        except Exception as err:
            logger.error(f"OpenAI connection error: {str(err)}")
            return f"Real LLM Connection Failure: {str(err)}"

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        if not self.api_key or self.api_key.startswith("mock-"):
            yield (
                "Real LLM Notice: OPENAI_API_KEY or OPENROUTER_API_KEY is not configured. "
                "Please add a valid API key to your .env file to run real LLM queries."
            )
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield delta
                            except Exception:
                                continue
        except Exception as err:
            logger.error(f"Error streaming from real LLM API: {str(err)}")
            yield f"Real LLM Stream Error: {str(err)}"


class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
        except Exception as err:
            logger.error(f"Ollama connection error: {str(err)}")
            return f"Ollama Local LLM Error: Unable to connect to Ollama at {self.base_url}. Ensure Ollama is running."

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            delta = chunk.get("message", {}).get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
        except Exception as err:
            logger.error(f"Ollama stream error: {str(err)}")
            yield f"Ollama Local LLM Stream Error: Unable to connect to Ollama at {self.base_url}."
