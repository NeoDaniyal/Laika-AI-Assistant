from typing import Any, Dict, List, Optional
from backend.tools.base import Tool


class ToolRegistry:
    """In-memory registry to manage, look up, and execute tools safely."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Registers a tool instance. Overwrites if a tool with the same name exists."""
        if not isinstance(tool, Tool):
            raise TypeError(f"Expected instance of Tool, got {type(tool).__name__}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Retrieves a registered tool by its unique name."""
        return self._tools.get(name)

    def all(self) -> Dict[str, Tool]:
        """Returns all registered tools indexed by name."""
        return self._tools.copy()

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Finds and executes a registered tool by name with safety checks."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' is not registered.")
        return tool.execute(arguments)

    def to_schemas(self) -> List[Dict[str, Any]]:
        """Serializes all tool schemas into a list suitable for LLM context prompts."""
        return [tool.to_schema() for tool in self._tools.values()]


# Global singleton registry instance
registry = ToolRegistry()