import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.database_models import AuditLog, User, Document, ScheduledTask
from app.models.schemas import AuditLogResponse, UserResponse, ScheduledTaskResponse
from app.security.auth import require_admin
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Administration Panel"])

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100))
    return result.scalars().all()


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/system-status")
async def check_detailed_system_status(
    user=Depends(require_admin)
):
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "stt_provider": settings.STT_PROVIDER,
        "tts_provider": settings.TTS_PROVIDER,
        "vision_provider": settings.VISION_PROVIDER,
        "upload_dir_size_bytes": 0,
        "timestamp": datetime.datetime.now().isoformat()
    }


@router.post("/provider/test")
async def test_ai_provider_connectivity(
    provider: str,
    user=Depends(require_admin)
):
    try:
        from app.ai import get_llm_provider
        p = get_llm_provider(provider)
        res = await p.generate_response(
            prompt="connectivity_test",
            system_prompt="Return 'Connection OK' and nothing else.",
            history=[]
        )
        return {"status": "success", "message": f"Provider test completed: {res}"}
    except Exception as e:
        return {"status": "failed", "detail": str(e)}
