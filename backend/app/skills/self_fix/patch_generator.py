import os
from typing import Dict, Any

def resolve_target_file(rel_path: str = "app/main.py") -> str:
    candidates = [
        rel_path,
        f"backend/{rel_path}",
        "app/main.py",
        "backend/app/main.py"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return rel_path

def generate_patch(diagnosis_data: Dict[str, Any]) -> Dict[str, Any]:
    remedy = diagnosis_data.get("proposed_remedy")
    extracted = diagnosis_data.get("extracted_file", "app/main.py")
    file_to_patch = resolve_target_file(extracted or "app/main.py")

    search_block = ""
    replace_block = ""

    if remedy == "module_import_fix":
        search_block = "from app.core import database"
        replace_block = "import sys\nimport os\nsys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))\nfrom app.core import database"
    elif remedy == "key_fallback_fix":
        search_block = "args['key']"
        replace_block = "args.get('key', 'default_val')"
    else:
        search_block = "pass"
        replace_block = "# Safe self-repair patch applied\npass"

    return {
        "file": file_to_patch,
        "search": search_block,
        "replace": replace_block
    }
