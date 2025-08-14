"""
Context Bridge MCP Server Implementation

Provides IDE context to all MCP agents through a unified interface.
"""

import asyncio
import json
from typing import Dict, List, Optional, Set, Union
from datetime import datetime, timedelta
import logging
from pathlib import Path

from fastmcp import FastMCP
from pydantic import ValidationError

from .models import (
    IDEContext,
    ContextEvent,
    ContextEventType,
    ContextQuery,
    ContextSubscription,
    DiagnosticInfo,
    FileSelection,
)
from .config import ContextBridgeConfig
from .pubsub import PubSubBackend, InMemoryPubSub, RedisPubSubAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextBridgeServer:
    """
    MCP Server that bridges IDE context to agents

    Features:
    - Maintains current IDE context state
    - Publishes context changes via Redis or in-memory pub/sub
    - Provides query interface for agents
    - Caches context for performance
    - Automatic fallback from Redis to in-memory when Redis is unavailable
    """

    def __init__(self, config: Optional[ContextBridgeConfig] = None):
        self.config = config or ContextBridgeConfig()
        self.mcp = FastMCP("context-bridge")
        self.pubsub_backend: Optional[PubSubBackend] = None
        self.backend_type: str = "none"  # 'redis', 'memory', or 'none'

        # Current context state
        self.current_context: Optional[IDEContext] = None
        self.context_history: List[IDEContext] = []
        self.max_history_size = self.config.max_history_size

        # Subscriptions
        self.subscriptions: Dict[str, ContextSubscription] = {}

        # Performance metrics
        self.metrics = {
            "queries_served": 0,
            "events_published": 0,
            "avg_query_time_ms": 0,
        }

        # Register MCP tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tool endpoints"""

        @self.mcp.tool()
        async def get_ide_context(query: Optional[Dict] = None) -> Dict:
            """
            Get current IDE context

            Args:
                query: Optional ContextQuery parameters

            Returns:
                Current IDE context matching query parameters
            """
            start_time = datetime.utcnow()

            try:
                if not self.current_context:
                    return {
                        "error": "No context available",
                        "status": "not_initialized",
                    }

                # Parse query if provided
                context_query = ContextQuery(**query) if query else ContextQuery()

                # Build response based on query
                response = {
                    "project_root": self.current_context.project_root,
                    "timestamp": self.current_context.timestamp.isoformat(),
                }

                if context_query.include_selection and self.current_context.selection:
                    response["selection"] = self.current_context.selection.dict()

                if context_query.include_diagnostics:
                    diagnostics = self.current_context.diagnostics
                    if context_query.diagnostic_severity_filter:
                        diagnostics = [
                            d
                            for d in diagnostics
                            if d.severity in context_query.diagnostic_severity_filter
                        ]
                    response["diagnostics"] = [d.dict() for d in diagnostics]

                if context_query.include_open_tabs:
                    response["open_tabs"] = self.current_context.open_tabs

                response["active_file"] = self.current_context.active_file

                # Update metrics
                self.metrics["queries_served"] += 1
                query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                self._update_avg_query_time(query_time)

                return response

            except Exception as e:
                logger.error(f"Error getting IDE context: {e}")
                return {"error": str(e), "status": "error"}

        @self.mcp.tool()
        async def update_ide_context(context_data: Dict) -> Dict:
            """
            Update IDE context (called by IDE integration)

            Args:
                context_data: New context information

            Returns:
                Confirmation of update
            """
            try:
                # Parse and validate context
                new_context = IDEContext(**context_data)

                # Store previous context in history
                if self.current_context:
                    self.context_history.append(self.current_context)
                    if len(self.context_history) > self.max_history_size:
                        self.context_history.pop(0)

                # Update current context
                old_context = self.current_context
                self.current_context = new_context

                # Publish context change event
                event = ContextEvent(
                    event_type=ContextEventType.CONTEXT_SYNC,
                    event_data={"context": new_context.dict()},
                )
                await self._publish_event(event)

                # Detect and publish specific change events
                await self._detect_and_publish_changes(old_context, new_context)

                return {
                    "status": "success",
                    "message": "Context updated successfully",
                    "timestamp": new_context.timestamp.isoformat(),
                }

            except ValidationError as e:
                logger.error(f"Invalid context data: {e}")
                return {"status": "error", "error": str(e)}
            except Exception as e:
                logger.error(f"Error updating context: {e}")
                return {"status": "error", "error": str(e)}

        @self.mcp.tool()
        async def subscribe_to_context(subscription_data: Dict) -> Dict:
            """
            Subscribe to context change events

            Args:
                subscription_data: ContextSubscription parameters

            Returns:
                Subscription confirmation with ID
            """
            try:
                subscription = ContextSubscription(**subscription_data)
                self.subscriptions[subscription.subscriber_id] = subscription

                logger.info(f"New subscription: {subscription.subscriber_id}")

                return {
                    "status": "success",
                    "subscription_id": subscription.subscriber_id,
                    "subscribed_events": subscription.event_types,
                }

            except Exception as e:
                logger.error(f"Subscription error: {e}")
                return {"status": "error", "error": str(e)}

        @self.mcp.tool()
        async def get_context_history(limit: int = 10) -> Dict:
            """
            Get context history

            Args:
                limit: Maximum number of historical contexts to return

            Returns:
                List of historical contexts
            """
            history = self.context_history[-limit:]
            return {
                "history": [ctx.dict() for ctx in history],
                "total_count": len(self.context_history),
            }

        @self.mcp.tool()
        async def get_metrics() -> Dict:
            """Get server performance metrics"""
            return self.metrics

    async def _publish_event(self, event: ContextEvent):
        """Publish event to pub/sub backend"""
        try:
            if self.pubsub_backend:
                channel = f"context:{event.event_type.value}"
                message = event.to_redis_message()  # JSON format works for both backends
                delivered = await self.pubsub_backend.publish(channel, message)
                self.metrics["events_published"] += 1
                logger.debug(f"Published event: {event.event_type} to {delivered} subscribers")
            else:
                logger.debug(f"No pub/sub backend available, event not published: {event.event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    async def _detect_and_publish_changes(
        self, old: Optional[IDEContext], new: IDEContext
    ):
        """Detect specific changes and publish appropriate events"""
        if not old:
            return

        # File change detection
        if old.active_file != new.active_file:
            event = ContextEvent(
                event_type=ContextEventType.FILE_CHANGED,
                event_data={"old_file": old.active_file, "new_file": new.active_file},
            )
            await self._publish_event(event)

        # Selection change detection
        if old.selection != new.selection:
            event = ContextEvent(
                event_type=ContextEventType.SELECTION_CHANGED,
                event_data={
                    "selection": new.selection.dict() if new.selection else None
                },
            )
            await self._publish_event(event)

        # Diagnostics change detection
        if len(old.diagnostics) != len(new.diagnostics):
            event = ContextEvent(
                event_type=ContextEventType.DIAGNOSTICS_UPDATED,
                event_data={
                    "diagnostic_count": len(new.diagnostics),
                    "errors": len(
                        [d for d in new.diagnostics if d.severity == "error"]
                    ),
                    "warnings": len(
                        [d for d in new.diagnostics if d.severity == "warning"]
                    ),
                },
            )
            await self._publish_event(event)

    def _update_avg_query_time(self, query_time_ms: float):
        """Update rolling average query time"""
        current_avg = self.metrics["avg_query_time_ms"]
        count = self.metrics["queries_served"]
        self.metrics["avg_query_time_ms"] = (
            current_avg * (count - 1) + query_time_ms
        ) / count

    async def start(self):
        """Start the server and initialize pub/sub backend"""
        # Configure logging
        self.config.configure_logging()
        
        backend_mode = self.config.get_effective_backend()
        
        if backend_mode == "memory":
            # Use in-memory pub/sub
            self.pubsub_backend = InMemoryPubSub()
            self.backend_type = "memory"
            logger.info("Using in-memory pub/sub backend")
        
        elif backend_mode == "redis":
            # Try Redis only
            if await self._init_redis():
                self.backend_type = "redis"
                logger.info("Using Redis pub/sub backend")
            else:
                logger.error("Redis required but not available")
                raise RuntimeError("Redis backend required but connection failed")
        
        else:  # auto mode
            # Try Redis first, fallback to in-memory
            if await self._init_redis():
                self.backend_type = "redis"
                logger.info("Using Redis pub/sub backend")
            else:
                logger.warning("Redis not available, falling back to in-memory pub/sub")
                self.pubsub_backend = InMemoryPubSub()
                self.backend_type = "memory"
                logger.info("Using in-memory pub/sub backend")
        
        logger.info(f"Context Bridge Server started with {self.backend_type} backend")
    
    async def _init_redis(self) -> bool:
        """Initialize Redis connection and adapter"""
        try:
            import redis.asyncio as redis
            
            redis_client = await redis.from_url(
                self.config.redis_url,
                socket_connect_timeout=self.config.redis_connect_timeout,
                retry_on_timeout=self.config.redis_retry_on_timeout,
                max_connections=self.config.redis_max_connections
            )
            
            # Test connection
            await redis_client.ping()
            
            # Create adapter
            adapter = RedisPubSubAdapter(redis_client)
            await adapter.initialize()
            self.pubsub_backend = adapter
            
            return True
            
        except ImportError:
            logger.warning("Redis library not installed, cannot use Redis backend")
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return False

    async def stop(self):
        """Cleanup connections"""
        if self.pubsub_backend:
            await self.pubsub_backend.close()
            logger.info(f"Closed {self.backend_type} pub/sub backend")


# Create and export server instance with default config
from .config import get_default_config
server = ContextBridgeServer(config=get_default_config())
mcp = server.mcp

# Export for direct import
__all__ = ["ContextBridgeServer", "server", "mcp", "ContextBridgeConfig"]
