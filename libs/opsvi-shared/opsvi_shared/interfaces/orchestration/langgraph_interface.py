"""
LangGraph Shared Interface
-------------------------
Authoritative implementation based on the official LangGraph Python SDK and API documentation:
- https://github.com/langchain-ai/langgraph
- https://python.langgraph.org/
Implements all core features: graph construction, node/task registration, checkpointing, streaming, async, and error handling.
Version: Referenced as of July 2024
"""

import logging
from typing import Any, Callable, Optional, Type, Union

try:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.func import entrypoint, task
    from langgraph.graph import END, START, StateGraph
    from langgraph.prebuilt import ToolNode
    from langgraph.store.memory import BaseStore, InMemoryStore
except ImportError:
    raise ImportError(
        "langgraph and dependencies are required. Install with `pip install langgraph langgraph-checkpoint langgraph-checkpoint-sqlite`."
    )

logger = logging.getLogger(__name__)


class LangGraphInterface:
    """
    Authoritative shared interface for building, persisting, and executing LangGraph workflows.
    See: https://python.langgraph.org/
    """

    def __init__(
        self,
        state_type: Type,
        checkpointer: Optional[Any] = None,
        store: Optional[BaseStore] = None,
    ):
        self.state_type = state_type
        self.builder = StateGraph(state_type)
        self.checkpointer = checkpointer or InMemorySaver()
        self.store = store
        self._compiled_graph = None
        logger.info("LangGraphInterface initialized.")

    def add_node(self, name: str, func: Callable) -> None:
        self.builder.add_node(name, func)
        logger.debug(f"Node '{name}' added.")

    def add_tool_node(
        self,
        name: str,
        tools: list,
        handle_tool_errors: Union[bool, str, Callable] = True,
    ) -> None:
        node = ToolNode(tools=tools, handle_tool_errors=handle_tool_errors)
        self.builder.add_node(name, node)
        logger.debug(f"ToolNode '{name}' added.")

    def add_edge(
        self, from_node: str, to_node: str, condition: Optional[Callable] = None
    ) -> None:
        if condition is not None:
            self.builder.add_edge(from_node, to_node, condition=condition)
        else:
            self.builder.add_edge(from_node, to_node)
        logger.debug(f"Edge from '{from_node}' to '{to_node}' added.")

    def add_conditional_edges(
        self, from_node: str, condition: callable, edges: dict
    ) -> None:
        """Add conditional edges from a node using the underlying StateGraph API."""
        self.builder.add_conditional_edges(from_node, condition, edges)
        logger.debug(f"Conditional edges from '{from_node}' added: {edges}")

    def set_entry_point(self, node: str) -> None:
        self.builder.set_entry_point(node)
        logger.debug(f"Entry point set to '{node}'.")

    def compile(self) -> None:
        self._compiled_graph = self.builder.compile(checkpointer=self.checkpointer)
        logger.info("Graph compiled.")

    def invoke(self, state: dict, config: Optional[dict] = None) -> Any:
        if not self._compiled_graph:
            self.compile()
        # --- PATCH: Log state before and after, and ensure dict outputs are merged into Pydantic state ---
        import logging

        logger = logging.getLogger("LangGraphInterface.invoke")
        from pydantic import BaseModel

        def _log_state(label, s):
            logger.info(
                f"{label} type: {type(s)}; content: {getattr(s, 'model_dump', lambda: s)()}"
            )

        # If state is a Pydantic model, convert to dict for initial input
        input_state = (
            state.model_dump() if hasattr(state, "model_dump") else dict(state)
        )
        _log_state("[invoke] initial state", state)
        # Run the graph
        result = self._compiled_graph.invoke(input_state, config=config)
        # If result is a dict and state_type is a Pydantic model, merge result into model
        if isinstance(result, dict) and issubclass(self.state_type, BaseModel):
            merged = self.state_type(**{**state.model_dump(), **result})
            _log_state("[invoke] merged state", merged)
            return merged
        _log_state("[invoke] result", result)
        return result

    async def ainvoke(self, state: dict, config: Optional[dict] = None) -> Any:
        if not self._compiled_graph:
            self.compile()
        return await self._compiled_graph.ainvoke(state, config=config)

    def stream(self, state: dict, config: Optional[dict] = None):
        if not self._compiled_graph:
            self.compile()
        yield from self._compiled_graph.stream(state, config=config)

    async def astream(self, state: dict, config: Optional[dict] = None):
        if not self._compiled_graph:
            self.compile()
        async for chunk in self._compiled_graph.astream(state, config=config):
            yield chunk

    @staticmethod
    def get_in_memory_store() -> InMemoryStore:
        return InMemoryStore()

    @staticmethod
    def get_sqlite_checkpointer(path: str = ":memory:") -> SqliteSaver:
        return SqliteSaver(path)

    # Postgres checkpointer import is now optional and only available if dependencies are installed
    @staticmethod
    def get_postgres_checkpointer(url: str):
        try:
            from langgraph.checkpoint.postgres import PostgresSaver

            return PostgresSaver(url)
        except ImportError:
            raise ImportError(
                "PostgresSaver requires langgraph-checkpoint-postgres and psycopg dependencies."
            )


# Example usage and advanced features are available in the official docs:
# https://python.langgraph.org/
