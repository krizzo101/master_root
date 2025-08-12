"""
Logging Configuration for Smart Decomposition Architecture

Intelligent log decomposition with targeted investigation capabilities.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
import re
from typing import Dict, Optional

from pydantic import BaseModel


class LogLevel(str, Enum):
    """Log levels for different output targets"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """Intelligent log decomposition categories"""

    CONSOLE = "console"  # User-friendly progress
    DEBUG = "debug"  # Comprehensive technical details
    API = "api"  # External API calls and responses
    WORKFLOW = "workflow"  # DAG execution and agent coordination
    PERFORMANCE = "performance"  # Timing and resource metrics
    COMPLEXITY = "complexity"  # Decision-making transparency
    ERROR = "error"  # Failures, exceptions, recovery
    AUDIT = "audit"  # Security and compliance events


@dataclass
class LogFileConfig:
    """Configuration for individual log files"""

    category: LogCategory
    filename: str
    level: LogLevel
    max_size_mb: int = 100
    backup_count: int = 5
    format_type: str = "json"  # json or text


class LogConfig(BaseModel):
    """Comprehensive logging configuration"""

    # Base configuration - logs in app root, not project root
    log_dir: Path = Path(__file__).parent.parent.parent / "logs"
    session_id: Optional[str] = None

    # Console configuration
    console_level: LogLevel = LogLevel.INFO
    console_rich: bool = True
    console_progress: bool = True

    # File logging levels
    debug_level: LogLevel = LogLevel.DEBUG
    api_level: LogLevel = LogLevel.DEBUG
    workflow_level: LogLevel = LogLevel.INFO
    performance_level: LogLevel = LogLevel.INFO
    complexity_level: LogLevel = LogLevel.INFO
    error_level: LogLevel = LogLevel.WARNING
    audit_level: LogLevel = LogLevel.INFO

    # Advanced options
    include_stack_traces: bool = True
    truncate_prompts_console: int = 200  # Chars for console output
    full_prompts_in_api_log: bool = True
    correlation_tracking: bool = True

    def model_post_init(self, __context):
        """Initialize session-specific configurations"""
        if not self.session_id:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Note: log directory creation moved to LoggerFactory to allow config updates first

    def get_log_files(self) -> Dict[LogCategory, LogFileConfig]:
        """Get configuration for all log files"""
        session_prefix = f"oamat_smart_{self.session_id}"

        return {
            LogCategory.DEBUG: LogFileConfig(
                category=LogCategory.DEBUG,
                filename=f"{session_prefix}_debug.jsonl",
                level=self.debug_level,
            ),
            LogCategory.API: LogFileConfig(
                category=LogCategory.API,
                filename=f"{session_prefix}_api.jsonl",
                level=self.api_level,
            ),
            LogCategory.WORKFLOW: LogFileConfig(
                category=LogCategory.WORKFLOW,
                filename=f"{session_prefix}_workflow.jsonl",
                level=self.workflow_level,
            ),
            LogCategory.PERFORMANCE: LogFileConfig(
                category=LogCategory.PERFORMANCE,
                filename=f"{session_prefix}_performance.jsonl",
                level=self.performance_level,
            ),
            LogCategory.COMPLEXITY: LogFileConfig(
                category=LogCategory.COMPLEXITY,
                filename=f"{session_prefix}_complexity.jsonl",
                level=self.complexity_level,
            ),
            LogCategory.ERROR: LogFileConfig(
                category=LogCategory.ERROR,
                filename=f"{session_prefix}_error.jsonl",
                level=self.error_level,
            ),
            LogCategory.AUDIT: LogFileConfig(
                category=LogCategory.AUDIT,
                filename=f"{session_prefix}_audit.jsonl",
                level=self.audit_level,
            ),
        }

    def get_console_format(self) -> str:
        """Get console logging format"""
        return "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    def get_file_format(self) -> str:
        """Get file logging format (for text files)"""
        return (
            "%(asctime)s [%(levelname)s] %(name)s [%(correlation_id)s] "
            "%(pathname)s:%(lineno)d - %(message)s"
        )

    # Enhanced logging support methods

    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Sanitize names for filesystem compatibility by removing/replacing invalid characters.

        Args:
            name: The name to sanitize (e.g., agent role, component name)

        Returns:
            Sanitized name safe for filesystem paths
        """
        if not name:
            return "unknown"

        # Replace problematic characters with underscores or safe alternatives
        sanitized = re.sub(
            r'[<>:"/\\|?*\s]', "_", name
        )  # Replace invalid filesystem chars and spaces
        sanitized = re.sub(r"[&]", "and", sanitized)  # Replace & with 'and'
        sanitized = re.sub(r"[+]", "plus", sanitized)  # Replace + with 'plus'
        sanitized = re.sub(r"[%]", "percent", sanitized)  # Replace % with 'percent'
        sanitized = re.sub(
            r"_{2,}", "_", sanitized
        )  # Replace multiple underscores with single
        sanitized = sanitized.strip("_")  # Remove leading/trailing underscores

        # Ensure we have a valid name
        if not sanitized:
            return "unknown"

        return sanitized

    def get_enhanced_log_filename(
        self, log_type: str, specific_name: str = None
    ) -> str:
        """Get session-based filename for enhanced logging types"""
        if specific_name:
            sanitized_name = self.sanitize_name(specific_name)
            return f"{log_type}_{sanitized_name}_{self.session_id}.jsonl"
        else:
            return f"{log_type}_{self.session_id}.jsonl"

    def get_tool_log_filename(self, tool_name: str) -> str:
        """Get filename for tool-specific logs"""
        return self.get_enhanced_log_filename("tool", tool_name)

    def get_agent_log_filename(self, agent_role: str) -> str:
        """Get filename for agent-specific logs"""
        return self.get_enhanced_log_filename("agent", agent_role)

    def get_component_log_filename(self, component: str) -> str:
        """Get filename for component-specific logs"""
        return self.get_enhanced_log_filename("component", component)

    def get_audit_log_filename(self, audit_type: str) -> str:
        """Get filename for audit-specific logs"""
        return self.get_enhanced_log_filename("audit", audit_type)

    def get_session_log_directory(self) -> Path:
        """Get the session-specific log directory"""
        session_dir = self.log_dir / f"session_{self.session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir


# Default configuration instance
default_config = LogConfig()
