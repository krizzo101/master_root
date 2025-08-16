"""
Parallel execution logging infrastructure
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .config import config
from .models import LogEntry, RecursionContext, PerformanceMetrics


class ParallelLogger:
    """Comprehensive logging for parallel Claude Code execution"""

    def __init__(self):
        self.logs_dir = Path(config.logging.logs_dir)
        self.ensure_logs_directory()
        self.log_file = (
            self.logs_dir / f"parallel-execution-{int(datetime.now().timestamp())}.log"
        )
        self.log_level = config.logging.log_level

        # Log level priorities
        self.levels = {
            "TRACE": 0,
            "DEBUG": 10,
            "INFO": 20,
            "WARN": 30,
            "ERROR": 40,
            "RECURSION": 25,
            "PERF": 15,
            "PARALLEL": 15,
            "CHILD_STDOUT": 5,
            "CHILD_STDERR": 5,
        }

        self.current_level = self.levels.get(self.log_level, 20)

    def ensure_logs_directory(self) -> None:
        """Create logs directory if it doesn't exist"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def should_log(self, level: str) -> bool:
        """Check if a log level should be logged"""
        level_priority = self.levels.get(level, 20)

        # Special handling for specific log types
        if level == "RECURSION" and not config.logging.enable_recursion_logging:
            return False
        if level == "PERF" and not config.logging.enable_performance_logging:
            return False
        # Always surface child process outputs when enabled, regardless of base log level
        if level in ("CHILD_STDOUT", "CHILD_STDERR"):
            return config.logging.enable_child_process_logging
        if level == "TRACE" and not getattr(
            config.logging, "enable_trace_logging", False
        ):
            return False

        return level_priority >= self.current_level

    def log(
        self,
        level: str,
        job_id: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a message with structured data"""
        if not self.should_log(level):
            return

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            job_id=job_id,
            message=message,
            data=data,
        )

        # Write to file
        with open(self.log_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": entry.timestamp,
                        "level": entry.level,
                        "job_id": entry.job_id,
                        "message": entry.message,
                        "data": entry.data,
                    }
                )
                + "\n"
            )

        # Write to stderr for MCP compliance
        print(
            f"[{entry.timestamp}] [{level}] [JOB:{job_id}] {message}", file=sys.stderr
        )
        if data:
            print(
                f"[{entry.timestamp}] [{level}] [JOB:{job_id}] DATA: {json.dumps(data, indent=2)}",
                file=sys.stderr,
            )

    def log_recursion(
        self,
        job_id: str,
        event: str,
        context: RecursionContext,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log recursion-specific events"""
        log_data = {
            "depth": context.depth,
            "max_depth": context.max_depth,
            "root_job_id": context.root_job_id,
            "parent_job_id": context.parent_job_id,
            "call_stack_depth": len(context.call_stack),
            "recursion_path": context.recursion_path[-3:],  # Last 3 items
            "is_recursive": context.is_recursive,
        }

        if data:
            log_data.update(data)

        self.log("RECURSION", job_id, f"RECURSION_{event.upper()}", log_data)

        # Warn when approaching limits
        if context.depth >= context.max_depth - 1:
            self.log(
                "WARN",
                job_id,
                "APPROACHING_RECURSION_LIMIT",
                {
                    "depth": context.depth,
                    "max_depth": context.max_depth,
                    "remaining_depth": context.max_depth - context.depth,
                },
            )

    def log_performance(
        self, job_id: str, event: str, metrics: PerformanceMetrics
    ) -> None:
        """Log performance metrics"""
        metrics_data = {
            "job_id": metrics.job_id,
            "start_time": (
                metrics.start_time.isoformat() if metrics.start_time else None
            ),
            "spawn_time": (
                metrics.spawn_time.isoformat() if metrics.spawn_time else None
            ),
            "first_output_time": (
                metrics.first_output_time.isoformat()
                if metrics.first_output_time
                else None
            ),
            "completion_time": (
                metrics.completion_time.isoformat() if metrics.completion_time else None
            ),
            "total_duration": metrics.total_duration,
            "spawn_delay": metrics.spawn_delay,
            "execution_duration": metrics.execution_duration,
            "output_size": metrics.output_size,
            "error_count": metrics.error_count,
        }

        self.log("PERF", job_id, f"PERFORMANCE_{event.upper()}", metrics_data)

    def log_parallel(
        self, job_id: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log parallel execution events"""
        self.log("PARALLEL", job_id, message, data)

    def log_debug(
        self, job_id: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log debug information"""
        self.log("DEBUG", job_id, message, data)

    def log_trace(
        self, job_id: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log ultra-detailed trace information"""
        self.log("TRACE", job_id, message, data)

    def log_error(
        self,
        job_id: str,
        message: str,
        error: Optional[Exception] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log error with exception details"""
        error_data = data or {}
        if error:
            error_data["error_type"] = type(error).__name__
            error_data["error_message"] = str(error)
            error_data["error_traceback"] = self._get_traceback(error)
        self.log("ERROR", job_id, message, error_data)

    def log_child_output(self, job_id: str, output_type: str, output: str) -> None:
        """Log child process output with chunking for large outputs"""
        if not output:
            return

        # Chunk large outputs
        max_chunk_size = 4096
        if len(output) > max_chunk_size:
            chunks = [
                output[i : i + max_chunk_size]
                for i in range(0, len(output), max_chunk_size)
            ]
            for i, chunk in enumerate(chunks):
                self.log(
                    f"CHILD_{output_type.upper()}",
                    job_id,
                    f"Output chunk {i+1}/{len(chunks)}",
                    {
                        "chunk": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "total_size": len(output),
                    },
                )
        else:
            self.log(
                f"CHILD_{output_type.upper()}",
                job_id,
                f"{output_type} output",
                {"output": output},
            )

    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback from exception"""
        import traceback

        return "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )


# Global logger instance
logger = ParallelLogger()
