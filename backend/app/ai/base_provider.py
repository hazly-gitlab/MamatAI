from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> str:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        pass
