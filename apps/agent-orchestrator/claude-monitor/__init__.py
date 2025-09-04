"""
Claude Monitor Package

Real-time monitoring and data collection for Claude orchestrator systems.
"""

from .orchestrator.data_collector import (
    DataCollector,
    OrchestratorState,
    ProcessMetrics,
    SessionMetrics,
    TaskMetrics,
    collect_session_metrics,
    collect_task_metrics,
    finish_session_metrics,
    finish_task_metrics,
    get_global_collector,
)

__version__ = "1.0.0"
__all__ = [
    "DataCollector",
    "ProcessMetrics",
    "SessionMetrics",
    "TaskMetrics",
    "OrchestratorState",
    "get_global_collector",
    "collect_task_metrics",
    "finish_task_metrics",
    "collect_session_metrics",
    "finish_session_metrics",
]
