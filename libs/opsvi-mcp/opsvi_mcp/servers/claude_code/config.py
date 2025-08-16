"""
Configuration for Claude Code MCP Server
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RecursionLimits:
    """Recursion control configuration"""

    max_depth: int = 3
    max_concurrent_at_depth: int = 5
    max_total_jobs: int = 20
    timeout_multiplier: float = 1.5


@dataclass
class LoggingConfig:
    """Logging configuration"""

    log_level: str = "DEBUG"  # Changed to DEBUG for detailed logging
    enable_performance_logging: bool = True
    enable_child_process_logging: bool = True
    enable_recursion_logging: bool = True
    logs_dir: str = "/home/opsvi/master_root/logs/claude-code"
    enable_trace_logging: bool = True  # Added for ultra-detailed trace logging


@dataclass
class ServerConfig:
    """Main server configuration"""

    base_timeout: int = 300000  # 5 minutes in ms
    max_timeout: int = 1800000  # 30 minutes in ms
    claude_code_token: Optional[str] = None
    recursion: RecursionLimits = None
    logging: LoggingConfig = None

    def __post_init__(self):
        if self.recursion is None:
            self.recursion = RecursionLimits()
        if self.logging is None:
            self.logging = LoggingConfig()

        # Load from environment
        if not self.claude_code_token:
            self.claude_code_token = os.getenv("CLAUDE_CODE_TOKEN")

        # Override from environment if present
        if os.getenv("CLAUDE_MAX_RECURSION_DEPTH"):
            self.recursion.max_depth = int(os.getenv("CLAUDE_MAX_RECURSION_DEPTH"))
        if os.getenv("CLAUDE_MAX_CONCURRENT_AT_DEPTH"):
            self.recursion.max_concurrent_at_depth = int(
                os.getenv("CLAUDE_MAX_CONCURRENT_AT_DEPTH")
            )
        if os.getenv("CLAUDE_MAX_TOTAL_JOBS"):
            self.recursion.max_total_jobs = int(os.getenv("CLAUDE_MAX_TOTAL_JOBS"))
        if os.getenv("CLAUDE_TIMEOUT_MULTIPLIER"):
            self.recursion.timeout_multiplier = float(
                os.getenv("CLAUDE_TIMEOUT_MULTIPLIER")
            )

        if os.getenv("CLAUDE_LOG_LEVEL"):
            self.logging.log_level = os.getenv("CLAUDE_LOG_LEVEL")
        if os.getenv("CLAUDE_PERF_LOGGING"):
            self.logging.enable_performance_logging = (
                os.getenv("CLAUDE_PERF_LOGGING") == "true"
            )
        if os.getenv("CLAUDE_CHILD_LOGGING"):
            self.logging.enable_child_process_logging = (
                os.getenv("CLAUDE_CHILD_LOGGING") == "true"
            )
        if os.getenv("CLAUDE_RECURSION_LOGGING"):
            self.logging.enable_recursion_logging = (
                os.getenv("CLAUDE_RECURSION_LOGGING") != "false"
            )


# Global configuration instance
config = ServerConfig()
