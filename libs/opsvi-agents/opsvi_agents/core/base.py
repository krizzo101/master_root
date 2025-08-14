"""
Base Agent Implementation for OPSVI-Agents Core V2.

This module provides the foundational BaseAgent class and supporting infrastructure
for the synchronous-first, evolutionary agent system.
"""

import asyncio
import inspect
import json
import logging
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Set, Tuple, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states."""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"
    TERMINATED = "terminated"


@dataclass
class AgentMetadata:
    """Metadata for agent identification and configuration."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    version: str = "2.0.0"
    type: str = "base"
    capabilities: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    priority: int = 5
    max_retries: int = 3
    timeout: int = 300
    checkpoint_interval: int = 60
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        data = asdict(self)
        data['capabilities'] = list(self.capabilities)
        data['tags'] = list(self.tags)
        return data


@dataclass
class Checkpoint:
    """Agent checkpoint for state recovery."""
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    state: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    iteration: int = 0
    description: str = ""
    
    def save(self, path: Path) -> None:
        """Save checkpoint to disk."""
        checkpoint_file = path / f"checkpoint_{self.id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(asdict(self), f, indent=2, default=str)
    
    @classmethod
    def load(cls, path: Path, checkpoint_id: str) -> 'Checkpoint':
        """Load checkpoint from disk."""
        checkpoint_file = path / f"checkpoint_{checkpoint_id}.json"
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        return cls(**data)


class BaseAgent:
    """
    Base agent class for OPSVI-Agents Core V2.
    
    Provides synchronous-first design with optional async support,
    comprehensive error handling, checkpoint system, and tool integration.
    """
    
    def __init__(self, metadata: Optional[AgentMetadata] = None):
        """Initialize base agent with metadata."""
        self.metadata = metadata or AgentMetadata()
        self.state = AgentState.CREATED
        self._state_data: Dict[str, Any] = {}
        self._tools: Dict[str, Callable] = {}
        self._checkpoints: List[Checkpoint] = []
        self._error_count = 0
        self._start_time: Optional[float] = None
        self._last_checkpoint_time: Optional[float] = None
        
        # Performance tracking
        self._metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_duration': 0.0,
            'tool_calls': {}
        }
        
        logger.info(f"Agent {self.metadata.id} created: {self.metadata.name}")
    
    # Lifecycle Methods (787 pattern)
    
    def initialize(self, **kwargs) -> None:
        """Initialize agent with configuration."""
        self.state = AgentState.INITIALIZING
        try:
            self._initialize_internal(**kwargs)
            self.state = AgentState.READY
            logger.info(f"Agent {self.metadata.id} initialized")
        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"Agent {self.metadata.id} initialization failed: {e}")
            raise
    
    def _initialize_internal(self, **kwargs) -> None:
        """Internal initialization logic - override in subclasses."""
        pass
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task synchronously with error recovery and checkpointing.
        
        Args:
            task: Task dictionary with 'action' and optional parameters
            
        Returns:
            Result dictionary with status and output
        """
        self.state = AgentState.RUNNING
        self._start_time = time.time()
        self._metrics['total_executions'] += 1
        
        result = {
            'status': 'pending',
            'output': None,
            'error': None,
            'duration': 0,
            'retries': 0
        }
        
        for attempt in range(self.metadata.max_retries):
            try:
                # Create checkpoint if needed
                self._maybe_checkpoint(f"pre_execution_attempt_{attempt}")
                
                # Execute task
                output = self._execute_task(task)
                
                # Success
                result['status'] = 'success'
                result['output'] = output
                result['retries'] = attempt
                self._metrics['successful_executions'] += 1
                break
                
            except Exception as e:
                self._error_count += 1
                result['error'] = str(e)
                result['retries'] = attempt + 1
                
                logger.warning(f"Agent {self.metadata.id} attempt {attempt + 1} failed: {e}")
                
                if attempt < self.metadata.max_retries - 1:
                    # Try recovery
                    if self._recover_from_error(e, task, attempt):
                        continue
                else:
                    # Final failure
                    result['status'] = 'failed'
                    self._metrics['failed_executions'] += 1
                    self.state = AgentState.ERROR
                    logger.error(f"Agent {self.metadata.id} task failed after {attempt + 1} attempts")
                    
        # Record metrics
        duration = time.time() - self._start_time
        result['duration'] = duration
        self._metrics['total_duration'] += duration
        
        self.state = AgentState.COMPLETED
        return result
    
    def _execute_task(self, task: Dict[str, Any]) -> Any:
        """Internal task execution - override in subclasses."""
        action = task.get('action', 'default')
        
        # Check if action is a registered tool
        if action in self._tools:
            return self._call_tool(action, task.get('params', {}))
        
        # Default execution
        return self._default_execution(task)
    
    def _default_execution(self, task: Dict[str, Any]) -> Any:
        """Default task execution logic."""
        return f"Executed task: {task.get('action', 'unknown')}"
    
    async def execute_async(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task asynchronously.
        
        Wraps synchronous execution for compatibility.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, task)
    
    def pause(self) -> None:
        """Pause agent execution."""
        if self.state == AgentState.RUNNING:
            self.state = AgentState.PAUSED
            self.create_checkpoint("paused")
            logger.info(f"Agent {self.metadata.id} paused")
    
    def resume(self) -> None:
        """Resume agent execution."""
        if self.state == AgentState.PAUSED:
            self.state = AgentState.READY
            logger.info(f"Agent {self.metadata.id} resumed")
    
    def terminate(self) -> None:
        """Terminate agent."""
        self.state = AgentState.TERMINATED
        self.create_checkpoint("terminated")
        logger.info(f"Agent {self.metadata.id} terminated")
    
    # Tool Methods (257 pattern)
    
    def register_tool(self, name: str, tool: Callable, permissions: Optional[Set[str]] = None) -> None:
        """
        Register a tool for use by the agent.
        
        Args:
            name: Tool name
            tool: Callable tool function
            permissions: Optional set of required permissions
        """
        self._tools[name] = tool
        self.metadata.capabilities.add(f"tool:{name}")
        logger.debug(f"Agent {self.metadata.id} registered tool: {name}")
    
    def _call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """
        Call a registered tool with parameters.
        
        Args:
            name: Tool name
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
        
        tool = self._tools[name]
        
        # Track tool usage
        if name not in self._metrics['tool_calls']:
            self._metrics['tool_calls'][name] = 0
        self._metrics['tool_calls'][name] += 1
        
        # Execute tool
        try:
            if inspect.iscoroutinefunction(tool):
                # Handle async tools in sync context
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(tool(**params))
                loop.close()
                return result
            else:
                return tool(**params)
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            raise
    
    def list_tools(self) -> List[str]:
        """List registered tools."""
        return list(self._tools.keys())
    
    # Checkpoint Methods
    
    def create_checkpoint(self, description: str = "") -> Checkpoint:
        """
        Create a checkpoint of current state.
        
        Args:
            description: Optional checkpoint description
            
        Returns:
            Created checkpoint
        """
        checkpoint = Checkpoint(
            agent_id=self.metadata.id,
            state=self._get_state_snapshot(),
            iteration=len(self._checkpoints),
            description=description
        )
        
        self._checkpoints.append(checkpoint)
        self._last_checkpoint_time = time.time()
        
        logger.debug(f"Agent {self.metadata.id} created checkpoint: {checkpoint.id}")
        return checkpoint
    
    def _maybe_checkpoint(self, description: str = "") -> None:
        """Create checkpoint if interval has passed."""
        if self._last_checkpoint_time is None:
            self.create_checkpoint(description)
        elif time.time() - self._last_checkpoint_time > self.metadata.checkpoint_interval:
            self.create_checkpoint(description)
    
    def restore_checkpoint(self, checkpoint: Union[Checkpoint, str]) -> None:
        """
        Restore agent state from checkpoint.
        
        Args:
            checkpoint: Checkpoint object or checkpoint ID
        """
        if isinstance(checkpoint, str):
            # Find checkpoint by ID
            checkpoint = next((c for c in self._checkpoints if c.id == checkpoint), None)
            if not checkpoint:
                raise ValueError(f"Checkpoint not found: {checkpoint}")
        
        self._restore_state_snapshot(checkpoint.state)
        logger.info(f"Agent {self.metadata.id} restored from checkpoint: {checkpoint.id}")
    
    def _get_state_snapshot(self) -> Dict[str, Any]:
        """Get current state snapshot for checkpointing."""
        return {
            'state': self.state.value,
            'state_data': self._state_data.copy(),
            'error_count': self._error_count,
            'metrics': self._metrics.copy()
        }
    
    def _restore_state_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore state from snapshot."""
        self.state = AgentState(snapshot.get('state', 'ready'))
        self._state_data = snapshot.get('state_data', {})
        self._error_count = snapshot.get('error_count', 0)
        self._metrics = snapshot.get('metrics', self._metrics)
    
    # Error Recovery
    
    def _recover_from_error(self, error: Exception, task: Dict[str, Any], attempt: int) -> bool:
        """
        Attempt to recover from error.
        
        Args:
            error: Exception that occurred
            task: Task being executed
            attempt: Current attempt number
            
        Returns:
            True if recovery successful, False otherwise
        """
        error_type = type(error).__name__
        
        # Try checkpoint recovery
        if self._checkpoints and attempt > 0:
            try:
                self.restore_checkpoint(self._checkpoints[-1])
                logger.info(f"Agent {self.metadata.id} recovered from checkpoint")
                return True
            except Exception as e:
                logger.warning(f"Checkpoint recovery failed: {e}")
        
        # Error-specific recovery strategies
        if error_type in ['TimeoutError', 'ConnectionError']:
            # Wait and retry for network errors
            time.sleep(min(2 ** attempt, 30))
            return True
        elif error_type == 'MemoryError':
            # Clear caches and retry
            self._clear_caches()
            return True
        
        return False
    
    def _clear_caches(self) -> None:
        """Clear internal caches to free memory."""
        # Keep only recent checkpoints
        if len(self._checkpoints) > 10:
            self._checkpoints = self._checkpoints[-10:]
    
    # State Management
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state."""
        return {
            'metadata': self.metadata.to_dict(),
            'state': self.state.value,
            'state_data': self._state_data,
            'metrics': self._metrics,
            'error_count': self._error_count,
            'checkpoints': len(self._checkpoints)
        }
    
    def set_state_data(self, key: str, value: Any) -> None:
        """Set state data value."""
        self._state_data[key] = value
    
    def get_state_data(self, key: str, default: Any = None) -> Any:
        """Get state data value."""
        return self._state_data.get(key, default)
    
    # Metrics
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        metrics = self._metrics.copy()
        if self._metrics['total_executions'] > 0:
            metrics['success_rate'] = self._metrics['successful_executions'] / self._metrics['total_executions']
            metrics['average_duration'] = self._metrics['total_duration'] / self._metrics['total_executions']
        return metrics
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self._metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_duration': 0.0,
            'tool_calls': {}
        }
    
    def __repr__(self) -> str:
        """String representation of agent."""
        return f"BaseAgent(id={self.metadata.id}, name={self.metadata.name}, state={self.state.value})"