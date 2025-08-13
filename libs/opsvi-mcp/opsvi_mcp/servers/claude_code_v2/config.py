"""
Configuration for Claude Code V2 Server
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerConfig:
    """Configuration for the Claude Code V2 MCP Server"""

    # API Configuration
    claude_token: str = os.environ.get("CLAUDE_CODE_TOKEN", "")

    # Paths
    python_path: str = os.environ.get("PYTHONPATH", "/home/opsvi/master_root/libs")
    default_results_dir: str = os.environ.get(
        "CLAUDE_RESULTS_DIR", "/tmp/claude_results"
    )

    # Execution limits
    max_concurrent_first_level: int = int(
        os.environ.get("CLAUDE_MAX_CONCURRENT_L1", "10")
    )
    max_recursion_depth: int = int(os.environ.get("CLAUDE_MAX_RECURSION", "3"))
    default_timeout: int = int(os.environ.get("CLAUDE_DEFAULT_TIMEOUT", "600"))

    # Child management
    enable_child_management: bool = (
        os.environ.get("CLAUDE_ENABLE_CHILDREN", "true") == "true"
    )
    child_timeout_ratio: float = float(
        os.environ.get("CLAUDE_CHILD_TIMEOUT_RATIO", "0.5")
    )

    # Logging
    log_level: str = os.environ.get("CLAUDE_LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.environ.get("CLAUDE_LOG_FILE")

    # Result management
    auto_cleanup_age_hours: int = int(os.environ.get("CLAUDE_CLEANUP_HOURS", "24"))
    compress_results: bool = (
        os.environ.get("CLAUDE_COMPRESS_RESULTS", "false") == "true"
    )

    def __post_init__(self):
        """Validate and create necessary directories"""

        # Ensure results directory exists
        os.makedirs(self.default_results_dir, exist_ok=True)

        # Validate token
        if not self.claude_token:
            raise ValueError("CLAUDE_CODE_TOKEN environment variable is required")
