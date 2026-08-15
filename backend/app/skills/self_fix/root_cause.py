from typing import Dict, Any

def diagnose_root_cause(extracted_error: Dict[str, Any]) -> Dict[str, Any]:
    exc_type = extracted_error.get("exception_type", "")
    msg = extracted_error.get("message", "")

    diagnosis = "Unknown software error."
    fix_type = "generic_remediation"

    if "ModuleNotFoundError" in exc_type or "No module named" in msg:
        diagnosis = "Required module or nested package import is missing from python environment path."
        fix_type = "module_import_fix"
    elif "ConnectionRefusedError" in exc_type or "Connect call failed" in msg:
        diagnosis = "Core backing connection could not be established."
        fix_type = "connection_retry_fix"
    elif "KeyError" in exc_type:
        diagnosis = "Attempted to access non-existent dictionary key."
        fix_type = "key_fallback_fix"

    return {
        "diagnosis": diagnosis,
        "proposed_remedy": fix_type,
        "extracted_file": extracted_error.get("file"),
        "extracted_line": extracted_error.get("line")
    }
