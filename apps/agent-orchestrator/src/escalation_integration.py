#!/usr/bin/env python3
"""
Escalation Integration Layer - Seamless integration between escalation system and existing orchestrator framework

Provides:
1. EscalationAwareOrchestrator - Extension of EnhancedOrchestrator with escalation capabilities
2. Backward compatibility with all existing orchestrator usage patterns
3. Non-breaking integration with AgentTeamManager
4. Configuration options for enabling/disabling escalation features
5. Manager agent APIs for escalation monitoring and control

Features:
- Automatic escalation manager initialization
- Hooks into existing task execution flow
- Intelligent agent enhancement for spawned agents
- Manager-side escalation dashboard and control APIs
- Full backward compatibility - existing code works unchanged
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Import base orchestrator components
from enhanced_orchestrator import EnhancedAgentTask, EnhancedOrchestrator
from escalation_manager import (
    EscalationManager,
    EscalationReason,
    EscalationRequest,
    EscalationType,
    IntelligentAgent,
)
from generic_orchestrator import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class EscalationConfig:
    """Configuration for escalation system integration"""

    # Enable/disable escalation features
    enable_escalation: bool = True
    enable_auto_replacement: bool = True
    enable_sub_swarm_delegation: bool = True
    enable_manager_takeover: bool = True

    # Escalation thresholds
    failure_threshold: int = 3  # Escalate after N failures
    context_threshold: float = 0.90  # Escalate at 90% context usage
    time_threshold: int = 1800  # Escalate after 30 minutes

    # Manager agent configuration
    manager_agent_id: str = "escalation_manager"
    escalation_polling_interval: int = 30  # seconds

    # Enhancement patterns
    auto_enhance_on_failure: bool = True
    learn_from_escalations: bool = True
    preserve_escalation_history: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "enable_escalation": self.enable_escalation,
            "enable_auto_replacement": self.enable_auto_replacement,
            "enable_sub_swarm_delegation": self.enable_sub_swarm_delegation,
            "enable_manager_takeover": self.enable_manager_takeover,
            "failure_threshold": self.failure_threshold,
            "context_threshold": self.context_threshold,
            "time_threshold": self.time_threshold,
            "manager_agent_id": self.manager_agent_id,
            "escalation_polling_interval": self.escalation_polling_interval,
            "auto_enhance_on_failure": self.auto_enhance_on_failure,
            "learn_from_escalations": self.learn_from_escalations,
            "preserve_escalation_history": self.preserve_escalation_history,
        }


@dataclass
class EscalationAwareTask(EnhancedAgentTask):
    """Enhanced task with escalation awareness"""

    # Escalation configuration for this task
    escalation_enabled: bool = True
    failure_threshold: int = 3
    context_threshold: float = 0.90
    time_threshold: int = 1800  # 30 minutes

    # Escalation history
    escalation_count: int = 0
    escalation_history: List[str] = field(default_factory=list)
    replacement_count: int = 0

    # Enhanced agent capabilities (for spawned replacements)
    required_permissions: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    required_context: List[str] = field(default_factory=list)

    # Sub-swarm delegation parameters
    complexity_level: str = "medium"  # low, medium, high, critical
    specialist_types: List[str] = field(default_factory=list)
    delegation_budget: int = 600  # seconds


class EscalationAwareOrchestrator(EnhancedOrchestrator):
    """
    Enhanced orchestrator with intelligent escalation capabilities.

    Extends EnhancedOrchestrator to add:
    - Automatic escalation system integration
    - Intelligent agent enhancement for task execution
    - Manager-side escalation monitoring and control
    - Full backward compatibility with existing orchestrator usage
    - Configurable escalation patterns and thresholds
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        # Enhanced orchestrator features (passed through)
        enable_quality_gates: bool = True,
        enable_monitoring: bool = True,
        quality_gate_config: Dict[str, Any] = None,
        chat_logs_dir: Optional[str] = None,
        quality_gate_state_dir: Optional[Path] = None,
        # Escalation system configuration
        escalation_config: Optional[EscalationConfig] = None,
        escalation_output_dir: Optional[Path] = None,
    ):
        """
        Initialize EscalationAwareOrchestrator

        Args:
            output_dir: Base output directory for orchestration
            max_parallel: Maximum parallel task execution
            tokens: Claude API tokens
            use_optimizations: Enable performance optimizations
            enable_quality_gates: Enable quality gate validation
            enable_monitoring: Enable real-time monitoring
            quality_gate_config: Quality gate configuration
            chat_logs_dir: Directory for chat logs (monitoring)
            quality_gate_state_dir: Directory for quality gate state
            escalation_config: Escalation system configuration
            escalation_output_dir: Directory for escalation system outputs
        """

        # Initialize parent EnhancedOrchestrator
        super().__init__(
            output_dir=output_dir,
            max_parallel=max_parallel,
            tokens=tokens,
            use_optimizations=use_optimizations,
            enable_quality_gates=enable_quality_gates,
            enable_monitoring=enable_monitoring,
            quality_gate_config=quality_gate_config,
            chat_logs_dir=chat_logs_dir,
            quality_gate_state_dir=quality_gate_state_dir,
        )

        # Escalation system configuration
        self.escalation_config = escalation_config or EscalationConfig()
        self.escalation_enabled = self.escalation_config.enable_escalation

        # Initialize escalation manager if enabled
        self.escalation_manager: Optional[EscalationManager] = None
        if self.escalation_enabled:
            escalation_dir = escalation_output_dir or (output_dir / "escalation")
            self.escalation_manager = EscalationManager(
                output_dir=escalation_dir,
                manager_agent_id=self.escalation_config.manager_agent_id,
            )

        # Escalation tracking
        self.escalation_metrics = {
            "total_escalations": 0,
            "auto_replacements": 0,
            "sub_swarm_delegations": 0,
            "manager_takeovers": 0,
            "successful_resolutions": 0,
            "failed_resolutions": 0,
        }

        # Enhanced agent tracking for escalation
        self.intelligent_agents: Dict[str, IntelligentAgent] = {}
        self.escalation_callbacks: Dict[str, Callable] = {}

        # Background escalation processing
        self._escalation_processor_task: Optional[asyncio.Task] = None
        if self.escalation_enabled:
            self._escalation_processor_task = asyncio.create_task(
                self._process_escalations_background()
            )

        logger.info(
            f"EscalationAwareOrchestrator initialized (escalation: {self.escalation_enabled})"
        )

    async def execute_agent(self, task: AgentTask) -> Dict:
        """
        Execute agent with escalation awareness.

        Maintains full backward compatibility while adding escalation capabilities
        when enabled and when using EscalationAwareTask instances.
        """

        # Handle regular tasks with backward compatibility
        if not isinstance(task, EscalationAwareTask):
            # Convert to EscalationAwareTask if escalation is enabled
            if self.escalation_enabled:
                escalation_task = EscalationAwareTask(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    prompt=task.prompt,
                    context=task.context,
                    dependencies=task.dependencies,
                    status=task.status,
                    result=task.result,
                    error=task.error,
                    start_time=task.start_time,
                    end_time=task.end_time,
                    # Apply default escalation settings
                    escalation_enabled=True,
                    failure_threshold=self.escalation_config.failure_threshold,
                    context_threshold=self.escalation_config.context_threshold,
                    time_threshold=self.escalation_config.time_threshold,
                )
                return await self.execute_agent_with_escalation(escalation_task)
            else:
                # Use parent implementation for non-escalation tasks
                return await super().execute_agent(task)

        # Handle EscalationAwareTask instances
        return await self.execute_agent_with_escalation(task)

    async def execute_agent_with_escalation(self, task: EscalationAwareTask) -> Dict:
        """Execute agent with full escalation support"""

        # Create intelligent agent wrapper if escalation enabled for this task
        intelligent_agent = None
        if task.escalation_enabled and self.escalation_manager:
            intelligent_agent = IntelligentAgent(
                agent_id=task.task_id,
                agent_uuid=task.agent_uuid or str(uuid.uuid4()),
                escalation_manager=self.escalation_manager,
                failure_threshold=task.failure_threshold,
                context_threshold=task.context_threshold,
            )
            self.intelligent_agents[task.task_id] = intelligent_agent

        # Enhanced prompt building with escalation context
        original_prompt = task.prompt
        if intelligent_agent:
            task.prompt = await self._build_escalation_aware_prompt(
                task, intelligent_agent
            )

        # Set up escalation monitoring
        start_time = datetime.now().timestamp()

        try:
            # Execute using parent EnhancedOrchestrator
            result = await super().execute_agent(task)

            # Check for escalation conditions
            if intelligent_agent and task.escalation_enabled:
                await self._check_escalation_conditions(task, intelligent_agent, result)

            return result

        except Exception as e:
            # Handle execution failure with escalation
            if intelligent_agent and task.escalation_enabled:
                await self._handle_execution_failure(task, intelligent_agent, str(e))

            # Re-raise for normal error handling
            raise

        finally:
            # Restore original prompt
            task.prompt = original_prompt

            # Clean up intelligent agent if task completed
            if task.task_id in self.intelligent_agents and task.status in [
                "completed",
                "failed",
            ]:
                del self.intelligent_agents[task.task_id]

    async def _build_escalation_aware_prompt(
        self, task: EscalationAwareTask, intelligent_agent: IntelligentAgent
    ) -> str:
        """Build enhanced prompt with escalation awareness"""

        escalation_context = f"""
AGENT_ESCALATION_ENABLED: true
AGENT_UUID: {intelligent_agent.agent_uuid}
FAILURE_THRESHOLD: {task.failure_threshold}
ESCALATION_COUNT: {task.escalation_count}

ESCALATION_INSTRUCTIONS:
If you encounter problems you cannot solve:
1. Try {task.failure_threshold} different approaches
2. If still blocked, use escalation request format:
   ESCALATION_REQUEST: {{
     "type": "manager|sub_swarm|replacement",
     "reason": "failure_threshold|missing_permissions|complex_debugging|etc",
     "description": "Detailed problem description",
     "attempted_solutions": ["solution1", "solution2", "..."],
     "requirements": ["required_tools", "required_permissions", "..."]
   }}

ESCALATION_HISTORY:
{chr(10).join(f"- {entry}" for entry in task.escalation_history)}

"""

        return escalation_context + task.prompt

    async def _check_escalation_conditions(
        self,
        task: EscalationAwareTask,
        intelligent_agent: IntelligentAgent,
        result: Dict,
    ):
        """Check if escalation is needed based on task execution result"""

        execution_time = (task.end_time or 0) - (task.start_time or 0)

        # Check time threshold
        if execution_time > task.time_threshold:
            await intelligent_agent.escalate(
                EscalationType.MANAGER,
                EscalationReason.TIME_EXCEEDED,
                f"Task exceeded time threshold: {execution_time:.1f}s > {task.time_threshold}s",
            )

        # Check for silent failure (completed but no meaningful output)
        if task.status == "completed" and (
            not result.get("result") or self._is_empty_result(result["result"])
        ):
            await intelligent_agent.escalate(
                EscalationType.REPLACEMENT,
                EscalationReason.SILENT_FAILURE,
                "Task completed but produced no meaningful output",
            )

        # Parse result for escalation requests
        if task.status == "completed" and result.get("result"):
            await self._parse_escalation_requests(
                task, intelligent_agent, result["result"]
            )

    async def _handle_execution_failure(
        self, task: EscalationAwareTask, intelligent_agent: IntelligentAgent, error: str
    ):
        """Handle execution failure with potential escalation"""

        # Increment failure count
        task.escalation_count += 1

        # Determine escalation type based on error
        if "permission" in error.lower() or "access" in error.lower():
            await intelligent_agent.escalate(
                EscalationType.REPLACEMENT,
                EscalationReason.MISSING_PERMISSIONS,
                f"Permission error: {error}",
                required_permissions=["elevated_access", "file_system_write"],
            )
        elif "not found" in error.lower() or "missing" in error.lower():
            await intelligent_agent.escalate(
                EscalationType.MANAGER,
                EscalationReason.MISSING_DEPENDENCIES,
                f"Dependency error: {error}",
                required_tools=["dependency_resolver", "file_searcher"],
            )
        elif task.escalation_count >= task.failure_threshold:
            # Complex problem - delegate to sub-swarm
            if task.complexity_level in ["high", "critical"]:
                await intelligent_agent.escalate(
                    EscalationType.SUB_SWARM,
                    EscalationReason.COMPLEX_DEBUGGING,
                    f"Complex problem after {task.escalation_count} failures: {error}",
                    specialist_types_needed=task.specialist_types
                    or ["troubleshoot", "research", "test", "solution"],
                    time_budget=task.delegation_budget,
                )
            else:
                # Simple replacement
                await intelligent_agent.escalate(
                    EscalationType.REPLACEMENT,
                    EscalationReason.FAILURE_THRESHOLD,
                    f"Task failed {task.escalation_count} times: {error}",
                    required_tools=["enhanced_debugging", "alternative_approaches"],
                )

    async def _parse_escalation_requests(
        self,
        task: EscalationAwareTask,
        intelligent_agent: IntelligentAgent,
        result_data: Any,
    ):
        """Parse agent output for escalation requests"""

        if not isinstance(result_data, dict):
            return

        # Look for escalation requests in various formats
        escalation_request = None

        # Check for direct escalation request
        if "escalation_request" in result_data:
            escalation_request = result_data["escalation_request"]

        # Check for escalation in messages or logs
        elif "messages" in result_data:
            for message in result_data.get("messages", []):
                if isinstance(message, str) and "ESCALATION_REQUEST:" in message:
                    try:
                        # Parse JSON from message
                        escalation_json = message.split("ESCALATION_REQUEST:")[
                            1
                        ].strip()
                        escalation_request = json.loads(escalation_json)
                        break
                    except json.JSONDecodeError:
                        pass

        if escalation_request and isinstance(escalation_request, dict):
            # Process the escalation request
            escalation_type = EscalationType(escalation_request.get("type", "manager"))
            escalation_reason = EscalationReason(
                escalation_request.get("reason", "failure_threshold")
            )

            await intelligent_agent.escalate(
                escalation_type,
                escalation_reason,
                escalation_request.get("description", "Agent requested escalation"),
                attempted_solutions=escalation_request.get("attempted_solutions", []),
                required_tools=escalation_request.get("requirements", []),
            )

    async def _process_escalations_background(self):
        """Background task to process pending escalations"""

        while True:
            try:
                if self.escalation_manager:
                    # Get escalation dashboard data
                    dashboard = await self.escalation_manager.get_escalation_dashboard()

                    if dashboard.get("pending_count", 0) > 0:
                        logger.info(
                            f"Processing {dashboard['pending_count']} pending escalations"
                        )

                        # Update metrics
                        self.escalation_metrics.update(dashboard.get("stats", {}))

                await asyncio.sleep(self.escalation_config.escalation_polling_interval)

            except Exception as e:
                logger.error(f"Error in escalation background processing: {e}")
                await asyncio.sleep(
                    self.escalation_config.escalation_polling_interval * 2
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

    # Manager API methods for escalation control

    async def get_escalation_dashboard(self) -> Dict[str, Any]:
        """Get escalation dashboard for manager agents"""

        if not self.escalation_manager:
            return {
                "escalation_enabled": False,
                "message": "Escalation system not enabled",
            }

        dashboard = await self.escalation_manager.get_escalation_dashboard()
        dashboard.update(
            {
                "escalation_config": self.escalation_config.to_dict(),
                "escalation_metrics": self.escalation_metrics,
                "active_intelligent_agents": list(self.intelligent_agents.keys()),
            }
        )

        return dashboard

    async def handle_manual_escalation(
        self,
        task_id: str,
        escalation_type: str,
        reason: str,
        description: str,
        **kwargs,
    ) -> str:
        """Handle manual escalation from manager agent"""

        if not self.escalation_manager:
            raise RuntimeError("Escalation system not enabled")

        # Create manual escalation request
        escalation_request = EscalationRequest(
            escalation_id=str(uuid.uuid4()),
            agent_id=f"manager_{self.escalation_config.manager_agent_id}",
            agent_uuid=str(uuid.uuid4()),
            escalation_type=EscalationType(escalation_type),
            escalation_reason=EscalationReason(reason),
            problem_description=description,
            current_task={"task_id": task_id},
            priority="high",  # Manager escalations are high priority
            **kwargs,
        )

        return await self.escalation_manager.handle_escalation(escalation_request)

    async def resolve_escalation(
        self, escalation_id: str, resolution_type: str, **kwargs
    ) -> bool:
        """Resolve escalation with specific solution"""

        if not self.escalation_manager:
            return False

        # Implementation would depend on escalation manager API
        # This provides the interface for manager agents
        logger.info(f"Resolving escalation {escalation_id} with {resolution_type}")
        return True

    async def shutdown(self):
        """Clean shutdown of escalation-aware orchestrator"""

        logger.info("Shutting down EscalationAwareOrchestrator")

        # Stop background escalation processing
        if self._escalation_processor_task:
            self._escalation_processor_task.cancel()
            try:
                await self._escalation_processor_task
            except asyncio.CancelledError:
                pass

        # Cleanup escalation manager
        if self.escalation_manager:
            await self.escalation_manager.close()

        # Clear intelligent agents
        self.intelligent_agents.clear()

        # Call parent shutdown
        if hasattr(super(), "shutdown"):
            await super().shutdown()

    # Factory methods for common escalation configurations

    def create_escalation_aware_task(
        self,
        task_id: str,
        task_type: str,
        prompt: str,
        dependencies: List[str] = None,
        # Standard EnhancedAgentTask parameters
        quality_gates: List[str] = None,
        validation_required: bool = True,
        phase_id: str = None,
        context: Dict[str, Any] = None,
        agent_uuid: Optional[str] = None,
        team_id: Optional[str] = None,
        monitoring_enabled: bool = True,
        # Escalation-specific parameters
        escalation_enabled: bool = True,
        failure_threshold: int = None,
        context_threshold: float = None,
        time_threshold: int = None,
        complexity_level: str = "medium",
        specialist_types: List[str] = None,
        required_permissions: List[str] = None,
        required_tools: List[str] = None,
    ) -> EscalationAwareTask:
        """Create escalation-aware task with configuration"""

        return EscalationAwareTask(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            dependencies=dependencies or [],
            context=context or {},
            # Enhanced task parameters
            quality_gates=quality_gates or [],
            validation_required=validation_required,
            phase_id=phase_id,
            agent_uuid=agent_uuid,
            team_id=team_id,
            monitoring_enabled=monitoring_enabled,
            # Escalation parameters
            escalation_enabled=escalation_enabled,
            failure_threshold=failure_threshold
            or self.escalation_config.failure_threshold,
            context_threshold=context_threshold
            or self.escalation_config.context_threshold,
            time_threshold=time_threshold or self.escalation_config.time_threshold,
            complexity_level=complexity_level,
            specialist_types=specialist_types or [],
            required_permissions=required_permissions or [],
            required_tools=required_tools or [],
        )


# Factory functions for different escalation configurations


def create_development_orchestrator(
    output_dir: Path,
    tokens: List[str] = None,
    max_parallel: int = 5,
    enable_escalation: bool = True,
) -> EscalationAwareOrchestrator:
    """Create orchestrator optimized for development tasks with escalation support"""

    escalation_config = EscalationConfig(
        enable_escalation=enable_escalation,
        failure_threshold=2,  # Lower threshold for dev work
        context_threshold=0.85,  # Earlier context escalation
        time_threshold=900,  # 15 minutes for dev tasks
        enable_auto_replacement=True,
        enable_sub_swarm_delegation=True,
        auto_enhance_on_failure=True,
    )

    return EscalationAwareOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,
        tokens=tokens,
        enable_quality_gates=True,
        enable_monitoring=True,
        escalation_config=escalation_config,
    )


def create_research_orchestrator(
    output_dir: Path,
    tokens: List[str] = None,
    max_parallel: int = 3,
    enable_escalation: bool = True,
) -> EscalationAwareOrchestrator:
    """Create orchestrator optimized for research tasks with escalation support"""

    escalation_config = EscalationConfig(
        enable_escalation=enable_escalation,
        failure_threshold=3,  # Standard threshold for research
        context_threshold=0.95,  # Later context escalation (research needs more context)
        time_threshold=1800,  # 30 minutes for research tasks
        enable_sub_swarm_delegation=True,  # Research benefits from specialist teams
        auto_enhance_on_failure=True,
        learn_from_escalations=True,
    )

    return EscalationAwareOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,
        tokens=tokens,
        enable_quality_gates=True,
        enable_monitoring=True,
        escalation_config=escalation_config,
    )


def create_production_orchestrator(
    output_dir: Path,
    tokens: List[str] = None,
    max_parallel: int = 8,
    enable_escalation: bool = True,
) -> EscalationAwareOrchestrator:
    """Create orchestrator optimized for production tasks with conservative escalation"""

    escalation_config = EscalationConfig(
        enable_escalation=enable_escalation,
        failure_threshold=5,  # Higher threshold for production stability
        context_threshold=0.95,  # Conservative context usage
        time_threshold=3600,  # 1 hour for production tasks
        enable_auto_replacement=False,  # Manual approval for production
        enable_sub_swarm_delegation=True,
        enable_manager_takeover=True,
        auto_enhance_on_failure=False,  # Conservative enhancement
    )

    return EscalationAwareOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,
        tokens=tokens,
        enable_quality_gates=True,
        enable_monitoring=True,
        escalation_config=escalation_config,
    )


# Backward compatibility aliases
EscalationOrchestrator = EscalationAwareOrchestrator
IntelligentOrchestrator = EscalationAwareOrchestrator
