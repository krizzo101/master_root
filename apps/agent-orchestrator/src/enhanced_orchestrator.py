#!/usr/bin/env python3
"""
Enhanced Agent Orchestrator with Quality Gate Support

Extends the GenericOrchestrator with quality gate validation and dependency management.
Provides non-breaking integration while enabling complex dependency chains.
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Import base orchestrator components
from generic_orchestrator import (
    AgentTask,
    DependencyManager,
    GenericOrchestrator,
    MessageBus,
    TokenPool,
)
from quality_gates import GateStatus, QualityGateManager, ValidationResult

from .agent_monitor import AgentStatus, AgentStatusMonitor

logger = logging.getLogger(__name__)


@dataclass
class EnhancedAgentTask(AgentTask):
    """Enhanced agent task with quality gate and monitoring support"""

    # Quality gate support
    quality_gates: List[str] = field(default_factory=list)  # Gates this task depends on
    validation_required: bool = True  # Whether to validate deliverable
    phase_id: Optional[str] = None  # Execution phase this task belongs to

    # Monitoring support
    agent_uuid: Optional[str] = None  # Predictable UUID for log file tracking
    team_id: Optional[str] = None  # Team identifier for coordinated execution
    monitoring_enabled: bool = True  # Enable real-time monitoring
    background_execution: bool = False  # Allow background execution

    def __post_init__(self):
        # Generate UUID if not provided
        if self.agent_uuid is None:
            self.agent_uuid = str(uuid.uuid4())

        # Extract team_id from agent_uuid if follows pattern
        if self.team_id is None and self.agent_uuid:
            parts = self.agent_uuid.split("-")
            if len(parts) >= 3 and parts[0] == "team":
                self.team_id = "-".join(parts[:3])  # team-phase1-001


@dataclass
class BackgroundJob:
    """Background execution job tracking"""

    job_id: str
    team_id: str
    agent_uuids: List[str]
    status: str = "running"  # running, completed, failed
    start_time: float = field(default_factory=lambda: datetime.now().timestamp())
    end_time: Optional[float] = None
    results: Dict[str, Any] = field(default_factory=dict)


class EnhancedDependencyManager(DependencyManager):
    """Enhanced dependency manager with quality gate integration"""

    def __init__(self, quality_gate_manager: QualityGateManager = None):
        super().__init__()
        self.quality_gate_manager = quality_gate_manager

    async def can_run(self, task: EnhancedAgentTask) -> bool:
        """Check if task dependencies and quality gates are satisfied"""
        # Check basic dependencies first
        if not await super().can_run(task):
            return False

        # Check quality gates if manager is available
        if self.quality_gate_manager and task.quality_gates:
            for gate_id in task.quality_gates:
                gate_status = await self.quality_gate_manager.check_quality_gates(
                    gate_id
                )
                if gate_status != GateStatus.PASSED:
                    logger.debug(
                        f"Task {task.task_id} blocked by gate {gate_id} (status: {gate_status})"
                    )
                    return False

        return True

    async def validate_task_deliverable(
        self, task: EnhancedAgentTask
    ) -> ValidationResult:
        """Validate task deliverable using quality gate manager"""
        if not task.validation_required or not self.quality_gate_manager:
            return ValidationResult(True, "Validation skipped or not configured")

        return await self.quality_gate_manager.validate_deliverable(
            task.task_id, task.result
        )


class EnhancedOrchestrator(GenericOrchestrator):
    """
    Enhanced orchestrator with monitoring and quality gate integration.

    Extends GenericOrchestrator to add:
    - Real-time agent monitoring via AgentStatusMonitor
    - Quality gate validation via QualityGateManager
    - UUID management for predictable log file tracking
    - Background execution with status tracking
    - Full backward compatibility with existing code
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        # Enhanced features
        enable_quality_gates: bool = True,
        enable_monitoring: bool = True,
        quality_gate_config: Dict[str, Any] = None,
        chat_logs_dir: Optional[str] = None,
        quality_gate_state_dir: Optional[Path] = None,
    ):
        # Initialize parent class
        super().__init__(output_dir, max_parallel, tokens, use_optimizations)

        # Enhanced features flags
        self.enable_quality_gates = enable_quality_gates
        self.enable_monitoring = enable_monitoring

        # Quality gate system
        self.quality_gate_manager: Optional[QualityGateManager] = None
        if enable_quality_gates:
            gate_state_dir = quality_gate_state_dir or (output_dir / "quality_gates")
            self.quality_gate_manager = QualityGateManager(gate_state_dir)

            # Replace dependency manager with enhanced version
            self.dep_manager = EnhancedDependencyManager(self.quality_gate_manager)

            # Initialize common quality gates if config provided
            if quality_gate_config:
                asyncio.create_task(self._initialize_quality_gates(quality_gate_config))

        # Monitoring system
        self.agent_monitor: Optional[AgentStatusMonitor] = None
        if enable_monitoring:
            self.agent_monitor = AgentStatusMonitor(chat_logs_dir)

        # Background execution tracking
        self.background_jobs: Dict[str, BackgroundJob] = {}
        self._background_task_lock = asyncio.Lock()

        # Enhanced metrics
        self.quality_metrics = {
            "gates_validated": 0,
            "gates_failed": 0,
            "deliverables_validated": 0,
            "deliverables_failed": 0,
            "quality_gate_wait_time": 0,
        }

        self.monitoring_metrics = {
            "agents_monitored": 0,
            "background_jobs": 0,
            "uuid_assignments": 0,
        }

        # Enhanced hooks
        self.monitoring_hook: Optional[Callable] = None

        logger.info(
            f"EnhancedOrchestrator initialized (quality_gates: {enable_quality_gates}, monitoring: {enable_monitoring})"
        )

    async def _initialize_quality_gates(self, config: Dict[str, Any]):
        """Initialize quality gates from configuration"""
        try:
            # Define gates from config
            gates_config = config.get("gates", [])
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

            # Define phases from config
            phases_config = config.get("phases", [])
            for phase_config in phases_config:
                await self.quality_gate_manager.define_phase(
                    phase_id=phase_config["phase_id"],
                    name=phase_config["name"],
                    description=phase_config["description"],
                    gates=phase_config["gates"],
                )

            # Start validation loop
            await self.quality_gate_manager.start_validation_loop()

            logger.info(
                f"Initialized {len(gates_config)} quality gates and {len(phases_config)} phases"
            )

        except Exception as e:
            logger.error(f"Failed to initialize quality gates: {e}")
            raise

    async def define_quality_gate(
        self,
        gate_id: str,
        name: str,
        description: str,
        validator_type: str,
        config: Dict[str, Any],
        dependencies: List[str] = None,
    ):
        """Define a quality gate (convenience method)"""
        if not self.quality_gate_manager:
            raise RuntimeError("Quality gates not enabled")

        return await self.quality_gate_manager.define_gate(
            gate_id, name, description, validator_type, config, dependencies
        )

    async def define_phase(
        self, phase_id: str, name: str, description: str, gates: List[str]
    ):
        """Define an execution phase (convenience method)"""
        if not self.quality_gate_manager:
            raise RuntimeError("Quality gates not enabled")

        return await self.quality_gate_manager.define_phase(
            phase_id, name, description, gates
        )

    async def wait_for_quality_gates(self, task: EnhancedAgentTask) -> bool:
        """Wait for all quality gates required by a task"""
        if not self.quality_gate_manager or not task.quality_gates:
            return True

        wait_start = datetime.now().timestamp()

        try:
            await self.quality_gate_manager.block_until_dependencies_ready(
                task.task_id, task.quality_gates
            )

            wait_time = datetime.now().timestamp() - wait_start
            self.quality_metrics["quality_gate_wait_time"] += wait_time

            logger.info(
                f"Task {task.task_id} quality gates satisfied after {wait_time:.2f}s"
            )
            return True

        except Exception as e:
            logger.error(f"Task {task.task_id} quality gate validation failed: {e}")
            task.error = f"Quality gate validation failed: {str(e)}"
            task.status = "failed"
            return False

    async def execute_agent(self, task: AgentTask) -> Dict:
        """
        Execute agent with enhanced features.
        Maintains backward compatibility by handling both regular and enhanced tasks.
        """

        # Convert regular tasks to enhanced for internal processing
        if not isinstance(task, EnhancedAgentTask):
            enhanced_task = EnhancedAgentTask(
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
                # Disable enhanced features for backward compatibility
                monitoring_enabled=False,
                quality_gates=[],
            )
            # Use parent implementation for backward compatibility
            return await super().execute_agent(enhanced_task)

        # Handle enhanced tasks
        return await self.execute_agent_enhanced(task)

    async def execute_agent_enhanced(self, task: EnhancedAgentTask) -> Dict:
        """Execute enhanced agent task with full monitoring and quality gate support"""

        # Wait for quality gates before execution
        if not await self.wait_for_quality_gates(task):
            # Task failed quality gate validation
            return task.to_dict()

        # Pre-execution monitoring hook
        if self.monitoring_hook:
            await self.monitoring_hook(task, "pre_execute")

        # Store original task details for monitoring
        if task.monitoring_enabled and task.agent_uuid:
            self.monitoring_metrics["agents_monitored"] += 1
            self.monitoring_metrics["uuid_assignments"] += 1

        # Build enhanced command with UUID as session ID for predictable log files
        session_id = task.agent_uuid if task.monitoring_enabled else str(uuid.uuid4())

        # Build enhanced prompt with metadata
        prompt = await self._build_enhanced_prompt(task)

        # Prepare command
        cmd = self.claude_cmd + [
            "--session-id",
            session_id,
            "--add-dir",
            str(self.output_dir),
            "--",  # Important: separator before prompt
            prompt,
        ]

        # Get token
        token, token_idx = await self.token_pool.acquire()
        env = os.environ.copy()
        env["CLAUDE_CODE_TOKEN"] = token

        # Add enhanced metadata to environment
        if task.team_id:
            env["AGENT_TEAM_ID"] = task.team_id
        env["AGENT_UUID"] = task.agent_uuid or ""

        # Execute
        task.start_time = datetime.now().timestamp()
        task.status = "running"
        await self.dep_manager.mark_running(task.task_id)

        try:
            logger.info(
                f"Executing {task.task_id} (UUID: {task.agent_uuid}) ({task.task_type})"
            )

            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            task.end_time = datetime.now().timestamp()
            duration = task.end_time - task.start_time

            if process.returncode == 0:
                task.status = "completed"
                task.result = json.loads(stdout.decode())
                await self.dep_manager.mark_completed(task.task_id)
                self.metrics["completed"] += 1

                logger.info(f"✓ {task.task_id} completed in {duration:.2f}s")
            else:
                task.status = "failed"
                task.error = stderr.decode()
                await self.dep_manager.mark_failed(task.task_id)
                self.metrics["failed"] += 1

                logger.error(f"✗ {task.task_id} failed: {task.error}")

            self.metrics["total_duration"] += duration

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            await self.dep_manager.mark_failed(task.task_id)
            self.metrics["failed"] += 1

            logger.error(f"✗ {task.task_id} exception: {e}")

        # Validate deliverable if enabled
        if (
            task.validation_required
            and self.quality_gate_manager
            and task.status == "completed"
        ):
            validation = await self.dep_manager.validate_task_deliverable(task)

            if validation.success:
                self.quality_metrics["deliverables_validated"] += 1
                logger.info(
                    f"Task {task.task_id} deliverable validated: {validation.message}"
                )
            else:
                self.quality_metrics["deliverables_failed"] += 1
                logger.warning(
                    f"Task {task.task_id} deliverable validation failed: {validation.message}"
                )

                # Mark task as failed if deliverable validation fails
                task.status = "failed"
                task.error = f"Deliverable validation failed: {validation.message}"
                await self.dep_manager.mark_failed(task.task_id)

        # Post-execution monitoring hook
        if self.monitoring_hook:
            await self.monitoring_hook(task, "post_execute")

        # Save enhanced task state
        task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text(json.dumps(task.to_dict(), indent=2))

        return task.to_dict()

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute batch with enhanced dependency and quality gate management"""

        if self.quality_gate_manager:
            logger.info("Starting quality gate validation background process")

        # Execute using parent implementation
        results = await super().execute_batch(tasks)

        # Generate quality report
        if self.quality_gate_manager:
            quality_report = await self.quality_gate_manager.get_status_report()

            # Save quality report
            report_file = self.output_dir / "quality_gate_report.json"
            report_file.write_text(json.dumps(quality_report, indent=2))

            logger.info(f"Quality gate report saved to {report_file}")

        return results

    async def run(
        self,
        task_generator: Callable[[], List[AgentTask]],
        result_processor: Optional[Callable[[List[Dict]], None]] = None,
    ) -> Dict:
        """Run orchestration with quality gate support"""

        try:
            # Run the orchestration
            result = await super().run(task_generator, result_processor)

            # Add quality metrics to result
            if self.enable_quality_gates:
                result["quality_metrics"] = self.quality_metrics

                if self.quality_gate_manager:
                    result[
                        "quality_status"
                    ] = await self.quality_gate_manager.get_status_report()

            return result

        finally:
            # Cleanup quality gate manager
            if self.quality_gate_manager:
                await self.quality_gate_manager.stop_validation_loop()

    async def get_quality_status(self) -> Dict[str, Any]:
        """Get current quality gate status"""
        if not self.quality_gate_manager:
            return {"status": "quality_gates_disabled"}

        return await self.quality_gate_manager.get_status_report()

    async def trigger_gate_validation(self, gate_id: str) -> ValidationResult:
        """Manually trigger validation of a specific gate"""
        if not self.quality_gate_manager:
            raise RuntimeError("Quality gates not enabled")

        return await self.quality_gate_manager.validate_gate(gate_id)

    # Enhanced monitoring and background execution methods

    async def launch_background_team(
        self, tasks: List[EnhancedAgentTask], team_id: Optional[str] = None
    ) -> str:
        """
        Launch a team of agents in background execution.
        Returns job_id for monitoring and management.
        """

        job_id = team_id or f"bg-{str(uuid.uuid4())[:8]}"
        agent_uuids = [task.agent_uuid for task in tasks if task.agent_uuid]

        # Create background job
        job = BackgroundJob(
            job_id=job_id, team_id=team_id or job_id, agent_uuids=agent_uuids
        )

        async with self._background_task_lock:
            self.background_jobs[job_id] = job

        self.monitoring_metrics["background_jobs"] += 1

        # Launch background task
        asyncio.create_task(self._execute_background_team(job, tasks))

        logger.info(f"Launched background team {job_id} with {len(tasks)} agents")
        return job_id

    async def get_background_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of background job"""

        async with self._background_task_lock:
            job = self.background_jobs.get(job_id)
            if not job:
                return None

        # Get individual agent statuses if monitoring enabled
        agent_statuses = {}
        if self.enable_monitoring and self.agent_monitor:
            for agent_uuid in job.agent_uuids:
                try:
                    status = await self.agent_monitor.get_agent_status(agent_uuid)
                    agent_statuses[agent_uuid] = {
                        "status": status.status,
                        "progress": status.progress.progress_percentage,
                        "errors": status.error_count,
                        "last_activity": status.last_activity_timestamp,
                    }
                except Exception as e:
                    agent_statuses[agent_uuid] = {"error": str(e)}

        return {
            "job_id": job.job_id,
            "team_id": job.team_id,
            "status": job.status,
            "start_time": job.start_time,
            "end_time": job.end_time,
            "agent_count": len(job.agent_uuids),
            "agent_statuses": agent_statuses,
            "results": job.results,
        }

    async def get_agent_status(self, agent_uuid: str) -> Optional[AgentStatus]:
        """Get real-time status for specific agent"""

        if not self.enable_monitoring or not self.agent_monitor:
            logger.warning("Monitoring not enabled")
            return None

        try:
            return await self.agent_monitor.get_agent_status(agent_uuid)
        except Exception as e:
            logger.error(f"Error getting agent status for {agent_uuid}: {e}")
            return None

    async def get_team_status(self, team_id: str) -> Dict[str, AgentStatus]:
        """Get status for all agents in a team"""

        if not self.enable_monitoring or not self.agent_monitor:
            return {}

        try:
            return await self.agent_monitor.get_all_agent_statuses(team_id)
        except Exception as e:
            logger.error(f"Error getting team status for {team_id}: {e}")
            return {}

    async def _execute_background_team(
        self, job: BackgroundJob, tasks: List[EnhancedAgentTask]
    ):
        """Execute background team and update job status"""

        try:
            # Mark tasks for background execution
            for task in tasks:
                task.background_execution = True

            # Execute batch using base orchestrator
            results = await self.execute_batch(tasks)

            # Update job status
            async with self._background_task_lock:
                job.status = "completed"
                job.end_time = datetime.now().timestamp()
                job.results = {r["task_id"]: r for r in results}

            logger.info(f"Background team {job.job_id} completed")

        except Exception as e:
            async with self._background_task_lock:
                job.status = "failed"
                job.end_time = datetime.now().timestamp()
                job.results = {"error": str(e)}

            logger.error(f"Background team {job.job_id} failed: {e}")

    async def _build_enhanced_prompt(self, task: EnhancedAgentTask) -> str:
        """Build enhanced prompt with metadata"""

        if self.task_builder_hook:
            return await self.task_builder_hook(task)

        # Add metadata to prompt for agent awareness
        metadata_prefix = ""
        if task.agent_uuid:
            metadata_prefix += f"AGENT_UUID: {task.agent_uuid}\n"
        if task.team_id:
            metadata_prefix += f"TEAM_ID: {task.team_id}\n"
        if task.quality_gates:
            metadata_prefix += f"QUALITY_GATES: {', '.join(task.quality_gates)}\n"

        if metadata_prefix:
            metadata_prefix += "\n"

        return metadata_prefix + task.prompt

    def create_enhanced_task(
        self,
        task_id: str,
        task_type: str,
        prompt: str,
        dependencies: List[str] = None,
        quality_gates: List[str] = None,
        validation_required: bool = True,
        phase_id: str = None,
        context: Dict[str, Any] = None,
        # Enhanced parameters
        agent_uuid: Optional[str] = None,
        team_id: Optional[str] = None,
        monitoring_enabled: bool = True,
    ) -> EnhancedAgentTask:
        """Convenience method to create enhanced tasks"""

        return EnhancedAgentTask(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            dependencies=dependencies or [],
            quality_gates=quality_gates or [],
            validation_required=validation_required,
            phase_id=phase_id,
            context=context or {},
            # Enhanced parameters
            agent_uuid=agent_uuid,
            team_id=team_id,
            monitoring_enabled=monitoring_enabled,
        )


# Factory functions for common configurations


def create_database_orchestrator(
    output_dir: Path, database_url: str, max_parallel: int = 5, tokens: List[str] = None
) -> EnhancedOrchestrator:
    """Create orchestrator pre-configured for database operations"""

    quality_config = {
        "gates": [
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
        ],
        "phases": [
            {
                "phase_id": "database_setup",
                "name": "Database Setup",
                "description": "Initialize database and extensions",
                "gates": ["database_ready", "migration_ready"],
            }
        ],
    }

    return EnhancedOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,
        tokens=tokens,
        enable_quality_gates=True,
        quality_gate_config=quality_config,
    )


def create_web_service_orchestrator(
    output_dir: Path,
    api_endpoints: List[str],
    max_parallel: int = 3,
    tokens: List[str] = None,
) -> EnhancedOrchestrator:
    """Create orchestrator pre-configured for web service operations"""

    gates = []
    for i, endpoint in enumerate(api_endpoints):
        gates.append(
            {
                "gate_id": f"api_ready_{i}",
                "name": f"API Ready {endpoint}",
                "description": f"API endpoint {endpoint} is responding",
                "validator_type": "http",
                "config": {
                    "url": endpoint,
                    "method": "GET",
                    "expected_status": [
                        200,
                        404,
                    ],  # Either OK or Not Found is acceptable
                },
            }
        )

    quality_config = {
        "gates": gates,
        "phases": [
            {
                "phase_id": "api_validation",
                "name": "API Validation",
                "description": "Validate all API endpoints are accessible",
                "gates": [g["gate_id"] for g in gates],
            }
        ],
    }

    return EnhancedOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,
        tokens=tokens,
        enable_quality_gates=True,
        quality_gate_config=quality_config,
    )
