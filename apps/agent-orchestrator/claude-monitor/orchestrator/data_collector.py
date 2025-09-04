#!/usr/bin/env python3
"""
Real-time Orchestrator Data Collection Module

Provides comprehensive monitoring and data collection for orchestrator processes,
including real-time performance metrics, session tracking, and process monitoring.
"""

import asyncio
import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ProcessMetrics:
    """System-level process metrics"""

    pid: int
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    io_read_bytes: int
    io_write_bytes: int
    num_threads: int
    open_files: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionMetrics:
    """Session-level orchestration metrics"""

    session_id: str
    start_time: float
    end_time: Optional[float] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    total_tokens_used: int = 0
    avg_task_duration: float = 0.0
    peak_concurrent_tasks: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskMetrics:
    """Individual task execution metrics"""

    task_id: str
    task_type: str
    status: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    token_usage: int = 0
    agent_uuid: Optional[str] = None
    team_id: Optional[str] = None
    error_message: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class OrchestratorState:
    """Current orchestrator state snapshot"""

    active_sessions: Set[str] = field(default_factory=set)
    total_processes: int = 0
    total_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    system_load: float = 0.0
    memory_usage_mb: float = 0.0
    timestamp: float = field(default_factory=time.time)


class DataCollector:
    """
    Real-time data collector for orchestrator monitoring

    Collects and aggregates metrics from multiple sources:
    - Process-level system metrics
    - Task execution metrics
    - Session orchestration metrics
    - Real-time state snapshots
    """

    def __init__(
        self,
        output_dir: str = "./monitoring_data",
        collection_interval: float = 1.0,
        max_history_size: int = 10000,
        enable_file_output: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.collection_interval = collection_interval
        self.max_history_size = max_history_size
        self.enable_file_output = enable_file_output

        # Create output directory
        if self.enable_file_output:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.process_metrics_history = deque(maxlen=max_history_size)
        self.session_metrics_history = deque(maxlen=max_history_size)
        self.task_metrics_history = deque(maxlen=max_history_size)
        self.state_history = deque(maxlen=max_history_size)

        # Active tracking
        self.active_sessions: Dict[str, SessionMetrics] = {}
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.monitored_processes: Dict[int, psutil.Process] = {}

        # Threading
        self._stop_event = threading.Event()
        self._collector_thread = None
        self._lock = threading.RLock()

        # Callbacks
        self.metric_callbacks: List[callable] = []

        logger.info(f"DataCollector initialized with output_dir={output_dir}")

    def start_collection(self):
        """Start background data collection thread"""
        if self._collector_thread and self._collector_thread.is_alive():
            logger.warning("DataCollector already running")
            return

        self._stop_event.clear()
        self._collector_thread = threading.Thread(target=self._collection_loop)
        self._collector_thread.daemon = True
        self._collector_thread.start()
        logger.info("DataCollector started")

    def stop_collection(self):
        """Stop background data collection"""
        if self._collector_thread:
            self._stop_event.set()
            self._collector_thread.join(timeout=5.0)
            logger.info("DataCollector stopped")

    def register_process(self, pid: int):
        """Register a process for monitoring"""
        try:
            process = psutil.Process(pid)
            with self._lock:
                self.monitored_processes[pid] = process
            logger.info(f"Registered process {pid} for monitoring")
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} not found")

    def unregister_process(self, pid: int):
        """Unregister a process from monitoring"""
        with self._lock:
            if pid in self.monitored_processes:
                del self.monitored_processes[pid]
                logger.info(f"Unregistered process {pid}")

    def start_session(self, session_id: str) -> SessionMetrics:
        """Start tracking a new orchestration session"""
        with self._lock:
            session = SessionMetrics(session_id=session_id, start_time=time.time())
            self.active_sessions[session_id] = session
            logger.info(f"Started session tracking: {session_id}")
            return session

    def end_session(self, session_id: str):
        """End session tracking and archive metrics"""
        with self._lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.end_time = time.time()

                # Calculate final metrics
                session.avg_task_duration = self._calculate_avg_task_duration(
                    session_id
                )

                # Archive and remove from active
                self.session_metrics_history.append(session)
                del self.active_sessions[session_id]

                # Write to file if enabled
                if self.enable_file_output:
                    self._write_session_data(session)

                logger.info(f"Ended session tracking: {session_id}")

    def start_task(
        self,
        task_id: str,
        task_type: str,
        agent_uuid: str = None,
        team_id: str = None,
        dependencies: List[str] = None,
    ) -> TaskMetrics:
        """Start tracking a task execution"""
        with self._lock:
            task = TaskMetrics(
                task_id=task_id,
                task_type=task_type,
                status="running",
                start_time=time.time(),
                agent_uuid=agent_uuid,
                team_id=team_id,
                dependencies=dependencies or [],
            )
            self.active_tasks[task_id] = task

            # Update session metrics
            session_id = self._extract_session_from_task(task_id)
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.total_tasks += 1
                session.running_tasks += 1
                session.peak_concurrent_tasks = max(
                    session.peak_concurrent_tasks, session.running_tasks
                )

            logger.debug(f"Started task tracking: {task_id}")
            return task

    def end_task(
        self,
        task_id: str,
        status: str = "completed",
        error_message: str = None,
        token_usage: int = 0,
    ):
        """End task tracking and update metrics"""
        with self._lock:
            if task_id not in self.active_tasks:
                logger.warning(f"Task {task_id} not found in active tasks")
                return

            task = self.active_tasks[task_id]
            task.end_time = time.time()
            task.status = status
            task.error_message = error_message
            task.token_usage = token_usage
            task.duration = task.end_time - task.start_time if task.start_time else 0

            # Archive and remove from active
            self.task_metrics_history.append(task)
            del self.active_tasks[task_id]

            # Update session metrics
            session_id = self._extract_session_from_task(task_id)
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.running_tasks -= 1
                session.total_tokens_used += token_usage

                if status == "completed":
                    session.completed_tasks += 1
                elif status == "failed":
                    session.failed_tasks += 1

            logger.debug(f"Ended task tracking: {task_id} ({status})")

    def get_current_state(self) -> OrchestratorState:
        """Get current orchestrator state snapshot"""
        with self._lock:
            state = OrchestratorState(
                active_sessions=set(self.active_sessions.keys()),
                total_processes=len(self.monitored_processes),
                total_tasks=len(self.active_tasks) + len(self.task_metrics_history),
                running_tasks=len(self.active_tasks),
                completed_tasks=len(
                    [t for t in self.task_metrics_history if t.status == "completed"]
                ),
                failed_tasks=len(
                    [t for t in self.task_metrics_history if t.status == "failed"]
                ),
                system_load=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
            )
            return state

    def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for a specific session"""
        with self._lock:
            # Check active sessions first
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]

            # Check history
            for session in self.session_metrics_history:
                if session.session_id == session_id:
                    return session

            return None

    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """Get metrics for a specific task"""
        with self._lock:
            # Check active tasks first
            if task_id in self.active_tasks:
                return self.active_tasks[task_id]

            # Check history
            for task in self.task_metrics_history:
                if task.task_id == task_id:
                    return task

            return None

    def get_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated metrics summary for a time window"""
        cutoff_time = time.time() - (time_window_minutes * 60)

        with self._lock:
            # Filter recent tasks
            recent_tasks = [
                t for t in self.task_metrics_history if t.timestamp > cutoff_time
            ]

            # Calculate summary
            summary = {
                "time_window_minutes": time_window_minutes,
                "total_tasks": len(recent_tasks),
                "completed_tasks": len(
                    [t for t in recent_tasks if t.status == "completed"]
                ),
                "failed_tasks": len([t for t in recent_tasks if t.status == "failed"]),
                "avg_task_duration": sum(t.duration or 0 for t in recent_tasks)
                / max(1, len(recent_tasks)),
                "total_token_usage": sum(t.token_usage for t in recent_tasks),
                "active_sessions": len(self.active_sessions),
                "current_running_tasks": len(self.active_tasks),
                "monitored_processes": len(self.monitored_processes),
                "timestamp": time.time(),
            }

            return summary

    def register_callback(self, callback: callable):
        """Register a callback for metric updates"""
        self.metric_callbacks.append(callback)

    def _collection_loop(self):
        """Main collection loop running in background thread"""
        logger.info("Starting data collection loop")

        while not self._stop_event.is_set():
            try:
                # Collect process metrics
                self._collect_process_metrics()

                # Collect current state
                state = self.get_current_state()
                self.state_history.append(state)

                # Write periodic snapshots
                if self.enable_file_output:
                    self._write_state_snapshot(state)

                # Call registered callbacks
                for callback in self.metric_callbacks:
                    try:
                        callback(state)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

                # Wait for next collection interval
                self._stop_event.wait(self.collection_interval)

            except Exception as e:
                logger.error(f"Collection loop error: {e}")
                self._stop_event.wait(self.collection_interval)

        logger.info("Data collection loop stopped")

    def _collect_process_metrics(self):
        """Collect metrics from monitored processes"""
        with self._lock:
            current_time = time.time()
            dead_pids = []

            for pid, process in self.monitored_processes.items():
                try:
                    # Check if process still exists
                    if not process.is_running():
                        dead_pids.append(pid)
                        continue

                    # Collect metrics
                    metrics = ProcessMetrics(
                        pid=pid,
                        cpu_percent=process.cpu_percent(),
                        memory_mb=process.memory_info().rss / 1024 / 1024,
                        memory_percent=process.memory_percent(),
                        io_read_bytes=process.io_counters().read_bytes,
                        io_write_bytes=process.io_counters().write_bytes,
                        num_threads=process.num_threads(),
                        open_files=len(process.open_files()),
                        timestamp=current_time,
                    )

                    self.process_metrics_history.append(metrics)

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    dead_pids.append(pid)
                except Exception as e:
                    logger.error(f"Error collecting metrics for PID {pid}: {e}")

            # Clean up dead processes
            for pid in dead_pids:
                del self.monitored_processes[pid]
                logger.debug(f"Removed dead process {pid} from monitoring")

    def _extract_session_from_task(self, task_id: str) -> str:
        """Extract session ID from task ID (simple heuristic)"""
        # This is a simple implementation - adjust based on your task ID format
        parts = task_id.split("_")
        if len(parts) >= 2:
            return f"{parts[0]}_{parts[1]}"
        return "default_session"

    def _calculate_avg_task_duration(self, session_id: str) -> float:
        """Calculate average task duration for a session"""
        session_tasks = [
            t
            for t in self.task_metrics_history
            if self._extract_session_from_task(t.task_id) == session_id
            and t.duration is not None
        ]

        if not session_tasks:
            return 0.0

        return sum(t.duration for t in session_tasks) / len(session_tasks)

    def _write_session_data(self, session: SessionMetrics):
        """Write session data to file"""
        try:
            filename = f"session_{session.session_id}_{int(session.start_time)}.json"
            filepath = self.output_dir / filename

            with open(filepath, "w") as f:
                json.dump(asdict(session), f, indent=2)

            logger.debug(f"Wrote session data: {filepath}")
        except Exception as e:
            logger.error(f"Error writing session data: {e}")

    def _write_state_snapshot(self, state: OrchestratorState):
        """Write current state snapshot to file"""
        try:
            # Only write periodic snapshots (every 10 collections)
            if int(state.timestamp) % 10 != 0:
                return

            filename = f"state_snapshot_{int(state.timestamp)}.json"
            filepath = self.output_dir / filename

            with open(filepath, "w") as f:
                json.dump(asdict(state), f, indent=2)

            logger.debug(f"Wrote state snapshot: {filepath}")
        except Exception as e:
            logger.error(f"Error writing state snapshot: {e}")


# Convenience functions for quick integration
_global_collector: Optional[DataCollector] = None


def get_global_collector() -> DataCollector:
    """Get or create global data collector instance"""
    global _global_collector
    if _global_collector is None:
        _global_collector = DataCollector()
        _global_collector.start_collection()
    return _global_collector


def collect_task_metrics(task_id: str, task_type: str, **kwargs) -> TaskMetrics:
    """Convenience function to start task tracking"""
    collector = get_global_collector()
    return collector.start_task(task_id, task_type, **kwargs)


def finish_task_metrics(task_id: str, status: str = "completed", **kwargs):
    """Convenience function to end task tracking"""
    collector = get_global_collector()
    collector.end_task(task_id, status, **kwargs)


def collect_session_metrics(session_id: str) -> SessionMetrics:
    """Convenience function to start session tracking"""
    collector = get_global_collector()
    return collector.start_session(session_id)


def finish_session_metrics(session_id: str):
    """Convenience function to end session tracking"""
    collector = get_global_collector()
    collector.end_session(session_id)
