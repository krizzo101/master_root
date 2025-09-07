"""Configuration for Claude Code Clone."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ClaudeCodeConfig(BaseSettings):
    """Configuration for Claude Code Clone."""

    # LLM Provider Configuration
    provider: str = Field(
        default="openai", description="LLM provider (openai, anthropic, perplexity)"
    )
    model: str = Field(default="gpt-5-mini", description="Model to use (o4-mini, o3, gpt-5-mini, gpt-5, gpt-5-nano)")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    organization: Optional[str] = Field(
        default=None, description="Organization ID (OpenAI)"
    )

    # Execution Configuration
    working_directory: str = Field(
        default=".", description="Working directory for operations"
    )
    max_tokens: int = Field(default=4000, description="Maximum tokens per request")
    temperature: float = Field(default=0.1, description="Temperature for generation")
    timeout: int = Field(default=300, description="Request timeout in seconds")

    # File Operations
    allowed_file_extensions: List[str] = Field(
        default=[
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".swift",
            ".kt",
            ".scala",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            ".sql",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".xml",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".md",
            ".txt",
            ".rst",
            ".tex",
            ".latex",
        ],
        description="Allowed file extensions for operations",
    )
    max_file_size: int = Field(
        default=1024 * 1024, description="Maximum file size in bytes (1MB)"
    )

    # Security Configuration
    enable_file_operations: bool = Field(
        default=True, description="Enable file read/write operations"
    )
    enable_shell_operations: bool = Field(
        default=False, description="Enable shell command execution"
    )
    allowed_shell_commands: List[str] = Field(
        default=[], description="Allowed shell commands"
    )

    # Streaming Configuration
    enable_streaming: bool = Field(
        default=True, description="Enable streaming responses"
    )
    stream_chunk_size: int = Field(
        default=1024, description="Stream chunk size in bytes"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")

    # Advanced Configuration
    custom_instructions: Optional[str] = Field(
        default=None, description="Custom system instructions"
    )
    context_window: int = Field(default=128000, description="Context window size")

    class Config:
        env_prefix = "CLAUDE_CODE_"
        env_file = ".env"
        case_sensitive = False
