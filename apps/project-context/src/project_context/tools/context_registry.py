"""Context-aware tool registry for MCP tools with unified backend integration."""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Type, Union

import structlog

from ..db.connections import get_db
from ..ingestion.adapters.chat_adapter import ChatAdapter
from ..ingestion.adapters.code_adapter import CodeAdapter
from ..ingestion.registry import AdapterRegistry

logger = structlog.get_logger(__name__)


class ContextToolRegistry:
    """Registry for MCP tools with unified context backend integration."""

    def __init__(self):
        """Initialize the context tool registry."""
        self.adapter_registry = AdapterRegistry()
        self.chat_adapter: Optional[ChatAdapter] = None
        self.code_adapter: Optional[CodeAdapter] = None
        self.db = None

        self.logger = logger.bind(component="context_tool_registry")

        # Tool categorization for adapter routing
        self.chat_tools = {
            "search_conversations",
            "get_conversation_summary",
            "find_chat_patterns",
            "get_message_history",
            "analyze_conversation_flow",
        }

        self.code_tools = {
            "get_complexity",
            "get_call_graph",
            "get_imports",
            "get_documentation",
            "find_files",
            "find_symbols",
            "get_symbol_details",
            "find_symbol_usages",
            "search_code",
            "search_files_by_content",
        }

        self.system_tools = {
            "get_api_endpoints",
            "get_dependencies",
            "get_entry_points",
            "find_agents",
            "get_data_models",
            "get_tests",
            "get_config",
            "get_quality_metrics",
            "get_todos",
            "validate_intelligence",
            "get_security_issues",
            "get_recent_changes",
            "get_file_info",
            "get_project_summary",
        }

    async def initialize(self) -> None:
        """Initialize adapters and database connections."""
        try:
            # Initialize database connection
            self.db = await get_db()
            self.logger.info("Database connection established")

            # Initialize adapters
            await self._initialize_adapters()

            self.logger.info("Context tool registry initialized successfully")

        except Exception as e:
            self.logger.error(
                "Failed to initialize context tool registry", error=str(e)
            )
            raise

    async def _initialize_adapters(self) -> None:
        """Initialize chat and code adapters."""
        try:
            # Initialize ChatAdapter
            chat_config = ChatAdapter.default_config()
            self.chat_adapter = ChatAdapter(chat_config)
            await self.chat_adapter.initialize()

            # Initialize CodeAdapter
            code_config = CodeAdapter.default_config()
            self.code_adapter = CodeAdapter(code_config)
            await self.code_adapter.initialize()

            # Register adapters
            self.adapter_registry.register_adapter(
                "chat",
                ChatAdapter,
                chat_config,
                {"description": "Chat and conversation data adapter"},
            )

            self.adapter_registry.register_adapter(
                "code",
                CodeAdapter,
                code_config,
                {"description": "Code analysis and file system adapter"},
            )

            self.logger.info("Adapters initialized and registered")

        except Exception as e:
            self.logger.error("Failed to initialize adapters", error=str(e))
            raise

    def get_adapter_for_tool(
        self, tool_name: str
    ) -> Optional[Union[ChatAdapter, CodeAdapter]]:
        """Get the appropriate adapter for a given tool."""
        if tool_name in self.chat_tools:
            return self.chat_adapter
        elif tool_name in self.code_tools:
            return self.code_adapter
        else:
            # System tools use direct database access
            return None

    async def execute_tool_with_context(
        self, tool_name: str, tool_func: Callable, *args, **kwargs
    ) -> Dict[str, Any]:
        """Execute a tool with appropriate context backend integration."""
        try:
            # Get the appropriate adapter
            adapter = self.get_adapter_for_tool(tool_name)

            if adapter:
                # Tools with adapter integration
                self.logger.debug(
                    "Executing tool with adapter context",
                    tool=tool_name,
                    adapter_type=type(adapter).__name__,
                )

                # Add adapter context to kwargs
                kwargs["_adapter"] = adapter
                kwargs["_context_db"] = self.db

            else:
                # System tools with direct database access
                self.logger.debug(
                    "Executing system tool with direct database access", tool=tool_name
                )
                kwargs["_context_db"] = self.db

            # Execute the tool function
            result = await tool_func(*args, **kwargs)

            # Add metadata about the execution context
            if isinstance(result, dict):
                result["_context_meta"] = {
                    "tool_name": tool_name,
                    "adapter_type": type(adapter).__name__ if adapter else "direct_db",
                    "execution_timestamp": asyncio.get_event_loop().time(),
                }

            return result

        except Exception as e:
            self.logger.error(
                "Error executing tool with context", tool=tool_name, error=str(e)
            )
            raise

    async def get_context_statistics(self) -> Dict[str, Any]:
        """Get statistics about the context system."""
        try:
            stats = {
                "adapters": {},
                "database": {},
                "tools": {
                    "chat_tools": len(self.chat_tools),
                    "code_tools": len(self.code_tools),
                    "system_tools": len(self.system_tools),
                    "total_tools": len(self.chat_tools)
                    + len(self.code_tools)
                    + len(self.system_tools),
                },
            }

            # Chat adapter stats
            if self.chat_adapter:
                chat_stats = await self.chat_adapter.get_status()
                stats["adapters"]["chat"] = chat_stats

            # Code adapter stats
            if self.code_adapter:
                code_stats = await self.code_adapter.get_status()
                stats["adapters"]["code"] = code_stats

            # Database stats
            if self.db:
                # Get some basic database statistics
                context_items_count = await self.db.fetchval(
                    "SELECT COUNT(*) FROM context_items"
                )
                stats["database"]["context_items_count"] = context_items_count

            return stats

        except Exception as e:
            self.logger.error("Error getting context statistics", error=str(e))
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.chat_adapter:
                await self.chat_adapter.cleanup()

            if self.code_adapter:
                await self.code_adapter.cleanup()

            self.logger.info("Context tool registry cleaned up")

        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))


# Global registry instance
_context_registry: Optional[ContextToolRegistry] = None


async def get_context_registry() -> ContextToolRegistry:
    """Get or create the global context tool registry."""
    global _context_registry

    if _context_registry is None:
        _context_registry = ContextToolRegistry()
        await _context_registry.initialize()

    return _context_registry


def context_aware_tool(tool_name: str):
    """Decorator to make a tool context-aware with automatic adapter integration."""

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            registry = await get_context_registry()
            return await registry.execute_tool_with_context(
                tool_name, func, *args, **kwargs
            )

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__ = func.__annotations__

        return wrapper

    return decorator
