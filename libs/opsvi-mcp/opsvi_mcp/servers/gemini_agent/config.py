"""
Configuration for Gemini Agent MCP Server
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class GeminiConfig:
    """Configuration for Gemini Agent server"""

    # API Configuration
    api_key: str = field(default_factory=lambda: os.environ.get("GEMINI_API_KEY", ""))
    model: str = (
        "gemini-2.5-pro"  # Default model preference; CLI reads gemini-settings.json
    )

    # Context and Limits
    context_window: int = 1_000_000  # 1M tokens
    max_requests_per_minute: int = 60
    max_requests_per_day: int = 1000

    # Execution Settings
    timeout_seconds: int = 300  # 5 minutes default
    enable_web_search: bool = True
    enable_file_operations: bool = True
    enable_shell_commands: bool = True

    # Working Directory
    working_directory: str = field(
        default_factory=lambda: os.environ.get(
            "GEMINI_WORKING_DIR", "/home/opsvi/master_root"
        )
    )

    # MCP Settings
    enable_mcp_servers: bool = True
    mcp_servers_config: Optional[str] = field(
        default_factory=lambda: os.environ.get(
            "GEMINI_MCP_CONFIG", "gemini-settings.json"
        )
    )

    # Safety Settings
    allow_file_modification: bool = True
    allow_shell_execution: bool = True
    allowed_directories: List[str] = field(
        default_factory=lambda: ["/home/opsvi/master_root", "/tmp"]
    )

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "/tmp/gemini_agent.log"

    # ReAct Loop Settings
    max_iterations: int = 10
    enable_reasoning: bool = True
    enable_self_correction: bool = True

    # Integration Settings
    github_token: Optional[str] = field(
        default_factory=lambda: os.environ.get("GITHUB_TOKEN")
    )
    google_cloud_project: Optional[str] = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT")
    )

    # Cache Settings
    enable_cache: bool = True
    cache_directory: str = "/tmp/gemini_cache"
    cache_ttl_seconds: int = 3600  # 1 hour

    def validate(self) -> bool:
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")

        # Ensure working directory exists
        work_dir = Path(self.working_directory)
        if not work_dir.exists():
            work_dir.mkdir(parents=True, exist_ok=True)

        # Ensure cache directory exists if caching enabled
        if self.enable_cache:
            cache_dir = Path(self.cache_directory)
            cache_dir.mkdir(parents=True, exist_ok=True)

        return True

    def to_cli_args(self) -> List[str]:
        """Convert config to Gemini CLI arguments"""
        args = []

        if self.model:
            args.extend(["--model", self.model])

        # Note: Gemini CLI doesn't have direct web search flag
        # It's enabled through MCP servers in the config

        # Gemini CLI doesn't use --config, settings are in gemini-settings.json
        # which is loaded automatically from the project root

        return args

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Create config from environment variables"""
        return cls()
