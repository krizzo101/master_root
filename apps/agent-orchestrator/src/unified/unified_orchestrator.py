#!/usr/bin/env python3
"""
Unified Agent Orchestrator
Consolidates all working features from various orchestrator implementations
with modular, configurable feature loading and graceful degradation.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.generic_orchestrator import (
        AgentTask,
        DependencyManager,
        GenericOrchestrator,
        MessageBus,
        TokenPool,
    )
except ImportError:
    from generic_orchestrator import (
        AgentTask,
        DependencyManager,
        GenericOrchestrator,
        MessageBus,
        TokenPool,
    )

# CRITICAL SAFETY WARNING:
# TokenPool in this system MUST fail catastrophically if token distribution fails.
# NO FALLBACK to single tokens from environment variables is allowed.
# Agents are FORBIDDEN from adding fallback mechanisms to TokenPool usage.

from .orchestrator_module import ModuleConfig, ModuleRegistry, OrchestratorModule

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    """Feature flags for enabling/disabling capabilities"""

    QUALITY_GATES = "quality_gates"
    AGENT_MONITORING = "agent_monitoring"
    EXECUTION_PLAN = "execution_plan"
    COLLABORATION = "collaboration"
    ENHANCED_METRICS = "enhanced_metrics"
    BACKGROUND_EXECUTION = "background_execution"
    AUTO_RECOVERY = "auto_recovery"
    STATE_PERSISTENCE = "state_persistence"


@dataclass
class UnifiedConfig:
    """Configuration for unified orchestrator"""

    # Base configuration
    output_dir: Path
    max_parallel: int = 10
    tokens: List[str] = None
    use_optimizations: bool = True

    # Feature flags
    enabled_features: Set[FeatureFlag] = field(
        default_factory=lambda: {
            FeatureFlag.ENHANCED_METRICS,
            FeatureFlag.BACKGROUND_EXECUTION,
        }
    )

    # Module configurations
    module_configs: Dict[str, ModuleConfig] = field(default_factory=dict)

    # New dynamic architecture fields
    master_mcp_registry_path: Optional[Path] = None
    agent_execution_profile: str = "standard"
    agent_debug_mode: bool = False
    agent_base_work_dir: Optional[Path] = None
    enable_dynamic_configs: bool = False
    log_to_work_dir: bool = False

    # Collaboration settings (if enabled)
    enable_collaboration: bool = False
    max_team_size: int = 5
    workspace_sync_interval: float = 60.0

    # Quality gate settings (if enabled)
    enable_quality_gates: bool = False
    gate_timeout: float = 300.0
    require_all_gates: bool = False

    # Monitoring settings (if enabled)
    enable_monitoring: bool = False
    status_check_interval: float = 30.0

    # Recovery settings
    enable_auto_recovery: bool = False
    max_retries: int = 3
    retry_delay: float = 5.0

    # State persistence
    enable_state_persistence: bool = False
    checkpoint_interval: float = 60.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        config_dict = asdict(self)
        config_dict["enabled_features"] = [f.value for f in self.enabled_features]
        config_dict["output_dir"] = str(self.output_dir)
        return config_dict


@dataclass
class EnhancedAgentTask(AgentTask):
    """Enhanced task with additional metadata"""

    # Team collaboration fields
    team_id: Optional[str] = None
    assigned_agents: List[str] = field(default_factory=list)
    collaboration_mode: Optional[str] = None  # shared, handoff, review

    # Quality gate fields
    quality_gates: Dict[str, bool] = field(default_factory=dict)
    validation_required: bool = False
    gate_results: Dict[str, Any] = field(default_factory=dict)

    # Monitoring fields
    retries: int = 0
    last_error: Optional[str] = None
    health_status: str = "healthy"

    # Execution plan fields
    phase: Optional[str] = None
    execution_mode: str = "parallel"  # parallel, sequential, mixed
    priority: int = 0

    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)

    # Dynamic architecture support
    mcp_needs: List[str] = field(
        default_factory=list
    )  # Required MCP servers for this task
    work_dir_name: Optional[str] = None  # Custom working directory name
    debug_mode: bool = False  # Enable debug mode for this specific task

    @classmethod
    def from_agent_task(cls, task: AgentTask) -> "EnhancedAgentTask":
        """Convert regular AgentTask to EnhancedAgentTask"""
        return cls(
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
        )


class UnifiedOrchestrator(GenericOrchestrator):
    """
    Unified orchestrator with modular feature loading.
    Consolidates all working features from various implementations.
    """

    def __init__(self, config: UnifiedConfig):
        """Initialize unified orchestrator with configuration"""

        # Store config
        self.config = config

        # Initialize base orchestrator with all parameters including new ones
        super().__init__(
            output_dir=config.output_dir,
            max_parallel=config.max_parallel,
            tokens=config.tokens,
            use_optimizations=config.use_optimizations,
            master_mcp_registry_path=config.master_mcp_registry_path,
            agent_execution_profile=config.agent_execution_profile,
            agent_debug_mode=config.agent_debug_mode,
            agent_base_work_dir=config.agent_base_work_dir,
            enable_dynamic_configs=config.enable_dynamic_configs,
            log_to_work_dir=config.log_to_work_dir,
        )

        # Initialize module registry
        self.module_registry = ModuleRegistry()

        # Additional components based on features
        self.teams: Dict[str, List[str]] = {}
        self.agent_registry: Dict[str, Dict] = {}
        self.background_jobs: Dict[str, asyncio.Task] = {}
        self.quality_gates: Dict[str, Callable] = {}
        self.execution_plan = None
        self.state_checkpoint = None

        # Enhanced metrics
        self.enhanced_metrics = {
            "tasks_by_type": {},
            "tasks_by_status": {},
            "average_duration_by_type": {},
            "team_performance": {},
            "quality_gate_results": {},
            "recovery_attempts": 0,
            "checkpoint_saves": 0,
        }

        # Setup directories
        self._setup_directories()

        # Load enabled modules
        asyncio.create_task(self._load_modules())

        logger.info(
            f"Unified Orchestrator initialized with features: {[f.value for f in config.enabled_features]}"
        )

    def _setup_directories(self):
        """Setup required directories"""
        dirs = [
            self.output_dir / "tasks",
            self.output_dir / "logs",
            self.output_dir / "teams",
            self.output_dir / "checkpoints",
            self.output_dir / "quality_reports",
            self.output_dir / "metrics",
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    async def _load_modules(self):
        """Load and initialize enabled feature modules"""

        # Load quality gates module if enabled
        if FeatureFlag.QUALITY_GATES in self.config.enabled_features:
            await self._load_quality_gates_module()

        # Load monitoring module if enabled
        if FeatureFlag.AGENT_MONITORING in self.config.enabled_features:
            await self._load_monitoring_module()

        # Load collaboration module if enabled
        if FeatureFlag.COLLABORATION in self.config.enabled_features:
            await self._load_collaboration_module()

        # Load execution plan module if enabled
        if FeatureFlag.EXECUTION_PLAN in self.config.enabled_features:
            await self._load_execution_plan_module()

        # Initialize all loaded modules
        init_results = await self.module_registry.initialize_all()
        logger.info(f"Module initialization results: {init_results}")

    async def _load_quality_gates_module(self):
        """Load quality gates functionality"""
        try:
            # Try to import quality gate components
            from src.modules.quality_gates_module import QualityGatesModule

            config = self.config.module_configs.get(
                "quality_gates",
                ModuleConfig(
                    enabled=True,
                    priority=1,
                    config={
                        "timeout": self.config.gate_timeout,
                        "require_all": self.config.require_all_gates,
                    },
                ),
            )

            module = QualityGatesModule(self, config)
            self.module_registry.register(module)
            logger.info("Quality gates module loaded")

        except ImportError as e:
            logger.warning(f"Quality gates module not available: {e}")
            # Graceful degradation - continue without quality gates

    async def _load_monitoring_module(self):
        """Load agent monitoring functionality"""
        try:
            from src.modules.monitoring_module import MonitoringModule

            config = self.config.module_configs.get(
                "monitoring",
                ModuleConfig(
                    enabled=True,
                    priority=2,
                    config={"check_interval": self.config.status_check_interval},
                ),
            )

            module = MonitoringModule(self, config)
            self.module_registry.register(module)
            logger.info("Monitoring module loaded")

        except ImportError as e:
            logger.warning(f"Monitoring module not available: {e}")

    async def _load_collaboration_module(self):
        """Load collaboration functionality"""
        try:
            from src.modules.collaboration_module import CollaborationModule

            config = self.config.module_configs.get(
                "collaboration",
                ModuleConfig(
                    enabled=True,
                    priority=3,
                    config={
                        "max_team_size": self.config.max_team_size,
                        "sync_interval": self.config.workspace_sync_interval,
                    },
                ),
            )

            module = CollaborationModule(self, config)
            self.module_registry.register(module)
            logger.info("Collaboration module loaded")

        except ImportError as e:
            logger.warning(f"Collaboration module not available: {e}")

    async def _load_execution_plan_module(self):
        """Load execution plan functionality"""
        try:
            from src.modules.execution_plan_module import ExecutionPlanModule

            config = self.config.module_configs.get(
                "execution_plan",
                ModuleConfig(
                    enabled=True, priority=0, config={}  # Highest priority - runs first
                ),
            )

            module = ExecutionPlanModule(self, config)
            self.module_registry.register(module)
            logger.info("Execution plan module loaded")

        except ImportError as e:
            logger.warning(f"Execution plan module not available: {e}")

    async def execute_agent(self, task: AgentTask) -> Dict:
        """
        Execute agent task with enhanced features.
        """

        # Convert to enhanced task if needed
        if not isinstance(task, EnhancedAgentTask):
            task = EnhancedAgentTask.from_agent_task(task)

        # Pre-execution hooks from modules
        for module in self.module_registry.get_enabled_modules():
            await module.pre_task_execution(task)

        # Validate task with modules
        for module in self.module_registry.get_enabled_modules():
            error = module.validate_task(task)
            if error:
                task.status = "failed"
                task.error = f"Validation failed ({module.name}): {error}"
                logger.error(task.error)
                return task.to_dict()

        # Auto-recovery handling
        if FeatureFlag.AUTO_RECOVERY in self.config.enabled_features:
            max_retries = self.config.max_retries
        else:
            max_retries = 1

        result = None
        for attempt in range(max_retries):
            try:
                # Execute base task
                result = await super().execute_agent(task)

                # If successful, break retry loop
                if task.status == "completed":
                    break

                # If failed and retries remaining
                if attempt < max_retries - 1:
                    task.retries += 1
                    self.enhanced_metrics["recovery_attempts"] += 1
                    logger.info(
                        f"Retrying task {task.task_id} (attempt {attempt + 2}/{max_retries})"
                    )
                    await asyncio.sleep(self.config.retry_delay)

            except Exception as e:
                task.last_error = str(e)
                if attempt == max_retries - 1:
                    raise

        # Post-execution hooks from modules
        for module in self.module_registry.get_enabled_modules():
            await module.post_task_execution(task)

            if task.status == "completed":
                await module.on_task_success(task)
            else:
                await module.on_task_failure(task)

        # Update enhanced metrics
        self._update_enhanced_metrics(task)

        # Save enhanced task state
        task_file = self.output_dir / "tasks" / f"{task.task_id}_enhanced.json"
        task_file.write_text(json.dumps(task.to_dict(), indent=2, default=str))

        return result or task.to_dict()

    def _update_enhanced_metrics(self, task: EnhancedAgentTask):
        """Update enhanced metrics"""

        # Task type metrics
        if task.task_type not in self.enhanced_metrics["tasks_by_type"]:
            self.enhanced_metrics["tasks_by_type"][task.task_type] = 0
        self.enhanced_metrics["tasks_by_type"][task.task_type] += 1

        # Status metrics
        if task.status not in self.enhanced_metrics["tasks_by_status"]:
            self.enhanced_metrics["tasks_by_status"][task.status] = 0
        self.enhanced_metrics["tasks_by_status"][task.status] += 1

        # Duration metrics
        if task.start_time and task.end_time:
            duration = task.end_time - task.start_time
            if task.task_type not in self.enhanced_metrics["average_duration_by_type"]:
                self.enhanced_metrics["average_duration_by_type"][task.task_type] = []
            self.enhanced_metrics["average_duration_by_type"][task.task_type].append(
                duration
            )

        # Team performance metrics
        if task.team_id:
            if task.team_id not in self.enhanced_metrics["team_performance"]:
                self.enhanced_metrics["team_performance"][task.team_id] = {
                    "completed": 0,
                    "failed": 0,
                    "total_duration": 0,
                }

            team_metrics = self.enhanced_metrics["team_performance"][task.team_id]
            if task.status == "completed":
                team_metrics["completed"] += 1
            elif task.status == "failed":
                team_metrics["failed"] += 1

            if task.start_time and task.end_time:
                team_metrics["total_duration"] += task.end_time - task.start_time

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """
        Execute batch with enhanced features.
        """

        # Convert all tasks to enhanced tasks
        enhanced_tasks = []
        for task in tasks:
            if isinstance(task, EnhancedAgentTask):
                enhanced_tasks.append(task)
            else:
                enhanced_tasks.append(EnhancedAgentTask.from_agent_task(task))

        # Pre-batch hooks from modules
        for module in self.module_registry.get_enabled_modules():
            await module.pre_batch_execution(enhanced_tasks)

        # State persistence checkpoint
        if FeatureFlag.STATE_PERSISTENCE in self.config.enabled_features:
            await self._save_checkpoint(enhanced_tasks)

        # Execute batch
        results = await super().execute_batch(enhanced_tasks)

        # Post-batch hooks from modules
        for module in self.module_registry.get_enabled_modules():
            await module.post_batch_execution(enhanced_tasks, results)

        return results

    async def _save_checkpoint(self, tasks: List[EnhancedAgentTask]):
        """Save execution state checkpoint"""

        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "tasks": [t.to_dict() for t in tasks],
            "metrics": self.metrics,
            "enhanced_metrics": self.enhanced_metrics,
            "teams": self.teams,
            "background_jobs": list(self.background_jobs.keys()),
        }

        checkpoint_file = (
            self.output_dir
            / "checkpoints"
            / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        checkpoint_file.write_text(json.dumps(checkpoint, indent=2, default=str))

        self.enhanced_metrics["checkpoint_saves"] += 1
        logger.info(f"Saved checkpoint: {checkpoint_file}")

    async def load_checkpoint(self, checkpoint_file: Path) -> bool:
        """Load execution state from checkpoint"""

        if not checkpoint_file.exists():
            logger.error(f"Checkpoint file not found: {checkpoint_file}")
            return False

        try:
            checkpoint = json.loads(checkpoint_file.read_text())

            # Restore metrics
            self.metrics = checkpoint.get("metrics", {})
            self.enhanced_metrics = checkpoint.get("enhanced_metrics", {})
            self.teams = checkpoint.get("teams", {})

            logger.info(f"Loaded checkpoint from {checkpoint_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return False

    async def launch_background_job(self, job_id: str, coroutine):
        """Launch a background job"""

        if job_id in self.background_jobs:
            logger.warning(f"Job {job_id} already running")
            return

        task = asyncio.create_task(coroutine)
        self.background_jobs[job_id] = task
        logger.info(f"Launched background job: {job_id}")

    async def get_background_job_status(self, job_id: str) -> str:
        """Get status of a background job"""

        if job_id not in self.background_jobs:
            return "not_found"

        task = self.background_jobs[job_id]
        if task.done():
            if task.exception():
                return "failed"
            return "completed"

        return "running"

    def get_metrics(self) -> Dict:
        """
        Get metrics from the orchestrator.
        Required method for orchestrator interface compliance.
        """
        return self.metrics

    async def cleanup(self):
        """Cleanup orchestrator resources"""

        # Cancel background jobs
        for job_id, task in self.background_jobs.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled background job: {job_id}")

        # Cleanup modules
        await self.module_registry.cleanup_all()

        # Save final metrics
        metrics_file = (
            self.output_dir
            / "metrics"
            / f"final_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        metrics_file.write_text(
            json.dumps(
                {
                    "basic_metrics": self.metrics,
                    "enhanced_metrics": self.enhanced_metrics,
                    "module_metrics": self.module_registry.get_metrics(),
                },
                indent=2,
                default=str,
            )
        )

        logger.info("Orchestrator cleanup complete")

    async def run(
        self,
        task_generator: Callable[[], List[AgentTask]],
        result_processor: Optional[Callable[[List[Dict]], None]] = None,
    ) -> Dict:
        """
        Run orchestration with unified features.
        """

        logger.info("=" * 60)
        logger.info("UNIFIED AGENT ORCHESTRATOR")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Features: {[f.value for f in self.config.enabled_features]}")
        logger.info(f"Modules: {self.module_registry.list_modules()}")
        logger.info("=" * 60)

        try:
            # Run base orchestration
            result = await super().run(task_generator, result_processor)

            # Add enhanced metrics to result
            result["enhanced_metrics"] = self.enhanced_metrics
            result["module_status"] = self.module_registry.get_status()

            # Save comprehensive report
            report_file = (
                self.output_dir
                / f"unified_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            report_file.write_text(json.dumps(result, indent=2, default=str))

            return result

        finally:
            await self.cleanup()


# Factory functions for common configurations


def create_minimal_orchestrator(output_dir: Path, **kwargs) -> UnifiedOrchestrator:
    """Create minimal orchestrator with basic features only"""

    config = UnifiedConfig(
        output_dir=output_dir, enabled_features=set(), **kwargs  # No extra features
    )

    return UnifiedOrchestrator(config)


def create_standard_orchestrator(output_dir: Path, **kwargs) -> UnifiedOrchestrator:
    """Create standard orchestrator with commonly used features"""

    config = UnifiedConfig(
        output_dir=output_dir,
        enabled_features={
            FeatureFlag.ENHANCED_METRICS,
            FeatureFlag.BACKGROUND_EXECUTION,
            FeatureFlag.AUTO_RECOVERY,
        },
        enable_auto_recovery=True,
        **kwargs,
    )

    return UnifiedOrchestrator(config)


def create_advanced_orchestrator(output_dir: Path, **kwargs) -> UnifiedOrchestrator:
    """Create advanced orchestrator with all features"""

    config = UnifiedConfig(
        output_dir=output_dir,
        enabled_features={
            FeatureFlag.QUALITY_GATES,
            FeatureFlag.AGENT_MONITORING,
            FeatureFlag.EXECUTION_PLAN,
            FeatureFlag.COLLABORATION,
            FeatureFlag.ENHANCED_METRICS,
            FeatureFlag.BACKGROUND_EXECUTION,
            FeatureFlag.AUTO_RECOVERY,
            FeatureFlag.STATE_PERSISTENCE,
        },
        enable_collaboration=True,
        enable_quality_gates=True,
        enable_monitoring=True,
        enable_auto_recovery=True,
        enable_state_persistence=True,
        **kwargs,
    )

    return UnifiedOrchestrator(config)


# Example usage
async def example_usage():
    """Example of using the unified orchestrator"""

    import tempfile

    def generate_test_tasks() -> List[EnhancedAgentTask]:
        """Generate test tasks"""
        tasks = []

        # Create enhanced tasks with various features
        for i in range(3):
            task = EnhancedAgentTask(
                task_id=f"task_{i}",
                task_type="analysis",
                prompt=f"Analyze topic {i}",
                dependencies=[f"task_{i-1}"] if i > 0 else [],
                priority=i,
                validation_required=True,
                team_id="team_alpha" if i % 2 == 0 else "team_beta",
            )
            tasks.append(task)

        return tasks

    # Create orchestrator with standard features
    orchestrator = create_standard_orchestrator(
        output_dir=Path(tempfile.mkdtemp(prefix="unified_test_")), max_parallel=3
    )

    # Run orchestration
    result = await orchestrator.run(task_generator=generate_test_tasks)

    print("\n=== EXECUTION SUMMARY ===")
    print(f"Total tasks: {result['metrics']['total']}")
    print(f"Completed: {result['metrics']['completed']}")
    print(f"Failed: {result['metrics']['failed']}")
    print(f"Enhanced metrics: {json.dumps(result['enhanced_metrics'], indent=2)}")


if __name__ == "__main__":
    asyncio.run(example_usage())
