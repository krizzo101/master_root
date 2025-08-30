"""
Configuration management for Tetra orchestrator.
Merges best practices from Razer (Pydantic) and Hecaton (YAML loading).
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TokenConfig(BaseModel):
    """Configuration for token management."""

    pool_size: int = Field(default=15, description="Maximum concurrent tokens")
    encrypted_file: Optional[Path] = Field(default=None, description="Path to encrypted token file")
    tokens: List[str] = Field(default_factory=list, description="Direct token list")
    acquire_timeout: float = Field(default=30.0, description="Timeout for acquiring token")


class GitConfig(BaseModel):
    """Git and worktree configuration."""

    base_branch: str = Field(default="main", description="Base branch for operations")
    branch_prefix: str = Field(default="tetra", description="Prefix for created branches")
    worktree_base: Path = Field(
        default=Path("/tmp/tetra_worktrees"), description="Base directory for worktrees"
    )
    cleanup_on_exit: bool = Field(default=True, description="Clean up worktrees on exit")
    remote_name: str = Field(default="origin", description="Git remote name")


class AIConfig(BaseModel):
    """AI provider configuration."""

    openai_model: str = Field(
        default="gpt-5-mini", description="OpenAI model for agent execution (GPT-5 series approved)"
    )
    openai_timeout: int = Field(default=60, description="OpenAI request timeout")
    openai_max_retries: int = Field(default=3, description="OpenAI retry count")

    claude_bin: Path = Field(default=Path("claude"), description="Claude binary path")
    claude_model: str = Field(default="sonnet", description="Claude model variant")
    claude_permission_mode: str = Field(default="acceptEdits", description="Claude permission mode")
    claude_allowed_tools: str = Field(default="*", description="Allowed Claude tools")
    claude_max_turns: int = Field(default=8, description="Maximum Claude conversation turns")
    claude_timeout: int = Field(default=900, description="Claude execution timeout")

    # Model selection based on task type (following 2025 standards)
    # O3/O4 series for reasoning, GPT-5 series for execution
    reasoning_model: str = Field(
        default="o4-mini", description="Model for reasoning/planning tasks (O3/O4 series)"
    )
    execution_model: str = Field(
        default="gpt-5-mini", description="Model for agent execution tasks (GPT-5 series)"
    )
    routing_strategy: str = Field(default="task_based", description="AI routing strategy")

    @field_validator("claude_bin")
    def resolve_claude_bin(cls, v: Path) -> Path:
        """Resolve Claude binary from environment or path."""
        env_bin = os.environ.get("CLAUDE_BIN")
        if env_bin:
            return Path(env_bin)
        return v


class QualityConfig(BaseModel):
    """Quality gates configuration."""

    compile_check: bool = Field(default=True, description="Run compile checks")
    run_tests: bool = Field(default=True, description="Run test suite")
    auto_fix_attempts: int = Field(default=1, description="Auto-fix attempt count")
    test_command: Optional[str] = Field(default=None, description="Custom test command")
    lint_command: Optional[str] = Field(default=None, description="Custom lint command")
    type_check_command: Optional[str] = Field(default=None, description="Custom type check command")


class WorkspaceConfig(BaseModel):
    """Workspace and directory configuration."""

    workspace_root: Path = Field(
        default=Path("./tetra_workspace"), description="Main workspace directory"
    )
    docs_dir: str = Field(default="docs", description="Documentation directory")
    plan_dir: str = Field(default="plan", description="Planning artifacts directory")
    src_dir: str = Field(default="src", description="Source code directory")
    tests_dir: str = Field(default="tests", description="Test directory")
    reports_dir: str = Field(default="reports", description="Reports directory")
    logs_dir: str = Field(default="logs", description="Logs directory")

    @field_validator("workspace_root")
    def resolve_workspace(cls, v: Path) -> Path:
        """Resolve and create workspace directory."""
        workspace = Path(v).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json/text)")
    correlation_id: bool = Field(default=True, description="Add correlation IDs")
    file_output: bool = Field(default=True, description="Enable file logging")
    console_output: bool = Field(default=True, description="Enable console logging")


class TetraConfig(BaseSettings):
    """Main Tetra configuration combining all subsections."""

    model_config = SettingsConfigDict(
        env_prefix="TETRA_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    tokens: TokenConfig = Field(default_factory=TokenConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    parallelism: int = Field(default=3, description="Maximum parallel operations")
    dry_run: bool = Field(default=False, description="Dry run mode")
    debug: bool = Field(default=False, description="Debug mode")

    @classmethod
    def from_yaml(cls, path: Path) -> "TetraConfig":
        """Load configuration from YAML file."""
        if path.exists():
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TetraConfig":
        """Create configuration from dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to dictionary."""
        return self.model_dump(exclude_none=True)

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        with open(path, "w") as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False)

    def merge(self, other: Dict[str, Any]) -> "TetraConfig":
        """Merge with another configuration dict."""
        current = self.to_dict()

        def deep_merge(base: dict, override: dict) -> dict:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = deep_merge(base[key], value)
                else:
                    base[key] = value
            return base

        merged = deep_merge(current, other)
        return TetraConfig.from_dict(merged)


_config: Optional[TetraConfig] = None


def get_config() -> TetraConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def load_config(config_path: Optional[Path] = None) -> TetraConfig:
    """
    Load configuration from file or environment.
    Priority: Environment > Config File > Defaults
    """
    global _config

    if config_path and config_path.exists():
        _config = TetraConfig.from_yaml(config_path)
    else:
        default_paths = [
            Path.home() / ".tetra" / "config.yaml",
            Path("/etc/tetra/config.yaml"),
            Path("./tetra.yaml"),
        ]

        for path in default_paths:
            if path.exists():
                _config = TetraConfig.from_yaml(path)
                break
        else:
            _config = TetraConfig()

    return _config


def set_config(config: TetraConfig) -> None:
    """Set the global configuration."""
    global _config
    _config = config
