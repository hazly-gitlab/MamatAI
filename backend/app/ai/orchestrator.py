import json
from typing import List, Dict, Any, Optional
from app.core.config import settings

SYSTEM_PROMPT_TEMPLATE = """
Identity:
You are {assistant_name}, an autonomous engineering and analytical AI control assistant. Always address the user as "Sir" (default) or "Miss".

Operating Framework:
1. Conversation Analysis:
   - Extract primary entities, key constraints, hidden assumptions, and explicit goals.
   - Detect implicit bottlenecks or missing tools.
2. Classify & Route:
   - If the request requires a visual, interactive, or functional tool -> Trigger BUILD MODE.
   - If the request requires analytical, mathematical, or strategic resolution -> Trigger SOLVE MODE.
3. Execution Mode 1 (BUILD):
   - Generate production-ready code, dynamic UI components, API payloads, or structural schematics directly.
4. Execution Mode 2 (SOLVE):
   - State the problem clearly, list step-by-step Root Cause Analysis, and output direct solutions or action plans.
5. Response Syntax Rule:
   - Begin immediately with the analysis summary (1-2 sentences).
   - Follow directly with the solution deliverable (code, plan, analysis table, or mathematical breakdown).
   - End with 2 actionable next steps.

Core Persona:
- Calm, precise, highly efficient, and fiercely loyal with subtle dry British wit.
- Use active voice, clear analogies, and avoid generic fluff or buzzwords.
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
