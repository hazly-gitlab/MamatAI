import re
import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Memory, SkillFailure, SkillExecution

logger = logging.getLogger("jarvis_self_learner")

def sanitize_failure_memory(text: str) -> str:
    """Strips sensitive tokens, API keys, and passwords before saving failure memories."""
    # Redact pass / key patterns
    sanitized = re.sub(r'(password|passwd|secret|token|key)\s*[:=]\s*\S+', r'\1: [REDACTED]', text, flags=re.IGNORECASE)
    return sanitized

class SelfLearner:
    async def extract_failure_pattern(
        self,
        error_message: str,
        execution_trace: List[Dict[str, Any]],
        db: AsyncSession,
        user_id: int = 1
    ) -> Dict[str, Any]:
        """Analyzes an execution failure trace and synthesizes a structured failure memory."""
        clean_msg = sanitize_failure_memory(error_message)

        pattern_name = "unknown_pattern"
        diagnosis = "Execution failure detected."
        solution = "Inspect dependencies and verify environment configuration."

        if "connection" in clean_msg.lower() or "timeout" in clean_msg.lower():
            pattern_name = "network_connection_timeout"
            diagnosis = "Target host or database socket connection timed out or is unreachable."
            solution = "Check network TCP port, verify firewall rules, and inspect database service status."
        elif "import" in clean_msg.lower() or "module" in clean_msg.lower():
            pattern_name = "missing_module_import"
            diagnosis = "Required Python package or sub-module path is missing from PYTHONPATH."
            solution = "Initialize package path, install missing requirements, or sandbox repair."

        # Store failure memory record in database
        memory_content = (
            f"Problem: {pattern_name}\n"
            f"Observed: {clean_msg[:300]}\n"
            f"Diagnosis: {diagnosis}\n"
            f"Previous Successful Solution: {solution}"
        )

        mem = Memory(
            user_id=user_id,
            content=memory_content,
            category="failure_memory",
            created_at=datetime.utcnow()
        )
        db.add(mem)
        await db.commit()

        logger.info(f"Learned failure pattern '{pattern_name}' and saved to long-term memory.")
        return {
            "pattern": pattern_name,
            "diagnosis": diagnosis,
            "solution": solution,
            "memory_id": mem.id
        }

    async def learn_from_user_feedback(
        self,
        user_correction: str,
        db: AsyncSession,
        user_id: int = 1
    ) -> Dict[str, Any]:
        """Learns and records user preferences or corrections to refine future skill decision policies."""
        clean_corr = sanitize_failure_memory(user_correction)

        mem = Memory(
            user_id=user_id,
            content=f"User Correction/Preference: {clean_corr}",
            category="user_preference",
            created_at=datetime.utcnow()
        )
        db.add(mem)
        await db.commit()

        return {
            "status": "success",
            "message": f"Successfully incorporated user feedback into memory matrix.",
            "memory_id": mem.id
        }
