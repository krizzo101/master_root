"""
Enhanced Base Agent with LLM Integration

This module defines the fundamental agent architecture with built-in LLM capabilities
that all agents in the OPSVI ecosystem should inherit from.
"""

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
from opsvi_llm import (
    ChatRequest,
    ChatResponse,
    LLMError,
    Message,
    OpenAIConfig,
    OpenAIProvider,
)

logger = structlog.get_logger(__name__)


class AgentState(Enum):
    """Agent execution states."""

    IDLE = "idle"
    RUNNING = "running"
    THINKING = "thinking"  # When using LLM for reasoning
    PLANNING = "planning"  # When planning actions
    EXECUTING = "executing"  # When executing tools/actions
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
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    CONVERSATION = "conversation"


@dataclass
class LLMAgentConfig:
    """Enhanced configuration for LLM-powered agents."""

    # Basic agent config
    name: str
    description: str = ""

    # LLM configuration
    model: str = "gpt-4"  # Default to GPT-4 for better reasoning
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Agent behavior
    max_iterations: int = 10
    timeout: int = 300
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    # System prompt (core instruction for the agent)
    system_prompt: Optional[str] = None

    # Memory and state
    memory_enabled: bool = True
    checkpoint_enabled: bool = True
    error_recovery: bool = True

    # Advanced features
    chain_of_thought: bool = True  # Enable CoT reasoning
    self_reflection: bool = True  # Enable self-reflection
    multi_shot_examples: List[Dict[str, str]] = field(default_factory=list)

    # Execution settings
    verbose: bool = False
    stream_output: bool = False
    parallel_tools: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemory:
    """Agent memory system for context retention."""

    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: Dict[str, Any] = field(default_factory=dict)
    episodic: List[Dict[str, Any]] = field(default_factory=list)  # Specific experiences
    semantic: Dict[str, Any] = field(default_factory=dict)  # General knowledge
    working: Dict[str, Any] = field(default_factory=dict)  # Current task context

    def add_to_short_term(self, item: Dict[str, Any], max_items: int = 10):
        """Add item to short-term memory with size limit."""
        self.short_term.append(item)
        if len(self.short_term) > max_items:
            # Move oldest to long-term
            old_item = self.short_term.pop(0)
            key = old_item.get("key", str(uuid.uuid4()))
            self.long_term[key] = old_item

    def recall(self, query: str, memory_type: str = "all") -> List[Dict[str, Any]]:
        """Recall relevant memories based on query."""
        results = []

        if memory_type in ["all", "short_term"]:
            results.extend(
                [m for m in self.short_term if query.lower() in str(m).lower()]
            )

        if memory_type in ["all", "long_term"]:
            for key, value in self.long_term.items():
                if query.lower() in str(value).lower():
                    results.append(value)

        if memory_type in ["all", "episodic"]:
            results.extend(
                [m for m in self.episodic if query.lower() in str(m).lower()]
            )

        return results


@dataclass
class AgentContext:
    """Enhanced runtime context for agent execution."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: AgentState = AgentState.IDLE
    iteration: int = 0

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Memory system
    memory: AgentMemory = field(default_factory=AgentMemory)

    # Conversation history
    messages: List[Message] = field(default_factory=list)

    # Execution tracking
    thoughts: List[str] = field(default_factory=list)  # Chain of thought
    plans: List[Dict[str, Any]] = field(default_factory=list)  # Action plans
    actions: List[Dict[str, Any]] = field(default_factory=list)  # Executed actions
    observations: List[str] = field(default_factory=list)  # Results/observations

    # State management
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    token_usage: Dict[str, int] = field(
        default_factory=lambda: {"prompt": 0, "completion": 0, "total": 0}
    )

    # Hierarchy
    parent_context: Optional["AgentContext"] = None
    child_contexts: List["AgentContext"] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result from agent execution."""

    success: bool
    output: Any
    context: AgentContext

    # Execution details
    final_answer: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    error: Optional[str] = None
    duration: float = 0.0
    iterations_used: int = 0
    model_calls: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "final_answer": self.final_answer,
            "reasoning": self.reasoning,
            "actions_taken": self.actions_taken,
            "error": self.error,
            "duration": self.duration,
            "iterations_used": self.iterations_used,
            "model_calls": self.model_calls,
            "token_usage": self.context.token_usage,
        }


class BaseLLMAgent(ABC):
    """
    Base agent with integrated LLM capabilities.

    This class provides:
    - LLM integration for reasoning and decision-making
    - Memory system for context retention
    - Tool registration and execution
    - Chain-of-thought reasoning
    - Self-reflection capabilities
    - Error recovery mechanisms
    """

    def __init__(self, config: LLMAgentConfig):
        """Initialize base LLM agent."""
        self.config = config
        self.context = AgentContext()

        # Initialize LLM provider
        self.llm_config = OpenAIConfig(
            provider_name="openai",
            default_model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
        )
        self.llm = OpenAIProvider(self.llm_config)

        # Tool and callback registries
        self._tools: Dict[str, Callable] = {}
        self._callbacks: Dict[str, List[Callable]] = {}

        # Logger
        self._logger = logger.bind(agent=config.name)

        # Initialize system prompt
        self._init_system_prompt()

    def _init_system_prompt(self):
        """Initialize the system prompt for the agent."""
        if not self.config.system_prompt:
            self.config.system_prompt = f"""You are {self.config.name}, an intelligent agent with the following capabilities:
{', '.join([cap.value for cap in self.config.capabilities])}

Your purpose: {self.config.description}

Guidelines:
1. Think step-by-step through problems
2. Use available tools when needed
3. Provide clear, actionable responses
4. Learn from previous interactions
5. Admit uncertainty when appropriate

Available tools: {', '.join(self.config.tools) if self.config.tools else 'None'}
"""

    async def think(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Use LLM to think about a problem.

        Args:
            prompt: The question or problem to think about
            context: Additional context to consider

        Returns:
            The LLM's reasoning/thought process
        """
        self.context.state = AgentState.THINKING

        messages = [
            Message(role="system", content=self.config.system_prompt),
        ]

        # Add context from memory if available
        if self.config.memory_enabled and self.context.memory.working:
            memory_context = json.dumps(self.context.memory.working, indent=2)
            messages.append(
                Message(
                    role="system", content=f"Current working memory:\n{memory_context}"
                )
            )

        # Add additional context if provided
        if context:
            messages.append(
                Message(role="system", content=f"Additional context:\n{context}")
            )

        # Add the prompt
        thought_prompt = prompt
        if self.config.chain_of_thought:
            thought_prompt = f"Think step by step about the following:\n{prompt}\n\nProvide your reasoning process."

        messages.append(Message(role="user", content=thought_prompt))

        # Get LLM response
        try:
            chat_request = ChatRequest(
                messages=messages,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            response = await self.llm.chat(chat_request)
            thought = response.content

            # Store thought in context
            self.context.thoughts.append(thought)

            # Update token usage
            if hasattr(response, "usage"):
                self.context.token_usage["prompt"] += response.usage.get(
                    "prompt_tokens", 0
                )
                self.context.token_usage["completion"] += response.usage.get(
                    "completion_tokens", 0
                )
                self.context.token_usage["total"] += response.usage.get(
                    "total_tokens", 0
                )

            return thought

        except Exception as e:
            self._logger.error("Failed to think", error=str(e))
            raise

    async def plan(
        self, goal: str, constraints: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create an action plan to achieve a goal.

        Args:
            goal: The goal to achieve
            constraints: List of constraints to consider

        Returns:
            List of planned actions
        """
        self.context.state = AgentState.PLANNING

        plan_prompt = f"""Create a step-by-step plan to achieve the following goal:
Goal: {goal}

Constraints:
{chr(10).join(f'- {c}' for c in (constraints or [])) if constraints else 'None'}

Available tools:
{chr(10).join(f'- {tool}' for tool in self._tools.keys()) if self._tools else 'None'}

Provide a JSON array of steps, where each step has:
- "action": the action to take
- "tool": the tool to use (if any)
- "parameters": parameters for the tool (if any)
- "expected_outcome": what we expect to achieve
"""

        thought = await self.think(plan_prompt)

        # Parse the plan from the thought
        try:
            # Extract JSON from the response
            import re

            json_match = re.search(r"\[.*?\]", thought, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                self.context.plans.append({"goal": goal, "steps": plan})
                return plan
        except json.JSONDecodeError:
            self._logger.warning("Failed to parse plan as JSON, creating simple plan")

        # Fallback to simple plan
        plan = [{"action": "execute", "description": thought}]
        self.context.plans.append({"goal": goal, "steps": plan})
        return plan

    async def reflect(self, observation: str) -> str:
        """
        Reflect on an observation or result.

        Args:
            observation: What was observed/resulted

        Returns:
            Reflection/analysis
        """
        if not self.config.self_reflection:
            return observation

        reflection_prompt = f"""Reflect on the following observation:
{observation}

Consider:
1. Was this expected?
2. What can we learn from this?
3. Should we adjust our approach?
4. What are the implications?
"""

        reflection = await self.think(reflection_prompt)
        self.context.observations.append(
            f"Observation: {observation}\nReflection: {reflection}"
        )
        return reflection

    @abstractmethod
    async def _execute_core(self, prompt: str, **kwargs) -> Any:
        """
        Core execution logic to be implemented by subclasses.

        This method should contain the specific logic for each agent type.
        It has access to self.think(), self.plan(), self.reflect(), and all
        LLM capabilities.
        """
        pass

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute agent with prompt."""
        self._logger.info("Starting execution", prompt=prompt[:100])

        # Initialize context
        self.context.state = AgentState.RUNNING
        self.context.start_time = datetime.now()
        start = time.time()

        try:
            # Store initial prompt in memory
            if self.config.memory_enabled:
                self.context.memory.add_to_short_term(
                    {
                        "type": "prompt",
                        "content": prompt,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Create checkpoint if enabled
            if self.config.checkpoint_enabled:
                self._create_checkpoint("start", {"prompt": prompt, "kwargs": kwargs})

            # Execute core logic
            output = await self._execute_core(prompt, **kwargs)

            # Mark success
            self.context.state = AgentState.COMPLETED
            self.context.end_time = datetime.now()
            duration = time.time() - start

            result = AgentResult(
                success=True,
                output=output,
                context=self.context,
                duration=duration,
                iterations_used=self.context.iteration,
                model_calls=len(self.context.thoughts),
                reasoning=self.context.thoughts,
                actions_taken=self.context.actions,
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
                recovery_result = await self._attempt_recovery(e, prompt, kwargs)
                if recovery_result:
                    return recovery_result

            result = AgentResult(
                success=False,
                output=None,
                context=self.context,
                error=str(e),
                duration=duration,
                iterations_used=self.context.iteration,
            )

            self._logger.error("Execution failed", error=str(e))
            return result

    def register_tool(self, name: str, tool: Callable) -> None:
        """Register a tool for agent use."""
        self._tools[name] = tool
        self._logger.debug("Tool registered", tool=name)

    async def use_tool(self, tool_name: str, **params) -> Any:
        """Execute a registered tool."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not registered")

        tool = self._tools[tool_name]

        # Log action
        action = {
            "tool": tool_name,
            "parameters": params,
            "timestamp": datetime.now().isoformat(),
        }
        self.context.actions.append(action)

        # Execute tool
        try:
            if asyncio.iscoroutinefunction(tool):
                result = await tool(**params)
            else:
                result = tool(**params)

            action["result"] = str(result)[:500]  # Store truncated result
            return result

        except Exception as e:
            action["error"] = str(e)
            raise

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register event callback."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    async def _trigger_callbacks(self, event: str, data: Any = None):
        """Trigger callbacks for an event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self._logger.error(
                        f"Callback failed for event {event}", error=str(e)
                    )

    def _create_checkpoint(self, name: str, data: Dict[str, Any]) -> None:
        """Create execution checkpoint."""
        checkpoint = {
            "name": name,
            "iteration": self.context.iteration,
            "timestamp": datetime.now().isoformat(),
            "state": self.context.state.value,
            "memory_snapshot": {
                "working": self.context.memory.working,
                "short_term_size": len(self.context.memory.short_term),
            },
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

    async def _attempt_recovery(
        self, error: Exception, prompt: str, kwargs: Dict
    ) -> Optional[AgentResult]:
        """Attempt to recover from error using LLM reasoning."""
        self._logger.info("Attempting recovery", error=str(error))

        recovery_prompt = f"""An error occurred during execution:
Error: {str(error)}
Original task: {prompt}

Please analyze this error and suggest:
1. What went wrong
2. How to fix or work around it
3. Alternative approach if available
"""

        try:
            recovery_thought = await self.think(recovery_prompt)

            # Try alternative approach
            alternative_prompt = (
                f"Given the error, try an alternative approach:\n{recovery_thought}"
            )
            output = await self._execute_core(alternative_prompt, **kwargs)

            return AgentResult(
                success=True,
                output=output,
                context=self.context,
                error=f"Recovered from: {str(error)}",
                duration=time.time() - self.context.start_time.timestamp(),
            )

        except Exception as recovery_error:
            self._logger.error("Recovery failed", error=str(recovery_error))
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
            "thoughts": len(self.context.thoughts),
            "actions": len(self.context.actions),
            "errors": len(self.context.errors),
            "checkpoints": len(self.context.checkpoints),
            "token_usage": self.context.token_usage,
            **self.context.metrics,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.config.name}, model={self.config.model}, state={self.context.state.value})>"


# Import asyncio for async support
import asyncio
