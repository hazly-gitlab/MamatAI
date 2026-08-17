import asyncio
import re
from typing import AsyncGenerator, List, Dict, Any
from app.ai.base_provider import BaseLLMProvider

class LocalMockProvider(BaseLLMProvider):
    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> str:
        p_lower = prompt.lower()
        if "weather" in p_lower:
            return "Based on weather tools, it is currently 28°C and partly cloudy in Kuala Lumpur with light breeze."
        elif "calculate" in p_lower or "calculator" in p_lower:
            return "The calculator result is 42. Is there anything else I can assist with?"
        elif "status" in p_lower or "health" in p_lower:
            return "System Diagnostic: All service endpoints (PostgreSQL, Redis, AI-Engine, STT, TTS) are operational and healthy."
        elif "explain this error" in p_lower or "screenshot" in p_lower or "read this" in p_lower:
            return "Looking at the uploaded image, we can see a standard traceback caused by an unhandled null pointer error in the connection pool. Fixing the config should resolve it."
        else:
            return f"Hello! I am JARVIS, your personal AI assistant. I received your request: '{prompt}'. Let me know how I can help you today."

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        response = await self.generate_response(prompt, system_prompt, history)
        words = re.findall(r'\S+|\s+', response)
        for word in words:
            yield word
            await asyncio.sleep(0.01)
