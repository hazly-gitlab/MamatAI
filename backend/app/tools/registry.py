import inspect
import logging
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("jarvis.tools")

class Tool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    permission_level: str = "user"
    requires_confirmation: bool = False
    timeout: int = 10

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        permission_level: str = "user",
        requires_confirmation: bool = False,
        timeout: int = 10
    ):
        def decorator(func: Callable):
            tool = Tool(
                name=name,
                description=description,
                input_schema=input_schema,
                permission_level=permission_level,
                requires_confirmation=requires_confirmation,
                timeout=timeout
            )
            self._tools[name] = tool
            self._handlers[name] = func
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_all_tools(self) -> Dict[str, Tool]:
        return self._tools

    async def execute(self, name: str, args: Dict[str, Any], context: Dict[str, Any] = None) -> Any:
        if name not in self._handlers:
            raise ValueError(f"Tool {name} not registered")

        handler = self._handlers[name]
        logger.info(f"Executing tool: {name} with arguments: {args}")

        sig = inspect.signature(handler)
        if "context" in sig.parameters:
            return await handler(**args, context=context)
        return await handler(**args)

tool_registry = ToolRegistry()
