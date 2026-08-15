import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
import asyncio
from app.core.database import AsyncSessionLocal, Base, engine
from app.models.models import User, UserRole, Memory
from app.skills.communication.handler import format_text_for_tts, translate_text, handle_communication_step, synthesize_tone_options
from app.skills.self_improve.learner import SelfLearner, sanitize_failure_memory
from app.skills.executor import SkillExecutor

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest.mark.asyncio
async def test_tts_text_formatting():
    sample = "**JARVIS Response**: _All_ `systems` 🚀 http://example.com"
    clean = format_text_for_tts(sample)
    assert "**" not in clean
    assert "_" not in clean
    assert "http" not in clean

@pytest.mark.asyncio
async def test_tone_options_synthesis():
    tones = synthesize_tone_options("Backend services operational")
    assert "Option 1 (The Professional)" in tones["option_1_professional"]
    assert "Option 2 (The Conversational)" in tones["option_2_conversational"]
    assert "Option 3 (The Punchy & Bold)" in tones["option_3_punchy_bold"]

@pytest.mark.asyncio
async def test_multilingual_translation():
    res_ms = translate_text("system status hello", "ms")
    assert "Status sistem" in res_ms or "Selamat" in res_ms

@pytest.mark.asyncio
async def test_communication_skill_execution():
    await reset_db()
    async with AsyncSessionLocal() as db:
        dummy_user = User(id=1, email="test@jarvis.ai", hashed_password="pwd", role=UserRole.USER)
        db.add(dummy_user)
        await db.commit()

        from app.skills.registry import SkillRegistry
        reg = SkillRegistry()
        await reg.sync_manifests_to_db(db)

        executor = SkillExecutor()
        res = await executor.execute("communication_management", {"text": "Hello JARVIS"}, db, dummy_user)
        assert res["status"] == "success"
        assert len(res["trace"]) == 5

@pytest.mark.asyncio
async def test_self_learner_failure_memory():
    await reset_db()
    async with AsyncSessionLocal() as db:
        dummy_user = User(id=1, email="test@jarvis.ai", hashed_password="pwd", role=UserRole.USER)
        db.add(dummy_user)
        await db.commit()

        learner = SelfLearner()
        pat = await learner.extract_failure_pattern("Database connection timeout password=my_secret_pw", [], db, user_id=1)
        assert pat["pattern"] == "network_connection_timeout"
        assert "my_secret_pw" not in pat["solution"]

@pytest.mark.asyncio
async def test_sanitize_failure_memory():
    raw = "Failed login for user password=secret_token_123"
    clean = sanitize_failure_memory(raw)
    assert "secret_token_123" not in clean
    assert "[REDACTED]" in clean
