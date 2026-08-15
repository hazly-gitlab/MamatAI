from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional

from app.api.deps import get_db, get_current_active_user, verify_admin
from app.models.models import User, ResearchSession, ResearchSource, ResearchFinding, ResearchConflict
from app.models.schemas import ResearchSessionOut, ResearchSourceOut, ResearchCreate
from app.skills.diagnostics.system_environment import (
    get_full_system_environment_report,
    get_cpu_info,
    get_memory_info,
    get_disk_info,
    get_docker_info,
    get_process_list,
    get_network_info
)
from app.skills.research.engine import ResearchEngine

router = APIRouter()
research_engine = ResearchEngine()

# --- SYSTEM & ENVIRONMENT MANAGEMENT ENDPOINTS ---
@router.get("/system/health")
async def get_system_health_endpoint(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return await get_full_system_environment_report(db)

@router.get("/system/resources")
async def get_system_resources_endpoint(
    user: User = Depends(get_current_active_user)
):
    cpu = await get_cpu_info()
    memory = await get_memory_info()
    disk = await get_disk_info()
    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk
    }

@router.get("/system/docker")
async def get_docker_status_endpoint(
    user: User = Depends(get_current_active_user)
):
    return await get_docker_info()

@router.get("/system/processes")
async def get_processes_endpoint(
    limit: Optional[int] = 15,
    user: User = Depends(get_current_active_user)
):
    return await get_process_list(limit=limit or 15)

@router.get("/system/network")
async def get_network_endpoint(
    user: User = Depends(get_current_active_user)
):
    return await get_network_info()


# --- WEB / KNOWLEDGE RESEARCH ENDPOINTS ---
@router.post("/research")
async def start_research_session(
    payload: ResearchCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    res = await research_engine.conduct_research(
        query=payload.query,
        user=user,
        db=db,
        mode=payload.mode or "quick"
    )
    return res

@router.get("/research/{session_id}")
async def get_research_session_endpoint(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    details = await research_engine.get_session_details(session_id, db)
    if not details:
        raise HTTPException(status_code=404, detail="Research session not found.")
    return details

@router.get("/research/{session_id}/sources", response_model=List[ResearchSourceOut])
async def get_research_sources_endpoint(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(ResearchSource).where(ResearchSource.session_id == session_id))
    return res.scalars().all()
