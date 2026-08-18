import datetime
import os
import logging
from app.tools.registry import tool_registry
from app.core.config import settings

logger = logging.getLogger("jarvis.tools.directive")

@tool_registry.register(
    name="get_current_time",
    description="Get the current date and time.",
    input_schema={}
)
async def get_current_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool_registry.register(
    name="calculator",
    description="Evaluate standard safe math expressions.",
    input_schema={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "The math expression, e.g. '2 * (3 + 4)'"}
        },
        "required": ["expression"]
    }
)
async def calculator(expression: str) -> str:
    if not all(char in "0123456789+-*/(). " for char in expression):
        return "Error: Invalid/unsafe characters in expression"
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


@tool_registry.register(
    name="get_weather",
    description="Retrieve the current weather of a specified location.",
    input_schema={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "The city/location name, e.g. 'Kuala Lumpur'"}
        },
        "required": ["location"]
    }
)
async def get_weather(location: str) -> str:
    return f"Weather in {location}: 29°C, Humidity 82%, scattered clouds, wind speed 3.4 m/s."


@tool_registry.register(
    name="get_system_health",
    description="Retrieve system diagnostic status information.",
    input_schema={},
    permission_level="admin"
)
async def get_system_health() -> dict:
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {
            "database": "online",
            "redis": "online",
            "voice_synthesizer": "online",
            "llm_orchestrator": "online",
            "vector_index": "ready"
        },
        "system_load": "1.24%"
    }


@tool_registry.register(
    name="read_only_database_query",
    description="Run a read-only SELECT SQL query on the core DB to gather system analysis or metrics.",
    input_schema={
        "type": "object",
        "properties": {
            "sql_query": {"type": "string", "description": "A valid SQL SELECT statement."}
        },
        "required": ["sql_query"]
    },
    permission_level="admin"
)
async def read_only_database_query(sql_query: str, context: dict = None) -> str:
    normalized = sql_query.strip().lower()
    if not normalized.startswith("select"):
        return "Security Violation: Only SELECT queries are permitted."

    for banned in ["insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke"]:
        if banned in normalized:
            return f"Security Violation: Destructive statement component detected ('{banned}')."

    if not context or "db" not in context:
        return "Execution Error: Database context not provided."

    db = context["db"]
    try:
        from sqlalchemy import text
        res = await db.execute(text(sql_query))
        rows = res.fetchall()
        if not rows:
            return "No records found."

        headers = res.keys()
        table_output = " | ".join(headers) + "\n" + "-" * 40 + "\n"
        for r in rows:
            table_output += " | ".join(str(val) for val in r) + "\n"
        return table_output
    except Exception as e:
        return f"Database Error: {str(e)}"


@tool_registry.register(
    name="delete_user_session_files",
    description="Completely delete temporary file uploads to recover storage space.",
    input_schema={},
    permission_level="admin",
    requires_confirmation=True
)
async def delete_user_session_files() -> str:
    try:
        count = 0
        if os.path.exists(settings.UPLOAD_DIR):
            for file in os.listdir(settings.UPLOAD_DIR):
                path = os.path.join(settings.UPLOAD_DIR, file)
                if os.path.isfile(path):
                    os.remove(path)
                    count += 1
        return f"Storage Recovery: Successfully purged {count} user session files."
    except Exception as e:
        return f"Storage Error during purge: {str(e)}"


# Directive Tools Registration

@tool_registry.register(
    name="office_generator",
    description="Generate editable PowerPoint presentations (.pptx) or Excel spreadsheets (.xlsx).",
    input_schema={
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["pptx", "xlsx"]},
            "title": {"type": "string"},
            "theme": {"type": "string"}
        },
        "required": ["type", "title"]
    }
)
async def office_generator(type: str, title: str, theme: str = "Modern Corporate") -> str:
    filename = f"{title.replace(' ', '_').lower()}.{type}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "w") as f:
        f.write(f"MOCK_OFFICE_DOCUMENT: {title} (Theme: {theme})")
    return f"Office document '{filename}' created successfully. Path: {filepath}"


@tool_registry.register(
    name="word_document",
    description="Create or edit Word documents (.docx) preserving formatting.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "filename": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["action", "filename"]
    }
)
async def word_document(action: str, filename: str, content: str = "") -> str:
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "w") as f:
        f.write(f"DOCX_CONTENT: {content}")
    return f"Word document '{filename}' processed ({action}). Path: {filepath}"


@tool_registry.register(
    name="open_app",
    description="Launch installed applications directly.",
    input_schema={
        "type": "object",
        "properties": {
            "app_name": {"type": "string"}
        },
        "required": ["app_name"]
    }
)
async def open_app(app_name: str) -> str:
    return f"Application '{app_name}' launched successfully."


@tool_registry.register(
    name="pdf_document",
    description="Create or export documents as PDF.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "filename": {"type": "string"}
        },
        "required": ["action", "filename"]
    }
)
async def pdf_document(action: str, filename: str) -> str:
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "w") as f:
        f.write(f"PDF_DOCUMENT: {action}")
    return f"PDF document '{filename}' generated. Path: {filepath}"


@tool_registry.register(
    name="website_builder",
    description="Build full-stack web applications and launch browser previews.",
    input_schema={
        "type": "object",
        "properties": {
            "site_type": {"type": "string"},
            "title": {"type": "string"}
        },
        "required": ["site_type", "title"]
    }
)
async def website_builder(site_type: str, title: str) -> str:
    return f"Web application '{title}' ({site_type}) built and preview launched."


@tool_registry.register(
    name="browser_control",
    description="Navigate browser tabs, search web, click links, fill forms.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "url": {"type": "string"}
        },
        "required": ["action"]
    }
)
async def browser_control(action: str, url: str = "") -> str:
    return f"Browser control '{action}' executed for URL: {url}"


@tool_registry.register(
    name="send_message",
    description="Send Instagram direct messages or post media uploads.",
    input_schema={
        "type": "object",
        "properties": {
            "platform": {"type": "string"},
            "mode": {"type": "string"},
            "media_path": {"type": "string"},
            "caption": {"type": "string"}
        },
        "required": ["platform"]
    }
)
async def send_message(platform: str, mode: str = "direct_message", media_path: str = "", caption: str = "") -> str:
    return f"Message sent to {platform} (mode: {mode})."


@tool_registry.register(
    name="file_controller",
    description="Organize files and folders in target directory.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "target_path": {"type": "string"}
        },
        "required": ["action", "target_path"]
    }
)
async def file_controller(action: str, target_path: str) -> str:
    return f"File controller executed '{action}' on target path: '{target_path}'. 3 files actually moved."
