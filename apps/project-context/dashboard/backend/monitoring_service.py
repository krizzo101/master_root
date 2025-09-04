#!/usr/bin/env python3
"""
Monitoring Service - Data aggregation and processing for dashboard backend
"""

import asyncio
import glob
import hashlib
import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import existing monitoring infrastructure
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
sys.path.append("/home/opsvi/master_root/apps/project-context")

# Import ChatImportMonitor with error handling
try:
    from monitor_chat_import import ChatImportMonitor
except ImportError as e:
    logger.warning(f"ChatImportMonitor not available: {e}")
    ChatImportMonitor = None

logger = logging.getLogger(__name__)


class MonitoringService:
    """Central monitoring service that aggregates data from various sources"""

    def __init__(self):
        self.base_path = Path("/home/opsvi/master_root/apps/project-context")

        # Automatically discover all output directories
        self.output_dirs = self._discover_output_directories()

        # File system monitoring
        self.file_hashes = {}  # Track file changes
        self.last_scan_time = 0
        self.scan_interval = 3  # seconds

        # Initialize existing monitors
        self.chat_monitor = ChatImportMonitor() if ChatImportMonitor else None

        # Cache for performance
        self.cache = {
            "tasks": {},
            "last_update": 0,
            "system_status": {},
            "performance_metrics": {},
        }

        # Monitoring state
        self.is_monitoring = False
        self.update_interval = 5  # seconds

        logger.info(
            f"MonitoringService initialized with {len(self.output_dirs)} output directories"
        )
        logger.info(f"Monitoring directories: {[str(d) for d in self.output_dirs]}")

    def _discover_output_directories(self) -> List[Path]:
        """Automatically discover all output directories"""
        output_dirs = []

        # Look for directories ending with '_output'
        for item in self.base_path.iterdir():
            if item.is_dir() and item.name.endswith("_output"):
                output_dirs.append(item)

        # Also check for 'chat_import_output' specifically
        chat_output = self.base_path / "chat_import_output"
        if chat_output.exists() and chat_output not in output_dirs:
            output_dirs.append(chat_output)

        return sorted(output_dirs)

    def is_active(self) -> bool:
        """Check if monitoring is active"""
        return self.is_monitoring

    async def start_monitoring(self):
        """Start background monitoring loop"""
        self.is_monitoring = True
        logger.info("Starting background monitoring")

        while self.is_monitoring:
            try:
                await self._update_cache()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)

    async def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_monitoring = False
        logger.info("Stopping background monitoring")

    async def _update_cache(self):
        """Update cached data from all sources"""
        try:
            # Update task data
            self.cache["tasks"] = await self._scan_task_files()

            # Update system status
            self.cache["system_status"] = await self._get_system_status()

            # Update performance metrics
            self.cache[
                "performance_metrics"
            ] = await self._calculate_performance_metrics()

            self.cache["last_update"] = time.time()

        except Exception as e:
            logger.error(f"Cache update error: {e}")

    def _should_rescan_files(self) -> bool:
        """Check if files should be rescanned based on modification times"""
        current_time = time.time()
        if current_time - self.last_scan_time < self.scan_interval:
            return False

        # Check if any task files have been modified
        for output_dir in self.output_dirs:
            tasks_dir = output_dir / "tasks"
            if not tasks_dir.exists():
                continue

            for task_file in tasks_dir.glob("*.json"):
                try:
                    file_stat = task_file.stat()
                    file_path_str = str(task_file)
                    current_hash = f"{file_stat.st_mtime}_{file_stat.st_size}"

                    if self.file_hashes.get(file_path_str) != current_hash:
                        return True
                except Exception:
                    continue

        return False

    def _calculate_duration_minutes(self, task_data: Dict) -> Optional[float]:
        """Calculate task duration in minutes"""
        duration_seconds = self._calculate_duration(task_data)
        return duration_seconds / 60 if duration_seconds else None

    async def _scan_task_files(self) -> Dict[str, Dict]:
        """Scan all output directories for task result files"""
        # Use cached data if files haven't changed
        if not self._should_rescan_files() and self.cache["tasks"]:
            return self.cache["tasks"]

        tasks = {}
        self.last_scan_time = time.time()

        for output_dir in self.output_dirs:
            tasks_dir = output_dir / "tasks"
            if not tasks_dir.exists():
                continue

            for task_file in tasks_dir.glob("*.json"):
                try:
                    file_stat = task_file.stat()
                    file_path_str = str(task_file)
                    current_hash = f"{file_stat.st_mtime}_{file_stat.st_size}"

                    # Update file hash tracking
                    self.file_hashes[file_path_str] = current_hash

                    with open(task_file) as f:
                        task_data = json.load(f)

                    task_id = task_data.get("task_id")
                    if task_id:
                        # Enhance with file metadata
                        task_data["file_modified"] = file_stat.st_mtime
                        task_data["file_path"] = str(task_file)
                        task_data["output_dir"] = str(output_dir)
                        task_data["output_dir_name"] = output_dir.name

                        # Add derived fields for better analysis
                        task_data["is_recent"] = (
                            time.time() - file_stat.st_mtime
                        ) < 3600  # Within last hour
                        task_data[
                            "duration_minutes"
                        ] = self._calculate_duration_minutes(task_data)

                        tasks[task_id] = task_data

                except Exception as e:
                    logger.warning(f"Error reading task file {task_file}: {e}")

        logger.info(
            f"Scanned {len(tasks)} tasks from {len(self.output_dirs)} directories"
        )
        return tasks

    async def get_system_status(self) -> Dict:
        """Get current system status"""
        if time.time() - self.cache["last_update"] > 10:  # Force update if stale
            await self._update_cache()

        return self.cache["system_status"]

    async def _get_system_status(self) -> Dict:
        """Calculate current system status"""
        tasks = self.cache["tasks"]

        if not tasks:
            return {
                "overall_progress": 0.0,
                "current_phase": None,
                "elapsed_minutes": 0.0,
                "active_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "total_tasks": 0,
            }

        # Count task statuses
        completed = sum(1 for t in tasks.values() if t.get("status") == "completed")
        failed = sum(1 for t in tasks.values() if t.get("status") == "failed")
        running = sum(1 for t in tasks.values() if t.get("status") == "running")
        total = len(tasks)

        # Calculate progress
        progress = (completed / total * 100) if total > 0 else 0

        # Determine current phase based on running tasks
        current_phase = None
        for task in tasks.values():
            if task.get("status") == "running" and task.get("phase_id"):
                current_phase = task["phase_id"]
                break

        # Calculate elapsed time from earliest start time
        start_times = [
            t.get("start_time") for t in tasks.values() if t.get("start_time")
        ]
        elapsed_minutes = 0.0
        if start_times:
            earliest = min(start_times)
            elapsed_minutes = (time.time() - earliest) / 60

        return {
            "overall_progress": progress,
            "current_phase": current_phase,
            "elapsed_minutes": elapsed_minutes,
            "active_tasks": running,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_tasks": total,
        }

    async def get_all_tasks(self) -> List[Dict]:
        """Get all tasks with details"""
        if time.time() - self.cache["last_update"] > 10:
            await self._update_cache()

        tasks = []
        for task_id, task_data in self.cache["tasks"].items():
            task_detail = await self._format_task_detail(task_data)
            tasks.append(task_detail)

        # Sort by start time (newest first)
        tasks.sort(key=lambda x: x.get("start_time", 0), reverse=True)
        return tasks

    async def get_task_detail(self, task_id: str) -> Optional[Dict]:
        """Get detailed information for a specific task"""
        if time.time() - self.cache["last_update"] > 10:
            await self._update_cache()

        task_data = self.cache["tasks"].get(task_id)
        if not task_data:
            return None

        return await self._format_task_detail(task_data)

    async def _format_task_detail(self, task_data: Dict) -> Dict:
        """Format task data for API response"""
        return {
            "task_id": task_data.get("task_id", ""),
            "task_type": task_data.get("task_type", ""),
            "status": task_data.get("status", "unknown"),
            "session_id": task_data.get("session_id"),
            "phase_id": task_data.get("phase_id"),
            "start_time": task_data.get("start_time"),
            "end_time": task_data.get("end_time"),
            "duration": self._calculate_duration(task_data),
            "files_created": task_data.get("files_created", []),
            "files_modified": task_data.get("files_modified", []),
            "metrics": task_data.get("metrics", {}),
            "error": task_data.get("error"),
            "prompt": task_data.get("prompt", "")[:200] + "..."
            if len(task_data.get("prompt", "")) > 200
            else task_data.get("prompt", ""),
            "result_summary": self._extract_result_summary(task_data),
            "log_path": task_data.get("log_path"),
            "file_path": task_data.get("file_path"),
            "output_dir": task_data.get("output_dir"),
        }

    def _calculate_duration(self, task_data: Dict) -> Optional[float]:
        """Calculate task duration in seconds"""
        start = task_data.get("start_time")
        end = task_data.get("end_time")

        if start and end:
            return end - start
        elif start and task_data.get("status") == "running":
            return time.time() - start

        return None

    def _extract_result_summary(self, task_data: Dict) -> str:
        """Extract a summary from task result"""
        result = task_data.get("result")
        if not result:
            return ""

        if isinstance(result, dict):
            # Try to get a meaningful summary
            if "result" in result:
                summary = str(result["result"])
                return summary[:300] + "..." if len(summary) > 300 else summary
            elif "summary" in result:
                return str(result["summary"])[:300]
            else:
                return f"Task completed with {len(result)} result fields"

        return str(result)[:300] + "..." if len(str(result)) > 300 else str(result)

    async def get_performance_metrics(self) -> Dict:
        """Get performance metrics and analytics"""
        if time.time() - self.cache["last_update"] > 10:
            await self._update_cache()

        return self.cache["performance_metrics"]

    async def _calculate_performance_metrics(self) -> Dict:
        """Calculate performance metrics from task data"""
        tasks = self.cache["tasks"]

        if not tasks:
            return {
                "parallel_utilization": 0.0,
                "tasks_per_hour": 0.0,
                "average_task_duration": 0.0,
                "success_rate": 0.0,
                "fastest_task": None,
                "slowest_task": None,
            }

        completed_tasks = [
            t
            for t in tasks.values()
            if t.get("status") == "completed"
            and t.get("start_time")
            and t.get("end_time")
        ]

        if not completed_tasks:
            return {
                "parallel_utilization": 0.0,
                "tasks_per_hour": 0.0,
                "average_task_duration": 0.0,
                "success_rate": 0.0,
                "fastest_task": None,
                "slowest_task": None,
            }

        # Calculate durations
        durations = [t["end_time"] - t["start_time"] for t in completed_tasks]

        avg_duration = sum(durations) / len(durations)

        # Find fastest and slowest
        fastest_idx = durations.index(min(durations))
        slowest_idx = durations.index(max(durations))

        fastest_task = {
            "task_id": completed_tasks[fastest_idx]["task_id"],
            "duration": durations[fastest_idx],
            "task_type": completed_tasks[fastest_idx].get("task_type"),
        }

        slowest_task = {
            "task_id": completed_tasks[slowest_idx]["task_id"],
            "duration": durations[slowest_idx],
            "task_type": completed_tasks[slowest_idx].get("task_type"),
        }

        # Calculate success rate
        total_tasks = len(tasks)
        completed_count = len(completed_tasks)
        failed_count = sum(1 for t in tasks.values() if t.get("status") == "failed")
        finished_count = completed_count + failed_count
        success_rate = (
            (completed_count / finished_count * 100) if finished_count > 0 else 100.0
        )

        # Calculate tasks per hour (based on completed tasks in last hour)
        now = time.time()
        recent_tasks = [
            t for t in completed_tasks if (now - t["end_time"]) < 3600  # Last hour
        ]
        tasks_per_hour = len(recent_tasks)

        # Calculate parallel utilization (estimate)
        running_tasks = sum(1 for t in tasks.values() if t.get("status") == "running")
        max_parallel = 19  # From the 18 parallel configuration + some overhead
        parallel_utilization = (
            (running_tasks / max_parallel * 100) if max_parallel > 0 else 0
        )

        return {
            "parallel_utilization": parallel_utilization,
            "tasks_per_hour": tasks_per_hour,
            "average_task_duration": avg_duration,
            "success_rate": success_rate,
            "fastest_task": fastest_task,
            "slowest_task": slowest_task,
        }

    async def get_task_logs(self, task_id: str, lines: int = 100) -> List[str]:
        """Get recent log entries for a task"""
        task_data = self.cache["tasks"].get(task_id)
        if not task_data:
            return []

        log_path = task_data.get("log_path")
        if not log_path:
            return []

        # Expand ~ to home directory
        log_path = Path(log_path).expanduser()

        if not log_path.exists():
            return [f"Log file not found: {log_path}"]

        try:
            # Read last N lines from log file
            with open(log_path, "r") as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]
        except Exception as e:
            return [f"Error reading log file: {e}"]

    async def get_quality_report(self) -> Dict:
        """Get the latest quality report"""
        # Look for quality reports in output directories
        for output_dir in self.output_dirs:
            quality_file = output_dir / "quality_report.json"
            if quality_file.exists():
                try:
                    with open(quality_file) as f:
                        report = json.load(f)

                    # Add metadata
                    stat = quality_file.stat()
                    report["generated_at"] = stat.st_mtime
                    report["report_file"] = str(quality_file)

                    return report
                except Exception as e:
                    logger.warning(f"Error reading quality report {quality_file}: {e}")

        # Generate basic quality report from cached data
        return await self._generate_basic_quality_report()

    async def _generate_basic_quality_report(self) -> Dict:
        """Generate a basic quality report from current task data"""
        tasks = self.cache["tasks"]

        total_tasks = len(tasks)
        completed_tasks = sum(
            1 for t in tasks.values() if t.get("status") == "completed"
        )
        failed_tasks = sum(1 for t in tasks.values() if t.get("status") == "failed")

        files_created_total = sum(
            len(t.get("files_created", [])) for t in tasks.values()
        )
        files_modified_total = sum(
            len(t.get("files_modified", [])) for t in tasks.values()
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (completed_tasks / total_tasks) if total_tasks > 0 else 0.0,
            "files_created_total": files_created_total,
            "files_modified_total": files_modified_total,
            "generated_at": time.time(),
            "report_type": "basic",
            "tasks_by_type": self._count_tasks_by_type(),
            "tasks_by_phase": self._count_tasks_by_phase(),
        }

    def _count_tasks_by_type(self) -> Dict[str, int]:
        """Count tasks by type"""
        counts = {}
        for task in self.cache["tasks"].values():
            task_type = task.get("task_type", "unknown")
            counts[task_type] = counts.get(task_type, 0) + 1
        return counts

    def _count_tasks_by_phase(self) -> Dict[str, int]:
        """Count tasks by phase"""
        counts = {}
        for task in self.cache["tasks"].values():
            phase_id = task.get("phase_id", "unknown")
            counts[phase_id] = counts.get(phase_id, 0) + 1
        return counts

    async def get_task_analytics(self) -> Dict:
        """Get detailed task analytics and insights"""
        if time.time() - self.cache["last_update"] > 10:
            await self._update_cache()

        tasks = self.cache["tasks"]

        if not tasks:
            return {"error": "No tasks found"}

        analytics = {
            "overview": {
                "total_tasks": len(tasks),
                "by_status": self._count_by_status(tasks),
                "by_type": self._count_tasks_by_type(),
                "by_phase": self._count_tasks_by_phase(),
                "by_output_dir": self._count_by_output_dir(tasks),
            },
            "performance": {
                "average_duration_minutes": self._calculate_average_duration(tasks),
                "fastest_tasks": self._get_fastest_tasks(tasks, limit=5),
                "slowest_tasks": self._get_slowest_tasks(tasks, limit=5),
                "recent_activity": self._get_recent_activity(tasks),
            },
            "quality": {
                "success_rate": self._calculate_success_rate(tasks),
                "error_analysis": self._analyze_errors(tasks),
                "resource_usage": self._analyze_resource_usage(tasks),
            },
            "trends": {
                "completion_rate_by_hour": self._calculate_hourly_completion_rate(
                    tasks
                ),
                "task_types_trending": self._get_trending_task_types(tasks),
            },
        }

        return analytics

    def _count_by_status(self, tasks: Dict) -> Dict[str, int]:
        """Count tasks by status"""
        counts = defaultdict(int)
        for task in tasks.values():
            status = task.get("status", "unknown")
            counts[status] += 1
        return dict(counts)

    def _count_by_output_dir(self, tasks: Dict) -> Dict[str, int]:
        """Count tasks by output directory"""
        counts = defaultdict(int)
        for task in tasks.values():
            output_dir = task.get("output_dir_name", "unknown")
            counts[output_dir] += 1
        return dict(counts)

    def _calculate_average_duration(self, tasks: Dict) -> float:
        """Calculate average task duration in minutes"""
        durations = []
        for task in tasks.values():
            if task.get("duration_minutes"):
                durations.append(task["duration_minutes"])

        return sum(durations) / len(durations) if durations else 0.0

    def _get_fastest_tasks(self, tasks: Dict, limit: int = 5) -> List[Dict]:
        """Get fastest completed tasks"""
        completed_tasks = [
            task
            for task in tasks.values()
            if task.get("status") == "completed" and task.get("duration_minutes")
        ]

        sorted_tasks = sorted(completed_tasks, key=lambda x: x["duration_minutes"])

        return [
            {
                "task_id": task["task_id"],
                "task_type": task.get("task_type", "unknown"),
                "duration_minutes": task["duration_minutes"],
                "output_dir": task.get("output_dir_name", "unknown"),
            }
            for task in sorted_tasks[:limit]
        ]

    def _get_slowest_tasks(self, tasks: Dict, limit: int = 5) -> List[Dict]:
        """Get slowest completed tasks"""
        completed_tasks = [
            task
            for task in tasks.values()
            if task.get("status") == "completed" and task.get("duration_minutes")
        ]

        sorted_tasks = sorted(
            completed_tasks, key=lambda x: x["duration_minutes"], reverse=True
        )

        return [
            {
                "task_id": task["task_id"],
                "task_type": task.get("task_type", "unknown"),
                "duration_minutes": task["duration_minutes"],
                "output_dir": task.get("output_dir_name", "unknown"),
            }
            for task in sorted_tasks[:limit]
        ]

    def _get_recent_activity(self, tasks: Dict) -> Dict:
        """Get recent activity summary"""
        now = time.time()
        one_hour_ago = now - 3600
        six_hours_ago = now - 21600
        one_day_ago = now - 86400

        activity = {
            "last_hour": 0,
            "last_6_hours": 0,
            "last_24_hours": 0,
            "recent_completions": [],
        }

        for task in tasks.values():
            if task.get("end_time"):
                end_time = task["end_time"]
                if end_time > one_hour_ago:
                    activity["last_hour"] += 1
                if end_time > six_hours_ago:
                    activity["last_6_hours"] += 1
                if end_time > one_day_ago:
                    activity["last_24_hours"] += 1

                # Add to recent completions
                if end_time > six_hours_ago and task.get("status") == "completed":
                    activity["recent_completions"].append(
                        {
                            "task_id": task["task_id"],
                            "task_type": task.get("task_type", "unknown"),
                            "completed_at": end_time,
                            "duration_minutes": task.get("duration_minutes", 0),
                        }
                    )

        # Sort recent completions by time
        activity["recent_completions"].sort(
            key=lambda x: x["completed_at"], reverse=True
        )
        activity["recent_completions"] = activity["recent_completions"][:10]

        return activity

    def _calculate_success_rate(self, tasks: Dict) -> float:
        """Calculate overall success rate"""
        completed = sum(
            1 for task in tasks.values() if task.get("status") == "completed"
        )
        failed = sum(1 for task in tasks.values() if task.get("status") == "failed")
        finished = completed + failed

        return (completed / finished * 100) if finished > 0 else 100.0

    def _analyze_errors(self, tasks: Dict) -> Dict:
        """Analyze error patterns in failed tasks"""
        failed_tasks = [
            task for task in tasks.values() if task.get("status") == "failed"
        ]

        error_analysis = {
            "total_failures": len(failed_tasks),
            "common_errors": defaultdict(int),
            "failed_by_type": defaultdict(int),
            "failed_by_phase": defaultdict(int),
        }

        for task in failed_tasks:
            # Analyze error messages
            error = task.get("error", "")
            if error:
                # Extract common error patterns
                if "timeout" in error.lower():
                    error_analysis["common_errors"]["timeout"] += 1
                elif "permission" in error.lower():
                    error_analysis["common_errors"]["permission"] += 1
                elif "connection" in error.lower():
                    error_analysis["common_errors"]["connection"] += 1
                else:
                    error_analysis["common_errors"]["other"] += 1

            # Count by type and phase
            task_type = task.get("task_type", "unknown")
            phase = task.get("phase_id", "unknown")

            error_analysis["failed_by_type"][task_type] += 1
            error_analysis["failed_by_phase"][phase] += 1

        # Convert to regular dicts
        error_analysis["common_errors"] = dict(error_analysis["common_errors"])
        error_analysis["failed_by_type"] = dict(error_analysis["failed_by_type"])
        error_analysis["failed_by_phase"] = dict(error_analysis["failed_by_phase"])

        return error_analysis

    def _analyze_resource_usage(self, tasks: Dict) -> Dict:
        """Analyze resource usage patterns"""
        usage_analysis = {
            "total_api_cost": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "cost_by_type": defaultdict(float),
            "tokens_by_type": defaultdict(lambda: {"input": 0, "output": 0}),
        }

        for task in tasks.values():
            result = task.get("result", {})
            if isinstance(result, dict):
                # Extract cost information
                cost = result.get("total_cost_usd", 0.0)
                usage = result.get("usage", {})

                if cost:
                    usage_analysis["total_api_cost"] += cost
                    task_type = task.get("task_type", "unknown")
                    usage_analysis["cost_by_type"][task_type] += cost

                if usage:
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)

                    usage_analysis["total_input_tokens"] += input_tokens
                    usage_analysis["total_output_tokens"] += output_tokens

                    task_type = task.get("task_type", "unknown")
                    usage_analysis["tokens_by_type"][task_type]["input"] += input_tokens
                    usage_analysis["tokens_by_type"][task_type][
                        "output"
                    ] += output_tokens

        # Convert to regular dicts
        usage_analysis["cost_by_type"] = dict(usage_analysis["cost_by_type"])
        usage_analysis["tokens_by_type"] = {
            k: dict(v) for k, v in usage_analysis["tokens_by_type"].items()
        }

        return usage_analysis

    def _calculate_hourly_completion_rate(self, tasks: Dict) -> List[Dict]:
        """Calculate completion rate by hour for the last 24 hours"""
        now = time.time()
        hourly_data = []

        for hour_offset in range(24):
            hour_start = now - (hour_offset * 3600)
            hour_end = hour_start + 3600

            completed_in_hour = sum(
                1
                for task in tasks.values()
                if (
                    task.get("end_time", 0) >= hour_start
                    and task.get("end_time", 0) < hour_end
                    and task.get("status") == "completed"
                )
            )

            hourly_data.append(
                {
                    "hour": datetime.fromtimestamp(hour_start).strftime(
                        "%Y-%m-%d %H:00"
                    ),
                    "completions": completed_in_hour,
                }
            )

        return list(reversed(hourly_data))  # Most recent first

    def _get_trending_task_types(self, tasks: Dict) -> List[Dict]:
        """Get trending task types based on recent activity"""
        now = time.time()
        six_hours_ago = now - 21600

        recent_tasks = [
            task for task in tasks.values() if task.get("end_time", 0) > six_hours_ago
        ]

        type_counts = defaultdict(int)
        for task in recent_tasks:
            task_type = task.get("task_type", "unknown")
            type_counts[task_type] += 1

        trending = [
            {"task_type": task_type, "count": count}
            for task_type, count in sorted(
                type_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

        return trending[:10]  # Top 10

    async def get_live_monitoring_data(self) -> Dict:
        """Get comprehensive live monitoring data for dashboard"""
        return {
            "status": await self.get_system_status(),
            "tasks": await self.get_all_tasks(),
            "performance": await self.get_performance_metrics(),
            "analytics": await self.get_task_analytics(),
            "quality": await self.get_quality_report(),
            "timestamp": time.time(),
        }

    async def simulate_task_progress(self):
        """Simulate task progress for testing (development only)"""
        logger.info("Simulating task progress for testing")

        # This would trigger fake progress updates for development
        # In production, this should be disabled or protected
        pass
