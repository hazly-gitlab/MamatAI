import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Skill, SkillExecution, SkillFailure, AuditLog
from app.skills.permissions import verify_skill_permission, RISK_LEVEL_MAP

logger = logging.getLogger("jarvis_skills")

class SkillExecutor:
    async def execute(
        self,
        skill_name: str,
        input_args: Dict[str, Any],
        db: AsyncSession,
        user: Any,
        pre_approved: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a registered skill end-to-end, managing permission levels,
        workflow sequencing, exception tracing, sandboxing, and audit trails.
        """
        res = await db.execute(select(Skill).where(Skill.name == skill_name))
        skill = res.scalars().first()
        if not skill:
            return {"status": "error", "message": f"Skill '{skill_name}' not found."}

        if not skill.enabled:
            return {"status": "error", "message": f"Skill '{skill_name}' is currently disabled."}

        from app.skills.registry import SkillRegistry
        registry = SkillRegistry()
        manifest = await registry.get_active_skill(skill_name, db)
        if not manifest:
            return {"status": "error", "message": f"Active version manifest not found for skill '{skill_name}'."}

        can_run, msg, next_action = verify_skill_permission(manifest, user, pre_approved)

        if not can_run:
            if next_action == "require_approval":
                audit = AuditLog(
                    user_id=user.id,
                    username=user.email,
                    action=f"execute_skill:{skill_name}",
                    parameters=input_args,
                    status="pending_confirmation",
                    timestamp=datetime.utcnow()
                )
                db.add(audit)
                await db.commit()
                await db.refresh(audit)

                exec_record = SkillExecution(
                    skill_id=skill.id,
                    skill_version=skill.current_version,
                    input_data=input_args,
                    status="pending_confirmation",
                    created_at=datetime.utcnow()
                )
                db.add(exec_record)
                await db.commit()

                return {
                    "status": "pending_confirmation",
                    "message": msg,
                    "audit_id": audit.id,
                    "skill_name": skill_name,
                    "parameters": input_args
                }
            else:
                return {"status": "denied", "message": msg}

        exec_record = SkillExecution(
            skill_id=skill.id,
            skill_version=skill.current_version,
            input_data=input_args,
            status="running",
            created_at=datetime.utcnow()
        )
        db.add(exec_record)
        await db.flush()

        start_time = time.time()
        workflow_steps = manifest.get("workflow", [])
        results_trace = []
        status_final = "success"

        try:
            for step in workflow_steps:
                logger.info(f"Executing step '{step}' in skill '{skill_name}'")
                step_res = await self.execute_step(skill_name, step, input_args, db, user)
                results_trace.append({
                    "step": step,
                    "status": step_res.get("status", "success"),
                    "result": step_res
                })

                if step_res.get("status") == "failed":
                    status_final = "failed"
                    failure = SkillFailure(
                        skill_execution_id=exec_record.id,
                        error_type="StepExecutionError",
                        error_message=step_res.get("message", "Step failed to complete."),
                        root_cause=step_res.get("root_cause", "Step logical failure"),
                        severity="high",
                        resolved=False,
                        created_at=datetime.utcnow()
                    )
                    db.add(failure)
                    break

        except Exception as e:
            status_final = "failed"
            logger.exception(f"Unhandled error during skill '{skill_name}' execution")
            failure = SkillFailure(
                skill_execution_id=exec_record.id,
                error_type=type(e).__name__,
                error_message=str(e),
                root_cause="Python Exception during execution trace",
                severity="critical",
                resolved=False,
                created_at=datetime.utcnow()
            )
            db.add(failure)
            results_trace.append({"step": "unhandled_exception", "status": "error", "message": str(e)})

        duration_ms = (time.time() - start_time) * 1000

        exec_record.status = status_final
        exec_record.execution_time_ms = duration_ms
        exec_record.output_data = {"trace": results_trace}

        audit = AuditLog(
            user_id=user.id,
            username=user.email,
            action=f"execute_skill:{skill_name}",
            parameters=input_args,
            status="success" if status_final == "success" else "failed",
            approved_by=user.email if pre_approved else None,
            execution_time_ms=duration_ms,
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        await db.commit()

        return {
            "status": status_final,
            "skill_name": skill_name,
            "version": skill.current_version,
            "execution_id": exec_record.id,
            "execution_time_ms": duration_ms,
            "trace": results_trace
        }

    async def execute_step(
        self,
        skill_name: str,
        step_name: str,
        input_args: Dict[str, Any],
        db: AsyncSession,
        user: Any
    ) -> Dict[str, Any]:
        """Maps step name to diagnostic, self_fix, or self_improve handlers."""
        step_clean = step_name.lower().strip()

        if skill_name == "system_diagnostics":
            from app.skills.diagnostics.system import handle_system_diagnostic_step
            return await handle_system_diagnostic_step(step_clean, input_args, db)

        elif skill_name == "database_diagnostics":
            from app.skills.diagnostics.database import handle_db_diagnostic_step
            return await handle_db_diagnostic_step(step_clean, input_args, db)

        elif skill_name == "application_diagnostics":
            from app.skills.diagnostics.application import handle_app_diagnostic_step
            return await handle_app_diagnostic_step(step_clean, input_args, db)

        elif skill_name == "self_fix":
            from app.skills.self_fix.diagnose import handle_self_fix_step
            return await handle_self_fix_step(step_clean, input_args, db, user)

        elif skill_name == "self_improve":
            from app.skills.self_improve.evaluator import handle_self_improve_step
            return await handle_self_improve_step(step_clean, input_args, db, user)

        return {"status": "success", "message": f"Step '{step_name}' bypassed (noop)."}
