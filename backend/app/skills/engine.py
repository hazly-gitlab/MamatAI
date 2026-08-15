import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Skill
from app.skills.registry import SkillRegistry
from app.skills.executor import SkillExecutor

logger = logging.getLogger("jarvis_skills")

class SkillEngine:
    def __init__(self):
        self.registry = SkillRegistry()
        self.executor = SkillExecutor()

    async def find_matching_skill(self, text: str, db: AsyncSession) -> Optional[Skill]:
        """Matches user natural language input against registered skill triggers."""
        text_lower = text.lower().strip()
        skills = await self.registry.list_skills(db)

        for skill in skills:
            if not skill.enabled:
                continue
            manifest = await self.registry.get_active_skill(skill.name, db)
            if not manifest:
                continue

            triggers = manifest.get("triggers", [])
            for trigger in triggers:
                if trigger.lower() in text_lower:
                    logger.info(f"Matched text '{text}' with Skill: {skill.name} (trigger: '{trigger}')")
                    return skill
        return None

    async def handle_conversational_skill(
        self,
        text: str,
        db: AsyncSession,
        user: Any,
        pre_approved: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Attempts to match, authorize, and run a Skill based on conversational text.
        Returns a dict containing execution details or approval triggers, or None if no match.
        """
        skill = await self.find_matching_skill(text, db)
        if not skill:
            return None

        logger.info(f"Directing intent to Skill Engine: {skill.name}")
        input_args = {"text": text, "query": text}

        result = await self.executor.execute(
            skill_name=skill.name,
            input_args=input_args,
            db=db,
            user=user,
            pre_approved=pre_approved
        )
        return result
