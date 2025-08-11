"""Base agent class providing core functionality for all agents in the system.

This module implements the foundational agent architecture with:
- Standardized agent interface and lifecycle management
- Message handling and communication protocols
- Error handling and logging infrastructure
- Plugin system for agent capabilities
- Tool integration framework
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union

# Import error handling utilities
from .error_handling import (
    ErrorHandler,
    ErrorSeverity,
    RetryConfig,
    with_retry,
    with_circuit_breaker,
    RetryableError,
    CircuitBreakerOpenError,
)

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RECOVERING = "recovering"  # Added for error recovery state


class MessageType(Enum):
    """Types of messages agents can send and receive."""

    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    NOTIFICATION = "notification"
    TASK = "task"
    RESPONSE = "response"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"


@dataclass
class AgentMessage:
    """Standardized message format for agent communication."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.TASK
    sender_id: str = ""
    recipient_id: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None


class AgentCapabilityType(Enum):
    TASK_PROCESSING = "task_processing"
    COMMUNICATION = "communication"
    ERROR_HANDLING = "error_handling"


@dataclass
class AgentCapability:
    """Represents a capability that an agent can provide."""

    name: str
    description: str
    version: str
    required_tools: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


class ToolProtocol(Protocol):
    """Protocol for tools that can be used by agents."""

    def name(self) -> str:
        """Return the tool name."""
        ...

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        ...


class MessageBusProtocol(Protocol):
    """Protocol for message bus communication."""

    async def send_message(self, message: AgentMessage) -> None:
        """Send a message through the bus."""
        ...

    async def register_handler(self, agent_id: str, handler: callable) -> None:
        """Register a message handler for an agent."""
        ...


class BaseAgent(ABC):
    """Base class for all agents in the system.

    Provides core functionality including:
    - Lifecycle management (initialize, start, stop)
    - Message handling and communication
    - Tool integration and capability management
    - Advanced error handling and recovery
    - State management and health monitoring
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        capabilities: Optional[List[AgentCapability]] = None,
        tools: Optional[List[ToolProtocol]] = None,
        message_bus: Optional[MessageBusProtocol] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the base agent.

        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name for the agent
            description: Brief description of the agent's purpose
            capabilities: List of capabilities this agent provides
            tools: List of tools available to this agent
            message_bus: Message bus for communication
            config: Agent-specific configuration
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.tools = {tool.name(): tool for tool in (tools or [])}
        self.message_bus = message_bus
        self.config = config or {}

        # State management
        self.state = AgentState.CREATED
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.last_heartbeat = datetime.now(timezone.utc)

        # Enhanced error handling and health monitoring
        self.error_handler = ErrorHandler(self.agent_id)
        self.retry_config = RetryConfig(
            max_attempts=self.config.get("max_retry_attempts", 3),
            base_delay=self.config.get("retry_base_delay", 1.0),
            max_delay=self.config.get("retry_max_delay", 60.0),
        )

        # Internal tracking
        self._tasks: Dict[str, asyncio.Task] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._shutdown_event = asyncio.Event()
        self._error_count = 0
        self._max_errors = self.config.get("max_errors", 10)
        self._last_error_time: Optional[datetime] = None
        self._recovery_attempts = 0

        # Setup logging
        self.logger = logging.getLogger(f"agent.{self.agent_id}")

    async def initialize(self) -> None:
        """Initialize the agent and prepare for operation."""
        try:
            self.state = AgentState.INITIALIZING
            self.logger.info(f"Initializing agent {self.name} ({self.agent_id})")

            # Register with message bus if available
            if self.message_bus:
                await self._safe_execute(
                    self.message_bus.register_handler,
                    self.agent_id,
                    self._handle_message,
                    context="message_bus_registration",
                )

            # Perform agent-specific initialization with error handling
            await self._safe_execute(
                self._initialize_agent, context="agent_initialization"
            )

            self.state = AgentState.READY
            self.logger.info(f"Agent {self.name} initialized successfully")

        except Exception as e:
            await self._handle_error(e, "initialization")
            raise

    async def start(self) -> None:
        """Start the agent and begin processing."""
        if self.state not in (AgentState.READY, AgentState.RECOVERING):
            raise RuntimeError(
                f"Agent must be in READY or RECOVERING state to start, current: {self.state}"
            )

        try:
            self.state = AgentState.RUNNING
            self.started_at = datetime.now(timezone.utc)

            self.logger.info(f"Starting agent {self.name}")

            # Start agent-specific operations with error handling
            await self._safe_execute(self._start_agent, context="agent_startup")

            # Start background tasks
            self._tasks["message_processor"] = asyncio.create_task(
                self._process_messages()
            )
            self._tasks["heartbeat"] = asyncio.create_task(self._heartbeat_loop())

            self.logger.info(f"Agent {self.name} started successfully")

        except Exception as e:
            await self._handle_error(e, "startup")
            raise

    async def stop(self) -> None:
        """Stop the agent and clean up resources."""
        if self.state in (AgentState.STOPPED, AgentState.STOPPING):
            return

        try:
            self.state = AgentState.STOPPING
            self.logger.info(f"Stopping agent {self.name}")

            # Signal shutdown
            self._shutdown_event.set()

            # Cancel running tasks with error handling
            for task_name, task in self._tasks.items():
                if not task.done():
                    self.logger.debug(f"Cancelling task: {task_name}")
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        self.logger.warning(f"Error cancelling task {task_name}: {e}")

            # Stop agent-specific operations with error handling
            await self._safe_execute(self._stop_agent, context="agent_shutdown")

            self.state = AgentState.STOPPED
            self.logger.info(f"Agent {self.name} stopped successfully")

        except Exception as e:
            await self._handle_error(e, "shutdown")
            self.state = AgentState.ERROR
            raise

    async def pause(self) -> None:
        """Pause the agent."""
        if self.state == AgentState.RUNNING:
            self.state = AgentState.PAUSED
            await self._pause_agent()

    async def resume(self) -> None:
        """Resume the agent."""
        if self.state == AgentState.PAUSED:
            self.state = AgentState.RUNNING
            await self._resume_agent()

    async def send_message(self, message: AgentMessage) -> None:
        """Send a message through the message bus."""
        if self.message_bus:
            await self._safe_execute(
                self.message_bus.send_message, message, context="message_sending"
            )
        else:
            self.logger.warning("No message bus available for sending message")

    @with_retry()
    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool with the given parameters."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not available")

        tool = self.tools[tool_name]

        try:
            self.logger.debug(f"Executing tool: {tool_name}")
            result = await self._safe_execute(
                tool.execute, parameters, context=f"tool_execution_{tool_name}"
            )
            self.logger.debug(f"Tool {tool_name} executed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Failed to execute tool {tool_name}: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent including health metrics."""
        health_status = self.error_handler.get_health_status()

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "error_count": self._error_count,
            "last_error_time": self._last_error_time.isoformat()
            if self._last_error_time
            else None,
            "recovery_attempts": self._recovery_attempts,
            "capabilities": [cap.name for cap in self.capabilities],
            "tools": list(self.tools.keys()),
            "health": health_status,
            "active_tasks": len([t for t in self._tasks.values() if not t.done()]),
            "message_queue_size": self._message_queue.qsize(),
        }

    @abstractmethod
    async def _initialize_agent(self) -> None:
        """Initialize agent-specific resources."""
        pass

    @abstractmethod
    async def _start_agent(self) -> None:
        """Start agent-specific operations."""
        pass

    @abstractmethod
    async def _stop_agent(self) -> None:
        """Stop agent-specific operations."""
        pass

    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task. Must be implemented by subclasses."""
        pass

    async def _pause_agent(self) -> None:
        """Pause agent-specific operations."""
        pass

    async def _resume_agent(self) -> None:
        """Resume agent-specific operations."""
        pass

    async def _handle_error(self, error: Exception, context: str) -> None:
        """Enhanced error handling with recovery strategies."""
        self._error_count += 1
        self._last_error_time = datetime.now(timezone.utc)

        # Determine error severity
        severity = (
            ErrorSeverity.HIGH
            if isinstance(
                error, (ConnectionError, TimeoutError, CircuitBreakerOpenError)
            )
            else ErrorSeverity.MEDIUM
        )

        # Use error handler for advanced error management
        recovery_result = await self.error_handler.handle_error(
            error, context, severity
        )

        self.logger.error(f"Error in {context}: {error}")

        # Attempt recovery if possible
        if recovery_result and self.state != AgentState.ERROR:
            await self._attempt_recovery(context, error)
        elif self._error_count >= self._max_errors:
            self.state = AgentState.ERROR
            self.logger.critical(
                f"Agent {self.name} entering ERROR state after {self._error_count} errors"
            )

    async def _attempt_recovery(self, context: str, error: Exception) -> bool:
        """Attempt to recover from an error."""
        if self._recovery_attempts >= 3:
            self.logger.warning("Maximum recovery attempts reached")
            return False

        try:
            self.state = AgentState.RECOVERING
            self._recovery_attempts += 1

            self.logger.info(
                f"Attempting recovery #{self._recovery_attempts} from {context} error"
            )

            # Wait before recovery attempt
            await asyncio.sleep(min(2**self._recovery_attempts, 30))

            # Reset error count on successful recovery
            if self.state == AgentState.RECOVERING:
                self.state = AgentState.READY
                self._error_count = max(0, self._error_count - 1)
                self.logger.info("Recovery successful")
                return True

        except Exception as recovery_error:
            self.logger.error(f"Recovery attempt failed: {recovery_error}")

        return False

    async def handle_message(self, message: AgentMessage) -> Any:
        """Handle a message (for test compatibility)."""
        if message.type == MessageType.TASK_REQUEST:
            try:
                task_result = await self.process_task(message.content)

                response = AgentMessage(
                    type=MessageType.TASK_RESPONSE,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    content=task_result,
                    correlation_id=message.id,
                )
                return response

            except Exception as e:
                await self._handle_error(e, "message_handling")
                raise

        return None

    @with_retry()
    async def execute_task(self, task_data: Dict[str, Any]) -> Any:
        """Execute a task with enhanced error handling."""
        try:
            self.logger.info(f"Executing task: {task_data.get('type', 'unknown')}")
            result = await self.process_task(task_data)
            self.logger.info("Task executed successfully")
            return result

        except Exception as e:
            await self._handle_error(e, "task_execution")
            raise

    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages with error handling."""
        try:
            self.logger.debug(
                f"Received message: {message.type} from {message.sender_id}"
            )

            if message.type in (MessageType.SHUTDOWN, MessageType.STATUS):
                await self._handle_control_message(message)
            else:
                await self._message_queue.put(message)

        except Exception as e:
            await self._handle_error(e, "message_handling")

    async def _handle_control_message(self, message: AgentMessage) -> None:
        """Handle control messages with error handling."""
        try:
            if message.type == MessageType.SHUTDOWN:
                self.logger.info("Received shutdown message")
                await self.stop()
            elif message.type == MessageType.STATUS:
                status = self.get_status()
                response = AgentMessage(
                    type=MessageType.STATUS,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    content=status,
                    correlation_id=message.id,
                )
                await self.send_message(response)

        except Exception as e:
            await self._handle_error(e, "control_message_handling")

    async def _process_messages(self) -> None:
        """Process messages from the queue with error handling."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for message with timeout to allow shutdown check
                try:
                    message = await asyncio.wait_for(
                        self._message_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process message
                await self.handle_message(message)
                self._message_queue.task_done()

            except Exception as e:
                await self._handle_error(e, "message_processing")
                # Continue processing other messages
                await asyncio.sleep(0.1)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat messages with error handling."""
        heartbeat_interval = self.config.get("heartbeat_interval", 30)

        while not self._shutdown_event.is_set():
            try:
                self.last_heartbeat = datetime.now(timezone.utc)

                if self.message_bus:
                    heartbeat_message = AgentMessage(
                        type=MessageType.HEARTBEAT,
                        sender_id=self.agent_id,
                        content={
                            "timestamp": self.last_heartbeat.isoformat(),
                            "status": self.get_status(),
                        },
                    )
                    await self.send_message(heartbeat_message)

                await asyncio.sleep(heartbeat_interval)

            except Exception as e:
                await self._handle_error(e, "heartbeat")
                await asyncio.sleep(heartbeat_interval)

    async def _safe_execute(self, func, *args, **kwargs):
        """Execute a function with error handling and recovery."""
        context = kwargs.pop("context", "unknown")
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            await self._handle_error(e, context)
            raise
