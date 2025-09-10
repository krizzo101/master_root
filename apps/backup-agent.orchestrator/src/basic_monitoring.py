"""
Basic Monitoring System
Real-time monitoring that integrates with working GenericOrchestrator
Built on proven orchestrator foundation
"""
import asyncio
import hashlib
import json
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

try:
    from .generic_orchestrator import AgentTask
except ImportError:
    from generic_orchestrator import AgentTask

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Recovery actions for failed tasks"""

    RETRY = "retry"
    USE_ALTERNATIVE = "use_alternative"
    SKIP = "skip"
    ESCALATE = "escalate"


@dataclass
class ExecutionContext:
    """Shared execution context across tasks"""

    context_id: str
    plan_id: str
    global_variables: Dict[str, Any] = field(default_factory=dict)
    shared_artifacts: Dict[str, Path] = field(default_factory=dict)
    decision_history: List[Dict] = field(default_factory=list)
    cross_task_knowledge: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResourcePrediction:
    """Predicted resource requirements for a task"""

    estimated_tokens: int
    estimated_duration: float
    memory_requirements: int  # MB
    parallel_compatibility: float  # 0-1 score
    optimal_batch_size: int
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskMetrics:
    """Metrics for individual task execution"""

    task_id: str
    task_type: str
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    retry_count: int = 0
    quality_gate_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SystemMetrics:
    """System-wide execution metrics"""

    timestamp: float
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_tasks: int
    avg_task_duration: float
    system_load: float
    memory_usage: float
    throughput: float  # tasks per minute

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextBroker:
    """Manages shared context across task execution"""

    def __init__(self, context_store_path: Path):
        self.context_store = context_store_path
        self.context_store.mkdir(parents=True, exist_ok=True)
        self.active_contexts: Dict[str, ExecutionContext] = {}
        self.context_subscribers: Dict[str, List[Callable]] = defaultdict(list)

    async def create_context(self, plan_id: str, initial_data: Dict = None) -> str:
        """Create new execution context for plan"""
        context_id = f"ctx_{plan_id}_{uuid.uuid4().hex[:8]}"
        context = ExecutionContext(
            context_id=context_id, plan_id=plan_id, global_variables=initial_data or {}
        )

        self.active_contexts[context_id] = context
        await self._persist_context(context)
        logger.info(f"Created execution context: {context_id}")
        return context_id

    async def update_context(self, context_id: str, updates: Dict[str, Any]):
        """Update context with new information"""
        if context_id not in self.active_contexts:
            logger.warning(f"Context {context_id} not found")
            return

        context = self.active_contexts[context_id]

        # Update different context types
        if "variables" in updates:
            context.global_variables.update(updates["variables"])
        if "artifacts" in updates:
            context.shared_artifacts.update(updates["artifacts"])
        if "knowledge" in updates:
            context.cross_task_knowledge.update(updates["knowledge"])
        if "decision" in updates:
            context.decision_history.append(
                {
                    "timestamp": time.time(),
                    "task_id": updates.get("task_id"),
                    "decision": updates["decision"],
                }
            )

        # Notify subscribers
        await self._notify_subscribers(context_id, updates)
        await self._persist_context(context)

    async def get_context_for_task(
        self, context_id: str, task_id: str
    ) -> Dict[str, Any]:
        """Get relevant context for specific task"""
        if context_id not in self.active_contexts:
            return {}

        context = self.active_contexts[context_id]

        return {
            "global_variables": context.global_variables,
            "shared_artifacts": context.shared_artifacts,
            "relevant_decisions": [
                d
                for d in context.decision_history
                if self._is_decision_relevant(d, task_id)
            ],
            "cross_task_knowledge": context.cross_task_knowledge,
            "context_id": context_id,
        }

    def subscribe_to_context_updates(self, context_id: str, callback: Callable):
        """Subscribe to context updates"""
        self.context_subscribers[context_id].append(callback)

    async def _notify_subscribers(self, context_id: str, updates: Dict[str, Any]):
        """Notify subscribers of context updates"""
        for callback in self.context_subscribers[context_id]:
            try:
                await callback(context_id, updates)
            except Exception as e:
                logger.error(f"Context subscriber error: {e}")

    async def _persist_context(self, context: ExecutionContext):
        """Persist context to disk"""
        try:
            context_file = self.context_store / f"{context.context_id}.json"
            with open(context_file, "w") as f:
                json.dump(context.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist context {context.context_id}: {e}")

    def _is_decision_relevant(self, decision: Dict, task_id: str) -> bool:
        """Check if decision is relevant to task"""
        # Simple relevance check - could be enhanced with ML
        decision_task = decision.get("task_id", "")
        return decision_task == task_id or "global" in decision.get("scope", [])


class ResourcePredictor:
    """ML-based resource requirement predictor"""

    def __init__(self, historical_data_path: Path):
        self.data_path = historical_data_path
        self.execution_history: List[Dict] = []
        self.task_patterns: Dict[str, Dict] = defaultdict(dict)
        self.load_historical_data()

    def load_historical_data(self):
        """Load historical execution data"""
        if self.data_path.exists():
            try:
                with open(self.data_path, "r") as f:
                    self.execution_history = json.load(f)
                self._analyze_patterns()
                logger.info(f"Loaded {len(self.execution_history)} historical records")
            except Exception as e:
                logger.error(f"Failed to load historical data: {e}")

    def record_execution(self, task: AgentTask, metrics: TaskMetrics):
        """Record task execution for learning"""
        execution_record = {
            "task_type": task.task_type,
            "prompt_length": len(getattr(task, "prompt", "")),
            "dependencies_count": len(getattr(task, "dependencies", [])),
            "actual_duration": metrics.duration or 0,
            "memory_used": metrics.memory_usage or 0,
            "tokens_used": self._extract_token_usage(metrics),
            "success": metrics.status == "completed",
            "timestamp": time.time(),
        }

        self.execution_history.append(execution_record)
        self._update_patterns(execution_record)

        # Periodic save
        if len(self.execution_history) % 10 == 0:
            self.save_historical_data()

    def predict_resources(self, task: AgentTask) -> ResourcePrediction:
        """Predict resource requirements for task"""

        # Extract task features
        features = {
            "task_type": task.task_type,
            "prompt_length": len(getattr(task, "prompt", "")),
            "dependencies_count": len(getattr(task, "dependencies", [])),
        }

        # Find similar historical tasks
        similar_tasks = self._find_similar_tasks(features)

        if not similar_tasks:
            # Use defaults for unknown patterns
            return ResourcePrediction(
                estimated_tokens=2000,
                estimated_duration=180.0,
                memory_requirements=512,
                parallel_compatibility=0.7,
                optimal_batch_size=3,
                confidence=0.3,
            )

        # Calculate predictions based on similar tasks
        tokens = int(sum(t["tokens_used"] for t in similar_tasks) / len(similar_tasks))
        duration = sum(t["actual_duration"] for t in similar_tasks) / len(similar_tasks)
        memory = int(sum(t["memory_used"] for t in similar_tasks) / len(similar_tasks))

        # Calculate parallel compatibility
        parallel_score = self._calculate_parallel_compatibility(task, similar_tasks)

        # Determine optimal batch size
        batch_size = self._determine_optimal_batch_size(features, similar_tasks)

        confidence = min(1.0, len(similar_tasks) / 10)

        return ResourcePrediction(
            estimated_tokens=max(tokens, 500),  # Minimum tokens
            estimated_duration=max(duration, 30.0),  # Minimum duration
            memory_requirements=max(memory, 256),  # Minimum memory
            parallel_compatibility=parallel_score,
            optimal_batch_size=batch_size,
            confidence=confidence,
        )

    def _find_similar_tasks(self, features: Dict, top_k: int = 5) -> List[Dict]:
        """Find similar tasks from history"""
        scores = []

        for record in self.execution_history:
            similarity = 0

            # Task type match (high weight)
            if record["task_type"] == features["task_type"]:
                similarity += 0.4

            # Prompt length similarity
            prompt_diff = abs(record["prompt_length"] - features["prompt_length"])
            prompt_sim = max(0, 1 - prompt_diff / 1000)  # Normalize by 1000 chars
            similarity += 0.3 * prompt_sim

            # Dependencies similarity
            dep_diff = abs(
                record["dependencies_count"] - features["dependencies_count"]
            )
            dep_sim = max(0, 1 - dep_diff / 5)  # Normalize by 5 dependencies
            similarity += 0.3 * dep_sim

            scores.append((similarity, record))

        # Return top-k similar tasks
        scores.sort(reverse=True, key=lambda x: x[0])
        return [record for score, record in scores[:top_k] if score > 0.3]

    def _extract_token_usage(self, metrics: TaskMetrics) -> int:
        """Extract token usage from metrics"""
        # Default estimation if not available
        return metrics.metadata.get("tokens_used", 1500)

    def _analyze_patterns(self):
        """Analyze patterns in historical data"""
        for record in self.execution_history:
            task_type = record["task_type"]
            if task_type not in self.task_patterns:
                self.task_patterns[task_type] = {
                    "avg_duration": 0,
                    "avg_tokens": 0,
                    "success_rate": 0,
                    "count": 0,
                }

    def _update_patterns(self, record: Dict):
        """Update task patterns with new record"""
        task_type = record["task_type"]
        pattern = self.task_patterns[task_type]

        count = pattern["count"]
        pattern["avg_duration"] = (
            (pattern["avg_duration"] * count) + record["actual_duration"]
        ) / (count + 1)
        pattern["avg_tokens"] = (
            (pattern["avg_tokens"] * count) + record["tokens_used"]
        ) / (count + 1)
        pattern["success_rate"] = (
            (pattern["success_rate"] * count) + (1 if record["success"] else 0)
        ) / (count + 1)
        pattern["count"] = count + 1

    def _calculate_parallel_compatibility(
        self, task: AgentTask, similar_tasks: List[Dict]
    ) -> float:
        """Calculate parallel compatibility score"""
        # Simple heuristic - could be enhanced
        if hasattr(task, "dependencies") and len(task.dependencies) > 2:
            return 0.3  # Low compatibility if many dependencies
        return 0.8  # Default high compatibility

    def _determine_optimal_batch_size(
        self, features: Dict, similar_tasks: List[Dict]
    ) -> int:
        """Determine optimal batch size"""
        # Simple heuristic based on task type
        task_type_batch_sizes = {
            "research": 2,
            "code": 1,
            "review": 3,
            "test": 4,
            "document": 3,
        }
        return task_type_batch_sizes.get(features["task_type"], 2)

    def save_historical_data(self):
        """Save historical data to disk"""
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, "w") as f:
                json.dump(self.execution_history, f, indent=2)
            logger.debug(f"Saved {len(self.execution_history)} historical records")
        except Exception as e:
            logger.error(f"Failed to save historical data: {e}")


class TaskMonitor:
    """Monitor for individual task execution"""

    def __init__(
        self, task: AgentTask, resource_prediction: Optional[ResourcePrediction] = None
    ):
        self.task = task
        self.metrics = TaskMetrics(task_id=task.task_id, task_type=task.task_type)
        self.checkpoints = []
        self.resource_prediction = resource_prediction
        self.actual_memory_samples = []
        self.context_updates = []

    def start(self):
        """Start monitoring task"""
        self.metrics.start_time = time.time()
        self.metrics.status = "running"
        logger.info(f"Task monitor started for {self.task.task_id}")

    def end(self, status: str, error: Optional[str] = None):
        """End monitoring task"""
        self.metrics.end_time = time.time()
        self.metrics.status = status
        self.metrics.error_message = error

        if self.metrics.start_time:
            self.metrics.duration = self.metrics.end_time - self.metrics.start_time

        logger.info(
            f"Task monitor ended for {self.task.task_id}: {status} ({self.metrics.duration:.2f}s)"
        )

    def add_checkpoint(self, name: str, data: Any = None):
        """Add checkpoint during task execution"""
        checkpoint = {"name": name, "timestamp": time.time(), "data": data}
        self.checkpoints.append(checkpoint)
        logger.debug(f"Checkpoint '{name}' added for task {self.task.task_id}")

    def update_quality_gates(self, results: Dict[str, Any]):
        """Update quality gate results"""
        self.metrics.quality_gate_results = results

    def get_metrics(self) -> TaskMetrics:
        """Get current task metrics"""
        return self.metrics

    def sample_memory_usage(self):
        """Sample current memory usage"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.actual_memory_samples.append(
                {"timestamp": time.time(), "memory_mb": memory_mb}
            )

            # Update metrics with latest sample
            self.metrics.memory_usage = int(memory_mb)
        except Exception as e:
            logger.debug(f"Failed to sample memory: {e}")

    def record_context_update(self, update_type: str, data: Dict[str, Any]):
        """Record context update during task execution"""
        self.context_updates.append(
            {"timestamp": time.time(), "type": update_type, "data": data}
        )

    def get_prediction_accuracy(self) -> Dict[str, float]:
        """Calculate prediction accuracy compared to actual metrics"""
        if not self.resource_prediction or not self.metrics.duration:
            return {}

        accuracy = {}

        # Duration accuracy
        if self.resource_prediction.estimated_duration > 0:
            duration_error = abs(
                self.metrics.duration - self.resource_prediction.estimated_duration
            )
            accuracy["duration"] = max(
                0, 1 - (duration_error / self.resource_prediction.estimated_duration)
            )

        # Memory accuracy
        if (
            self.metrics.memory_usage
            and self.resource_prediction.memory_requirements > 0
        ):
            memory_error = abs(
                self.metrics.memory_usage - self.resource_prediction.memory_requirements
            )
            accuracy["memory"] = max(
                0, 1 - (memory_error / self.resource_prediction.memory_requirements)
            )

        return accuracy


class RealTimeMonitor:
    """Real-time monitoring system for orchestrator execution"""

    def __init__(
        self,
        output_dir: Path,
        history_size: int = 1000,
        enable_enhancements: bool = True,
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Task monitoring
        self.task_monitors: Dict[str, TaskMonitor] = {}
        self.task_metrics_history = deque(maxlen=history_size)

        # System metrics
        self.system_metrics_history = deque(maxlen=history_size)
        self.start_time = time.time()

        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_tasks": 0,
            "avg_duration": 0.0,
            "throughput": 0.0,
            "peak_concurrent": 0,
        }

        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_task = None

        # Enhanced features
        if enable_enhancements:
            self.context_broker = ContextBroker(self.output_dir / "execution_contexts")
            self.resource_predictor = ResourcePredictor(
                self.output_dir / "resource_history.json"
            )
            self.prediction_accuracies = deque(maxlen=100)  # Track prediction accuracy
            self.adaptation_history = []
            self.current_execution_context = None
            self.adaptation_engine = PlanAdaptationEngine(self)

        logger.info(f"Real-time monitor initialized with output dir: {output_dir}")

    def register_event_callback(self, event: str, callback: Callable):
        """Register callback for monitoring events"""
        self.event_callbacks[event].append(callback)
        logger.debug(f"Registered callback for event: {event}")

    async def _trigger_event(self, event: str, data: Any):
        """Trigger event callbacks"""
        for callback in self.event_callbacks[event]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in event callback for {event}: {e}")

    def start_task_monitoring(self, task: AgentTask) -> TaskMonitor:
        """Start monitoring a specific task"""
        # Generate resource prediction if enhancements are enabled
        resource_prediction = None
        if hasattr(self, "resource_predictor"):
            resource_prediction = self.resource_predictor.predict_resources(task)
            logger.debug(
                f"Resource prediction for {task.task_id}: "
                f"{resource_prediction.estimated_duration:.1f}s, "
                f"{resource_prediction.estimated_tokens} tokens, "
                f"{resource_prediction.memory_requirements}MB"
            )

        monitor = TaskMonitor(task, resource_prediction)
        self.task_monitors[task.task_id] = monitor
        monitor.start()

        self.stats["total_tasks"] += 1
        self.stats["active_tasks"] += 1
        self.stats["peak_concurrent"] = max(
            self.stats["peak_concurrent"], self.stats["active_tasks"]
        )

        # Create enhanced event data
        event_data = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "timestamp": time.time(),
        }

        if resource_prediction:
            event_data["prediction"] = resource_prediction.to_dict()

        asyncio.create_task(self._trigger_event("task_started", event_data))

        return monitor

    def end_task_monitoring(
        self, task_id: str, status: str, error: Optional[str] = None
    ):
        """End monitoring for a specific task"""
        if task_id not in self.task_monitors:
            logger.warning(f"No monitor found for task {task_id}")
            return

        monitor = self.task_monitors[task_id]
        monitor.end(status, error)

        # Update statistics
        self.stats["active_tasks"] -= 1
        if status == "completed":
            self.stats["completed_tasks"] += 1
        else:
            self.stats["failed_tasks"] += 1

        # Update average duration
        if monitor.metrics.duration:
            total_completed = self.stats["completed_tasks"] + self.stats["failed_tasks"]
            if total_completed > 1:
                self.stats["avg_duration"] = (
                    self.stats["avg_duration"] * (total_completed - 1)
                    + monitor.metrics.duration
                ) / total_completed
            else:
                self.stats["avg_duration"] = monitor.metrics.duration

        # Store metrics in history
        self.task_metrics_history.append(monitor.get_metrics())

        # Record execution for learning if enhancements are enabled
        if hasattr(self, "resource_predictor"):
            self.resource_predictor.record_execution(monitor.task, monitor.metrics)

            # Track prediction accuracy
            if monitor.resource_prediction:
                accuracy = monitor.get_prediction_accuracy()
                if accuracy:
                    self.prediction_accuracies.append(accuracy)
                    logger.debug(f"Prediction accuracy for {task_id}: {accuracy}")

        # Create enhanced event data
        event_data = {
            "task_id": task_id,
            "status": status,
            "duration": monitor.metrics.duration,
            "timestamp": time.time(),
        }

        if hasattr(monitor, "resource_prediction") and monitor.resource_prediction:
            event_data["prediction_accuracy"] = monitor.get_prediction_accuracy()

        asyncio.create_task(self._trigger_event("task_completed", event_data))

        # Clean up
        del self.task_monitors[task_id]

    def start_system_monitoring(self, interval: float = 5.0):
        """Start system-wide monitoring"""
        if self.monitoring_active:
            logger.warning("System monitoring already active")
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(
            self._system_monitoring_loop(interval)
        )
        logger.info(f"System monitoring started with {interval}s interval")

    def stop_system_monitoring(self):
        """Stop system-wide monitoring"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()

        logger.info("System monitoring stopped")

    async def _system_monitoring_loop(self, interval: float):
        """System monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                current_time = time.time()
                runtime = current_time - self.start_time

                # Calculate throughput (tasks per minute)
                throughput = (
                    (self.stats["completed_tasks"] + self.stats["failed_tasks"])
                    / (runtime / 60)
                    if runtime > 0
                    else 0
                )

                system_metrics = SystemMetrics(
                    timestamp=current_time,
                    active_tasks=self.stats["active_tasks"],
                    completed_tasks=self.stats["completed_tasks"],
                    failed_tasks=self.stats["failed_tasks"],
                    total_tasks=self.stats["total_tasks"],
                    avg_task_duration=self.stats["avg_duration"],
                    system_load=0.0,  # Would implement actual system load monitoring
                    memory_usage=0.0,  # Would implement actual memory monitoring
                    throughput=throughput,
                )

                self.system_metrics_history.append(system_metrics)

                # Trigger system metrics event
                await self._trigger_event("system_metrics", system_metrics.to_dict())

                # Check for plan adaptation needs (if enhanced features enabled)
                if hasattr(self, "adaptation_engine"):
                    (
                        should_adapt,
                        trigger,
                        context,
                    ) = await self.adaptation_engine.should_adapt_plan(self.stats)

                    if should_adapt:
                        logger.info(f"Plan adaptation triggered: {trigger}")

                        # Perform adaptation based on trigger
                        if trigger == "high_failure_rate":
                            adaptation_result = await self.adaptation_engine.adapt_plan_for_failure_rate(
                                context
                            )
                        elif trigger == "performance_degradation":
                            adaptation_result = (
                                await self.adaptation_engine.adapt_plan_for_performance(
                                    context
                                )
                            )
                        else:
                            adaptation_result = {
                                "status": "unknown_trigger",
                                "trigger": trigger,
                            }

                        # Trigger adaptation event
                        await self._trigger_event(
                            "plan_adapted",
                            {
                                "trigger": trigger,
                                "context": context,
                                "result": adaptation_result,
                                "timestamp": current_time,
                            },
                        )

                # Save periodic snapshots
                if (
                    len(self.system_metrics_history) % 12 == 0
                ):  # Every minute if 5s interval
                    await self.save_monitoring_snapshot()

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def save_monitoring_snapshot(self):
        """Save current monitoring state to disk"""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.stats.copy(),
                "recent_system_metrics": [
                    m.to_dict() for m in list(self.system_metrics_history)[-10:]
                ],
                "recent_task_metrics": [
                    m.to_dict() for m in list(self.task_metrics_history)[-50:]
                ],
                "active_tasks": list(self.task_monitors.keys()),
            }

            snapshot_file = (
                self.output_dir / f"monitoring_snapshot_{int(time.time())}.json"
            )
            with open(snapshot_file, "w") as f:
                json.dump(snapshot, f, indent=2)

            logger.debug(f"Monitoring snapshot saved to {snapshot_file}")

        except Exception as e:
            logger.error(f"Error saving monitoring snapshot: {e}")

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        runtime = time.time() - self.start_time
        return {
            **self.stats,
            "runtime_seconds": runtime,
            "throughput_per_minute": (
                self.stats["completed_tasks"] + self.stats["failed_tasks"]
            )
            / (runtime / 60)
            if runtime > 0
            else 0,
            "success_rate": (
                self.stats["completed_tasks"]
                / max(1, self.stats["completed_tasks"] + self.stats["failed_tasks"])
            )
            * 100,
            "active_task_ids": list(self.task_monitors.keys()),
        }

    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """Get metrics for specific task"""
        if task_id in self.task_monitors:
            return self.task_monitors[task_id].get_metrics()

        # Check history
        for metrics in reversed(self.task_metrics_history):
            if metrics.task_id == task_id:
                return metrics

        return None

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health indicators"""
        stats = self.get_current_stats()

        # Determine health status
        health_score = 100
        warnings = []

        # Check failure rate
        if stats["success_rate"] < 80:
            health_score -= 20
            warnings.append("High failure rate detected")

        # Check if tasks are taking too long
        if stats["avg_duration"] > 300:  # 5 minutes
            health_score -= 15
            warnings.append("Tasks taking longer than expected")

        # Check for stalled tasks
        stalled_tasks = []
        current_time = time.time()
        for task_id, monitor in self.task_monitors.items():
            if (
                monitor.metrics.start_time
                and (current_time - monitor.metrics.start_time) > 600
            ):  # 10 minutes
                stalled_tasks.append(task_id)

        if stalled_tasks:
            health_score -= 25
            warnings.append(f"Stalled tasks detected: {stalled_tasks}")

        status = (
            "healthy"
            if health_score >= 80
            else "warning"
            if health_score >= 60
            else "critical"
        )

        return {
            "status": status,
            "health_score": health_score,
            "warnings": warnings,
            "statistics": stats,
            "stalled_tasks": stalled_tasks,
        }

    async def generate_monitoring_report(self) -> str:
        """Generate human-readable monitoring report"""
        stats = self.get_current_stats()
        health = self.get_system_health()

        report = [
            "=== Real-Time Monitoring Report ===",
            f"Status: {health['status'].upper()} (Health Score: {health['health_score']}/100)",
            f"Runtime: {stats['runtime_seconds']:.1f} seconds",
            "",
            "Task Statistics:",
            f"  Total Tasks: {stats['total_tasks']}",
            f"  Completed: {stats['completed_tasks']}",
            f"  Failed: {stats['failed_tasks']}",
            f"  Active: {stats['active_tasks']}",
            f"  Peak Concurrent: {stats['peak_concurrent']}",
            "",
            "Performance Metrics:",
            f"  Success Rate: {stats['success_rate']:.1f}%",
            f"  Average Duration: {stats['avg_duration']:.2f}s",
            f"  Throughput: {stats['throughput_per_minute']:.1f} tasks/min",
            "",
        ]

        # Add warnings if any
        if health["warnings"]:
            report.append("Warnings:")
            for warning in health["warnings"]:
                report.append(f"  ⚠️  {warning}")
            report.append("")

        # Add active tasks
        if stats["active_task_ids"]:
            report.append("Active Tasks:")
            for task_id in stats["active_task_ids"]:
                monitor = self.task_monitors[task_id]
                runtime = time.time() - (monitor.metrics.start_time or time.time())
                report.append(
                    f"  🔄 {task_id} ({monitor.metrics.task_type}) - {runtime:.1f}s"
                )
            report.append("")

        return "\n".join(report)

    async def create_execution_context(
        self, plan_id: str, initial_data: Dict = None
    ) -> str:
        """Create execution context for plan"""
        if hasattr(self, "context_broker"):
            context_id = await self.context_broker.create_context(plan_id, initial_data)
            self.current_execution_context = context_id
            return context_id
        return None

    async def update_execution_context(self, context_id: str, updates: Dict[str, Any]):
        """Update execution context"""
        if hasattr(self, "context_broker") and context_id:
            await self.context_broker.update_context(context_id, updates)

    def get_prediction_performance(self) -> Dict[str, Any]:
        """Get prediction performance metrics"""
        if not hasattr(self, "prediction_accuracies") or not self.prediction_accuracies:
            return {"status": "no_data", "message": "No prediction data available"}

        accuracies = list(self.prediction_accuracies)

        # Calculate averages
        duration_accuracies = [
            a.get("duration", 0) for a in accuracies if "duration" in a
        ]
        memory_accuracies = [a.get("memory", 0) for a in accuracies if "memory" in a]

        performance = {
            "total_predictions": len(accuracies),
            "avg_duration_accuracy": sum(duration_accuracies) / len(duration_accuracies)
            if duration_accuracies
            else 0,
            "avg_memory_accuracy": sum(memory_accuracies) / len(memory_accuracies)
            if memory_accuracies
            else 0,
            "recent_predictions": accuracies[-10:]
            if len(accuracies) > 10
            else accuracies,
        }

        return performance

    def get_resource_insights(self) -> Dict[str, Any]:
        """Get resource utilization insights"""
        if not hasattr(self, "resource_predictor"):
            return {"status": "disabled", "message": "Resource prediction is disabled"}

        insights = {
            "task_patterns": dict(self.resource_predictor.task_patterns),
            "historical_records": len(self.resource_predictor.execution_history),
            "prediction_performance": self.get_prediction_performance(),
        }

        # Calculate resource efficiency
        if self.task_metrics_history:
            recent_metrics = list(self.task_metrics_history)[-20:]  # Last 20 tasks
            avg_duration = sum(m.duration for m in recent_metrics if m.duration) / len(
                [m for m in recent_metrics if m.duration]
            )

            insights["recent_performance"] = {
                "avg_duration": avg_duration,
                "success_rate": len(
                    [m for m in recent_metrics if m.status == "completed"]
                )
                / len(recent_metrics)
                * 100,
                "memory_usage_trend": [
                    m.memory_usage for m in recent_metrics if m.memory_usage
                ][-5:],
            }

        return insights

    def get_enhanced_health_report(self) -> Dict[str, Any]:
        """Get enhanced system health report with predictions"""
        base_health = self.get_system_health()

        if not hasattr(self, "resource_predictor"):
            return base_health

        # Add prediction-based health indicators
        prediction_performance = self.get_prediction_performance()

        # Adjust health score based on prediction accuracy
        if prediction_performance.get("avg_duration_accuracy", 0) < 0.7:
            base_health["health_score"] -= 5
            base_health["warnings"].append("Low prediction accuracy detected")

        # Add resource optimization suggestions
        resource_insights = self.get_resource_insights()
        base_health["resource_insights"] = resource_insights
        base_health["prediction_performance"] = prediction_performance

        return base_health

    async def analyze_task_failure(self, task_id: str, error: str) -> Dict[str, Any]:
        """Analyze task failure and suggest recovery actions"""
        failure_analysis = {
            "task_id": task_id,
            "error": error,
            "timestamp": time.time(),
            "suggested_action": RecoveryAction.RETRY,
            "confidence": 0.5,
        }

        # Analyze error patterns
        error_lower = error.lower()

        # Transient errors
        if any(
            keyword in error_lower for keyword in ["timeout", "connection", "temporary"]
        ):
            failure_analysis.update(
                {
                    "category": "transient",
                    "suggested_action": RecoveryAction.RETRY,
                    "confidence": 0.9,
                }
            )

        # Resource limitation
        elif any(
            keyword in error_lower
            for keyword in ["memory", "limit exceeded", "too large"]
        ):
            failure_analysis.update(
                {
                    "category": "resource_limitation",
                    "suggested_action": RecoveryAction.USE_ALTERNATIVE,
                    "confidence": 0.8,
                }
            )

        # Store analysis in adaptation history
        if hasattr(self, "adaptation_history"):
            self.adaptation_history.append(failure_analysis)

        return failure_analysis

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get optimization suggestions based on monitoring data"""
        suggestions = []

        if not hasattr(self, "resource_predictor"):
            return suggestions

        # Analyze task patterns
        patterns = self.resource_predictor.task_patterns

        for task_type, pattern in patterns.items():
            if pattern.get("success_rate", 1) < 0.8:
                suggestions.append(
                    {
                        "type": "reliability",
                        "task_type": task_type,
                        "suggestion": f"Review {task_type} tasks - success rate is {pattern['success_rate']:.1%}",
                        "priority": "high",
                    }
                )

            if pattern.get("avg_duration", 0) > 300:  # 5 minutes
                suggestions.append(
                    {
                        "type": "performance",
                        "task_type": task_type,
                        "suggestion": f"Optimize {task_type} tasks - average duration is {pattern['avg_duration']:.1f}s",
                        "priority": "medium",
                    }
                )

        # Check system load
        if self.stats.get("peak_concurrent", 0) > 10:
            suggestions.append(
                {
                    "type": "scaling",
                    "suggestion": f"Consider scaling - peak concurrent tasks reached {self.stats['peak_concurrent']}",
                    "priority": "medium",
                }
            )

        return suggestions


class PlanAdaptationEngine:
    """Engine for dynamic plan modification during execution"""

    def __init__(self, monitor: RealTimeMonitor):
        self.monitor = monitor
        self.adaptation_history: List[Dict] = []
        self.adaptation_strategies: Dict[str, Callable] = {
            "task_failure": self._handle_task_failure,
            "resource_constraint": self._handle_resource_constraint,
            "quality_gate_failure": self._handle_quality_gate_failure,
        }

    async def should_adapt_plan(
        self, current_stats: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if plan adaptation is needed"""

        # Check failure rate
        total_tasks = current_stats.get("completed_tasks", 0) + current_stats.get(
            "failed_tasks", 0
        )
        if total_tasks > 5:  # Only after some tasks have run
            failure_rate = current_stats.get("failed_tasks", 0) / total_tasks
            if failure_rate > 0.4:  # More than 40% failure rate
                return (
                    True,
                    "high_failure_rate",
                    {
                        "failure_rate": failure_rate,
                        "failed_tasks": current_stats.get("failed_tasks", 0),
                        "total_tasks": total_tasks,
                    },
                )

        # Check if tasks are taking much longer than expected
        if hasattr(self.monitor, "resource_predictor"):
            recent_metrics = list(self.monitor.task_metrics_history)[-10:]
            if recent_metrics:
                actual_durations = [m.duration for m in recent_metrics if m.duration]
                if actual_durations:
                    avg_actual = sum(actual_durations) / len(actual_durations)
                    if avg_actual > 600:  # More than 10 minutes average
                        return (
                            True,
                            "performance_degradation",
                            {
                                "avg_duration": avg_actual,
                                "slow_tasks": len(
                                    [d for d in actual_durations if d > 300]
                                ),
                            },
                        )

        return False, None, {}

    async def adapt_plan_for_failure_rate(
        self, context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Adapt plan for high failure rate"""
        adaptations = []

        failure_rate = context.get("failure_rate", 0)

        if failure_rate > 0.6:
            # Very high failure rate - reduce complexity
            adaptations.append("reduce_parallel_execution")
            adaptations.append("add_retry_logic")
            adaptations.append("simplify_task_prompts")
        elif failure_rate > 0.4:
            # High failure rate - add resilience
            adaptations.append("add_retry_logic")
            adaptations.append("increase_timeout_limits")

        # Record adaptation
        adaptation_record = {
            "timestamp": time.time(),
            "trigger": "high_failure_rate",
            "context": context,
            "adaptations": adaptations,
        }

        self.adaptation_history.append(adaptation_record)
        logger.info(f"Plan adapted for failure rate {failure_rate:.2%}: {adaptations}")

        return {
            "status": "adapted",
            "adaptations": adaptations,
            "reason": "high_failure_rate",
        }

    async def adapt_plan_for_performance(
        self, context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Adapt plan for performance issues"""
        adaptations = []

        avg_duration = context.get("avg_duration", 0)

        if avg_duration > 900:  # More than 15 minutes
            adaptations.append("split_long_tasks")
            adaptations.append("increase_resource_allocation")
        elif avg_duration > 600:  # More than 10 minutes
            adaptations.append("optimize_task_batching")
            adaptations.append("review_task_complexity")

        # Record adaptation
        adaptation_record = {
            "timestamp": time.time(),
            "trigger": "performance_degradation",
            "context": context,
            "adaptations": adaptations,
        }

        self.adaptation_history.append(adaptation_record)
        logger.info(
            f"Plan adapted for performance (avg: {avg_duration:.1f}s): {adaptations}"
        )

        return {
            "status": "adapted",
            "adaptations": adaptations,
            "reason": "performance_degradation",
        }

    async def _handle_task_failure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle individual task failure"""
        failed_task_id = context.get("failed_task_id")
        error = context.get("error", "")

        # Analyze failure using monitor's analysis
        if hasattr(self.monitor, "analyze_task_failure"):
            analysis = await self.monitor.analyze_task_failure(failed_task_id, error)

            return {
                "status": "analyzed",
                "suggested_action": analysis.get("suggested_action"),
                "confidence": analysis.get("confidence", 0.5),
                "category": analysis.get("category", "unknown"),
            }

        return {"status": "no_analysis", "suggested_action": RecoveryAction.RETRY}

    async def _handle_resource_constraint(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resource constraints"""
        constraint_type = context.get("constraint_type", "unknown")

        adaptations = []
        if constraint_type == "memory":
            adaptations = ["reduce_parallel_tasks", "increase_memory_limits"]
        elif constraint_type == "token":
            adaptations = ["optimize_prompts", "batch_smaller_requests"]
        elif constraint_type == "time":
            adaptations = ["prioritize_critical_tasks", "extend_deadlines"]

        return {
            "status": "adapted",
            "adaptations": adaptations,
            "constraint_type": constraint_type,
        }

    async def _handle_quality_gate_failure(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle quality gate failures"""
        failed_gates = context.get("failed_gates", [])

        adaptations = []
        if "code_quality" in failed_gates:
            adaptations.append("add_code_review_step")
        if "test_coverage" in failed_gates:
            adaptations.append("enhance_testing_requirements")
        if "security_scan" in failed_gates:
            adaptations.append("add_security_review")

        return {
            "status": "adapted",
            "adaptations": adaptations,
            "failed_gates": failed_gates,
        }

    def get_adaptation_summary(self) -> Dict[str, Any]:
        """Get summary of adaptations made"""
        if not self.adaptation_history:
            return {"total_adaptations": 0, "message": "No adaptations made yet"}

        adaptations_by_trigger = defaultdict(int)
        recent_adaptations = []

        for adaptation in self.adaptation_history:
            trigger = adaptation.get("trigger", "unknown")
            adaptations_by_trigger[trigger] += 1

            if time.time() - adaptation.get("timestamp", 0) < 3600:  # Last hour
                recent_adaptations.append(adaptation)

        return {
            "total_adaptations": len(self.adaptation_history),
            "adaptations_by_trigger": dict(adaptations_by_trigger),
            "recent_adaptations": recent_adaptations[-5:],  # Last 5
            "most_common_trigger": max(
                adaptations_by_trigger.items(), key=lambda x: x[1]
            )[0]
            if adaptations_by_trigger
            else None,
        }


class MonitoringHooks:
    """Integration hooks for connecting monitoring with GenericOrchestrator"""

    def __init__(self, monitor: RealTimeMonitor):
        self.monitor = monitor

    def create_orchestrator_hooks(self):
        """Create hooks for GenericOrchestrator integration"""

        async def pre_execute_hook(task: AgentTask):
            """Pre-execution hook for monitoring"""
            task_monitor = self.monitor.start_task_monitoring(task)
            # Store only task_id in context to avoid JSON serialization issues
            task.context["task_monitor_id"] = task.task_id

        async def post_execute_hook(task: AgentTask):
            """Post-execution hook for monitoring"""
            status = task.status
            error = task.error
            self.monitor.end_task_monitoring(task.task_id, status, error)

        return pre_execute_hook, post_execute_hook


# Testing function
async def test_enhanced_monitoring():
    """Test enhanced monitoring system with new capabilities"""
    import tempfile
    from pathlib import Path

    print("Testing enhanced monitoring system...")

    # Create enhanced monitor
    output_dir = Path(tempfile.mkdtemp(prefix="enhanced_monitoring_test_"))
    monitor = RealTimeMonitor(output_dir, enable_enhancements=True)

    # Start system monitoring
    monitor.start_system_monitoring(interval=1.0)

    # Test execution context creation
    print("\n=== Testing Execution Context ===")
    context_id = await monitor.create_execution_context(
        "test_plan_001", {"plan_type": "development", "priority": "high"}
    )
    print(f"Created execution context: {context_id}")

    # Create test tasks with varied characteristics
    test_tasks = [
        AgentTask(
            task_id="research_task",
            task_type="research",
            prompt="Research modern web frameworks",
        ),
        AgentTask(
            task_id="code_task",
            task_type="code",
            prompt="Implement authentication system",
        ),
        AgentTask(
            task_id="review_task", task_type="review", prompt="Review code quality"
        ),
        AgentTask(
            task_id="test_task", task_type="test", prompt="Write comprehensive tests"
        ),
        AgentTask(
            task_id="failing_task", task_type="code", prompt="Complex failing task"
        ),
    ]

    # Simulate varied task execution patterns
    print("\n=== Simulating Enhanced Task Execution ===")
    for i, task in enumerate(test_tasks):
        print(f"Starting task: {task.task_id}")
        task_monitor = monitor.start_task_monitoring(task)

        # Simulate memory monitoring
        task_monitor.sample_memory_usage()

        # Simulate different execution patterns
        if task.task_id == "research_task":
            await asyncio.sleep(0.5)
            task_monitor.add_checkpoint("sources_found", {"sources": 5})
            await asyncio.sleep(0.5)
            status, error = "completed", None
        elif task.task_id == "code_task":
            await asyncio.sleep(1.0)
            task_monitor.add_checkpoint("design_complete", {"components": 3})
            await asyncio.sleep(1.5)
            task_monitor.add_checkpoint("implementation_done", {"lines_of_code": 150})
            status, error = "completed", None
        elif task.task_id == "failing_task":
            await asyncio.sleep(2.0)
            status, error = "failed", "Memory limit exceeded during complex operation"
        else:
            await asyncio.sleep(1.0)
            status, error = "completed", None

        # Update execution context with task results
        await monitor.update_execution_context(
            context_id,
            {
                "variables": {f"{task.task_id}_result": status},
                "knowledge": {
                    task.task_id: {
                        "status": status,
                        "duration": time.time() - task_monitor.metrics.start_time,
                    }
                },
            },
        )

        monitor.end_task_monitoring(task.task_id, status, error)

    # Wait for metrics collection and potential adaptation
    print("\n=== Waiting for System Analysis ===")
    await asyncio.sleep(3.0)

    # Test enhanced reporting capabilities
    print("\n=== Enhanced Monitoring Reports ===")

    # Basic monitoring report
    report = await monitor.generate_monitoring_report()
    print(f"\nBasic Report:\n{report}")

    # Enhanced health report
    enhanced_health = monitor.get_enhanced_health_report()
    print(f"\nEnhanced Health Report:")
    print(
        f"Status: {enhanced_health['status']} (Score: {enhanced_health['health_score']}/100)"
    )
    if enhanced_health.get("warnings"):
        print(f"Warnings: {enhanced_health['warnings']}")

    # Prediction performance
    prediction_performance = monitor.get_prediction_performance()
    print(f"\nPrediction Performance: {prediction_performance}")

    # Resource insights
    resource_insights = monitor.get_resource_insights()
    print(f"\nResource Insights:")
    print(f"- Task patterns tracked: {len(resource_insights.get('task_patterns', {}))}")
    print(f"- Historical records: {resource_insights.get('historical_records', 0)}")

    # Optimization suggestions
    suggestions = monitor.get_optimization_suggestions()
    if suggestions:
        print(f"\nOptimization Suggestions:")
        for suggestion in suggestions:
            print(
                f"- {suggestion['type'].title()}: {suggestion['suggestion']} (Priority: {suggestion['priority']})"
            )

    # Adaptation summary
    if hasattr(monitor, "adaptation_engine"):
        adaptation_summary = monitor.adaptation_engine.get_adaptation_summary()
        print(f"\nPlan Adaptation Summary:")
        print(f"- Total adaptations: {adaptation_summary['total_adaptations']}")
        if adaptation_summary.get("most_common_trigger"):
            print(f"- Most common trigger: {adaptation_summary['most_common_trigger']}")

    # Test failure analysis
    if monitor.adaptation_history:
        print(f"\nFailure Analysis Results:")
        for analysis in monitor.adaptation_history[-3:]:  # Last 3
            print(
                f"- {analysis.get('task_id', 'Unknown')}: {analysis.get('category', 'unknown')} "
                f"(Confidence: {analysis.get('confidence', 0):.2f})"
            )

    # Stop monitoring
    monitor.stop_system_monitoring()

    print(f"\nMonitoring data saved to: {output_dir}")
    return monitor


if __name__ == "__main__":
    asyncio.run(test_enhanced_monitoring())
