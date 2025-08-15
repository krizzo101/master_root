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
class SecurityConfig:
    """Security configuration"""
    
    default_permission_mode: str = "bypassPermissions"  # Full capabilities in sandbox
    allow_bypass_permissions: bool = True  # Enabled for sandbox environment
    allowed_directories: Optional[list] = None  # Restrict execution to specific directories
    max_file_size: int = 10_000_000  # 10MB max file size
    
    def validate_permission_mode(self, mode: str) -> str:
        """Validate and potentially override permission mode"""
        if mode == "bypassPermissions" and not self.allow_bypass_permissions:
            # Override dangerous permission mode unless explicitly allowed
            return "default"
        return mode


@dataclass
class ServerConfig:
    """Main server configuration with validation"""

    base_timeout: int = 300000  # 5 minutes in ms
    max_timeout: int = 1800000  # 30 minutes in ms
    claude_code_token: Optional[str] = None
    recursion: RecursionLimits = None
    logging: LoggingConfig = None
    security: SecurityConfig = None

    def __post_init__(self):
        if self.recursion is None:
            self.recursion = RecursionLimits()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.security is None:
            self.security = SecurityConfig()
        
        # Validate configuration
        self._validate_config()

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
        
        # Security environment overrides
        if os.getenv("CLAUDE_ALLOW_BYPASS_PERMISSIONS"):
            self.security.allow_bypass_permissions = (
                os.getenv("CLAUDE_ALLOW_BYPASS_PERMISSIONS").lower() == "true"
            )
        if os.getenv("CLAUDE_DEFAULT_PERMISSION_MODE"):
            self.security.default_permission_mode = os.getenv("CLAUDE_DEFAULT_PERMISSION_MODE")
    
    def _validate_config(self):
        """Validate configuration values"""
        # Validate timeouts
        if self.base_timeout <= 0:
            raise ValueError(f"base_timeout must be positive: {self.base_timeout}")
        if self.max_timeout < self.base_timeout:
            raise ValueError(f"max_timeout must be >= base_timeout: {self.max_timeout} < {self.base_timeout}")
        
        # Validate recursion limits
        if self.recursion.max_depth < 0:
            raise ValueError(f"max_depth must be non-negative: {self.recursion.max_depth}")
        if self.recursion.max_concurrent_at_depth <= 0:
            raise ValueError(f"max_concurrent_at_depth must be positive: {self.recursion.max_concurrent_at_depth}")
        if self.recursion.max_total_jobs <= 0:
            raise ValueError(f"max_total_jobs must be positive: {self.recursion.max_total_jobs}")
        
        # Validate permission mode
        valid_modes = {"default", "acceptEdits", "bypassPermissions", "plan"}
        if self.security.default_permission_mode not in valid_modes:
            raise ValueError(f"Invalid default_permission_mode: {self.security.default_permission_mode}")
        
        # Warn about dangerous configuration
        if self.security.allow_bypass_permissions:
            import warnings
            warnings.warn(
                "SECURITY WARNING: allow_bypass_permissions is enabled. "
                "This allows skipping permission prompts which could be dangerous.",
                RuntimeWarning
            )


# Global configuration instance
config = ServerConfig()
