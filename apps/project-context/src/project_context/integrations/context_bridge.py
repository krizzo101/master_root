"""Context Bridge for integrating IDE context with database queries."""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..db.connections import get_db

logger = logging.getLogger(__name__)


@dataclass
class IDEContext:
    """Represents the current IDE context state."""

    active_file: Optional[str] = None
    cursor_position: Optional[Dict[str, int]] = None
    selection: Optional[Dict[str, Any]] = None
    open_files: List[str] = None
    project_root: Optional[str] = None
    workspace_folders: List[str] = None
    language: Optional[str] = None
    git_branch: Optional[str] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.open_files is None:
            self.open_files = []
        if self.workspace_folders is None:
            self.workspace_folders = []
        if self.last_updated is None:
            self.last_updated = datetime.now()


class ContextBridge:
    """
    Manages IDE context integration with database queries.

    Subscribes to IDE context events via Redis pub/sub, caches the current
    IDE state in memory, and provides methods to merge IDE context with
    database query results.
    """

    def __init__(self):
        self.db = None
        self.current_context: Optional[IDEContext] = None
        self.pubsub = None
        self.subscription_task = None
        self._context_cache: Dict[str, Any] = {}
        self._running = False

    async def initialize(self):
        """Initialize the context bridge with database connections."""
        self.db = await get_db()
        if not self.db.redis_client:
            logger.warning("Redis client not available - Context Bridge disabled")
            return False

        logger.info("Context Bridge initialized successfully")
        return True

    async def start_subscription(self, channel: str = "context:updates"):
        """
        Start subscribing to IDE context events.

        Args:
            channel: Redis channel to subscribe to for context updates
        """
        if not self.db or not self.db.redis_client:
            logger.error("Cannot start subscription - Redis not available")
            return

        try:
            self.pubsub = self.db.redis_client.pubsub()
            await self.pubsub.subscribe(channel)

            self._running = True
            self.subscription_task = asyncio.create_task(self._listen_for_updates())

            logger.info(f"Started Context Bridge subscription on channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to start Context Bridge subscription: {e}")
            raise

    async def stop_subscription(self):
        """Stop the context subscription and cleanup resources."""
        self._running = False

        if self.subscription_task:
            self.subscription_task.cancel()
            try:
                await self.subscription_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()

        logger.info("Context Bridge subscription stopped")

    async def _listen_for_updates(self):
        """Internal method to listen for context updates from Redis."""
        try:
            async for message in self.pubsub.listen():
                if not self._running:
                    break

                if message["type"] == "message":
                    try:
                        context_data = json.loads(message["data"])
                        await self._update_context(context_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse context update: {e}")
                    except Exception as e:
                        logger.error(f"Error processing context update: {e}")
        except asyncio.CancelledError:
            logger.info("Context subscription listener cancelled")
        except Exception as e:
            logger.error(f"Context subscription listener error: {e}")

    async def _update_context(self, context_data: Dict[str, Any]):
        """Update the cached IDE context with new data."""
        try:
            # Convert datetime strings back to datetime objects if present
            if "last_updated" in context_data and isinstance(
                context_data["last_updated"], str
            ):
                context_data["last_updated"] = datetime.fromisoformat(
                    context_data["last_updated"]
                )

            self.current_context = IDEContext(**context_data)

            # Update the context cache
            self._context_cache.update(context_data)

            logger.debug(f"Updated IDE context: {self.current_context.active_file}")
        except Exception as e:
            logger.error(f"Failed to update IDE context: {e}")

    async def get_current_context(self) -> Optional[IDEContext]:
        """
        Get the current IDE context.

        Returns:
            Current IDE context or None if not available
        """
        # If we don't have cached context, try to load from Redis
        if not self.current_context and self.db and self.db.redis_client:
            try:
                cached_data = await self.db.get_ide_context("current")
                if cached_data:
                    await self._update_context(cached_data)
            except Exception as e:
                logger.error(f"Failed to load context from Redis: {e}")

        return self.current_context

    async def set_context(self, context: Union[IDEContext, Dict[str, Any]]):
        """
        Manually set the IDE context (useful for testing or direct updates).

        Args:
            context: IDE context as IDEContext object or dictionary
        """
        if isinstance(context, dict):
            context = IDEContext(**context)

        self.current_context = context
        self._context_cache.update(asdict(context))

        # Persist to Redis if available
        if self.db and self.db.redis_client:
            try:
                context_dict = asdict(context)
                # Convert datetime to string for JSON serialization
                if context_dict.get("last_updated"):
                    context_dict["last_updated"] = context_dict[
                        "last_updated"
                    ].isoformat()

                await self.db.redis_client.set(
                    "context:current",
                    json.dumps(context_dict),
                    ex=3600,  # Expire after 1 hour
                )
            except Exception as e:
                logger.error(f"Failed to persist context to Redis: {e}")

    def merge_with_query_results(
        self, query_results: List[Dict[str, Any]], include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Merge database query results with current IDE context.

        Args:
            query_results: Results from database queries
            include_context: Whether to include full IDE context in response

        Returns:
            Dictionary containing merged results and context
        """
        merged_result = {
            "query_results": query_results,
            "result_count": len(query_results),
            "timestamp": datetime.now().isoformat(),
        }

        if include_context and self.current_context:
            context_dict = asdict(self.current_context)
            # Convert datetime to string for JSON serialization
            if context_dict.get("last_updated"):
                context_dict["last_updated"] = context_dict["last_updated"].isoformat()

            merged_result["ide_context"] = context_dict

            # Add context-aware enhancements
            if self.current_context.active_file:
                merged_result["context_relevance"] = self._calculate_relevance(
                    query_results, self.current_context.active_file
                )

        return merged_result

    def _calculate_relevance(
        self, results: List[Dict[str, Any]], active_file: str
    ) -> Dict[str, Any]:
        """
        Calculate relevance scores based on current IDE context.

        Args:
            results: Query results to analyze
            active_file: Currently active file in IDE

        Returns:
            Dictionary with relevance information
        """
        relevance_info = {
            "active_file": active_file,
            "file_matches": 0,
            "related_files": [],
        }

        for result in results:
            # Check if result contains file path information
            file_fields = ["file_path", "path", "filename", "source_file"]
            result_file = None

            for field in file_fields:
                if field in result and result[field]:
                    result_file = result[field]
                    break

            if result_file:
                if result_file == active_file:
                    relevance_info["file_matches"] += 1
                elif result_file not in relevance_info["related_files"]:
                    relevance_info["related_files"].append(result_file)

        return relevance_info

    async def get_context_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current context state.

        Returns:
            Summary dictionary with context information
        """
        summary = {
            "bridge_status": "active" if self._running else "inactive",
            "has_context": self.current_context is not None,
            "redis_available": self.db and self.db.redis_client is not None,
            "subscription_active": self.subscription_task is not None
            and not self.subscription_task.done(),
        }

        if self.current_context:
            summary["context_summary"] = {
                "active_file": self.current_context.active_file,
                "open_files_count": len(self.current_context.open_files or []),
                "project_root": self.current_context.project_root,
                "language": self.current_context.language,
                "last_updated": self.current_context.last_updated.isoformat()
                if self.current_context.last_updated
                else None,
            }

        return summary


# Global context bridge instance
context_bridge = ContextBridge()


async def initialize_context_bridge() -> ContextBridge:
    """Initialize and return the global context bridge instance."""
    await context_bridge.initialize()
    return context_bridge


async def get_context_bridge() -> ContextBridge:
    """Get the global context bridge instance."""
    if not context_bridge.db:
        await initialize_context_bridge()
    return context_bridge
