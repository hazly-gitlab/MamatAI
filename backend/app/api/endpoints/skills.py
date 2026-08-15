from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional

from app.api.deps import get_db, verify_admin, get_current_active_user
from app.models.models import User, Skill, SkillVersion, SkillExecution, SkillFailure, SkillImprovement, RepairJob, AuditLog
from app.models.schemas import SkillOut, SkillVersionOut, SkillExecutionOut, RepairJobOut, SkillImprovementOut, AuditLogOut
from app.skills.engine import SkillEngine
from app.skills.registry import SkillRegistry
from app.skills.executor import SkillExecutor

router = APIRouter()
engine_instance = SkillEngine()

# --- SKILLS ENDPOINTS ---
@router.get("/", response_model=List[SkillOut])
async def list_skills(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    registry = SkillRegistry()
    await registry.sync_manifests_to_db(db)
    return await registry.list_skills(db)

@router.get("/{name}")
async def get_skill_detail(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    registry = SkillRegistry()
    skill = await registry.get_skill_by_name(name, db)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found.")
    manifest = await registry.get_active_skill(name, db)
    return {
        "skill": skill,
        "manifest": manifest
    }

@router.post("/{name}/execute")
async def execute_skill(
    name: str,
    input_args: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    executor = SkillExecutor()
    res = await executor.execute(name, input_args, db, user)
    return res

@router.get("/{name}/versions", response_model=List[SkillVersionOut])
async def get_skill_versions(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    registry = SkillRegistry()
    return await registry.get_skill_versions(name, db)


# --- SELF-DIAGNOSTIC ENDPOINTS ---
@router.get("/self-diagnostic/status")
async def get_diagnostic_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    from app.skills.diagnostics.system import handle_system_diagnostic_step
    report = await handle_system_diagnostic_step("compile_health_report", {}, db)
    return report

@router.post("/self-diagnostic/run")
async def run_diagnostic(
    skill_name: Optional[str] = "system_diagnostics",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    executor = SkillExecutor()
    return await executor.execute(skill_name or "system_diagnostics", {}, db, user)


# --- SELF-FIX ENDPOINTS ---
@router.get("/self-fix/jobs", response_model=List[RepairJobOut])
async def list_repair_jobs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(RepairJob).order_by(RepairJob.created_at.desc()))
    return res.scalars().all()

@router.post("/self-fix/diagnose")
async def diagnose_error_for_fix(
    error_payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    executor = SkillExecutor()
    return await executor.execute("self_fix", error_payload, db, user)

@router.post("/self-fix/{job_id}/approve")
async def approve_repair_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    res = await db.execute(select(RepairJob).where(RepairJob.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Repair job not found.")

    from app.skills.self_fix.diagnose import handle_self_fix_step
    patch_res = await handle_self_fix_step("apply_production_patch", {}, db, admin_user)
    v_res = await handle_self_fix_step("verify_production_health", {}, db, admin_user)

    return {
        "status": "success",
        "patch_result": patch_res,
        "verification": v_res
    }

@router.post("/self-fix/{job_id}/rollback")
async def rollback_repair_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    res = await db.execute(select(RepairJob).where(RepairJob.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Repair job not found.")

    from app.skills.self_fix.rollback import BackupManager
    restored = BackupManager.restore_backup("backend/app/main.py")
    job.status = "rolled_back"
    await db.commit()
    return {
        "status": "success" if restored else "failed",
        "message": "Successfully rolled back production changes to backup."
    }


# --- SELF-IMPROVEMENT ENDPOINTS ---
@router.get("/self-improvement/status")
async def get_improvement_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(SkillImprovement).order_by(SkillImprovement.created_at.desc()))
    return res.scalars().all()

@router.post("/self-improvement/evaluate")
async def evaluate_improvement(
    skill_name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    executor = SkillExecutor()
    return await executor.execute("self_improve", {"skill_name": skill_name}, db, user)


# --- AUDIT ENDPOINTS ---
@router.get("/audit/skills", response_model=List[AuditLogOut])
async def get_skill_audits(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    res = await db.execute(
        select(AuditLog)
        .where(AuditLog.action.like("execute_skill:%"))
        .order_by(AuditLog.timestamp.desc())
        .limit(100)
    )
    return res.scalars().all()

@router.get("/audit/repairs")
async def get_repair_audits(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    res = await db.execute(select(RepairJob).order_by(RepairJob.created_at.desc()).limit(100))
    return res.scalars().all()
