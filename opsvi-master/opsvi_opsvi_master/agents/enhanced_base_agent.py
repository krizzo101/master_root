"""Enhanced base agent with integrated monitoring and error handling.

This module extends the base agent with:
- Comprehensive performance monitoring and metrics
- Advanced error handling with circuit breakers and retry logic
- Real-time health status and alerting
- Enhanced tool execution with caching and optimization
- State persistence and recovery capabilities
"""

from __future__ import annotations

import asyncio
import json
import logging
import pickle
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from .base_agent import (
    BaseAgent,
    AgentMessage,
    AgentState,
    MessageType,
    AgentCapability,
    ToolProtocol,
)
from .error_handling import (
    ErrorHandler,
    ErrorSeverity,
    RetryConfig,
    with_retry,
    with_circuit_breaker,
)
from .monitoring import AgentMonitor, get_agent_monitor

logger = logging.getLogger(__name__)


class CacheProtocol(Protocol):
    """Protocol for cache implementations."""

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ...

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        ...


class SimpleMemoryCache:
    """Simple in-memory cache implementation."""

    def __init__(self, default_ttl: int = 3600):
        """Initialize cache with default TTL in seconds."""
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            entry = self._cache[key]
            if entry["expires_at"] > time.time():
                return entry["value"]
            else:
                del self._cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        self._cache[key] = {"value": value, "expires_at": time.time() + ttl}

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)

    def cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if entry["expires_at"] <= current_time
        ]
        for key in expired_keys:
            del self._cache[key]


class EnhancedBaseAgent(BaseAgent):
    """Enhanced base agent with monitoring, error handling, and optimization features."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        capabilities: Optional[List[AgentCapability]] = None,
        tools: Optional[List[ToolProtocol]] = None,
        message_bus: Optional[object] = None,
        config: Optional[Dict[str, Any]] = None,
        cache: Optional[CacheProtocol] = None,
        state_persistence_path: Optional[str] = None,
    ):
        """Initialize enhanced agent.

        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name for the agent
            description: Brief description of the agent's purpose
            capabilities: List of capabilities this agent provides
            tools: List of tools available to this agent
            message_bus: Message bus for communication
            config: Agent-specific configuration
            cache: Cache implementation for tool results
            state_persistence_path: Path to persist agent state
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=capabilities,
            tools=tools,
            message_bus=message_bus,
            config=config,
        )

        # Enhanced capabilities
        self.error_handler = ErrorHandler(agent_id)
        self.monitor = get_agent_monitor(agent_id)
        self.cache = cache or SimpleMemoryCache()
        self.state_persistence_path = state_persistence_path

        # Performance tracking
        self._task_timers: Dict[str, float] = {}
        self._tool_cache_hits = 0
        self._tool_cache_misses = 0

        # Configuration
        self.tool_cache_enabled = self.config.get("tool_cache_enabled", True)
        self.tool_cache_ttl = self.config.get("tool_cache_ttl", 3600)
        self.retry_config = RetryConfig(
            max_attempts=self.config.get("retry_max_attempts", 3),
            base_delay=self.config.get("retry_base_delay", 1.0),
            max_delay=self.config.get("retry_max_delay", 60.0),
        )

        self.logger = logging.getLogger(f"enhanced_agent.{self.agent_id}")

    async def initialize(self) -> None:
        """Initialize enhanced agent with monitoring and state recovery."""
        try:
            # Start monitoring
            await self.monitor.start()

            # Recover state if persistence is enabled
            await self._recover_state()

            # Initialize parent
            await super().initialize()

            self.logger.info(f"Enhanced agent {self.name} initialized with monitoring")

        except Exception as e:
            await self.error_handler.handle_error(
                e, "agent initialization", ErrorSeverity.CRITICAL
            )
            raise

    async def start(self) -> None:
        """Start enhanced agent with performance tracking."""
        start_time = self.monitor.start_task_timer()

        try:
            await super().start()
            self.monitor.end_task_timer(start_time, success=True)

        except Exception as e:
            self.monitor.end_task_timer(start_time, success=False)
            await self.error_handler.handle_error(
                e, "agent startup", ErrorSeverity.CRITICAL
            )
            raise

    async def stop(self) -> None:
        """Stop enhanced agent with state persistence."""
        try:
            # Persist state before stopping
            await self._persist_state()

            # Stop monitoring
            await self.monitor.stop()

            # Stop parent
            await super().stop()

            self.logger.info(f"Enhanced agent {self.name} stopped gracefully")

        except Exception as e:
            await self.error_handler.handle_error(
                e, "agent shutdown", ErrorSeverity.HIGH
            )
            raise

    @with_retry()
    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any], use_cache: bool = True
    ) -> Dict[str, Any]:
        """Execute tool with caching and error handling."""
        start_time = self.monitor.start_task_timer()

        try:
            # Check cache if enabled
            cache_key = None
            if self.tool_cache_enabled and use_cache:
                cache_key = self._generate_cache_key(tool_name, parameters)
                cached_result = await self.cache.get(cache_key)

                if cached_result is not None:
                    self._tool_cache_hits += 1
                    self.monitor.end_task_timer(start_time, success=True)
                    self.logger.debug(f"Cache hit for tool {tool_name}")
                    return cached_result

                self._tool_cache_misses += 1

            # Execute tool with circuit breaker protection
            circuit_breaker = self.error_handler.get_circuit_breaker(
                f"tool_{tool_name}"
            )
            result = await circuit_breaker.call(
                super().execute_tool, tool_name, parameters
            )

            # Cache result if enabled
            if cache_key and self.tool_cache_enabled:
                await self.cache.set(cache_key, result, self.tool_cache_ttl)

            self.monitor.end_task_timer(start_time, success=True)
            return result

        except Exception as e:
            self.monitor.end_task_timer(start_time, success=False)
            self.monitor.record_error()

            # Try error recovery
            recovery_result = await self.error_handler.handle_error(
                e,
                f"tool execution: {tool_name}",
                ErrorSeverity.MEDIUM,
                recovery_strategy=lambda: self._fallback_tool_execution(
                    tool_name, parameters
                ),
            )

            if recovery_result is not None:
                return recovery_result

            raise

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task with comprehensive monitoring."""
        task_id = task.get("id", "unknown")
        start_time = self.monitor.start_task_timer()
        self._task_timers[task_id] = start_time

        try:
            # Update heartbeat
            self.monitor.update_heartbeat()

            # Process task (implemented by subclasses)
            result = await self._process_task_impl(task)

            # Record successful completion
            duration = self.monitor.end_task_timer(start_time, success=True)
            self.logger.info(f"Task {task_id} completed in {duration:.2f}s")

            return result

        except Exception as e:
            # Record failure
            self.monitor.end_task_timer(start_time, success=False)
            self.monitor.record_error()

            # Handle error with context
            recovery_result = await self.error_handler.handle_error(
                e,
                f"task processing: {task_id}",
                ErrorSeverity.HIGH,
                recovery_strategy=lambda: self._fallback_task_processing(task),
            )

            if recovery_result is not None:
                return recovery_result

            raise
        finally:
            self._task_timers.pop(task_id, None)

    async def send_message(self, message: AgentMessage) -> None:
        """Send message with monitoring."""
        try:
            await super().send_message(message)
            self.monitor.record_message_sent()

        except Exception as e:
            await self.error_handler.handle_error(
                e, "message sending", ErrorSeverity.MEDIUM
            )
            raise

    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status including performance metrics."""
        base_status = self.get_status()
        performance_summary = self.monitor.get_performance_summary()
        error_health = self.error_handler.get_health_status()

        # Tool execution statistics
        total_tool_calls = self._tool_cache_hits + self._tool_cache_misses
        cache_hit_rate = (
            self._tool_cache_hits / total_tool_calls if total_tool_calls > 0 else 0.0
        )

        return {
            **base_status,
            "performance": performance_summary,
            "error_handling": error_health,
            "tool_cache": {
                "enabled": self.tool_cache_enabled,
                "hit_rate": cache_hit_rate,
                "hits": self._tool_cache_hits,
                "misses": self._tool_cache_misses,
            },
            "active_alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat(),
                }
                for alert in self.monitor.get_active_alerts()
            ],
        }

    # Abstract method to be implemented by subclasses
    async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Actual task processing implementation."""
        raise NotImplementedError("Subclasses must implement _process_task_impl")

    # Helper methods

    def _generate_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for tool execution using secure SHA256."""
        # Create deterministic hash of tool name and parameters using secure hash
        import hashlib

        params_str = json.dumps(parameters, sort_keys=True)
        content = f"{tool_name}:{params_str}"
        # Use SHA256 instead of MD5 for security
        return hashlib.sha256(content.encode()).hexdigest()[:16]  # Truncate

    async def _fallback_tool_execution(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fallback strategy for tool execution failures."""
        # Try with simplified parameters
        simplified_params = {
            k: v
            for k, v in parameters.items()
            if isinstance(v, (str, int, float, bool))
        }

        if simplified_params != parameters:
            try:
                self.logger.info(
                    f"Retrying tool {tool_name} with simplified parameters"
                )
                return await super().execute_tool(tool_name, simplified_params)
            except Exception:
                pass

        return None

    async def _fallback_task_processing(
        self, task: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fallback strategy for task processing failures."""
        # Default fallback: return partial result
        return {
            "status": "partial_failure",
            "error": "Task processing failed but agent remains operational",
            "task_id": task.get("id", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _persist_state(self) -> None:
        """Persist agent state to disk."""
        if not self.state_persistence_path:
            return

        try:
            state_data = {
                "agent_id": self.agent_id,
                "state": self.state.value,
                "created_at": self.created_at.isoformat(),
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "error_count": self._error_count,
                "tool_cache_stats": {
                    "hits": self._tool_cache_hits,
                    "misses": self._tool_cache_misses,
                },
                "config": self.config,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            persistence_path = Path(self.state_persistence_path)
            persistence_path.parent.mkdir(parents=True, exist_ok=True)

            with open(persistence_path, "w") as f:
                json.dump(state_data, f, indent=2)

            self.logger.debug(f"State persisted to {persistence_path}")

        except Exception as e:
            self.logger.warning(f"Failed to persist state: {e}")

    async def _recover_state(self) -> None:
        """Recover agent state from disk."""
        if not self.state_persistence_path:
            return

        try:
            persistence_path = Path(self.state_persistence_path)

            if not persistence_path.exists():
                return

            with open(persistence_path, "r") as f:
                state_data = json.load(f)

            # Restore relevant state
            if state_data.get("agent_id") == self.agent_id:
                self._error_count = state_data.get("error_count", 0)
                cache_stats = state_data.get("tool_cache_stats", {})
                self._tool_cache_hits = cache_stats.get("hits", 0)
                self._tool_cache_misses = cache_stats.get("misses", 0)

                self.logger.info(f"State recovered from {persistence_path}")

        except Exception as e:
            self.logger.warning(f"Failed to recover state: {e}")

    # Message handling with monitoring

    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages with monitoring."""
        self.monitor.record_message_received()

        try:
            await super()._handle_message(message)

        except Exception as e:
            await self.error_handler.handle_error(
                e, f"message handling: {message.type.value}", ErrorSeverity.MEDIUM
            )
            raise

    # Maintenance tasks

    async def _start_agent(self) -> None:
        """Start agent-specific tasks including cache cleanup."""
        # Start cache cleanup task if using memory cache
        if isinstance(self.cache, SimpleMemoryCache):
            self._tasks["cache_cleanup"] = asyncio.create_task(
                self._cache_cleanup_loop()
            )

        # Start maintenance task
        self._tasks["maintenance"] = asyncio.create_task(self._maintenance_loop())

    async def _stop_agent(self) -> None:
        """Stop agent-specific tasks."""
        # Nothing specific to stop for enhanced agent
        pass

    async def _cache_cleanup_loop(self) -> None:
        """Periodic cache cleanup for memory cache."""
        while not self._shutdown_event.is_set():
            try:
                if isinstance(self.cache, SimpleMemoryCache):
                    self.cache.cleanup_expired()

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.warning(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)

    async def _maintenance_loop(self) -> None:
        """Periodic maintenance tasks."""
        while not self._shutdown_event.is_set():
            try:
                # Update heartbeat
                self.monitor.update_heartbeat()

                # Persist state
                await self._persist_state()

                # Log performance summary
                if self._error_count > 0:
                    summary = self.get_enhanced_status()
                    self.logger.info(
                        f"Agent health check: {summary['performance']['tasks']['success_rate']:.1%} success rate"
                    )

                await asyncio.sleep(600)  # Maintenance every 10 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.warning(f"Maintenance error: {e}")
                await asyncio.sleep(60)
