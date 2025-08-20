"""Tool registry for agent tool management."""

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ToolDefinition:
    """Tool definition with metadata."""

    name: str
    func: Callable
    description: str
    parameters: Dict[str, Any]
    required: List[str]
    category: str = "general"
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ToolRegistry:
    """Singleton tool registry for managing agent tools."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, Set[str]] = {}
        self._tags: Dict[str, Set[str]] = {}
        self._logger = logger.bind(component="ToolRegistry")
        self._initialized = True

    def register(
        self,
        name: str,
        func: Callable,
        description: str = None,
        category: str = "general",
        tags: List[str] = None,
    ) -> None:
        """Register a tool."""
        # Extract parameters from function signature
        sig = inspect.signature(func)
        parameters = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_info = {"type": "any"}
            if param.annotation != inspect.Parameter.empty:
                param_info["type"] = str(param.annotation)
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            else:
                required.append(param_name)

            parameters[param_name] = param_info

        # Create tool definition
        tool = ToolDefinition(
            name=name,
            func=func,
            description=description or func.__doc__ or "",
            parameters=parameters,
            required=required,
            category=category,
            tags=tags or [],
        )

        # Register tool
        self._tools[name] = tool

        # Update category index
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(name)

        # Update tag index
        for tag in tool.tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(name)

        self._logger.info("Tool registered", tool=name, category=category)

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self, category: str = None, tag: str = None) -> List[str]:
        """List available tools."""
        if category:
            return list(self._categories.get(category, []))
        elif tag:
            return list(self._tags.get(tag, []))
        else:
            return list(self._tools.keys())

    def get_categories(self) -> List[str]:
        """Get all categories."""
        return list(self._categories.keys())

    def get_tags(self) -> List[str]:
        """Get all tags."""
        return list(self._tags.keys())

    def execute(self, name: str, **kwargs) -> Any:
        """Execute a tool."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        # Validate required parameters
        missing = set(tool.required) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required parameters for {name}: {missing}")

        # Execute tool
        try:
            result = tool.func(**kwargs)
            self._logger.debug("Tool executed", tool=name)
            return result
        except Exception as e:
            self._logger.error("Tool execution failed", tool=name, error=str(e))
            raise

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._categories.clear()
        self._tags.clear()
        self._logger.info("Registry cleared")

    def __contains__(self, name: str) -> bool:
        """Check if tool exists."""
        return name in self._tools

    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)


# Global registry instance
registry = ToolRegistry()
