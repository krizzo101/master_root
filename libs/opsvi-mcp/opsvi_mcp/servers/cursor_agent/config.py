"""
Configuration for Cursor Agent MCP Server
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class CursorConfig:
    """Configuration for Cursor Agent integration"""

    # Cursor IDE Configuration
    cursor_executable: str = os.environ.get("CURSOR_EXECUTABLE", "cursor")
    cursor_workspace: str = os.environ.get("CURSOR_WORKSPACE", os.getcwd())
    cursor_profile: Optional[str] = os.environ.get("CURSOR_PROFILE")

    # Communication Configuration
    communication_method: str = os.environ.get(
        "CURSOR_COMM_METHOD", "websocket"
    )  # websocket, file, pipe
    websocket_host: str = os.environ.get("CURSOR_WS_HOST", "localhost")
    websocket_port: int = int(os.environ.get("CURSOR_WS_PORT", "7070"))
    file_watch_dir: str = os.environ.get("CURSOR_WATCH_DIR", ".cursor/agent_requests")
    pipe_path: str = os.environ.get("CURSOR_PIPE_PATH", "/tmp/cursor_agent_pipe")

    # Agent Configuration
    default_agents: List[str] = field(
        default_factory=lambda: [
            "@diagram",
            "@code_review",
            "@documentation",
            "@test",
            "@refactor",
        ]
    )
    custom_agents_dir: str = os.environ.get("CURSOR_CUSTOM_AGENTS", ".cursor/prompts")
    agent_timeout: int = int(os.environ.get("CURSOR_AGENT_TIMEOUT", "60"))

    # Output Configuration
    output_dir: str = os.environ.get("CURSOR_OUTPUT_DIR", ".cursor/agent_outputs")
    inline_rendering: bool = (
        os.environ.get("CURSOR_INLINE_RENDER", "true").lower() == "true"
    )
    format_output: bool = (
        os.environ.get("CURSOR_FORMAT_OUTPUT", "true").lower() == "true"
    )

    # Context Configuration
    include_workspace_context: bool = (
        os.environ.get("CURSOR_INCLUDE_CONTEXT", "true").lower() == "true"
    )
    max_context_files: int = int(os.environ.get("CURSOR_MAX_CONTEXT_FILES", "10"))
    context_file_limit: int = int(
        os.environ.get("CURSOR_CONTEXT_FILE_LIMIT", "5000")
    )  # lines per file

    # Diagram-specific Configuration
    diagram_theme: str = os.environ.get("CURSOR_DIAGRAM_THEME", "high-contrast")
    diagram_format: str = os.environ.get("CURSOR_DIAGRAM_FORMAT", "mermaid")
    diagram_auto_render: bool = (
        os.environ.get("CURSOR_DIAGRAM_AUTO_RENDER", "true").lower() == "true"
    )

    # Security Configuration
    allowed_agents: Optional[List[str]] = None
    blocked_agents: Optional[List[str]] = None
    require_confirmation: bool = (
        os.environ.get("CURSOR_REQUIRE_CONFIRM", "false").lower() == "true"
    )

    def __post_init__(self):
        """Validate and initialize configuration"""

        # Create necessary directories
        os.makedirs(self.file_watch_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.custom_agents_dir, exist_ok=True)

        # Load allowed/blocked agents from environment
        if not self.allowed_agents:
            allowed = os.environ.get("CURSOR_ALLOWED_AGENTS")
            self.allowed_agents = allowed.split(",") if allowed else None

        if not self.blocked_agents:
            blocked = os.environ.get("CURSOR_BLOCKED_AGENTS")
            self.blocked_agents = blocked.split(",") if blocked else []

    def is_agent_allowed(self, agent_name: str) -> bool:
        """Check if an agent is allowed to be invoked"""

        # Check blocked list first
        if self.blocked_agents and agent_name in self.blocked_agents:
            return False

        # Check allowed list if configured
        if self.allowed_agents:
            return agent_name in self.allowed_agents

        # Default to allow
        return True
