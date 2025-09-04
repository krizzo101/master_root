#!/usr/bin/env python3
"""
Escalation Manager - Intelligent escalation patterns for autonomous agent coordination

Implements:
1. Pattern 1: Escalation to Manager - Agent attempts solution 3 times, then escalates
2. Pattern 2: Sub-Swarm Delegation - Complex problems delegated to specialized teams
3. Manager-side enhancement logic for spawning better replacement agents
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EscalationType(Enum):
    """Types of escalation available"""

    MANAGER = "manager"  # Escalate to manager agent
    SUB_SWARM = "sub_swarm"  # Delegate to specialized sub-team
    REPLACEMENT = "replacement"  # Request enhanced replacement agent
    EMERGENCY = "emergency"  # Critical system failure


class EscalationReason(Enum):
    """Reasons for escalation"""

    FAILURE_THRESHOLD = "failure_threshold"  # Failed 3+ times
    CONTEXT_EXHAUSTION = "context_exhaustion"  # Approaching token limits
    MISSING_PERMISSIONS = "missing_permissions"  # Need elevated access
    MISSING_DEPENDENCIES = "missing_dependencies"  # Can't find required files
    COMPLEX_DEBUGGING = "complex_debugging"  # Issue requires specialized team
    RESOURCE_CONFLICT = "resource_conflict"  # Can't access needed resources
    TIME_EXCEEDED = "time_exceeded"  # Task taking too long
    SILENT_FAILURE = "silent_failure"  # Completed but no output


@dataclass
class EscalationRequest:
    """Request for escalation from agent to manager"""

    escalation_id: str
    agent_id: str
    agent_uuid: str
    escalation_type: EscalationType
    escalation_reason: EscalationReason

    # Problem description
    problem_description: str
    attempted_solutions: List[str] = field(default_factory=list)
    failure_count: int = 0

    # Context information
    current_task: Dict[str, Any] = field(default_factory=dict)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    error_logs: List[str] = field(default_factory=list)

    # Enhancement requirements for replacement agent
    required_permissions: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    required_context: List[str] = field(default_factory=list)

    # Sub-swarm requirements
    specialist_types_needed: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low, medium, high, critical
    time_budget: int = 600  # seconds

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: str = "normal"  # low, normal, high, critical
    status: str = "pending"  # pending, assigned, in_progress, resolved, failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            **asdict(self),
            "escalation_type": self.escalation_type.value,
            "escalation_reason": self.escalation_reason.value,
        }


@dataclass
class EscalationResponse:
    """Response to escalation request"""

    escalation_id: str
    response_type: str  # replacement_spawned, sub_swarm_created, manager_takeover

    # Replacement agent info
    new_agent_uuid: Optional[str] = None
    enhanced_capabilities: List[str] = field(default_factory=list)

    # Sub-swarm info
    sub_swarm_id: Optional[str] = None
    sub_swarm_agents: List[str] = field(default_factory=list)

    # Instructions
    handoff_instructions: str = ""
    context_preservation: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    resolved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolver_agent: str = ""


class IntelligentAgent:
    """
    Base class for agents with escalation capabilities.

    Provides automatic escalation when agents encounter problems they can't solve:
    - Tracks failure count and escalates after 3 attempts
    - Monitors context usage and escalates at 90%
    - Detects missing dependencies and escalates with requirements
    """

    def __init__(
        self,
        agent_id: str,
        agent_uuid: str,
        escalation_manager: "EscalationManager",
        failure_threshold: int = 3,
        context_threshold: float = 0.90,
    ):
        self.agent_id = agent_id
        self.agent_uuid = agent_uuid
        self.escalation_manager = escalation_manager

        # Escalation thresholds
        self.failure_threshold = failure_threshold
        self.context_threshold = context_threshold

        # State tracking
        self.failure_count = 0
        self.attempted_solutions: List[str] = []
        self.current_task: Dict[str, Any] = {}
        self.start_time = time.time()

        logger.info(f"IntelligentAgent {agent_id} initialized with escalation support")

    async def attempt_solution(self, problem: str, solution_func, *args, **kwargs):
        """
        Attempt a solution with automatic escalation on failure.

        Args:
            problem: Description of the problem being solved
            solution_func: Function to execute for solution
            *args, **kwargs: Arguments for solution function

        Returns:
            Result of solution function or escalation response
        """
        solution_description = f"{solution_func.__name__}({args}, {kwargs})"
        logger.info(f"Agent {self.agent_id} attempting: {solution_description}")

        try:
            result = (
                await solution_func(*args, **kwargs)
                if asyncio.iscoroutinefunction(solution_func)
                else solution_func(*args, **kwargs)
            )

            # Reset failure count on success
            if result and not self._is_empty_result(result):
                self.failure_count = 0
                return result
            else:
                # Silent failure detection
                await self._handle_failure(
                    problem,
                    solution_description,
                    EscalationReason.SILENT_FAILURE,
                    "Solution completed but produced no meaningful output",
                )

        except PermissionError as e:
            await self._handle_failure(
                problem,
                solution_description,
                EscalationReason.MISSING_PERMISSIONS,
                str(e),
            )

        except FileNotFoundError as e:
            await self._handle_failure(
                problem,
                solution_description,
                EscalationReason.MISSING_DEPENDENCIES,
                str(e),
            )

        except Exception as e:
            await self._handle_failure(
                problem,
                solution_description,
                EscalationReason.FAILURE_THRESHOLD,
                str(e),
            )

        return None

    async def check_context_usage(self, current_tokens: int, max_tokens: int = 200000):
        """Check if context usage requires escalation"""
        usage_ratio = current_tokens / max_tokens

        if usage_ratio >= self.context_threshold:
            await self.escalate(
                EscalationType.REPLACEMENT,
                EscalationReason.CONTEXT_EXHAUSTION,
                f"Context usage at {usage_ratio:.1%} ({current_tokens}/{max_tokens} tokens)",
                required_context=["preserve_current_state", "continue_from_checkpoint"],
            )

    async def escalate(
        self,
        escalation_type: EscalationType,
        reason: EscalationReason,
        problem_description: str,
        **kwargs,
    ) -> str:
        """
        Escalate problem to manager or sub-swarm.

        Args:
            escalation_type: Type of escalation needed
            reason: Reason for escalation
            problem_description: Description of the problem
            **kwargs: Additional escalation parameters

        Returns:
            Escalation ID for tracking
        """
        escalation_request = EscalationRequest(
            escalation_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            agent_uuid=self.agent_uuid,
            escalation_type=escalation_type,
            escalation_reason=reason,
            problem_description=problem_description,
            attempted_solutions=self.attempted_solutions.copy(),
            failure_count=self.failure_count,
            current_task=self.current_task.copy(),
            **kwargs,
        )

        logger.warning(
            f"Agent {self.agent_id} escalating: {reason.value} -> {escalation_type.value}"
        )

        return await self.escalation_manager.handle_escalation(escalation_request)

    async def _handle_failure(
        self,
        problem: str,
        solution_description: str,
        reason: EscalationReason,
        error_message: str,
    ):
        """Handle solution failure with potential escalation"""
        self.failure_count += 1
        self.attempted_solutions.append(f"{solution_description}: {error_message}")

        logger.warning(
            f"Agent {self.agent_id} failure {self.failure_count}/{self.failure_threshold}: {error_message}"
        )

        # Escalate if threshold reached
        if self.failure_count >= self.failure_threshold:
            if reason == EscalationReason.MISSING_PERMISSIONS:
                await self.escalate(
                    EscalationType.REPLACEMENT,
                    reason,
                    problem,
                    required_permissions=["elevated_access", "file_system_write"],
                )
            elif reason == EscalationReason.MISSING_DEPENDENCIES:
                await self.escalate(
                    EscalationType.MANAGER,
                    reason,
                    problem,
                    required_tools=["dependency_resolver", "file_searcher"],
                )
            elif "complex" in problem.lower() or "debug" in problem.lower():
                await self.escalate(
                    EscalationType.SUB_SWARM,
                    EscalationReason.COMPLEX_DEBUGGING,
                    problem,
                    specialist_types_needed=[
                        "troubleshoot",
                        "research",
                        "test",
                        "solution",
                    ],
                    time_budget=600,
                )
            else:
                await self.escalate(
                    EscalationType.REPLACEMENT,
                    EscalationReason.FAILURE_THRESHOLD,
                    problem,
                    required_tools=["enhanced_debugging", "alternative_approaches"],
                )

    def _is_empty_result(self, result) -> bool:
        """Check if result is effectively empty"""
        if result is None:
            return True
        if isinstance(result, (str, list, dict)) and not result:
            return True
        if isinstance(result, dict) and all(not v for v in result.values()):
            return True
        return False


class ManagerCommunicationBus:
    """
    Communication bus for agent-to-manager escalation.

    Provides structured APIs for manager agents to:
    - Receive escalation requests from agents
    - Send escalation responses with solutions
    - Monitor escalation status across the swarm
    """

    def __init__(self, message_dir: Path):
        self.message_dir = message_dir
        self.message_dir.mkdir(parents=True, exist_ok=True)

        # Create escalation-specific directories
        (self.message_dir / "escalations").mkdir(exist_ok=True)
        (self.message_dir / "responses").mkdir(exist_ok=True)

        self._lock = asyncio.Lock()

    async def send_escalation(self, request: EscalationRequest) -> str:
        """Send escalation request to manager"""
        async with self._lock:
            escalation_file = (
                self.message_dir / "escalations" / f"{request.escalation_id}.json"
            )
            escalation_file.write_text(json.dumps(request.to_dict(), indent=2))

            logger.info(
                f"Escalation {request.escalation_id} sent to manager communication bus"
            )
            return request.escalation_id

    async def get_pending_escalations(self) -> List[EscalationRequest]:
        """Get all pending escalations for manager review"""
        escalations = []

        for escalation_file in (self.message_dir / "escalations").glob("*.json"):
            try:
                data = json.loads(escalation_file.read_text())
                if data.get("status") == "pending":
                    # Convert back to EscalationRequest
                    data["escalation_type"] = EscalationType(data["escalation_type"])
                    data["escalation_reason"] = EscalationReason(
                        data["escalation_reason"]
                    )
                    escalations.append(EscalationRequest(**data))

            except Exception as e:
                logger.error(f"Failed to load escalation from {escalation_file}: {e}")

        return sorted(
            escalations, key=lambda x: (x.priority, x.created_at), reverse=True
        )

    async def send_response(self, response: EscalationResponse):
        """Send response to escalation"""
        async with self._lock:
            response_file = (
                self.message_dir / "responses" / f"{response.escalation_id}.json"
            )
            response_file.write_text(json.dumps(asdict(response), indent=2))

            # Mark escalation as resolved
            escalation_file = (
                self.message_dir / "escalations" / f"{response.escalation_id}.json"
            )
            if escalation_file.exists():
                data = json.loads(escalation_file.read_text())
                data["status"] = "resolved"
                escalation_file.write_text(json.dumps(data, indent=2))

            logger.info(f"Response sent for escalation {response.escalation_id}")

    async def get_response(self, escalation_id: str) -> Optional[EscalationResponse]:
        """Get response for specific escalation"""
        response_file = self.message_dir / "responses" / f"{escalation_id}.json"

        if response_file.exists():
            data = json.loads(response_file.read_text())
            return EscalationResponse(**data)

        return None


class EscalationManager:
    """
    Manages intelligent escalation patterns for agent coordination.

    Features:
    - Automatic escalation processing
    - Manager-side enhancement logic
    - Sub-swarm delegation
    - Learning from escalation patterns
    """

    def __init__(
        self, output_dir: Path, manager_agent_id: str = "orchestrator_manager"
    ):
        self.output_dir = output_dir
        self.manager_agent_id = manager_agent_id

        # Initialize communication bus
        self.comm_bus = ManagerCommunicationBus(output_dir / "escalation_bus")

        # Escalation tracking
        self.active_escalations: Dict[str, EscalationRequest] = {}
        self.escalation_stats = {
            "total_escalations": 0,
            "resolved_escalations": 0,
            "sub_swarms_created": 0,
            "replacements_spawned": 0,
            "manager_interventions": 0,
        }

        # Learning system - track what enhancements work
        self.enhancement_patterns: Dict[str, List[str]] = {}

        logger.info(f"EscalationManager initialized for output directory: {output_dir}")

    async def handle_escalation(self, request: EscalationRequest) -> str:
        """Process escalation request and determine response"""

        self.escalation_stats["total_escalations"] += 1
        self.active_escalations[request.escalation_id] = request

        logger.info(
            f"Processing escalation {request.escalation_id}: {request.escalation_reason.value} -> {request.escalation_type.value}"
        )

        # Send to communication bus for manager processing
        await self.comm_bus.send_escalation(request)

        # Auto-resolve simple cases
        if request.escalation_type == EscalationType.REPLACEMENT:
            await self._auto_spawn_replacement(request)
        elif request.escalation_type == EscalationType.SUB_SWARM:
            await self._auto_create_sub_swarm(request)

        return request.escalation_id

    async def _auto_spawn_replacement(self, request: EscalationRequest):
        """Automatically spawn enhanced replacement agent"""

        # Determine enhancements based on escalation reason
        enhancements = []

        if request.escalation_reason == EscalationReason.MISSING_PERMISSIONS:
            enhancements.extend(["elevated_permissions", "file_system_access"])
        elif request.escalation_reason == EscalationReason.CONTEXT_EXHAUSTION:
            enhancements.extend(["context_handoff", "state_preservation"])
        elif request.escalation_reason == EscalationReason.MISSING_DEPENDENCIES:
            enhancements.extend(["dependency_resolution", "file_search_tools"])
        elif request.escalation_reason == EscalationReason.FAILURE_THRESHOLD:
            enhancements.extend(["alternative_strategies", "enhanced_debugging"])

        # Add user-specified requirements
        enhancements.extend(request.required_tools)
        enhancements.extend(request.required_permissions)

        new_agent_uuid = str(uuid.uuid4())

        response = EscalationResponse(
            escalation_id=request.escalation_id,
            response_type="replacement_spawned",
            new_agent_uuid=new_agent_uuid,
            enhanced_capabilities=enhancements,
            handoff_instructions=self._generate_handoff_instructions(request),
            context_preservation={
                "attempted_solutions": request.attempted_solutions,
                "current_task": request.current_task,
                "environment_info": request.environment_info,
            },
            resolver_agent=self.manager_agent_id,
        )

        await self.comm_bus.send_response(response)
        self.escalation_stats["replacements_spawned"] += 1

        # Learn from this pattern
        reason_key = request.escalation_reason.value
        if reason_key not in self.enhancement_patterns:
            self.enhancement_patterns[reason_key] = []
        self.enhancement_patterns[reason_key].extend(enhancements)

        logger.info(
            f"Auto-spawned replacement agent {new_agent_uuid} with enhancements: {enhancements}"
        )

    async def _auto_create_sub_swarm(self, request: EscalationRequest):
        """Automatically create specialized sub-swarm for complex problems"""

        sub_swarm_id = f"subswarm_{uuid.uuid4().hex[:8]}"

        # Default specialist types for complex debugging
        specialists = request.specialist_types_needed or [
            "troubleshoot_specialist",
            "research_specialist",
            "test_specialist",
            "solution_specialist",
        ]

        # Generate UUIDs for sub-swarm agents
        agent_uuids = [
            f"{sub_swarm_id}_{specialist}_{uuid.uuid4().hex[:8]}"
            for specialist in specialists
        ]

        response = EscalationResponse(
            escalation_id=request.escalation_id,
            response_type="sub_swarm_created",
            sub_swarm_id=sub_swarm_id,
            sub_swarm_agents=agent_uuids,
            handoff_instructions=self._generate_sub_swarm_instructions(request),
            context_preservation={
                "problem_context": request.problem_description,
                "failed_attempts": request.attempted_solutions,
                "time_budget": request.time_budget,
                "complexity": request.estimated_complexity,
            },
            resolver_agent=self.manager_agent_id,
        )

        await self.comm_bus.send_response(response)
        self.escalation_stats["sub_swarms_created"] += 1

        logger.info(
            f"Auto-created sub-swarm {sub_swarm_id} with {len(specialists)} specialists: {specialists}"
        )

    def _generate_handoff_instructions(self, request: EscalationRequest) -> str:
        """Generate instructions for replacement agent handoff"""

        instructions = f"""
# Agent Handoff Instructions

## Problem Context
{request.problem_description}

## Previous Attempts (DO NOT REPEAT)
{chr(10).join(f"- {attempt}" for attempt in request.attempted_solutions)}

## Enhanced Capabilities Available
You have been spawned with enhanced capabilities to solve this problem.
Use your additional tools and permissions to find alternative solutions.

## Current Task State
{json.dumps(request.current_task, indent=2)}

## Environment Information
{json.dumps(request.environment_info, indent=2)}

## Next Actions
1. Analyze why previous attempts failed
2. Use your enhanced capabilities to try alternative approaches
3. If still blocked, escalate with more specific requirements
"""

        return instructions.strip()

    def _generate_sub_swarm_instructions(self, request: EscalationRequest) -> str:
        """Generate instructions for sub-swarm coordination"""

        instructions = f"""
# Sub-Swarm Coordination Instructions

## Problem Requiring Specialized Team
{request.problem_description}

## Time Budget: {request.time_budget} seconds
## Complexity: {request.estimated_complexity}

## Team Composition
Each specialist has a specific role:

1. **Troubleshoot Specialist**: Analyze the problem and identify root causes
2. **Research Specialist**: Find relevant documentation, examples, and solutions
3. **Test Specialist**: Validate potential solutions and identify edge cases
4. **Solution Specialist**: Implement the final working solution

## Coordination Protocol
1. Troubleshoot specialist starts with problem analysis
2. Research specialist provides additional context and examples
3. Test specialist validates approaches from troubleshoot + research
4. Solution specialist implements the validated approach
5. All results are shared back to the main agent

## Failed Attempts to Avoid
{chr(10).join(f"- {attempt}" for attempt in request.attempted_solutions)}

## Success Criteria
- Provide working solution to original agent
- Document what was tried and why it worked
- Complete within time budget
"""

        return instructions.strip()

    async def get_escalation_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data for manager agents"""

        pending_escalations = await self.comm_bus.get_pending_escalations()

        return {
            "stats": self.escalation_stats,
            "pending_count": len(pending_escalations),
            "pending_escalations": [
                {
                    "id": req.escalation_id,
                    "agent": req.agent_id,
                    "type": req.escalation_type.value,
                    "reason": req.escalation_reason.value,
                    "priority": req.priority,
                    "created": req.created_at,
                    "description": req.problem_description[:100] + "..."
                    if len(req.problem_description) > 100
                    else req.problem_description,
                }
                for req in pending_escalations[:10]  # Show top 10
            ],
            "enhancement_patterns": self.enhancement_patterns,
            "active_escalations": len(self.active_escalations),
        }

    async def close(self):
        """Clean up resources"""
        logger.info("EscalationManager shutting down")

        # Save final statistics
        stats_file = self.output_dir / "escalation_stats.json"
        stats_file.write_text(
            json.dumps(
                {
                    **self.escalation_stats,
                    "enhancement_patterns": self.enhancement_patterns,
                    "shutdown_time": datetime.now().isoformat(),
                },
                indent=2,
            )
        )
