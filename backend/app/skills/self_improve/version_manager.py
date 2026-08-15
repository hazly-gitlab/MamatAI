import logging
from typing import Dict, Any, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Skill, SkillVersion, SkillImprovement, EvaluationResult

logger = logging.getLogger("jarvis_version_manager")

async def evaluate_and_promote(
    skill_name: str,
    new_version_str: str,
    new_manifest_def: Dict[str, Any],
    candidate_score: float,
    db: AsyncSession,
    reason: str = "Automated performance optimization"
) -> Tuple[bool, str]:
    """
    Evaluates new skill version score against the current version.
    Promotes only if candidate_score > old_score.
    Rejects if candidate_score <= old_score (regression detected).
    """
    res = await db.execute(select(Skill).where(Skill.name == skill_name))
    skill = res.scalars().first()
    if not skill:
        return False, f"Skill '{skill_name}' not found."

    # Get current version score
    v_res = await db.execute(
        select(SkillVersion)
        .where((SkillVersion.skill_id == skill.id) & (SkillVersion.version == skill.current_version))
    )
    curr_v = v_res.scalars().first()
    old_score = curr_v.evaluation_score if (curr_v and curr_v.evaluation_score is not None) else 0.80

    # Compare scores
    if candidate_score > old_score:
        # PROMOTED!
        # Create new SkillVersion in DB
        new_v = SkillVersion(
            skill_id=skill.id,
            version=new_version_str,
            definition=new_manifest_def,
            status="active",
            evaluation_score=candidate_score
        )
        db.add(new_v)

        # Supersede old version
        if curr_v:
            curr_v.status = "superseded"

        # Update current version pointer on skill
        skill.current_version = new_version_str

        # Record improvement
        imp = SkillImprovement(
            skill_id=skill.id,
            old_version=curr_v.version if curr_v else "1.0.0",
            new_version=new_version_str,
            reason=f"{reason} (Score improved from {old_score:.2f} to {candidate_score:.2f})",
            evaluation_score=candidate_score,
            status="approved"
        )
        db.add(imp)
        await db.commit()

        logger.info(f"PROMOTED Skill '{skill_name}' from v{curr_v.version if curr_v else '1.0.0'} ({old_score:.2f}) to v{new_version_str} ({candidate_score:.2f})")
        return True, f"Promoted skill {skill_name} to v{new_version_str} (Score: {candidate_score:.2f} > {old_score:.2f})."
    else:
        # REJECTED! (Regression detected)
        rej_v = SkillVersion(
            skill_id=skill.id,
            version=new_version_str,
            definition=new_manifest_def,
            status="rejected",
            evaluation_score=candidate_score
        )
        db.add(rej_v)

        imp = SkillImprovement(
            skill_id=skill.id,
            old_version=curr_v.version if curr_v else "1.0.0",
            new_version=new_version_str,
            reason=f"Candidate rejected due to score regression ({candidate_score:.2f} <= {old_score:.2f})",
            evaluation_score=candidate_score,
            status="rejected"
        )
        db.add(imp)
        await db.commit()

        logger.warning(f"REJECTED Skill '{skill_name}' v{new_version_str} (Score: {candidate_score:.2f} <= {old_score:.2f})")
        return False, f"Rejected candidate v{new_version_str} due to regression (Candidate: {candidate_score:.2f} <= Current: {old_score:.2f})."
