import os
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.models import Skill, SkillVersion
from app.skills.loader import load_all_manifests, load_manifest_from_file
from app.skills.validator import validate_manifest
from app.skills.permissions import get_risk_level

logger = logging.getLogger("jarvis_skills")

class SkillRegistry:
    def __init__(self, manifests_dir: Optional[str] = None):
        if not manifests_dir:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            manifests_dir = os.path.join(current_dir, "manifests")
        self.manifests_dir = manifests_dir

    async def sync_manifests_to_db(self, db: AsyncSession):
        """Loads all local YAML files and synchronizes them with the database."""
        logger.info(f"Synchronizing skill manifests from {self.manifests_dir}")
        manifests = load_all_manifests(self.manifests_dir)

        for data in manifests:
            is_valid, errors = validate_manifest(data)
            if not is_valid:
                logger.error(f"Skipping invalid manifest {data.get('name', 'unknown')}: {errors}")
                continue

            name = data["name"]
            version = data["version"]
            desc = data["description"]
            risk_name = data.get("permissions", {}).get("level", "read_only")
            risk_val = get_risk_level(risk_name)

            res = await db.execute(select(Skill).where(Skill.name == name))
            skill = res.scalars().first()

            if not skill:
                skill = Skill(
                    name=name,
                    description=desc,
                    enabled=True,
                    current_version=version,
                    risk_level=risk_val
                )
                db.add(skill)
                await db.flush()
                logger.info(f"Created new Skill in DB: {name} v{version}")
            else:
                skill.description = desc
                skill.risk_level = risk_val
                await db.flush()

            v_res = await db.execute(
                select(SkillVersion)
                .where((SkillVersion.skill_id == skill.id) & (SkillVersion.version == version))
            )
            skill_version = v_res.scalars().first()

            if not skill_version:
                skill_version = SkillVersion(
                    skill_id=skill.id,
                    version=version,
                    definition=data,
                    status="active"
                )
                db.add(skill_version)
                logger.info(f"Seeded Skill Version: {name} v{version}")
            else:
                skill_version.definition = data

        await db.commit()

    async def get_active_skill(self, name: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Retrieve active skill configuration from database."""
        res = await db.execute(select(Skill).where((Skill.name == name) & (Skill.enabled == True)))
        skill = res.scalars().first()
        if not skill:
            return None

        v_res = await db.execute(
            select(SkillVersion)
            .where((SkillVersion.skill_id == skill.id) & (SkillVersion.version == skill.current_version))
        )
        version = v_res.scalars().first()
        if not version:
            return None

        return version.definition

    async def list_skills(self, db: AsyncSession) -> List[Skill]:
        """List all skills in the database."""
        res = await db.execute(select(Skill).order_by(Skill.id))
        return list(res.scalars().all())

    async def get_skill_by_name(self, name: str, db: AsyncSession) -> Optional[Skill]:
        res = await db.execute(select(Skill).where(Skill.name == name))
        return res.scalars().first()

    async def get_skill_versions(self, name: str, db: AsyncSession) -> List[SkillVersion]:
        skill = await self.get_skill_by_name(name, db)
        if not skill:
            return []
        res = await db.execute(select(SkillVersion).where(SkillVersion.skill_id == skill.id).order_by(SkillVersion.version.desc()))
        return list(res.scalars().all())
