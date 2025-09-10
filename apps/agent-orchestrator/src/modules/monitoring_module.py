#!/usr/bin/env python3
"""
Monitoring Module for UnifiedOrchestrator
Provides real-time monitoring and health checks for agent tasks
"""

import asyncio
import json
import logging
import psutil
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from ..unified.orchestrator_module import OrchestratorModule, ModuleConfig

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class TaskMetrics:
    """Metrics for a single task"""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "pending"
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    error_count: int = 0
    retry_count: int = 0
    health_checks: List[Dict] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    @property
    def avg_cpu(self) -> float:
        """Average CPU usage"""
        return sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
    
    @property
    def avg_memory(self) -> float:
        """Average memory usage"""
        return sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
    
    @property
    def health_status(self) -> HealthStatus:
        """Determine health status from checks"""
        if not self.health_checks:
            return HealthStatus.UNKNOWN
            
        latest_check = self.health_checks[-1]
        return HealthStatus(latest_check.get("status", "unknown"))


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    active_tasks: int
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_usage": self.disk_usage,
            "active_tasks": self.active_tasks,
            "pending_tasks": self.pending_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks
        }


class MonitoringModule(OrchestratorModule):
    """
    Module implementing monitoring and health checks for tasks.
    Tracks resource usage, performance metrics, and system health.
    """
    
    def __init__(self, orchestrator, config: ModuleConfig = None):
        super().__init__(orchestrator, config)
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.system_metrics: deque = deque(maxlen=1000)  # Keep last 1000 samples
        self.alerts: List[Dict] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self.logs_dir = None
        self.check_interval = config.config.get("check_interval", 30.0) if config else 30.0
        
        # Thresholds for alerts
        self.thresholds = {
            "cpu_critical": 90.0,
            "cpu_warning": 70.0,
            "memory_critical": 90.0,
            "memory_warning": 70.0,
            "task_duration_warning": 300.0,  # 5 minutes
            "task_duration_critical": 600.0,  # 10 minutes
            "error_rate_warning": 0.1,  # 10% error rate
            "error_rate_critical": 0.25  # 25% error rate
        }
        
        # Performance tracking
        self.performance_stats = defaultdict(lambda: {
            "count": 0,
            "total_duration": 0,
            "min_duration": float('inf'),
            "max_duration": 0,
            "errors": 0
        })
    
    @property
    def name(self) -> str:
        return "monitoring"
    
    @property
    def description(self) -> str:
        return "Real-time monitoring and health checks for agent tasks"
    
    async def _initialize(self):
        """Initialize monitoring module"""
        # Setup logs directory
        self.logs_dir = self.orchestrator.output_dir / "monitoring_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Start monitoring background task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"Monitoring module initialized with check interval: {self.check_interval}s")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Check task health
                await self._check_task_health()
                
                # Process alerts
                await self._process_alerts()
                
                # Save monitoring snapshot
                await self._save_monitoring_snapshot()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _collect_system_metrics(self):
        """Collect system-wide metrics"""
        try:
            # Get task counts by status
            task_statuses = self._count_task_statuses()
            
            # Collect system metrics
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_usage=psutil.disk_usage('/').percent,
                active_tasks=task_statuses.get("running", 0),
                pending_tasks=task_statuses.get("pending", 0),
                completed_tasks=task_statuses.get("completed", 0),
                failed_tasks=task_statuses.get("failed", 0)
            )
            
            self.system_metrics.append(metrics)
            
            # Check for system-level alerts
            if metrics.cpu_percent > self.thresholds["cpu_critical"]:
                await self._create_alert("system", "critical", 
                                        f"CPU usage critical: {metrics.cpu_percent:.1f}%")
            elif metrics.cpu_percent > self.thresholds["cpu_warning"]:
                await self._create_alert("system", "warning",
                                        f"CPU usage high: {metrics.cpu_percent:.1f}%")
                                        
            if metrics.memory_percent > self.thresholds["memory_critical"]:
                await self._create_alert("system", "critical",
                                        f"Memory usage critical: {metrics.memory_percent:.1f}%")
            elif metrics.memory_percent > self.thresholds["memory_warning"]:
                await self._create_alert("system", "warning",
                                        f"Memory usage high: {metrics.memory_percent:.1f}%")
                                        
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _count_task_statuses(self) -> Dict[str, int]:
        """Count tasks by status"""
        statuses = defaultdict(int)
        for metrics in self.task_metrics.values():
            statuses[metrics.status] += 1
        return dict(statuses)
    
    async def _check_task_health(self):
        """Check health of running tasks"""
        for task_id, metrics in self.task_metrics.items():
            if metrics.status in ["completed", "failed"]:
                continue
                
            # Check task duration
            duration = metrics.duration
            if duration:
                if duration > self.thresholds["task_duration_critical"]:
                    await self._create_alert(task_id, "critical",
                                            f"Task running too long: {duration:.1f}s")
                    metrics.health_checks.append({
                        "timestamp": datetime.now().isoformat(),
                        "status": "critical",
                        "reason": "excessive_duration"
                    })
                elif duration > self.thresholds["task_duration_warning"]:
                    await self._create_alert(task_id, "warning",
                                            f"Task duration warning: {duration:.1f}s")
                    metrics.health_checks.append({
                        "timestamp": datetime.now().isoformat(),
                        "status": "warning",
                        "reason": "long_duration"
                    })
                else:
                    metrics.health_checks.append({
                        "timestamp": datetime.now().isoformat(),
                        "status": "healthy",
                        "reason": "normal"
                    })
            
            # Check resource usage for the task
            if metrics.cpu_usage:
                avg_cpu = metrics.avg_cpu
                if avg_cpu > self.thresholds["cpu_warning"]:
                    await self._create_alert(task_id, "warning",
                                            f"Task CPU usage high: {avg_cpu:.1f}%")
    
    async def _create_alert(self, source: str, level: str, message: str):
        """Create an alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "level": level,
            "message": message,
            "processed": False
        }
        
        self.alerts.append(alert)
        logger.warning(f"Alert created: [{level}] {source}: {message}")
        
        # Save alert to file
        alert_file = self.logs_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with alert_file.open('a') as f:
            f.write(json.dumps(alert) + '\n')
    
    async def _process_alerts(self):
        """Process pending alerts"""
        unprocessed = [a for a in self.alerts if not a["processed"]]
        
        if unprocessed:
            # Group alerts by level
            by_level = defaultdict(list)
            for alert in unprocessed:
                by_level[alert["level"]].append(alert)
                alert["processed"] = True
            
            # Log summary
            if by_level["critical"]:
                logger.critical(f"{len(by_level['critical'])} critical alerts")
            if by_level["warning"]:
                logger.warning(f"{len(by_level['warning'])} warning alerts")
    
    async def _save_monitoring_snapshot(self):
        """Save current monitoring state to file"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": self.system_metrics[-1].to_dict() if self.system_metrics else None,
            "task_count": len(self.task_metrics),
            "task_statuses": self._count_task_statuses(),
            "active_alerts": len([a for a in self.alerts if not a["processed"]]),
            "performance_summary": dict(self.performance_stats)
        }
        
        snapshot_file = self.logs_dir / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        snapshot_file.write_text(json.dumps(snapshot, indent=2, default=str))
    
    def start_task_monitoring(self, task: 'AgentTask'):
        """Start monitoring a task"""
        if task.task_id not in self.task_metrics:
            self.task_metrics[task.task_id] = TaskMetrics(
                task_id=task.task_id,
                start_time=datetime.now(),
                status="running"
            )
            logger.debug(f"Started monitoring task: {task.task_id}")
    
    def update_task_metrics(self, task_id: str, **kwargs):
        """Update metrics for a task"""
        if task_id in self.task_metrics:
            metrics = self.task_metrics[task_id]
            for key, value in kwargs.items():
                if hasattr(metrics, key):
                    setattr(metrics, key, value)
    
    async def pre_task_execution(self, task: 'AgentTask'):
        """Start monitoring before task execution"""
        self.start_task_monitoring(task)
        
        # Update task health status if available
        if hasattr(task, 'health_status'):
            task.health_status = "monitoring"
    
    async def post_task_execution(self, task: 'AgentTask'):
        """Update monitoring after task execution"""
        if task.task_id in self.task_metrics:
            metrics = self.task_metrics[task.task_id]
            metrics.end_time = datetime.now()
            metrics.status = task.status
            
            # Update performance stats
            task_type = task.task_type if hasattr(task, 'task_type') else "unknown"
            stats = self.performance_stats[task_type]
            stats["count"] += 1
            
            if metrics.duration:
                stats["total_duration"] += metrics.duration
                stats["min_duration"] = min(stats["min_duration"], metrics.duration)
                stats["max_duration"] = max(stats["max_duration"], metrics.duration)
            
            if task.status == "failed":
                stats["errors"] += 1
                metrics.error_count += 1
            
            # Check error rate
            if stats["count"] > 10:  # Only check after enough samples
                error_rate = stats["errors"] / stats["count"]
                if error_rate > self.thresholds["error_rate_critical"]:
                    await self._create_alert(task_type, "critical",
                                            f"High error rate for {task_type}: {error_rate:.1%}")
                elif error_rate > self.thresholds["error_rate_warning"]:
                    await self._create_alert(task_type, "warning",
                                            f"Elevated error rate for {task_type}: {error_rate:.1%}")
    
    async def on_task_success(self, task: 'AgentTask'):
        """Handle successful task completion"""
        if task.task_id in self.task_metrics:
            metrics = self.task_metrics[task.task_id]
            logger.info(f"Task {task.task_id} completed successfully. "
                       f"Duration: {metrics.duration:.2f}s, "
                       f"Avg CPU: {metrics.avg_cpu:.1f}%, "
                       f"Avg Memory: {metrics.avg_memory:.1f}%")
    
    async def on_task_failure(self, task: 'AgentTask'):
        """Handle task failure"""
        if task.task_id in self.task_metrics:
            metrics = self.task_metrics[task.task_id]
            metrics.error_count += 1
            
            # Check if task has been retried
            if hasattr(task, 'retries'):
                metrics.retry_count = task.retries
            
            await self._create_alert(task.task_id, "warning",
                                    f"Task failed after {metrics.retry_count} retries")
    
    def get_task_health(self, task_id: str) -> Dict[str, Any]:
        """Get health status for a specific task"""
        if task_id not in self.task_metrics:
            return {"status": "unknown", "message": "Task not monitored"}
        
        metrics = self.task_metrics[task_id]
        return {
            "status": metrics.health_status.value,
            "duration": metrics.duration,
            "cpu_usage": metrics.avg_cpu,
            "memory_usage": metrics.avg_memory,
            "error_count": metrics.error_count,
            "retry_count": metrics.retry_count,
            "latest_check": metrics.health_checks[-1] if metrics.health_checks else None
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        if not self.system_metrics:
            return {"status": "unknown", "message": "No metrics collected"}
        
        latest = self.system_metrics[-1]
        
        # Determine overall health
        if latest.cpu_percent > self.thresholds["cpu_critical"] or \
           latest.memory_percent > self.thresholds["memory_critical"]:
            status = "critical"
        elif latest.cpu_percent > self.thresholds["cpu_warning"] or \
             latest.memory_percent > self.thresholds["memory_warning"]:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "disk_usage": latest.disk_usage,
            "active_tasks": latest.active_tasks,
            "pending_tasks": latest.pending_tasks,
            "completed_tasks": latest.completed_tasks,
            "failed_tasks": latest.failed_tasks,
            "timestamp": latest.timestamp.isoformat()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics"""
        # Calculate aggregated metrics
        total_tasks = len(self.task_metrics)
        completed_tasks = sum(1 for m in self.task_metrics.values() if m.status == "completed")
        failed_tasks = sum(1 for m in self.task_metrics.values() if m.status == "failed")
        
        avg_duration = 0
        if completed_tasks > 0:
            durations = [m.duration for m in self.task_metrics.values() 
                        if m.duration and m.status == "completed"]
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_tasks_monitored": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "average_duration": avg_duration,
            "total_alerts": len(self.alerts),
            "unprocessed_alerts": len([a for a in self.alerts if not a["processed"]]),
            "system_health": self.get_system_health(),
            "performance_by_type": dict(self.performance_stats)
        }
    
    async def _cleanup(self):
        """Cleanup module resources"""
        # Cancel monitoring task
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Save final report
        if self.logs_dir:
            final_report = {
                "timestamp": datetime.now().isoformat(),
                "metrics": self.get_metrics(),
                "task_metrics": {
                    task_id: {
                        "duration": m.duration,
                        "status": m.status,
                        "cpu_avg": m.avg_cpu,
                        "memory_avg": m.avg_memory,
                        "errors": m.error_count,
                        "retries": m.retry_count
                    }
                    for task_id, m in self.task_metrics.items()
                },
                "alerts": self.alerts
            }
            
            report_file = self.logs_dir / f"final_monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.write_text(json.dumps(final_report, indent=2, default=str))
        
        logger.info("Monitoring module cleanup complete")