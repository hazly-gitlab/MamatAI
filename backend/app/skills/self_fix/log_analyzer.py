import re
from typing import Dict, Any

def analyze_logs(log_content: str) -> Dict[str, Any]:
    """Parses exception string tracebacks to extract core files and error statements."""
    lines = log_content.split("\n")
    error_line = lines[-1] if lines else ""

    matches = re.findall(r'File "([^"]+)", line (\d+)', log_content)

    file_ref = ""
    line_number = 0
    if matches:
        file_ref, line_str = matches[-1]
        line_number = int(line_str)

    return {
        "file": file_ref,
        "line": line_number,
        "exception_type": error_line.split(":")[0] if ":" in error_line else "Exception",
        "message": error_line
    }
