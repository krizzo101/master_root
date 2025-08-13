"""
Context Bridge Client Library

Provides easy access to context bridge for MCP agents.
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import logging
import httpx
from pydantic import ValidationError

from .models import (
    IDEContext,
    ContextEvent,
    ContextEventType,
    ContextQuery,
    ContextSubscription,
    DiagnosticInfo,
)

logger = logging.getLogger(__name__)


class ContextBridgeClient:
    """
    Client for accessing Context Bridge from agents

    Features:
    - Async context queries with caching
    - Event subscription support
    - Automatic reconnection
    - Performance optimized
    """

    def __init__(
        self,
        bridge_url: str = "http://localhost:8000",
        cache_ttl: int = 60,
        auto_reconnect: bool = True,
    ):
        self.bridge_url = bridge_url
        self.cache_ttl = cache_ttl
        self.auto_reconnect = auto_reconnect

        # HTTP client for MCP calls
        self.client = httpx.AsyncClient(timeout=30.0)

        # Context cache
        self._context_cache: Optional[IDEContext] = None
        self._cache_timestamp: Optional[datetime] = None

        # Event handlers
        self._event_handlers: Dict[ContextEventType, List[Callable]] = {}

        # Connection state
        self.connected = False
        self._reconnect_task: Optional[asyncio.Task] = None

    async def get_context(
        self, query: Optional[ContextQuery] = None, force_refresh: bool = False
    ) -> Optional[IDEContext]:
        """
        Get current IDE context

        Args:
            query: Optional query parameters to filter context
            force_refresh: Bypass cache and get fresh context

        Returns:
            Current IDE context or None if unavailable
        """
        try:
            # Check cache unless forced refresh
            if not force_refresh and self._is_cache_valid():
                logger.debug("Returning cached context")
                return self._context_cache

            # Prepare query parameters
            params = query.dict() if query else {}

            # Call context bridge
            response = await self.client.post(
                f"{self.bridge_url}/tools/get_ide_context", json={"query": params}
            )

            if response.status_code == 200:
                data = response.json()
                if "error" not in data:
                    context = IDEContext(**data)
                    self._update_cache(context)
                    return context
                else:
                    logger.error(f"Context bridge error: {data['error']}")
                    return None
            else:
                logger.error(f"HTTP error {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return self._context_cache  # Return cached version as fallback

    async def get_active_file_content(self) -> Optional[str]:
        """
        Get content of currently active file

        Returns:
            File content or None if no active file
        """
        context = await self.get_context()
        if context and context.active_file:
            try:
                with open(context.active_file, "r") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read active file: {e}")
        return None

    async def get_diagnostics(
        self,
        file_path: Optional[str] = None,
        severity_filter: Optional[List[str]] = None,
    ) -> List[DiagnosticInfo]:
        """
        Get diagnostics for a file or all files

        Args:
            file_path: Optional file to filter diagnostics
            severity_filter: Optional list of severities to include

        Returns:
            List of diagnostic messages
        """
        query = ContextQuery(
            include_diagnostics=True, diagnostic_severity_filter=severity_filter
        )

        context = await self.get_context(query)
        if not context:
            return []

        if file_path:
            return context.get_relevant_diagnostics(file_path)
        return context.diagnostics

    async def subscribe(
        self,
        event_types: List[ContextEventType],
        handler: Callable[[ContextEvent], None],
        subscriber_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to context events

        Args:
            event_types: List of event types to subscribe to
            handler: Callback function for events
            subscriber_id: Optional custom subscriber ID

        Returns:
            Subscription ID
        """
        if subscriber_id is None:
            subscriber_id = f"agent_{id(self)}_{datetime.utcnow().timestamp()}"

        # Register handler locally
        for event_type in event_types:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)

        # Subscribe on server
        subscription = ContextSubscription(
            subscriber_id=subscriber_id, event_types=event_types
        )

        response = await self.client.post(
            f"{self.bridge_url}/tools/subscribe_to_context",
            json={"subscription_data": subscription.dict()},
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Subscribed with ID: {subscriber_id}")
            return subscriber_id
        else:
            raise Exception(f"Subscription failed: {response.status_code}")

    async def wait_for_file_change(
        self, timeout: Optional[float] = None
    ) -> Optional[str]:
        """
        Wait for active file to change

        Args:
            timeout: Optional timeout in seconds

        Returns:
            New active file path or None if timeout
        """
        event_received = asyncio.Event()
        new_file = None

        def handler(event: ContextEvent):
            nonlocal new_file
            if event.event_type == ContextEventType.FILE_CHANGED:
                new_file = event.event_data.get("new_file")
                event_received.set()

        sub_id = await self.subscribe([ContextEventType.FILE_CHANGED], handler)

        try:
            await asyncio.wait_for(event_received.wait(), timeout)
            return new_file
        except asyncio.TimeoutError:
            return None

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self._context_cache or not self._cache_timestamp:
            return False

        age = (datetime.utcnow() - self._cache_timestamp).total_seconds()
        return age < self.cache_ttl

    def _update_cache(self, context: IDEContext):
        """Update context cache"""
        self._context_cache = context
        self._cache_timestamp = datetime.utcnow()

    async def close(self):
        """Close client connections"""
        await self.client.aclose()


class EnhancedAgentBase:
    """
    Base class for context-aware agents

    Automatically integrates with Context Bridge
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.context_client = ContextBridgeClient()
        self.current_context: Optional[IDEContext] = None

    async def execute_with_context(self, task: str, **kwargs) -> Any:
        """
        Execute task with automatic context enhancement

        Args:
            task: Task to execute
            **kwargs: Additional parameters

        Returns:
            Task execution result
        """
        # Get current context
        self.current_context = await self.context_client.get_context()

        # Enhance task with context
        enhanced_task = self._enhance_task_with_context(task)

        # Execute core task
        return await self.execute_core(enhanced_task, **kwargs)

    def _enhance_task_with_context(self, task: str) -> str:
        """
        Enhance task description with IDE context

        Args:
            task: Original task

        Returns:
            Enhanced task with context
        """
        if not self.current_context:
            return task

        context_info = []

        if self.current_context.active_file:
            context_info.append(f"Current file: {self.current_context.active_file}")

        if self.current_context.selection:
            context_info.append(
                f"Selected text (lines {self.current_context.selection.start_line}-"
                f"{self.current_context.selection.end_line}): "
                f"{self.current_context.selection.selected_text[:100]}..."
            )

        diagnostics = self.current_context.get_relevant_diagnostics()
        if diagnostics:
            errors = [d for d in diagnostics if d.severity == "error"]
            warnings = [d for d in diagnostics if d.severity == "warning"]
            context_info.append(
                f"Current file has {len(errors)} errors, {len(warnings)} warnings"
            )

        if context_info:
            context_str = "\n".join(context_info)
            return f"{task}\n\nContext:\n{context_str}"

        return task

    async def execute_core(self, task: str, **kwargs) -> Any:
        """
        Core execution method to be implemented by specific agents

        Args:
            task: Enhanced task to execute
            **kwargs: Additional parameters

        Returns:
            Execution result
        """
        raise NotImplementedError("Agents must implement execute_core method")


# Example usage for quick testing
async def example_usage():
    """Example of using the Context Bridge Client"""

    # Create client
    client = ContextBridgeClient()

    # Get current context
    context = await client.get_context()
    if context:
        print(f"Active file: {context.active_file}")
        print(f"Open tabs: {context.open_tabs}")
        print(f"Diagnostics: {len(context.diagnostics)} issues")

    # Get diagnostics for current file
    diagnostics = await client.get_diagnostics()
    for diag in diagnostics[:5]:  # Show first 5
        print(f"{diag.severity}: {diag.message} at line {diag.line}")

    # Subscribe to file changes
    def on_file_change(event: ContextEvent):
        print(f"File changed: {event.event_data}")

    await client.subscribe([ContextEventType.FILE_CHANGED], on_file_change)

    # Clean up
    await client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
