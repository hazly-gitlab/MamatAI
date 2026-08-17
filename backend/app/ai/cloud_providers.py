import httpx
import json
from typing import AsyncGenerator, List, Dict, Any
from app.ai.base_provider import BaseLLMProvider
from app.core.config import settings

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL
        self.url = "https://api.openai.com/v1/chat/completions"

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> str:
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

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
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

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]

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
