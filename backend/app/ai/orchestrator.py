import json
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings

SYSTEM_PROMPT_TEMPLATE = """
Identity:
You are {assistant_name}, a complete, production-grade, highly-secure personal and organizational AI assistant, modeled after futuristic AI control centers like JARVIS.

Core Guidelines:
1. Always maintain a helpful, secure, and professional tone.
2. For mathematical calculations, use the 'calculator' tool.
3. For fetching weather or system statistics, use the respective tools.
4. If a tool request could be destructive (e.g., delete_document, executing dangerous queries), verify permissions first.
5. Never allow arbitrary model-generated shell commands to execute directly. Keep everything sandboxed.
6. Support both Malay and English fluidly based on user interaction preference.
7. Keep responses safe, structured, and informative. When citing retrieved documents, prepend or append citation source references clearly.
"""

def get_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(assistant_name=settings.APP_NAME)

def build_messages_with_context(
    history: List[Dict[str, str]],
    rag_context: Optional[str] = None,
    vision_context: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Builds the complete message history for the LLM, incorporating system prompt,
    history, RAG, and image vision descriptions.
    """
    messages = []

    # Prepend System Prompt
    system_prompt = get_system_prompt()
    if rag_context:
        system_prompt += f"\n\nRetrieved Context (RAG):\n{rag_context}\n"
    if vision_context:
        system_prompt += f"\n\nVision Analysis Content:\n{vision_context}\n"

    messages.append({"role": "system", "content": system_prompt})

    # Append History
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    return messages
