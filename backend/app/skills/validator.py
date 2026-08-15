from typing import Dict, Any, List, Tuple

def validate_manifest(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a loaded manifest structure.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_keys = ["name", "version", "description", "permissions", "workflow"]

    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required key: '{key}'")

    if "name" in data and not isinstance(data["name"], str):
        errors.append("Key 'name' must be a string")

    if "permissions" in data:
        perms = data["permissions"]
        if not isinstance(perms, dict):
            errors.append("Key 'permissions' must be a dictionary")
        elif "level" not in perms:
            errors.append("Permissions must specify a 'level' (read_only, low_risk, sensitive, dangerous)")

    if "workflow" in data and not isinstance(data["workflow"], list):
        errors.append("Key 'workflow' must be a list of steps")

    return len(errors) == 0, errors
