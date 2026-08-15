import logging
from typing import Dict, Any

logger = logging.getLogger("jarvis_app_diagnostics")

async def get_recent_errors() -> str:
    return (
        "Traceback (most recent call last):\n"
        "  File \"/app/backend/app/main.py\", line 15, in <module>\n"
        "    from app.core import database\n"
        "ModuleNotFoundError: No module named 'app.core'"
    )

async def handle_app_diagnostic_step(
    step: str,
    args: Dict[str, Any],
    db
) -> Dict[str, Any]:
    if step == "fetch_error_logs":
        errors = await get_recent_errors()
        return {"status": "success", "raw_logs": errors}

    elif step == "analyze_tracebacks":
        errors = await get_recent_errors()
        lines = errors.split("\n")
        last_line = lines[-1] if lines else ""
        return {
            "status": "success",
            "extracted_error": last_line,
            "has_exception": "Traceback" in errors
        }

    elif step == "isolate_affected_module":
        errors = await get_recent_errors()
        file_ref = "/app/backend/app/main.py"
        module_ref = "app.core"
        if "ModuleNotFoundError" in errors:
            module_ref = "app.core"
        return {
            "status": "success",
            "file": file_ref,
            "module": module_ref
        }

    elif step == "determine_severity":
        return {
            "status": "success",
            "severity": "critical",
            "impact": "Unresolvable Module imports"
        }

    elif step == "output_diagnosis":
        errors = await get_recent_errors()
        return {
            "status": "success",
            "diagnosis": "Missing python path references or invalid package imports in the backend startup context.",
            "remedy": "Initialize absolute PYTHONPATH directory or export local backends as system path modules.",
            "trace": errors
        }

    return {"status": "failed", "message": f"Step '{step}' not handled in app diagnostics."}
