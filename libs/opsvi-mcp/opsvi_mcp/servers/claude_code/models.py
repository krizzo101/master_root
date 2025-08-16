"""
Data models for Claude Code MCP Server
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status"""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class RecursionContext:
    """Tracks recursion state for a job"""

    job_id: str
    parent_job_id: Optional[str] = None
    depth: int = 0
    max_depth: int = 3
    call_stack: List[str] = field(default_factory=list)
    root_job_id: str = ""
    recursion_path: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    is_recursive: bool = False
    task: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance tracking for jobs"""

    job_id: str
    start_time: datetime = field(default_factory=datetime.now)
    spawn_time: Optional[datetime] = None
    first_output_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    spawn_delay: Optional[float] = None
    execution_duration: Optional[float] = None
    output_size: Optional[int] = None
    error_count: int = 0


@dataclass
class ClaudeJob:
    """Represents a Claude Code execution job"""

    id: str
    task: str
    status: JobStatus = JobStatus.RUNNING
    process: Optional[Any] = None  # asyncio.subprocess.Process instance
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    cwd: Optional[str] = None
    output_format: str = "json"
    permission_mode: str = "default"  # Changed from bypassPermissions for security
    verbose: bool = False
    recursion_context: Optional[RecursionContext] = None
    parent_job_id: Optional[str] = None
    stdout_buffer: str = ""
    stderr_buffer: str = ""
    env: Optional[Dict[str, str]] = None  # Custom environment variables
    model: Optional[str] = None  # Model to use (e.g., 'sonnet', 'opus')
    mcp_config_path: Optional[str] = None  # Path to temporary MCP config file


@dataclass
class LogEntry:
    """Log entry structure"""

    timestamp: str
    level: Literal[
        "ERROR",
        "WARN",
        "INFO",
        "DEBUG",
        "TRACE",
        "RECURSION",
        "PERF",
        "PARALLEL",
        "CHILD_STDOUT",
        "CHILD_STDERR",
    ]
    job_id: str
    message: str
    data: Optional[Dict[str, Any]] = None
    call_depth: Optional[int] = None
    parent_job_id: Optional[str] = None


@dataclass
class DashboardData:
    """Dashboard metrics and statistics"""

    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    average_duration: float
    parallel_efficiency: float
    nested_depth: int
    system_load: float
    recursion_stats: Dict[str, Any]
    job_details: Optional[List[Dict[str, Any]]] = None
