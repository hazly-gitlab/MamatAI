import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
import asyncio
from app.core.database import AsyncSessionLocal, Base, engine
from app.models.models import User, UserRole
from app.skills.diagnostics.system_environment import (
    get_os_info, get_cpu_info, get_memory_info, get_disk_info,
    get_network_info, get_docker_info, get_postgres_health,
    get_redis_health, get_full_system_environment_report
)
from app.skills.research.search_provider import search_web_knowledge
from app.skills.research.source_scorer import score_source
from app.skills.research.conflict_detector import detect_conflicts
from app.skills.research.engine import ResearchEngine
from app.skills.engine import SkillEngine

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

# --- SYSTEM & ENVIRONMENT TESTS ---
@pytest.mark.asyncio
async def test_os_detection():
    os_info = await get_os_info()
    assert "system" in os_info
    assert "platform_str" in os_info

@pytest.mark.asyncio
async def test_cpu_information():
    cpu = await get_cpu_info()
    assert "logical_cores" in cpu
    assert cpu["logical_cores"] >= 1

@pytest.mark.asyncio
async def test_memory_information():
    mem = await get_memory_info()
    assert "total_mb" in mem
    assert mem["total_mb"] > 0

@pytest.mark.asyncio
async def test_disk_information():
    disk = await get_disk_info()
    assert "free_gb" in disk
    assert disk["free_gb"] >= 0

@pytest.mark.asyncio
async def test_network_detection():
    net = await get_network_info()
    assert "hostname" in net

@pytest.mark.asyncio
async def test_docker_detection():
    docker = await get_docker_info()
    assert "running_inside_container" in docker

@pytest.mark.asyncio
async def test_postgres_health():
    await reset_db()
    async with AsyncSessionLocal() as db:
        pg = await get_postgres_health(db)
        assert pg["status"] == "healthy"

@pytest.mark.asyncio
async def test_redis_health():
    red = await get_redis_health()
    assert "status" in red

@pytest.mark.asyncio
async def test_full_environment_report():
    await reset_db()
    async with AsyncSessionLocal() as db:
        rep = await get_full_system_environment_report(db)
        assert rep["status"] in ["healthy", "degraded"]


# --- RESEARCH TESTS ---
@pytest.mark.asyncio
async def test_source_scoring():
    res = score_source("https://www.postgresql.org/docs/current/security.html", "PostgreSQL Docs", "Official documentation for hostssl scram-sha-256")
    assert res["authoritative"] is True
    assert res["score"] > 0.85

@pytest.mark.asyncio
async def test_search_provider():
    sources = await search_web_knowledge("PostgreSQL security recommendations", mode="quick")
    assert len(sources) >= 1

@pytest.mark.asyncio
async def test_conflict_detection():
    findings = [
        {"claim": "Use SSL mode to encrypt postgresql transport", "evidence": "SSL adds packet encryption security"},
        {"claim": "SSL mode adds latency overhead", "evidence": "Performance trade-off"}
    ]
    conflicts = detect_conflicts(findings)
    assert len(conflicts) >= 1
    assert "SSL Encryption" in conflicts[0]["topic"]

@pytest.mark.asyncio
async def test_research_session_synthesis():
    await reset_db()
    async with AsyncSessionLocal() as db:
        user = User(id=1, email="researcher@jarvis.ai", hashed_password="pwd", role=UserRole.USER)
        db.add(user)
        await db.commit()

        re_engine = ResearchEngine()
        res = await re_engine.conduct_research("latest PostgreSQL security recommendations", user, db, mode="deep")
        assert res["confidence_score"] > 0.8
        assert len(res["sources"]) >= 1
        assert "Synthesized research report" in res["synthesis"]


# --- COMBINED WORKFLOW TESTS ---
@pytest.mark.asyncio
async def test_system_intent_trigger():
    await reset_db()
    async with AsyncSessionLocal() as db:
        user = User(id=1, email="user@jarvis.ai", hashed_password="pwd", role=UserRole.USER)
        db.add(user)
        await db.commit()

        from app.skills.registry import SkillRegistry
        reg = SkillRegistry()
        await reg.sync_manifests_to_db(db)

        engine_inst = SkillEngine()
        skill_res = await engine_inst.handle_conversational_skill("Jarvis, check my system.", db, user)
        assert skill_res is not None
        assert skill_res["skill_name"] == "system_environment_management"
        assert skill_res["status"] == "success"

@pytest.mark.asyncio
async def test_research_intent_trigger():
    await reset_db()
    async with AsyncSessionLocal() as db:
        user = User(id=1, email="user@jarvis.ai", hashed_password="pwd", role=UserRole.USER)
        db.add(user)
        await db.commit()

        from app.skills.registry import SkillRegistry
        reg = SkillRegistry()
        await reg.sync_manifests_to_db(db)

        engine_inst = SkillEngine()
        skill_res = await engine_inst.handle_conversational_skill("Jarvis, research the latest PostgreSQL security recommendations.", db, user)
        assert skill_res is not None
        assert skill_res["skill_name"] == "web_knowledge_research"
        assert skill_res["status"] == "success"
