from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime

from app.api.deps import get_db, verify_admin, get_current_active_user
from app.models.models import ToolSetting, AuditLog, User
from app.models.schemas import ToolSettingOut, ToolSettingUpdate, AuditLogOut
from app.tools.registry import execute_tool

router = APIRouter()

@router.get("/", response_model=List[ToolSettingOut])
async def list_tools(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(ToolSetting).order_by(ToolSetting.id))
    return result.scalars().all()

@router.put("/{tool_id}", response_model=ToolSettingOut)
async def update_tool_setting(
    tool_id: int,
    tool_in: ToolSettingUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    result = await db.execute(select(ToolSetting).where(ToolSetting.id == tool_id))
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if tool_in.enabled is not None:
        tool.enabled = tool_in.enabled
    if tool_in.requires_confirmation is not None:
        tool.requires_confirmation = tool_in.requires_confirmation
    if tool_in.permission_level is not None:
        tool.permission_level = tool_in.permission_level

    await db.commit()
    await db.refresh(tool)
    return tool

@router.get("/audit", response_model=List[AuditLogOut])
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100))
    return result.scalars().all()

@router.post("/execute/{tool_name}")
async def run_tool(
    tool_name: str,
    args: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    """
    Directly execute a tool, checking permissions, configurations, and confirmation requirements.
    If the tool requires confirmation, return a pending_confirmation response instead.
    """
    result = await db.execute(select(ToolSetting).where(ToolSetting.name == tool_name))
    tool_setting = result.scalars().first()

    if not tool_setting:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' is not registered.")

    if not tool_setting.enabled:
        raise HTTPException(status_code=400, detail=f"Tool '{tool_name}' is currently disabled.")

    # Check permissions (e.g. if tool requires administrator, check if user is admin)
    if tool_setting.permission_level == "administrator" and user.role != "administrator":
        # Log denied execution
        audit = AuditLog(
            user_id=user.id,
            username=user.email,
            action=f"execute_tool:{tool_name}",
            parameters=args,
            status="denied",
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=403, detail="Permission denied for this tool.")

    # Check if tool requires confirmation and wasn't pre-confirmed/pre-approved
    pre_approved = args.get("_approved", False) or not tool_setting.requires_confirmation

    if tool_setting.requires_confirmation and not pre_approved:
        # Create a pending audit log entry representing the confirmation request
        audit = AuditLog(
            user_id=user.id,
            username=user.email,
            action=f"execute_tool:{tool_name}",
            parameters=args,
            status="pending_confirmation",
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        await db.commit()
        await db.refresh(audit)

        return {
            "status": "pending_confirmation",
            "message": f"Execution of '{tool_name}' requires your explicit approval.",
            "audit_id": audit.id,
            "tool_name": tool_name,
            "parameters": args
        }

    # Execute tool
    start_time = datetime.utcnow()
    try:
        execution_result = await execute_tool(tool_name, args)
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Log successful execution
        audit = AuditLog(
            user_id=user.id,
            username=user.email,
            action=f"execute_tool:{tool_name}",
            parameters=args,
            status="success",
            approved_by=user.email if tool_setting.requires_confirmation else None,
            execution_time_ms=duration,
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        await db.commit()

        return {
            "status": "success",
            "result": execution_result
        }
    except Exception as e:
        # Log failure
        audit = AuditLog(
            user_id=user.id,
            username=user.email,
            action=f"execute_tool:{tool_name}",
            parameters=args,
            status="failed",
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@router.post("/confirm/{audit_id}")
async def confirm_pending_tool(
    audit_id: int,
    approve: bool,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    """Approve or deny a pending tool confirmation request."""
    result = await db.execute(select(AuditLog).where(AuditLog.id == audit_id))
    audit = result.scalars().first()

    if not audit:
        raise HTTPException(status_code=404, detail="Audit/pending request not found")

    if audit.status != "pending_confirmation":
        raise HTTPException(status_code=400, detail="This action is not pending confirmation")

    # Get tool name from action "execute_tool:name"
    tool_name = audit.action.split(":")[-1] if ":" in audit.action else audit.action

    if not approve:
        audit.status = "denied"
        await db.commit()
        return {"status": "denied", "message": "Action was rejected by user."}

    # User approved execution: execute now
    start_time = datetime.utcnow()
    try:
        execution_result = await execute_tool(tool_name, audit.parameters or {})
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        audit.status = "success"
        audit.approved_by = user.email
        audit.execution_time_ms = duration
        await db.commit()

        return {
            "status": "success",
            "message": "Action approved and completed successfully.",
            "result": execution_result
        }
    except Exception as e:
        audit.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Action execution failed: {str(e)}")
