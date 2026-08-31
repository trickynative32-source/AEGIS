import asyncio
import inspect
import logging
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("AEGIS.Tools")

class ToolMetadata(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    permission_level: str = "normal"  # "normal", "sensitive", "destructive"
    category: str = "general"

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._metadata: Dict[str, ToolMetadata] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        permission_level: str = "normal",
        category: str = "general"
    ):
        def decorator(func: Callable):
            self._tools[name] = func
            self._metadata[name] = ToolMetadata(
                name=name,
                description=description,
                parameters=parameters,
                permission_level=permission_level,
                category=category
            )
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        return self._metadata.get(name)

    def get_all_tools_metadata(self) -> List[Dict[str, Any]]:
        """Returns JSON schema format suitable for LLM tool calling (OpenAI/OpenRouter format)."""
        schemas = []
        for name, meta in self._metadata.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": meta.name,
                    "description": meta.description,
                    "parameters": meta.parameters
                }
            })
        return schemas

    async def execute(self, name: str, arguments: Dict[str, Any], require_confirmation: bool = False) -> Dict[str, Any]:
        """Executes a tool with validation, permission check, and verification."""
        if name not in self._tools:
            return {
                "success": False,
                "error": f"Tool '{name}' is not registered in AEGIS tool registry.",
                "verified": False
            }

        meta = self._metadata[name]

        # Check permission level
        if meta.permission_level in ["sensitive", "destructive"] and require_confirmation:
            return {
                "success": False,
                "needs_confirmation": True,
                "tool_name": name,
                "arguments": arguments,
                "message": f"Action '{name}' requires user confirmation before proceeding.",
                "verified": False
            }

        func = self._tools[name]
        try:
            # Handle both async and sync tools
            if inspect.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = await asyncio.to_thread(func, **arguments)

            return {
                "success": True,
                "tool": name,
                "result": result,
                "verified": True
            }
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {str(e)}", exc_info=True)
            return {
                "success": False,
                "tool": name,
                "error": str(e),
                "verified": False
            }

registry = ToolRegistry()
