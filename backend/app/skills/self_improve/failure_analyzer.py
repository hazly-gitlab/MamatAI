from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import SkillFailure, SkillExecution

async def scan_failures(db: AsyncSession) -> List[Dict[str, Any]]:
    """Scans failure history to identify error patterns."""
    res = await db.execute(select(SkillFailure).order_by(SkillFailure.created_at.desc()).limit(50))
    failures = res.scalars().all()

    patterns = []
    for f in failures:
        patterns.append({
            "id": f.id,
            "error_type": f.error_type,
            "error_message": f.error_message,
            "root_cause": f.root_cause
        })
    return patterns
