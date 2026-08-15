import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
import asyncio
from app.core.database import AsyncSessionLocal, Base, engine
from app.skills.registry import SkillRegistry
from app.skills.executor import SkillExecutor
from app.skills.permissions import verify_skill_permission
from app.skills.self_fix.sandbox import Sandbox
from app.skills.self_improve.version_manager import evaluate_and_promote
from app.models.models import User, UserRole

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest.mark.asyncio
async def test_skill_manifest_sync_and_list():
    await reset_db()
    async with AsyncSessionLocal() as db:
        registry = SkillRegistry()
        await registry.sync_manifests_to_db(db)
        skills = await registry.list_skills(db)
        assert len(skills) >= 5
        names = [s.name for s in skills]
        assert "system_diagnostics" in names
        assert "database_diagnostics" in names
        assert "self_fix" in names
        assert "self_improve" in names

@pytest.mark.asyncio
async def test_system_diagnostics_execution():
    await reset_db()
    async with AsyncSessionLocal() as db:
        registry = SkillRegistry()
        await registry.sync_manifests_to_db(db)
        dummy_user = User(id=1, email="test@jarvis.ai", hashed_password="pwd", role=UserRole.USER)
        db.add(dummy_user)
        await db.commit()

        executor = SkillExecutor()
        res = await executor.execute("system_diagnostics", {}, db, dummy_user)
        assert res["status"] == "success"
        assert len(res["trace"]) == 4

@pytest.mark.asyncio
async def test_sandbox_security():
    sb = Sandbox()
    res = sb.run_command(["rm", "-rf", "/"])
    assert res["exit_code"] == -1
    assert "Restricted binary" in res["stderr"]
    sb.cleanup()

@pytest.mark.asyncio
async def test_version_promotion_and_regression_rejection():
    await reset_db()
    async with AsyncSessionLocal() as db:
        registry = SkillRegistry()
        await registry.sync_manifests_to_db(db)

        # Candidate 0.95 > 0.80 -> Promote
        promoted, _ = await evaluate_and_promote(
            skill_name="system_diagnostics",
            new_version_str="1.1.0",
            new_manifest_def={"name": "system_diagnostics", "version": "1.1.0"},
            candidate_score=0.95,
            db=db
        )
        assert promoted is True

        # Candidate 0.70 < 0.95 -> Reject (regression)
        rejected_promoted, _ = await evaluate_and_promote(
            skill_name="system_diagnostics",
            new_version_str="1.2.0-regression",
            new_manifest_def={"name": "system_diagnostics", "version": "1.2.0-regression"},
            candidate_score=0.70,
            db=db
        )
        assert rejected_promoted is False
