#!/usr/bin/env python3
"""
AgentTeamManager - Primary Management Interface for Agent Teams

Unified interface that enables any management agent to launch and monitor agent teams.
Integrates all specialist components: Enhanced Orchestrator, Agent Status Monitor, and Quality Gate Manager.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Iterator, List, Optional

# Import specialist components
from enhanced_orchestrator import EnhancedAgentTask, EnhancedOrchestrator
from escalation_integration import (
    EscalationAwareOrchestrator,
    EscalationAwareTask,
    EscalationConfig,
)
from quality_gates import GateStatus, QualityGateManager, ValidationResult

from .agent_monitor import AgentStatus, AgentStatusMonitor

logger = logging.getLogger(__name__)


@dataclass
class TeamStatus:
    """Unified status aggregating all agent statuses in a team"""

    team_id: str
    status: str  # running, completed, failed, stuck, blocked
    agent_count: int
    agents_running: int = 0
    agents_completed: int = 0
    agents_failed: int = 0
    agents_stuck: int = 0
    agents_blocked: int = 0

    # Progress tracking
    overall_progress_percentage: float = 0.0
    estimated_completion_time: Optional[str] = None

    # Individual agent statuses
    agent_statuses: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Quality gate information
    quality_gates_status: Dict[str, str] = field(default_factory=dict)
    blocked_by_gates: List[str] = field(default_factory=list)

    # Escalation information
    escalation_count: int = 0
    active_escalations: List[str] = field(default_factory=list)
    resolved_escalations: int = 0

    # Timing information
    start_time: Optional[str] = None
    last_update: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "team_id": self.team_id,
            "status": self.status,
            "agent_count": self.agent_count,
            "agents_running": self.agents_running,
            "agents_completed": self.agents_completed,
            "agents_failed": self.agents_failed,
            "agents_stuck": self.agents_stuck,
            "agents_blocked": self.agents_blocked,
            "overall_progress_percentage": self.overall_progress_percentage,
            "estimated_completion_time": self.estimated_completion_time,
            "agent_statuses": self.agent_statuses,
            "quality_gates_status": self.quality_gates_status,
            "blocked_by_gates": self.blocked_by_gates,
            "escalation_count": self.escalation_count,
            "active_escalations": self.active_escalations,
            "resolved_escalations": self.resolved_escalations,
            "start_time": self.start_time,
            "last_update": self.last_update,
        }


@dataclass
class TeamResults:
    """Final results from team execution"""

    team_id: str
    status: str  # completed, failed, partial
    execution_time: float

    # Individual agent results
    agent_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Summary metrics
    success_rate: float = 0.0
    total_errors: int = 0
    deliverables_created: List[str] = field(default_factory=list)

    # Quality metrics
    quality_gates_passed: int = 0
    quality_gates_failed: int = 0
    validation_errors: List[str] = field(default_factory=list)

    # Full execution log
    execution_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "team_id": self.team_id,
            "status": self.status,
            "execution_time": self.execution_time,
            "agent_results": self.agent_results,
            "success_rate": self.success_rate,
            "total_errors": self.total_errors,
            "deliverables_created": self.deliverables_created,
            "quality_gates_passed": self.quality_gates_passed,
            "quality_gates_failed": self.quality_gates_failed,
            "validation_errors": self.validation_errors,
            "execution_summary": self.execution_summary,
        }


class AgentTeamManager:
    """
    Primary management interface for launching and monitoring agent teams.

    Provides a unified, simplified interface that hides the complexity of
    Enhanced Orchestrator, Agent Status Monitor, and Quality Gate Manager.
    Designed for use by management agents that need to coordinate teams.
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        chat_logs_dir: Optional[str] = None,
        enable_quality_gates: bool = True,
        enable_monitoring: bool = True,
        quality_gate_state_dir: Optional[Path] = None,
        # Escalation system parameters
        enable_escalation: bool = True,
        escalation_config: Optional[EscalationConfig] = None,
        use_escalation_aware_orchestrator: bool = True,
    ):
        """
        Initialize the AgentTeamManager

        Args:
            output_dir: Directory for orchestration outputs
            max_parallel: Maximum parallel agents
            tokens: Claude API tokens
            chat_logs_dir: Directory for chat logs (for monitoring)
            enable_quality_gates: Enable quality gate validation
            enable_monitoring: Enable real-time monitoring
            quality_gate_state_dir: Directory for quality gate state
            enable_escalation: Enable escalation system integration
            escalation_config: Custom escalation configuration
            use_escalation_aware_orchestrator: Use EscalationAwareOrchestrator instead of EnhancedOrchestrator
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Store escalation configuration
        self.enable_escalation = enable_escalation
        self.escalation_config = escalation_config

        # Initialize orchestrator - choose based on escalation configuration
        if use_escalation_aware_orchestrator and enable_escalation:
            self.orchestrator = EscalationAwareOrchestrator(
                output_dir=self.output_dir,
                max_parallel=max_parallel,
                tokens=tokens,
                enable_quality_gates=enable_quality_gates,
                enable_monitoring=enable_monitoring,
                chat_logs_dir=chat_logs_dir,
                quality_gate_state_dir=quality_gate_state_dir,
                escalation_config=escalation_config,
            )
        else:
            self.orchestrator = EnhancedOrchestrator(
                output_dir=self.output_dir,
                max_parallel=max_parallel,
                tokens=tokens,
                enable_quality_gates=enable_quality_gates,
                enable_monitoring=enable_monitoring,
                chat_logs_dir=chat_logs_dir,
                quality_gate_state_dir=quality_gate_state_dir,
            )

        # Initialize Agent Status Monitor
        self.monitor: Optional[AgentStatusMonitor] = None
        if enable_monitoring:
            self.monitor = AgentStatusMonitor(chat_logs_dir)

        # Get reference to quality gate manager
        self.quality_gate_manager = self.orchestrator.quality_gate_manager

        # Active teams tracking
        self.active_teams: Dict[str, Dict[str, Any]] = {}
        self.team_lock = asyncio.Lock()

        logger.info(f"AgentTeamManager initialized (output_dir: {output_dir})")

    def launch_monitored_team(self, task_definitions: List[Dict]) -> str:
        """
        Launch a monitored team of agents

        Args:
            task_definitions: List of task definitions, each containing:
                - task_id: Unique task identifier
                - task_type: Type of task (e.g., "specialist", "research")
                - prompt: Task prompt/instructions
                - dependencies: List of task IDs this depends on
                - quality_gates: List of quality gates required (optional)
                - agent_uuid: Predictable UUID for monitoring (optional)
                - team_id: Team identifier (optional)

        Returns:
            team_id: Unique identifier for the launched team
        """
        # Generate team ID if not provided
        team_id = None
        for task_def in task_definitions:
            if task_def.get("team_id"):
                team_id = task_def["team_id"]
                break

        if not team_id:
            team_id = f"team-{str(uuid.uuid4())[:8]}"

        # Convert task definitions to appropriate task type
        enhanced_tasks = []
        for task_def in task_definitions:
            # Extract enhanced parameters
            agent_uuid = task_def.get("agent_uuid")
            if not agent_uuid and team_id:
                # Generate predictable UUID based on team and task
                agent_uuid = f"{team_id}-{task_def['task_id']}-{str(uuid.uuid4())[:8]}"

            # Create escalation-aware task if escalation is enabled
            if self.enable_escalation and isinstance(
                self.orchestrator, EscalationAwareOrchestrator
            ):
                enhanced_task = self.orchestrator.create_escalation_aware_task(
                    task_id=task_def["task_id"],
                    task_type=task_def["task_type"],
                    prompt=task_def["prompt"],
                    dependencies=task_def.get("dependencies", []),
                    context=task_def.get("context", {}),
                    # Enhanced parameters
                    quality_gates=task_def.get("quality_gates", []),
                    validation_required=task_def.get("validation_required", True),
                    phase_id=task_def.get("phase_id"),
                    agent_uuid=agent_uuid,
                    team_id=team_id,
                    monitoring_enabled=True,
                    # Escalation parameters
                    escalation_enabled=task_def.get("escalation_enabled", True),
                    complexity_level=task_def.get("complexity_level", "medium"),
                    specialist_types=task_def.get("specialist_types", []),
                    required_permissions=task_def.get("required_permissions", []),
                    required_tools=task_def.get("required_tools", []),
                )
            else:
                # Use standard EnhancedAgentTask
                enhanced_task = EnhancedAgentTask(
                    task_id=task_def["task_id"],
                    task_type=task_def["task_type"],
                    prompt=task_def["prompt"],
                    dependencies=task_def.get("dependencies", []),
                    context=task_def.get("context", {}),
                    # Enhanced parameters
                    quality_gates=task_def.get("quality_gates", []),
                    validation_required=task_def.get("validation_required", True),
                    phase_id=task_def.get("phase_id"),
                    agent_uuid=agent_uuid,
                    team_id=team_id,
                    monitoring_enabled=True,
                )
            enhanced_tasks.append(enhanced_task)

        # Launch team in background using Enhanced Orchestrator
        asyncio.create_task(self._launch_team_background(team_id, enhanced_tasks))

        logger.info(
            f"Launched monitored team {team_id} with {len(enhanced_tasks)} agents"
        )
        return team_id

    async def _launch_team_background(
        self, team_id: str, tasks: List[EnhancedAgentTask]
    ):
        """Launch team execution in background"""
        start_time = datetime.now()

        # Register team
        async with self.team_lock:
            self.active_teams[team_id] = {
                "status": "running",
                "start_time": start_time.isoformat(),
                "tasks": {task.task_id: task for task in tasks},
                "agent_uuids": [task.agent_uuid for task in tasks if task.agent_uuid],
            }

        try:
            # Execute batch using Enhanced Orchestrator
            results = await self.orchestrator.execute_batch(tasks)

            # Update team status
            async with self.team_lock:
                self.active_teams[team_id]["status"] = "completed"
                self.active_teams[team_id]["end_time"] = datetime.now().isoformat()
                self.active_teams[team_id]["results"] = {
                    r["task_id"]: r for r in results
                }

            logger.info(f"Team {team_id} completed successfully")

        except Exception as e:
            # Update team status on failure
            async with self.team_lock:
                self.active_teams[team_id]["status"] = "failed"
                self.active_teams[team_id]["end_time"] = datetime.now().isoformat()
                self.active_teams[team_id]["error"] = str(e)

            logger.error(f"Team {team_id} failed: {e}")

    async def get_team_status(self, team_id: str) -> TeamStatus:
        """
        Get current status of a team

        Args:
            team_id: Team identifier

        Returns:
            TeamStatus object with current team state
        """
        async with self.team_lock:
            team_info = self.active_teams.get(team_id)

        if not team_info:
            # Return empty status for unknown team
            return TeamStatus(team_id=team_id, status="unknown", agent_count=0)

        # Get individual agent statuses if monitoring enabled
        agent_statuses = {}
        agents_running = 0
        agents_completed = 0
        agents_failed = 0
        agents_stuck = 0
        agents_blocked = 0

        if self.monitor and team_info.get("agent_uuids"):
            for agent_uuid in team_info["agent_uuids"]:
                try:
                    agent_status = await self.monitor.get_agent_status(agent_uuid)
                    agent_statuses[agent_uuid] = {
                        "status": agent_status.status,
                        "progress": agent_status.progress.progress_percentage,
                        "errors": agent_status.error_count,
                        "last_activity": agent_status.last_activity_timestamp,
                        "current_task": agent_status.progress.current_task,
                    }

                    # Count status types
                    if agent_status.status == "running":
                        agents_running += 1
                    elif agent_status.status == "completed":
                        agents_completed += 1
                    elif agent_status.status == "failed":
                        agents_failed += 1
                    elif agent_status.status == "stuck":
                        agents_stuck += 1
                    else:
                        agents_blocked += 1

                except Exception as e:
                    agent_statuses[agent_uuid] = {"error": str(e)}
                    agents_blocked += 1

        # Get quality gate status
        quality_gates_status = {}
        blocked_by_gates = []

        if self.quality_gate_manager:
            try:
                status_report = await self.quality_gate_manager.get_status_report()
                quality_gates_status = {
                    gate_id: gate_info["status"]
                    for gate_id, gate_info in status_report.get("gates", {}).items()
                }

                # Find blocking gates
                for gate_id, status in quality_gates_status.items():
                    if status in ["failed", "blocked"]:
                        blocked_by_gates.append(gate_id)

            except Exception as e:
                logger.warning(f"Error getting quality gate status: {e}")

        # Get escalation information
        escalation_count = 0
        active_escalations = []
        resolved_escalations = 0

        if self.enable_escalation and isinstance(
            self.orchestrator, EscalationAwareOrchestrator
        ):
            try:
                escalation_dashboard = (
                    await self.orchestrator.get_escalation_dashboard()
                )
                escalation_count = escalation_dashboard.get(
                    "escalation_metrics", {}
                ).get("total_escalations", 0)
                resolved_escalations = escalation_dashboard.get(
                    "escalation_metrics", {}
                ).get("successful_resolutions", 0)

                # Get active escalations for this team
                pending_escalations = escalation_dashboard.get(
                    "pending_escalations", []
                )
                for escalation in pending_escalations:
                    if escalation.get("agent", "").startswith(team_id):
                        active_escalations.append(escalation["id"])

            except Exception as e:
                logger.warning(f"Error getting escalation status: {e}")

        # Calculate overall progress
        total_agents = len(team_info.get("agent_uuids", []))
        if total_agents > 0:
            overall_progress = (agents_completed * 100) / total_agents
        else:
            overall_progress = 0.0

        # Determine overall team status
        overall_status = team_info.get("status", "unknown")
        if overall_status == "running":
            if agents_failed > 0:
                overall_status = "failed"
            elif agents_stuck > 0:
                overall_status = "stuck"
            elif blocked_by_gates:
                overall_status = "blocked"
            elif active_escalations:
                overall_status = "escalating"
            elif agents_completed == total_agents:
                overall_status = "completed"

        return TeamStatus(
            team_id=team_id,
            status=overall_status,
            agent_count=total_agents,
            agents_running=agents_running,
            agents_completed=agents_completed,
            agents_failed=agents_failed,
            agents_stuck=agents_stuck,
            agents_blocked=agents_blocked,
            overall_progress_percentage=overall_progress,
            agent_statuses=agent_statuses,
            quality_gates_status=quality_gates_status,
            blocked_by_gates=blocked_by_gates,
            escalation_count=escalation_count,
            active_escalations=active_escalations,
            resolved_escalations=resolved_escalations,
            start_time=team_info.get("start_time"),
        )

    async def monitor_continuously(
        self, team_id: str, interval: int = 15
    ) -> AsyncGenerator[TeamStatus, None]:
        """
        Monitor team continuously with regular status updates

        Args:
            team_id: Team identifier
            interval: Update interval in seconds

        Yields:
            TeamStatus objects as team state changes
        """
        logger.info(
            f"Starting continuous monitoring for team {team_id} (interval: {interval}s)"
        )

        last_status = None

        while True:
            try:
                current_status = await self.get_team_status(team_id)

                # Yield status if it's the first check or if status changed
                if (
                    last_status is None
                    or current_status.status != last_status.status
                    or current_status.agents_completed != last_status.agents_completed
                    or current_status.agents_failed != last_status.agents_failed
                ):
                    yield current_status
                    last_status = current_status

                # Stop monitoring if team is done
                if current_status.status in ["completed", "failed"]:
                    logger.info(
                        f"Team {team_id} monitoring complete (status: {current_status.status})"
                    )
                    break

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error monitoring team {team_id}: {e}")
                await asyncio.sleep(interval * 2)  # Wait longer on error

    def monitor_continuously_sync(
        self, team_id: str, interval: int = 15
    ) -> Iterator[TeamStatus]:
        """
        Synchronous version of continuous monitoring for compatibility

        Args:
            team_id: Team identifier
            interval: Update interval in seconds

        Yields:
            TeamStatus objects as team state changes
        """

        async def _async_generator():
            async for status in self.monitor_continuously(team_id, interval):
                yield status

        # Run async generator in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            async_gen = _async_generator()
            while True:
                try:
                    status = loop.run_until_complete(async_gen.__anext__())
                    yield status
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    async def get_final_results(self, team_id: str) -> TeamResults:
        """
        Get final results after team execution completes

        Args:
            team_id: Team identifier

        Returns:
            TeamResults object with execution summary
        """
        async with self.team_lock:
            team_info = self.active_teams.get(team_id)

        if not team_info:
            return TeamResults(
                team_id=team_id,
                status="unknown",
                execution_time=0.0,
                execution_summary="Team not found",
            )

        # Calculate execution time
        start_time = datetime.fromisoformat(team_info["start_time"])
        end_time_str = team_info.get("end_time")
        if end_time_str:
            end_time = datetime.fromisoformat(end_time_str)
            execution_time = (end_time - start_time).total_seconds()
        else:
            execution_time = (datetime.now() - start_time).total_seconds()

        # Collect agent results
        agent_results = team_info.get("results", {})

        # Calculate success metrics
        total_agents = len(team_info.get("agent_uuids", []))
        successful_agents = sum(
            1
            for result in agent_results.values()
            if result.get("status") == "completed"
        )
        success_rate = (
            (successful_agents / total_agents * 100) if total_agents > 0 else 0
        )

        # Count errors
        total_errors = sum(
            1 for result in agent_results.values() if result.get("error") is not None
        )

        # Collect deliverables
        deliverables = []
        for result in agent_results.values():
            if result.get("result") and isinstance(result["result"], dict):
                # Extract file paths or deliverables from result
                if "files_created" in result["result"]:
                    deliverables.extend(result["result"]["files_created"])

        # Get quality gate metrics
        quality_gates_passed = 0
        quality_gates_failed = 0
        validation_errors = []

        if self.quality_gate_manager:
            try:
                status_report = await self.quality_gate_manager.get_status_report()
                for gate_info in status_report.get("gates", {}).values():
                    if gate_info["status"] == "passed":
                        quality_gates_passed += 1
                    elif gate_info["status"] == "failed":
                        quality_gates_failed += 1
                        if gate_info.get("last_validation") and gate_info[
                            "last_validation"
                        ].get("message"):
                            validation_errors.append(
                                gate_info["last_validation"]["message"]
                            )
            except Exception as e:
                validation_errors.append(f"Error retrieving quality gate status: {e}")

        # Generate execution summary
        execution_summary = f"""Team {team_id} Execution Summary:
- Status: {team_info.get('status', 'unknown')}
- Execution Time: {execution_time:.2f} seconds
- Agents: {total_agents} total, {successful_agents} successful
- Success Rate: {success_rate:.1f}%
- Total Errors: {total_errors}
- Deliverables Created: {len(deliverables)}
- Quality Gates: {quality_gates_passed} passed, {quality_gates_failed} failed
"""

        return TeamResults(
            team_id=team_id,
            status=team_info.get("status", "unknown"),
            execution_time=execution_time,
            agent_results=agent_results,
            success_rate=success_rate,
            total_errors=total_errors,
            deliverables_created=deliverables,
            quality_gates_passed=quality_gates_passed,
            quality_gates_failed=quality_gates_failed,
            validation_errors=validation_errors,
            execution_summary=execution_summary,
        )

    async def setup_quality_gates(self, gates_config: List[Dict[str, Any]]) -> None:
        """
        Setup quality gates for team execution

        Args:
            gates_config: List of gate configurations, each containing:
                - gate_id: Unique gate identifier
                - name: Human-readable name
                - description: Gate description
                - validator_type: Type of validator (database, file, http, etc.)
                - config: Validator-specific configuration
                - dependencies: List of gate IDs this depends on (optional)
        """
        if not self.quality_gate_manager:
            logger.warning("Quality gates not enabled, skipping setup")
            return

        for gate_config in gates_config:
            await self.quality_gate_manager.define_gate(
                gate_id=gate_config["gate_id"],
                name=gate_config["name"],
                description=gate_config["description"],
                validator_type=gate_config["validator_type"],
                config=gate_config["config"],
                dependencies=gate_config.get("dependencies", []),
                timeout_seconds=gate_config.get("timeout_seconds", 300),
                retry_interval=gate_config.get("retry_interval", 30),
                max_retries=gate_config.get("max_retries", 10),
            )

        # Start validation loop if not already running
        await self.quality_gate_manager.start_validation_loop()

        logger.info(f"Setup {len(gates_config)} quality gates")

    async def cleanup_team(self, team_id: str) -> None:
        """
        Clean up team resources after completion

        Args:
            team_id: Team identifier
        """
        async with self.team_lock:
            if team_id in self.active_teams:
                del self.active_teams[team_id]

        logger.info(f"Cleaned up team {team_id}")

    def get_active_teams(self) -> List[str]:
        """Get list of active team IDs"""
        return list(self.active_teams.keys())

    # Escalation management methods

    async def get_escalation_dashboard(self) -> Dict[str, Any]:
        """Get escalation dashboard for all teams"""

        if not self.enable_escalation or not isinstance(
            self.orchestrator, EscalationAwareOrchestrator
        ):
            return {
                "escalation_enabled": False,
                "message": "Escalation system not enabled",
            }

        return await self.orchestrator.get_escalation_dashboard()

    async def handle_team_escalation(
        self,
        team_id: str,
        escalation_type: str,
        reason: str,
        description: str,
        **kwargs,
    ) -> Optional[str]:
        """Handle manual escalation for a team"""

        if not self.enable_escalation or not isinstance(
            self.orchestrator, EscalationAwareOrchestrator
        ):
            logger.warning("Escalation system not enabled")
            return None

        try:
            return await self.orchestrator.handle_manual_escalation(
                task_id=f"team_{team_id}",
                escalation_type=escalation_type,
                reason=reason,
                description=description,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Failed to handle escalation for team {team_id}: {e}")
            return None

    async def resolve_team_escalation(
        self, escalation_id: str, resolution_type: str, **kwargs
    ) -> bool:
        """Resolve a team escalation"""

        if not self.enable_escalation or not isinstance(
            self.orchestrator, EscalationAwareOrchestrator
        ):
            return False

        try:
            return await self.orchestrator.resolve_escalation(
                escalation_id=escalation_id, resolution_type=resolution_type, **kwargs
            )
        except Exception as e:
            logger.error(f"Failed to resolve escalation {escalation_id}: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the team manager and cleanup resources"""
        logger.info("Shutting down AgentTeamManager")

        # Shutdown orchestrator (includes escalation system if enabled)
        if hasattr(self.orchestrator, "shutdown"):
            await self.orchestrator.shutdown()

        # Stop quality gate validation loop
        if self.quality_gate_manager:
            await self.quality_gate_manager.stop_validation_loop()

        # Clear active teams
        async with self.team_lock:
            self.active_teams.clear()


# Factory functions for common team configurations


def create_database_migration_team_manager(
    output_dir: Path,
    database_url: str,
    tokens: List[str] = None,
    enable_escalation: bool = True,
) -> AgentTeamManager:
    """Create team manager pre-configured for database migration teams"""

    # Configure escalation for database operations
    escalation_config = None
    if enable_escalation:
        escalation_config = EscalationConfig(
            enable_escalation=True,
            failure_threshold=2,  # Lower threshold for database ops
            enable_auto_replacement=True,
            enable_sub_swarm_delegation=True,
            auto_enhance_on_failure=True,
        )

    manager = AgentTeamManager(
        output_dir=output_dir,
        max_parallel=3,  # Conservative for database operations
        tokens=tokens,
        enable_quality_gates=True,
        enable_monitoring=True,
        enable_escalation=enable_escalation,
        escalation_config=escalation_config,
    )

    # Setup common database migration quality gates
    asyncio.create_task(
        manager.setup_quality_gates(
            [
                {
                    "gate_id": "database_ready",
                    "name": "Database Ready",
                    "description": "Database is accessible and has required extensions",
                    "validator_type": "database",
                    "config": {
                        "connection_string": database_url,
                        "query": "SELECT * FROM pg_extension WHERE extname = 'vector'",
                    },
                },
                {
                    "gate_id": "migration_ready",
                    "name": "Migration Ready",
                    "description": "Database schema is ready for migration",
                    "validator_type": "database",
                    "config": {
                        "connection_string": database_url,
                        "query": "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'",
                    },
                    "dependencies": ["database_ready"],
                },
            ]
        )
    )

    return manager


def create_web_service_team_manager(
    output_dir: Path,
    api_endpoints: List[str],
    tokens: List[str] = None,
    enable_escalation: bool = True,
) -> AgentTeamManager:
    """Create team manager pre-configured for web service teams"""

    # Configure escalation for web service operations
    escalation_config = None
    if enable_escalation:
        escalation_config = EscalationConfig(
            enable_escalation=True,
            failure_threshold=3,  # Standard threshold for web services
            enable_auto_replacement=True,
            enable_sub_swarm_delegation=True,
            auto_enhance_on_failure=True,
        )

    manager = AgentTeamManager(
        output_dir=output_dir,
        max_parallel=5,
        tokens=tokens,
        enable_quality_gates=True,
        enable_monitoring=True,
        enable_escalation=enable_escalation,
        escalation_config=escalation_config,
    )

    # Setup API readiness gates
    gates_config = []
    for i, endpoint in enumerate(api_endpoints):
        gates_config.append(
            {
                "gate_id": f"api_ready_{i}",
                "name": f"API Ready {endpoint}",
                "description": f"API endpoint {endpoint} is responding",
                "validator_type": "http",
                "config": {
                    "url": endpoint,
                    "method": "GET",
                    "expected_status": [200, 404],
                },
            }
        )

    asyncio.create_task(manager.setup_quality_gates(gates_config))

    return manager
