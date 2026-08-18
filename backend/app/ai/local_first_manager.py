import re
import json
import httpx
import logging
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Tuple
from app.ai.base_provider import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger("jarvis.ai.local_first")

SENSITIVE_PATTERNS = [
    r"\b(?:\d[ -]*?){13,16}\b", # Credit card
    r"\b\d{3}-\d{2}-\d{4}\b",    # SSN
    r"(?i)\b(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|bearer\s+[a-zA-Z0-9._\-]+)\b", # API keys
    r"(?i)\b(?:password|passwd|secret|api_key|token)\s*[:=]\s*\S+", # Key-value secrets
    r"(?i)\[(?:sensitive|confidential|private|secret|rahasia|sulit)\]", # Privacy tags
    r"(?i)\b(?:confidential|top\s*secret|sulit|rahasia)\b"
]

def check_sensitive_data(text: str) -> bool:
    """Detect if text contains sensitive credentials, PII, or confidential flags."""
    if not text:
        return False
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

class LocalFirstLLMManager(BaseLLMProvider):
    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL
        self.openrouter_api_key = getattr(settings, "OPENROUTER_API_KEY", "") or settings.OPENAI_API_KEY
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions" if getattr(settings, "OPENROUTER_API_KEY", "") else "https://api.openai.com/v1/chat/completions"

    async def _check_ollama_status(self) -> Tuple[bool, str]:
        """Check if Ollama is available and if requested model exists."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.ollama_base_url}/api/tags")
                if resp.status_code != 200:
                    return False, f"Ollama HTTP error {resp.status_code}"

                data = resp.json()
                raw_models = data.get("models", [])
                if not raw_models:
                    return False, f"Ollama model missing: zero models installed on Ollama server"

                models = [m.get("name", "").split(":")[0] for m in raw_models]
                target_base = self.model.split(":")[0]

                if target_base not in models and not any(target_base in m for m in models):
                    return False, f"Ollama model missing: '{self.model}' not found in installed models {models}"

                return True, "OK"
        except httpx.TimeoutException:
            return False, "Ollama ping timeout"
        except Exception as err:
            return False, f"Ollama unavailable: {str(err)}"

    async def _call_ollama_single(
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

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.ollama_base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]

    async def _call_ollama_with_retry(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> Tuple[bool, str]:
        status_ok, status_msg = await self._check_ollama_status()
        if not status_ok:
            logger.warning(f"Ollama pre-check failed: {status_msg}. Retrying status check once...")
            await asyncio.sleep(0.5)
            status_ok, status_msg = await self._check_ollama_status()
            if not status_ok:
                return False, f"Ollama pre-check failed after retry: {status_msg}"

        try:
            res = await self._call_ollama_single(prompt, system_prompt, history)
            return True, res
        except Exception as err1:
            logger.warning(f"Ollama 1st attempt failed ({str(err1)}). Retrying once...")
            await asyncio.sleep(0.5)
            try:
                res = await self._call_ollama_single(prompt, system_prompt, history)
                return True, res
            except Exception as err2:
                return False, f"Ollama failed after 1 retry: {str(err2)}"

    async def _stream_ollama(
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

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", f"{self.ollama_base_url}/api/chat", json=payload) as response:
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

    async def _call_openrouter(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> Tuple[bool, str]:
        if not self.openrouter_api_key or self.openrouter_api_key.startswith("mock-"):
            return False, "OpenRouter API Key not configured."

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
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
                resp = await client.post(self.openrouter_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return True, data["choices"][0]["message"]["content"]
        except Exception as err:
            logger.error(f"OpenRouter fallback failed: {str(err)}")
            return False, f"OpenRouter API error: {str(err)}"

    async def _stream_openrouter(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
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
            async with client.stream("POST", self.openrouter_url, headers=headers, json=payload) as response:
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

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> str:
        full_text = prompt + " " + system_prompt + " " + " ".join([m.get("content", "") for m in history])
        is_sensitive = check_sensitive_data(full_text)

        ollama_ok, ollama_res = await self._call_ollama_with_retry(prompt, system_prompt, history)
        if ollama_ok:
            logger.info("Local-First LLM: Ollama request successful.")
            return ollama_res

        logger.warning(f"Local-First LLM: Ollama failed ({ollama_res}). Checking privacy rules for fallback...")

        if is_sensitive:
            logger.error("Privacy Guard Block: Sensitive data detected in prompt. Aborting OpenRouter cloud fallback.")
            return "Safe Error [PRIVACY_PROTECTION]: Local LLM (Ollama) failed for a request containing sensitive data. Cloud fallback aborted to protect privacy."

        logger.info("Local-First LLM: Falling back to OpenRouter cloud LLM...")
        openrouter_ok, openrouter_res = await self._call_openrouter(prompt, system_prompt, history)
        if openrouter_ok:
            return openrouter_res

        logger.error("Local-First LLM: Both Ollama and OpenRouter fallback failed.")
        return f"LLM Service Unavailable: Both local Ollama and OpenRouter fallback failed. (Local: {ollama_res} | Cloud: {openrouter_res})"

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        full_text = prompt + " " + system_prompt + " " + " ".join([m.get("content", "") for m in history])
        is_sensitive = check_sensitive_data(full_text)

        status_ok, status_msg = await self._check_ollama_status()
        if status_ok:
            try:
                async for chunk in self._stream_ollama(prompt, system_prompt, history):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"Streaming from Ollama failed: {str(e)}")

        if is_sensitive:
            yield "Safe Error [PRIVACY_PROTECTION]: Local LLM (Ollama) failed for a request containing sensitive data. Cloud fallback aborted to protect privacy."
            return

        if self.openrouter_api_key and not self.openrouter_api_key.startswith("mock-"):
            try:
                async for chunk in self._stream_openrouter(prompt, system_prompt, history):
                    yield chunk
                return
            except Exception as e:
                logger.error(f"Streaming from OpenRouter failed: {str(e)}")

        yield f"LLM Service Unavailable: Both local Ollama and OpenRouter fallback failed. (Local: {status_msg})"
