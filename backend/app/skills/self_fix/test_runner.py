import sys
from typing import Dict, Any
from app.skills.self_fix.sandbox import Sandbox

def run_sandbox_tests(sandbox: Sandbox, target_file: str) -> Dict[str, Any]:
    """Runs compile checks and tests inside the sandbox."""
    compile_cmd = [sys.executable, "-m", "py_compile", target_file]
    res = sandbox.run_command(compile_cmd)

    if res["status"] != "success":
        return {
            "status": "failed",
            "stage": "compile",
            "message": "Syntax validation failed inside sandbox.",
            "details": res["stderr"]
        }

    import_cmd = [sys.executable, "-c", f"import sys; sys.path.append('.'); import {target_file.replace('/', '.').replace('.py', '')}"]
    res = sandbox.run_command(import_cmd)
    if res["status"] != "success":
        return {
            "status": "failed",
            "stage": "import",
            "message": "Module validation import test failed.",
            "details": res["stderr"]
        }

    return {
        "status": "success",
        "stage": "all",
        "message": "All sandbox compile and import checks passed!"
    }
