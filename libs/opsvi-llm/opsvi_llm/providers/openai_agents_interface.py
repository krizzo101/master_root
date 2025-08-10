import asyncio
from collections.abc import Awaitable
import functools
import logging
import os
from typing import Any, Callable, Dict, List, Optional

from agents import (
    Agent,
    FileSearchTool,
    RunContextWrapper,
    Runner,
    WebSearchTool,
    enable_verbose_stdout_logging,
    function_tool,
)

logger = logging.getLogger(__name__)


class OpenAIAgentsInterface:
    """
    Modernized shared interface for OpenAI Agents/Assistants v2 API (python SDK).
    - Full agent, tool, thread, message, vector store, and orchestration support
    - Async, streaming, batch, error handling, logging, tracing, context, config
    - Advanced usage and extensibility patterns
    """

    def __init__(self, api_key_env: str = "OPENAI_API_KEY") -> None:
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            logger.error(f"Environment variable '{api_key_env}' not set.")
            raise OSError(f"Please set the '{api_key_env}' environment variable.")
        self.config = {
            "timeout": 60,
            "max_turns": 10,
            "debug": False,
            "tracing": False,
        }
        logger.info("OpenAIAgentsInterface initialized.")

    # --- Agent Creation & Tooling ---
    def create_agent(
        self,
        name: str,
        instructions: str,
        tools: Optional[List[Callable]] = None,
        handoffs: Optional[List[Agent]] = None,
        guardrails: Optional[List[Any]] = None,
        output_type: Optional[Any] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> Agent:
        """
        Create an Agent with tools, handoffs, guardrails, output type, and model.
        """
        agent = Agent(
            name=name,
            instructions=instructions,
            tools=tools or [],
            handoffs=handoffs or [],
            guardrails=guardrails or [],
            output_type=output_type,
            model=model,
            **kwargs,
        )
        logger.debug(f"Created agent: {agent}")
        return agent

    def register_tool(self, func: Callable) -> Callable:
        """Decorate a function as an agent tool."""
        return function_tool(func)

    def create_file_search_tool(
        self, vector_store_ids: Optional[List[str]] = None, max_num_results: int = 3
    ):
        return FileSearchTool(
            max_num_results=max_num_results, vector_store_ids=vector_store_ids or []
        )

    def create_web_search_tool(self):
        return WebSearchTool()

    # --- Agent Run (Sync/Async/Streaming) ---
    def run_agent_sync(
        self,
        agent: Agent,
        input_text: Any,
        max_turns: Optional[int] = None,
        context: Any = None,
    ) -> Any:
        """Run an agent synchronously."""
        return Runner.run_sync(
            agent,
            input_text,
            max_turns=max_turns or self.config["max_turns"],
            context=context,
        )

    async def run_agent_async(
        self,
        agent: Agent,
        input_text: Any,
        max_turns: Optional[int] = None,
        context: Any = None,
    ) -> Any:
        """Run an agent asynchronously."""
        return await Runner.run(
            agent,
            input_text,
            max_turns=max_turns or self.config["max_turns"],
            context=context,
        )

    async def run_agent_streamed(
        self, agent: Agent, input_text: Any, context: Any = None
    ) -> Awaitable:
        """Run an agent and stream events (async)."""
        result = Runner.run_streamed(agent, input=input_text, context=context)
        async for event in result.stream_events():
            yield event

    # --- Batch/Orchestration ---
    async def batch_run_agents(self, agent_inputs: List[Dict[str, Any]]) -> List[Any]:
        """Run multiple agents asynchronously in batch."""
        tasks = [self.run_agent_async(**params) for params in agent_inputs]
        return await asyncio.gather(*tasks)

    def as_tool(
        self,
        agent: Agent,
        tool_name: str,
        tool_description: str,
        custom_output_extractor: Optional[Callable] = None,
    ):
        """Expose an agent as a tool for orchestration."""
        return agent.as_tool(
            tool_name=tool_name,
            tool_description=tool_description,
            custom_output_extractor=custom_output_extractor,
        )

    # --- Context/Customization ---
    def create_context(self, **kwargs) -> RunContextWrapper:
        """Create a context object for agent runs."""
        return RunContextWrapper(context=kwargs)

    # --- Error Handling, Logging, Tracing ---
    def log_call(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(
                f"Calling {func.__name__} with args={args[1:]}, kwargs={kwargs}"
            )
            try:
                result = func(*args, **kwargs)
                logger.info(f"{func.__name__} result: {str(result)[:200]}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} error: {e}")
                raise

        return wrapper

    def enable_verbose_logging(self):
        enable_verbose_stdout_logging()
        logger.info("Verbose logging enabled.")

    def enable_tracing(self):
        self.config["tracing"] = True
        logger.info("Tracing enabled.")

    # --- Config ---
    def set_timeout(self, timeout: float):
        self.config["timeout"] = timeout

    def set_max_turns(self, max_turns: int):
        self.config["max_turns"] = max_turns

    def set_debug(self, debug: bool):
        self.config["debug"] = debug

    # --- Advanced Usage Example ---
    """
    Example advanced usage:
    >>> interface = OpenAIAgentsInterface()
    >>> agent = interface.create_agent(
    ...     name="Assistant",
    ...     instructions="You are a helpful assistant.",
    ...     tools=[interface.create_web_search_tool()],
    ... )
    >>> # Synchronous run
    >>> result = interface.run_agent_sync(agent, "Write a haiku about recursion in programming.")
    >>> # Async run
    >>> import asyncio
    >>> result = asyncio.run(interface.run_agent_async(agent, "Write a haiku about recursion in programming."))
    >>> # Streaming run
    >>> async def stream():
    ...     async for event in interface.run_agent_streamed(agent, "Tell me a joke."):
    ...         print(event)
    >>> asyncio.run(stream())
    >>> # Batch run
    >>> batch = [
    ...     {"agent": agent, "input_text": "Hi 1"},
    ...     {"agent": agent, "input_text": "Hi 2"},
    ... ]
    >>> results = asyncio.run(interface.batch_run_agents(batch))
    >>> # Agent as tool
    >>> tool = interface.as_tool(agent, tool_name="assistant_tool", tool_description="General assistant tool")
    """
