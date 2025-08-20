"""Base agent implementation for OPSVI-Agents Core V2."""

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import structlog

logger = structlog.get_logger(__name__)


class AgentState(Enum):
    """Agent execution states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(Enum):
    """Standard agent capabilities."""

    TOOL_USE = "tool_use"
    MEMORY = "memory"
    PLANNING = "planning"
    REASONING = "reasoning"
    LEARNING = "learning"
    PARALLEL = "parallel"
    STREAMING = "streaming"


@dataclass
class AgentConfig:
    """Configuration for agent instances."""

    name: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_iterations: int = 10
    timeout: int = 300
    capabilities: List[AgentCapability] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None
    memory_enabled: bool = False
    checkpoint_enabled: bool = True
    error_recovery: bool = True
    verbose: bool = False


@dataclass
class AgentContext:
    """Runtime context for agent execution."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: AgentState = AgentState.IDLE
    iteration: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    parent_context: Optional["AgentContext"] = None


@dataclass
class AgentMessage:
    """Message structure for agent communication."""

    role: str  # system, user, assistant, tool
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from agent execution."""

    success: bool
    output: Any
    context: AgentContext
    messages: List[AgentMessage] = field(default_factory=list)
    error: Optional[str] = None
    duration: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)


class BaseAgent(ABC):
    """Synchronous base agent implementation."""

    def __init__(self, config: AgentConfig):
        """Initialize base agent."""
        self.config = config
        self.context = AgentContext()
        self._tools = {}
        self._callbacks = {}
        self._logger = logger.bind(agent=config.name)

    @abstractmethod
    def _execute(self, prompt: str, **kwargs) -> Any:
        """Core execution logic to be implemented by subclasses."""
        pass

    def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute agent with prompt."""
        self._logger.info("Starting execution", prompt=prompt[:100])

        # Initialize context
        self.context.state = AgentState.RUNNING
        self.context.start_time = datetime.now()
        start = time.time()

        try:
            # Create checkpoint if enabled
            if self.config.checkpoint_enabled:
                self._create_checkpoint("start", {"prompt": prompt, "kwargs": kwargs})

            # Execute core logic
            output = self._execute(prompt, **kwargs)

            # Mark success
            self.context.state = AgentState.COMPLETED
            self.context.end_time = datetime.now()
            duration = time.time() - start

            result = AgentResult(
                success=True, output=output, context=self.context, duration=duration
            )

            self._logger.info("Execution completed", duration=duration)
            return result

        except Exception as e:
            # Handle errors
            self.context.state = AgentState.FAILED
            self.context.end_time = datetime.now()
            duration = time.time() - start

            error_info = {
                "error": str(e),
                "type": type(e).__name__,
                "timestamp": datetime.now().isoformat(),
            }
            self.context.errors.append(error_info)

            # Attempt recovery if enabled
            if self.config.error_recovery:
                recovery_result = self._attempt_recovery(e, prompt, kwargs)
                if recovery_result:
                    return recovery_result

            result = AgentResult(
                success=False,
                output=None,
                context=self.context,
                error=str(e),
                duration=duration,
            )

            self._logger.error("Execution failed", error=str(e))
            return result

    def register_tool(self, name: str, tool: Callable) -> None:
        """Register a tool for agent use."""
        self._tools[name] = tool
        self._logger.debug("Tool registered", tool=name)

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register event callback."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _create_checkpoint(self, name: str, data: Dict[str, Any]) -> None:
        """Create execution checkpoint."""
        checkpoint = {
            "name": name,
            "iteration": self.context.iteration,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        self.context.checkpoints.append(checkpoint)

        # Persist if path configured
        if "checkpoint_path" in self.config.metadata:
            path = Path(self.config.metadata["checkpoint_path"])
            path.mkdir(parents=True, exist_ok=True)
            checkpoint_file = path / f"{self.context.task_id}_{name}.json"
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint, f, indent=2, default=str)

    def _attempt_recovery(
        self, error: Exception, prompt: str, kwargs: Dict
    ) -> Optional[AgentResult]:
        """Attempt to recover from error."""
        self._logger.info("Attempting recovery", error=str(error))

        # Check for checkpoint recovery
        if self.context.checkpoints:
            last_checkpoint = self.context.checkpoints[-1]
            self._logger.info(
                "Recovering from checkpoint", checkpoint=last_checkpoint["name"]
            )
            # Subclasses can implement specific recovery logic

        return None

    def reset(self) -> None:
        """Reset agent context."""
        self.context = AgentContext()
        self._logger.info("Agent reset")

    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return {
            "session_id": self.context.session_id,
            "task_id": self.context.task_id,
            "state": self.context.state.value,
            "iterations": self.context.iteration,
            "errors": len(self.context.errors),
            "checkpoints": len(self.context.checkpoints),
            **self.context.metrics,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.config.name}, state={self.context.state.value})>"
