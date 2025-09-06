"""
Configuration settings for Enhanced Chat Monitor.

Manages all configuration options, defaults, and environment-specific settings
for the agent collaboration monitoring system.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Settings:
    """Configuration settings for Enhanced Chat Monitor."""

    # Core paths and directories
    chat_logs_dir: str = "/home/opsvi/.claude/projects/-home-opsvi-master-root"
    output_dir: str = "/tmp/enhanced-chat-monitor"

    # Monitoring intervals (seconds)
    file_poll_interval: float = 0.5
    analysis_update_interval: float = 2.0
    dashboard_refresh_interval: float = 1.0
    cleanup_interval: float = 30.0

    # Session management
    session_timeout: float = 300.0  # 5 minutes
    recent_events_window: float = 60.0  # 1 minute

    # Collaboration detection thresholds
    collaboration_log_threshold: int = 5  # Minimum significance to log
    workspace_conflict_threshold: float = 2.0  # Seconds for conflict detection
    communication_pattern_threshold: int = 3  # Min events to identify pattern

    # Display settings
    max_sessions_display: int = 10
    max_events_display: int = 20
    refresh_rate_hz: int = 2

    # Analysis settings
    network_analysis_depth: int = 3  # Levels of agent relationships to track
    workspace_history_size: int = 100  # File access events to remember

    # Focus mode settings
    focus_mode: str = "all"  # all, communication, workspace, handoffs

    # Output and logging
    verbose: bool = False
    save_on_exit: bool = True
    export_format: str = "json"  # json, csv

    # Advanced features
    enable_predictive_analysis: bool = True
    enable_performance_metrics: bool = True
    enable_historical_patterns: bool = True

    @classmethod
    def load(cls, config_path: Optional[str] = None, **overrides) -> "Settings":
        """
        Load settings from configuration file with environment variable and override support.

        Args:
            config_path: Optional path to configuration file
            **overrides: Direct setting overrides

        Returns:
            Configured Settings instance
        """
        settings = cls()

        # Load from config file if provided
        if config_path and Path(config_path).exists():
            settings = cls._load_from_file(config_path)

        # Apply environment variable overrides
        settings = settings._apply_env_overrides()

        # Apply direct overrides
        for key, value in overrides.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        # Validate and prepare settings
        settings._validate_and_prepare()

        return settings

    @classmethod
    def _load_from_file(cls, config_path: str) -> "Settings":
        """Load settings from JSON configuration file."""
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)

            # Create settings instance with config data
            settings = cls()
            for key, value in config_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            return settings

        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
            return cls()

    def _apply_env_overrides(self) -> "Settings":
        """Apply environment variable overrides."""
        env_mapping = {
            "CHAT_LOGS_DIR": "chat_logs_dir",
            "MONITOR_OUTPUT_DIR": "output_dir",
            "MONITOR_VERBOSE": ("verbose", lambda x: x.lower() == "true"),
            "MONITOR_FOCUS": "focus_mode",
            "MONITOR_SESSION_TIMEOUT": ("session_timeout", float),
            "MONITOR_POLL_INTERVAL": ("file_poll_interval", float),
        }

        for env_var, setting_info in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                if isinstance(setting_info, tuple):
                    setting_name, converter = setting_info
                    try:
                        setattr(self, setting_name, converter(env_value))
                    except (ValueError, TypeError) as e:
                        print(
                            f"Warning: Invalid environment variable {env_var}={env_value}: {e}"
                        )
                else:
                    setattr(self, setting_info, env_value)

        return self

    def _validate_and_prepare(self):
        """Validate settings and prepare derived configurations."""
        # Ensure directories exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Auto-detect chat logs directory based on current location
        self.chat_logs_dir = self._find_chat_logs_directory()

        # Validate intervals
        if self.file_poll_interval <= 0:
            self.file_poll_interval = 0.5
        if self.dashboard_refresh_interval <= 0:
            self.dashboard_refresh_interval = 1.0

        # Validate focus mode
        valid_focus_modes = {"all", "communication", "workspace", "handoffs"}
        if self.focus_mode not in valid_focus_modes:
            print(f"Warning: Invalid focus mode '{self.focus_mode}', using 'all'")
            self.focus_mode = "all"

        # Adjust settings based on focus mode
        if self.focus_mode == "communication":
            self.communication_pattern_threshold = 2
            self.max_events_display = 30
        elif self.focus_mode == "workspace":
            self.workspace_conflict_threshold = 1.0
            self.workspace_history_size = 200
        elif self.focus_mode == "handoffs":
            self.collaboration_log_threshold = 3
            self.network_analysis_depth = 5

    def _find_chat_logs_directory(self) -> str:
        """
        Intelligently find the chat logs directory based on current working directory
        and common Claude Code project patterns.
        """
        current_dir = Path.cwd()

        # Strategy 1: Check if current directory looks like master_root
        if self._looks_like_master_root(current_dir):
            project_name = current_dir.name
            claude_projects_path = (
                Path.home() / ".claude" / "projects" / f"-home-opsvi-{project_name}"
            )
            if claude_projects_path.exists():
                return str(claude_projects_path)

        # Strategy 2: Look for master_root in current path hierarchy
        for parent in [current_dir] + list(current_dir.parents):
            if self._looks_like_master_root(parent):
                project_name = parent.name
                claude_projects_path = (
                    Path.home() / ".claude" / "projects" / f"-home-opsvi-{project_name}"
                )
                if claude_projects_path.exists():
                    return str(claude_projects_path)

        # Strategy 3: Try common paths based on environment
        alternative_paths = [
            "/home/opsvi/.claude/projects/-home-opsvi-master-root",  # Most common
            "/home/opsvi/.claude/projects/-home-opsvi-master_root",  # Alternative naming
            "/home/opsvi/.claude/projects",  # Base directory
            os.path.expanduser("~/.claude/projects"),  # User home fallback
        ]

        for alt_path in alternative_paths:
            if Path(alt_path).exists() and list(Path(alt_path).glob("*.jsonl")):
                print(f"📂 Auto-detected chat logs directory: {alt_path}")
                return alt_path

        # Strategy 4: Default fallback with warning
        default_path = "/home/opsvi/.claude/projects/-home-opsvi-master-root"
        print(
            f"⚠️  Could not auto-detect chat logs directory from current location: {current_dir}"
        )
        print(f"📂 Using default: {default_path}")
        print(f"💡 Tip: Run from your project root directory for automatic detection")

        return default_path

    def _looks_like_master_root(self, directory: Path) -> bool:
        """Check if a directory looks like a Claude Code master_root project."""
        if not directory.is_dir():
            return False

        # Look for characteristic files/directories of master_root
        indicators = [
            "CLAUDE.md",
            ".claude",
            "apps",
            "libs",
            ".mcp.json",
            "chat_logs",  # symlink to session logs
        ]

        present_indicators = sum(
            1 for indicator in indicators if (directory / indicator).exists()
        )

        # If 3+ indicators present, likely a master_root project
        return present_indicators >= 3

    def get_focus_settings(self) -> Dict[str, Any]:
        """Get settings specific to current focus mode."""
        focus_configs = {
            "communication": {
                "show_communication_panel": True,
                "show_workspace_panel": False,
                "show_handoffs_panel": False,
                "highlight_communication_events": True,
            },
            "workspace": {
                "show_communication_panel": False,
                "show_workspace_panel": True,
                "show_handoffs_panel": False,
                "highlight_workspace_conflicts": True,
            },
            "handoffs": {
                "show_communication_panel": False,
                "show_workspace_panel": False,
                "show_handoffs_panel": True,
                "highlight_handoff_chains": True,
            },
            "all": {
                "show_communication_panel": True,
                "show_workspace_panel": True,
                "show_handoffs_panel": True,
                "highlight_all_events": True,
            },
        }

        return focus_configs.get(self.focus_mode, focus_configs["all"])

    def save(self, config_path: str):
        """Save current settings to configuration file."""
        try:
            # Convert settings to dictionary
            settings_dict = {}
            for key, value in self.__dict__.items():
                if not key.startswith("_"):
                    settings_dict[key] = value

            # Save to file
            with open(config_path, "w") as f:
                json.dump(settings_dict, f, indent=2)

        except Exception as e:
            print(f"Error saving configuration: {e}")

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"Settings(focus_mode={self.focus_mode}, chat_logs_dir={self.chat_logs_dir})"
