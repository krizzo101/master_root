#!/usr/bin/env python3
"""
Practical Agent Orchestrator - The Best of Both Worlds

Takes the reliable GenericOrchestrator and adds the actually useful features from Enhanced:
- Deterministic session IDs for easy monitoring
- Rich task result tracking
- Simple quality reporting (without gate complexity)
- Real-time progress monitoring
- Better debugging information

NO dependency hell, NO circular imports, NO half-implemented features.
"""

import asyncio
import hashlib
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Import reliable base orchestrator
from generic_orchestrator import (
    AgentTask,
    DependencyManager,
    GenericOrchestrator,
    TokenPool,
)

logger = logging.getLogger(__name__)


@dataclass
class PracticalAgentTask(AgentTask):
    """Enhanced agent task with monitoring and tracking support"""

    # Monitoring and tracking
    session_id: Optional[str] = None  # Deterministic session ID for log tracking
    phase_id: Optional[str] = None  # Execution phase (for organization)
    priority: str = "normal"  # high, normal, low
    tags: List[str] = field(default_factory=list)  # Organizational tags

    # Enhanced result tracking
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    commands_run: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Generate deterministic session ID if not provided
        if self.session_id is None:
            self.session_id = self.generate_deterministic_session_id()

    def generate_deterministic_session_id(self) -> str:
        """Generate deterministic UUID based on task_id for easy tracking"""
        seed_string = f"practical-{self.task_id}-{self.task_type}"
        hash_obj = hashlib.md5(seed_string.encode())
        hex_str = hash_obj.hexdigest()
        return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"

    def add_file_created(self, filepath: str):
        """Track file creation"""
        if filepath not in self.files_created:
            self.files_created.append(filepath)

    def add_file_modified(self, filepath: str):
        """Track file modification"""
        if filepath not in self.files_modified:
            self.files_modified.append(filepath)

    def add_metric(self, key: str, value: Any):
        """Add performance or quality metric"""
        self.metrics[key] = value

    def get_log_path(self) -> str:
        """Get the expected log file path for this task"""
        return f"~/.claude/projects/-home-opsvi-master-root-apps-project-context/{self.session_id}.jsonl"


@dataclass
class QualityReport:
    """Simple quality report without complex gate system"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_duration: float = 0.0

    # Task categorization
    tasks_by_type: Dict[str, int] = field(default_factory=dict)
    tasks_by_phase: Dict[str, int] = field(default_factory=dict)
    tasks_by_priority: Dict[str, int] = field(default_factory=dict)

    # Quality metrics
    files_created_total: int = 0
    files_modified_total: int = 0
    commands_run_total: int = 0

    # Performance metrics
    fastest_task: Optional[Dict] = None
    slowest_task: Optional[Dict] = None
    success_rate: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


class PracticalOrchestrator(GenericOrchestrator):
    """GenericOrchestrator + monitoring + quality reports - dependency hell"""

    def __init__(
        self,
        output_dir: Union[str, Path],  # Accept both string and Path!
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        enable_monitoring: bool = True,
        enable_quality_reports: bool = True,
        orchestrator_type: Optional[str] = None,
    ):
        # Set orchestrator type BEFORE calling parent init (for token loading)
        self._orchestrator_type = orchestrator_type

        # Fix the Path issue that breaks Enhanced
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        # Initialize base orchestrator
        super().__init__(output_dir, max_parallel, tokens, use_optimizations)

        # Practical enhancements
        self.enable_monitoring = enable_monitoring
        self.enable_quality_reports = enable_quality_reports

        # Monitoring data
        self.task_start_times: Dict[str, float] = {}
        self.task_durations: Dict[str, float] = {}
        self.session_id_map: Dict[str, str] = {}  # task_id -> session_id

        # Quality tracking
        self.quality_metrics = {
            "files_created_total": 0,
            "files_modified_total": 0,
            "commands_run_total": 0,
            "tasks_by_type": {},
            "tasks_by_phase": {},
            "tasks_by_priority": {},
        }

        # Progress tracking
        self.progress_callback: Optional[Callable] = None

        logger.info(
            f"PracticalOrchestrator initialized (monitoring: {enable_monitoring}, quality_reports: {enable_quality_reports})"
        )

    def set_progress_callback(self, callback: Callable[[str, Dict], None]):
        """Set callback for real-time progress updates"""
        self.progress_callback = callback

    def _notify_progress(self, event_type: str, data: Dict):
        """Send progress notification if callback is set"""
        if self.progress_callback:
            try:
                self.progress_callback(event_type, data)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    async def _execute_task_practical(
        self, task: PracticalAgentTask, token: str, token_idx: int
    ) -> Dict:
        """Execute task with enhanced monitoring and tracking"""

        # Pre-execution monitoring
        self.task_start_times[task.task_id] = datetime.now().timestamp()
        self.session_id_map[task.task_id] = task.session_id

        self._notify_progress(
            "task_started",
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "session_id": task.session_id,
                "phase_id": task.phase_id,
                "priority": task.priority,
            },
        )

        # Track quality metrics
        self.quality_metrics["tasks_by_type"][task.task_type] = (
            self.quality_metrics["tasks_by_type"].get(task.task_type, 0) + 1
        )
        if task.phase_id:
            self.quality_metrics["tasks_by_phase"][task.phase_id] = (
                self.quality_metrics["tasks_by_phase"].get(task.phase_id, 0) + 1
            )
        self.quality_metrics["tasks_by_priority"][task.priority] = (
            self.quality_metrics["tasks_by_priority"].get(task.priority, 0) + 1
        )

        # Execute using parent implementation (converted to AgentTask)
        base_task = AgentTask(
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

        result = await self._execute_task(base_task, token, token_idx)

        # Copy results back to practical task
        task.status = base_task.status
        task.result = base_task.result
        task.error = base_task.error
        task.start_time = base_task.start_time
        task.end_time = base_task.end_time

        # Post-execution tracking
        if task.end_time and task.start_time:
            duration = task.end_time - task.start_time
            self.task_durations[task.task_id] = duration

            # Update quality metrics from result
            if task.result and isinstance(task.result, dict):
                # Extract file information if present
                if "files_created" in task.result:
                    files = task.result["files_created"]
                    if isinstance(files, list):
                        task.files_created.extend(files)
                        self.quality_metrics["files_created_total"] += len(files)

                if "files_modified" in task.result:
                    files = task.result["files_modified"]
                    if isinstance(files, list):
                        task.files_modified.extend(files)
                        self.quality_metrics["files_modified_total"] += len(files)

                # Extract other metrics
                if "metrics" in task.result:
                    task.metrics.update(task.result["metrics"])

        self._notify_progress(
            "task_completed",
            {
                "task_id": task.task_id,
                "status": task.status,
                "duration": duration if task.end_time and task.start_time else 0,
                "files_created": len(task.files_created),
                "files_modified": len(task.files_modified),
                "session_id": task.session_id,
            },
        )

        # Save enhanced task result
        task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)

        # Convert to dict with all the enhanced fields
        enhanced_result = {
            **result,  # Base result
            "session_id": task.session_id,
            "phase_id": task.phase_id,
            "priority": task.priority,
            "tags": task.tags,
            "files_created": task.files_created,
            "files_modified": task.files_modified,
            "metrics": task.metrics,
            "log_path": task.get_log_path(),
        }

        task_file.write_text(json.dumps(enhanced_result, indent=2))

        return enhanced_result

    async def execute_batch(
        self, tasks: List[Union[AgentTask, PracticalAgentTask]]
    ) -> List[Dict]:
        """Execute batch with enhanced monitoring and quality reporting"""

        # Convert regular AgentTasks to PracticalAgentTasks
        practical_tasks = []
        for task in tasks:
            if isinstance(task, PracticalAgentTask):
                practical_tasks.append(task)
            else:
                # Convert AgentTask to PracticalAgentTask
                practical_task = PracticalAgentTask(
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
                practical_tasks.append(practical_task)

        # Notify start of batch
        self._notify_progress(
            "batch_started",
            {
                "total_tasks": len(practical_tasks),
                "task_types": [t.task_type for t in practical_tasks],
                "phases": list(
                    set([t.phase_id for t in practical_tasks if t.phase_id])
                ),
            },
        )

        # Execute tasks (override task execution method)
        results = []
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_semaphore(task):
            async with semaphore:
                # Wait for dependencies
                while not await self.dep_manager.can_run(task):
                    await asyncio.sleep(0.1)

                await self.dep_manager.mark_running(task.task_id)
                token, token_idx = await self.token_pool.acquire()

                return await self._execute_task_practical(task, token, token_idx)

        # Run all tasks
        tasks_coroutines = [execute_with_semaphore(task) for task in practical_tasks]
        results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)

        # Generate quality report
        if self.enable_quality_reports:
            quality_report = self._generate_quality_report(practical_tasks, results)

            # Save quality report
            report_file = self.output_dir / "quality_report.json"
            report_file.write_text(json.dumps(quality_report.to_dict(), indent=2))

            logger.info(f"Quality report saved to {report_file}")

            # Notify about quality report
            self._notify_progress(
                "quality_report_generated",
                {
                    "report_path": str(report_file),
                    "success_rate": quality_report.success_rate,
                    "total_files_created": quality_report.files_created_total,
                },
            )

        self._notify_progress(
            "batch_completed",
            {
                "total_tasks": len(practical_tasks),
                "completed": len(
                    [
                        r
                        for r in results
                        if isinstance(r, dict) and r.get("status") == "completed"
                    ]
                ),
                "failed": len(
                    [
                        r
                        for r in results
                        if isinstance(r, dict) and r.get("status") == "failed"
                    ]
                ),
            },
        )

        return results

    def _generate_quality_report(
        self, tasks: List[PracticalAgentTask], results: List[Dict]
    ) -> QualityReport:
        """Generate comprehensive quality report"""

        report = QualityReport()
        report.total_tasks = len(tasks)

        completed_tasks = []
        failed_tasks = []
        durations = []

        for i, (task, result) in enumerate(zip(tasks, results)):
            if isinstance(result, dict):
                if result.get("status") == "completed":
                    completed_tasks.append((task, result))
                    report.completed_tasks += 1
                elif result.get("status") == "failed":
                    failed_tasks.append((task, result))
                    report.failed_tasks += 1

                # Track duration
                if result.get("end_time") and result.get("start_time"):
                    duration = result["end_time"] - result["start_time"]
                    durations.append(duration)

        # Calculate metrics
        if durations:
            report.average_duration = sum(durations) / len(durations)

            # Find fastest and slowest tasks
            if completed_tasks:
                completed_with_duration = [
                    (t, r)
                    for t, r in completed_tasks
                    if r.get("end_time") and r.get("start_time")
                ]
                if completed_with_duration:
                    fastest = min(
                        completed_with_duration,
                        key=lambda x: x[1]["end_time"] - x[1]["start_time"],
                    )
                    slowest = max(
                        completed_with_duration,
                        key=lambda x: x[1]["end_time"] - x[1]["start_time"],
                    )

                    report.fastest_task = {
                        "task_id": fastest[0].task_id,
                        "duration": fastest[1]["end_time"] - fastest[1]["start_time"],
                    }
                    report.slowest_task = {
                        "task_id": slowest[0].task_id,
                        "duration": slowest[1]["end_time"] - slowest[1]["start_time"],
                    }

        # Success rate
        if report.total_tasks > 0:
            report.success_rate = report.completed_tasks / report.total_tasks

        # Copy aggregated metrics
        report.tasks_by_type = self.quality_metrics["tasks_by_type"].copy()
        report.tasks_by_phase = self.quality_metrics["tasks_by_phase"].copy()
        report.tasks_by_priority = self.quality_metrics["tasks_by_priority"].copy()
        report.files_created_total = self.quality_metrics["files_created_total"]
        report.files_modified_total = self.quality_metrics["files_modified_total"]
        report.commands_run_total = self.quality_metrics["commands_run_total"]

        return report

    def print_session_map(self):
        """Print mapping of task IDs to session IDs for easy monitoring"""
        print("\n🔍 Session ID Mapping for Log Monitoring:")
        print("=" * 60)
        for task_id, session_id in self.session_id_map.items():
            log_path = f"~/.claude/projects/-home-opsvi-master-root-apps-project-context/{session_id}.jsonl"
            print(f"Task: {task_id}")
            print(f"  Session: {session_id}")
            print(f"  Monitor: tail -f {log_path}")
            print()

    def get_monitoring_commands(self) -> List[str]:
        """Get shell commands for monitoring all active tasks"""
        commands = []
        for task_id, session_id in self.session_id_map.items():
            log_path = f"~/.claude/projects/-home-opsvi-master-root-apps-project-context/{session_id}.jsonl"
            commands.append(f"# {task_id}")
            commands.append(f"tail -f {log_path}")
            commands.append("")
        return commands


# Convenience function for easy usage
def create_practical_orchestrator(
    output_dir: Union[str, Path] = "./practical_output",
    max_parallel: int = 5,
    enable_monitoring: bool = True,
) -> PracticalOrchestrator:
    """Create a PracticalOrchestrator with sensible defaults"""

    return PracticalOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,
        enable_monitoring=enable_monitoring,
        enable_quality_reports=True,
        use_optimizations=True,
    )


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def example_usage():
        # Create orchestrator
        orchestrator = create_practical_orchestrator(
            output_dir="./example_output", max_parallel=2
        )

        # Create some example tasks
        tasks = [
            PracticalAgentTask(
                task_id="task1",
                task_type="development-specialist",
                prompt="Create a simple Python function",
                phase_id="implementation",
                priority="high",
                tags=["python", "function"],
            ),
            PracticalAgentTask(
                task_id="task2",
                task_type="qa-testing-guru",
                prompt="Write tests for the function",
                dependencies=["task1"],
                phase_id="testing",
                priority="normal",
                tags=["testing", "python"],
            ),
        ]

        # Set up progress monitoring
        def progress_handler(event_type: str, data: Dict):
            print(f"📊 {event_type}: {data}")

        orchestrator.set_progress_callback(progress_handler)

        # Execute tasks
        print("🚀 Starting task execution...")
        results = await orchestrator.execute_batch(tasks)

        # Print monitoring info
        orchestrator.print_session_map()

        print(f"✅ Completed {len(results)} tasks")
        print("📈 Quality report saved to ./example_output/quality_report.json")

    # Run example
    asyncio.run(example_usage())
