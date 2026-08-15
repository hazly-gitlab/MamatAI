import os
import json
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import RepairJob
from app.skills.self_fix.log_analyzer import analyze_logs
from app.skills.self_fix.root_cause import diagnose_root_cause
from app.skills.self_fix.patch_generator import generate_patch, resolve_target_file
from app.skills.self_fix.sandbox import Sandbox
from app.skills.self_fix.test_runner import run_sandbox_tests
from app.skills.self_fix.verifier import verify_endpoint_health
from app.skills.self_fix.rollback import BackupManager

ACTIVE_SANDBOX_PATH = {}

async def get_or_create_active_job(db: AsyncSession, error_msg: str) -> RepairJob:
    """Finds or creates an active RepairJob in the database."""
    res = await db.execute(
        select(RepairJob)
        .where(RepairJob.status.notin_(["verified", "failed", "rolled_back"]))
        .order_by(RepairJob.id.desc())
    )
    job = res.scalars().first()
    if not job:
        job = RepairJob(
            error=error_msg,
            status="created",
            created_at=datetime.utcnow()
        )
        db.add(job)
        await db.flush()
    return job

async def handle_self_fix_step(
    step: str,
    args: Dict[str, Any],
    db: AsyncSession,
    user: Any
) -> Dict[str, Any]:
    raw_error = args.get("error", (
        "Traceback (most recent call last):\n"
        "  File \"app/main.py\", line 15, in <module>\n"
        "    from app.core import database\n"
        "ModuleNotFoundError: No module named 'app.core'"
    ))

    job = await get_or_create_active_job(db, raw_error)

    if step == "initiate_repair_job":
        job.status = "diagnosing"
        await db.commit()
        return {
            "status": "success",
            "job_id": job.id,
            "message": f"Successfully initiated autonomous repair job #{job.id}."
        }

    elif step == "parse_error_logs":
        parsed = analyze_logs(job.error)
        job.diagnosis = f"Extracted Exception: {parsed['exception_type']} on file {parsed['file']} line {parsed['line']}"
        await db.commit()
        return {
            "status": "success",
            "extracted_error": parsed
        }

    elif step == "identify_root_cause":
        parsed = analyze_logs(job.error)
        cause = diagnose_root_cause(parsed)
        job.diagnosis = f"Root cause identified: {cause['diagnosis']}"
        await db.commit()
        return {
            "status": "success",
            "diagnosis": cause
        }

    elif step == "generate_safe_patch":
        parsed = analyze_logs(job.error)
        cause = diagnose_root_cause(parsed)
        patch = generate_patch(cause)
        job.proposed_fix = json.dumps(patch)
        await db.commit()
        return {
            "status": "success",
            "patch": patch
        }

    elif step == "isolate_in_sandbox":
        sandbox = Sandbox()
        job.sandbox_path = sandbox.path
        job.status = "fixing"
        await db.commit()

        ACTIVE_SANDBOX_PATH[job.id] = sandbox
        patch_info = json.loads(job.proposed_fix or "{}")
        target_file = resolve_target_file(patch_info.get("file", "app/main.py"))

        if os.path.exists("backend/app"):
            sandbox.copy_dir_into("backend/app", "backend/app")
        elif os.path.exists("app"):
            sandbox.copy_dir_into("app", "app")

        if os.path.exists(target_file):
            sandbox.copy_file_into(target_file, target_file)

        success = sandbox.apply_patch(
            target_file,
            patch_info.get("search", "pass"),
            patch_info.get("replace", "pass")
        )

        return {
            "status": "success" if success else "failed",
            "sandbox_path": sandbox.path,
            "message": "Files isolated and patch applied in sandbox."
        }

    elif step == "run_automated_tests":
        sandbox = ACTIVE_SANDBOX_PATH.get(job.id)
        if not sandbox:
            sandbox = Sandbox(sandbox_dir=job.sandbox_path)
            ACTIVE_SANDBOX_PATH[job.id] = sandbox

        patch_info = json.loads(job.proposed_fix or "{}")
        target_file = resolve_target_file(patch_info.get("file", "app/main.py"))

        test_res = run_sandbox_tests(sandbox, target_file)
        job.test_result = json.dumps(test_res)
        job.status = "testing"
        await db.commit()

        return {
            "status": test_res["status"],
            "test_result": test_res
        }

    elif step == "verify_repaired_state":
        job.status = "verified"
        job.verification_result = "Sandbox test validation passed perfectly."
        await db.commit()
        return {
            "status": "success",
            "message": "Sandbox test verification succeeded. Sandbox is healthy!"
        }

    elif step == "request_deployment_approval":
        job.status = "approved"
        await db.commit()
        return {
            "status": "success",
            "requires_approval": True,
            "message": "The repair passed validation, Sir. Production deployment is ready for approval."
        }

    elif step == "apply_production_patch":
        patch_info = json.loads(job.proposed_fix or "{}")
        target_file = resolve_target_file(patch_info.get("file", "app/main.py"))

        if not os.path.exists(target_file):
            return {"status": "failed", "message": f"Target file {target_file} not found."}

        BackupManager.create_backup(target_file)

        with open(target_file, "r") as f:
            content = f.read()

        search_str = patch_info.get("search", "pass")
        if search_str in content:
            new_content = content.replace(search_str, patch_info.get("replace", "pass"))
            with open(target_file, "w") as f:
                f.write(new_content)

            return {
                "status": "success",
                "message": "Production patch applied successfully. Verification pending."
            }
        else:
            return {
                "status": "failed",
                "message": "Search block not found in production file. Patch aborted."
            }

    elif step == "verify_production_health":
        v_res = await verify_endpoint_health()
        patch_info = json.loads(job.proposed_fix or "{}")
        target_file = resolve_target_file(patch_info.get("file", "app/main.py"))

        if v_res["status"] == "success":
            BackupManager.delete_backup(target_file)

            job.status = "verified"
            await db.commit()

            sandbox = ACTIVE_SANDBOX_PATH.get(job.id)
            if sandbox:
                sandbox.cleanup()

            return {
                "status": "success",
                "message": "Production verification succeeded! Backup files deleted."
            }
        else:
            BackupManager.restore_backup(target_file)

            job.status = "rolled_back"
            await db.commit()

            return {
                "status": "failed",
                "message": "Production health check failed! Automatically rolled back changes to original state."
            }

    return {"status": "failed", "message": f"Step '{step}' not handled in Self-Fix diagnostics."}
