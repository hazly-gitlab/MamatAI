from typing import Dict, Any, Tuple
from app.models.models import User, UserRole

RISK_LEVEL_MAP = {
    "read_only": 0,
    "low_risk": 1,
    "sensitive": 2,
    "dangerous": 3
}

def get_risk_level(level_name: str) -> int:
    """Returns risk level integer from risk level name."""
    return RISK_LEVEL_MAP.get(level_name.lower(), 0)

def verify_skill_permission(
    skill_manifest: Dict[str, Any],
    user: User,
    pre_approved: bool = False
) -> Tuple[bool, str, str]:
    """
    Verifies if the skill can execute under current permission context.
    Returns: (can_execute, status_message, next_step)
    - can_execute: True if okay to run right now.
    - status_message: user explanation.
    - next_step: "execute", "sandbox", "require_approval", "denied"
    """
    perms = skill_manifest.get("permissions", {})
    level_name = perms.get("level", "read_only").lower()
    risk_level = get_risk_level(level_name)

    if risk_level == 0:
        return True, "Safe diagnostic skill verified. Proceeding automatically.", "execute"

    if risk_level == 1:
        return True, "Skill executes within local sandboxed environment.", "sandbox"

    if risk_level == 2:
        if pre_approved:
            return True, "User confirmation received. Executing action.", "execute"
        return False, "This sensitive action requires your explicit approval.", "require_approval"

    if risk_level == 3:
        if user.role != UserRole.ADMINISTRATOR:
            return False, "Access Denied. Only System Administrators can authorize dangerous actions.", "denied"
        if pre_approved:
            return True, "Administrator approval and safety policy validated. Deploying change.", "execute"
        return False, "DANGEROUS: This high-impact system action requires Administrator approval and security checks.", "require_approval"

    return False, "Unknown permission level specified.", "denied"
