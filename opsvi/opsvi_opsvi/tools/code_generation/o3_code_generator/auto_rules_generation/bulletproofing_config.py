#!/usr/bin/env python3
"""
Bulletproofing Configuration System for Auto Rules Generation

This module provides comprehensive configuration management for user control
and settings in the bulletproofing system.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)


@dataclass
class PerformanceConfig:
    """Performance configuration settings."""

    max_execution_time: float = 30.0  # seconds
    max_memory_usage: float = 512.0  # MB
    max_cpu_usage: float = 80.0  # percent
    max_file_count: int = 1000  # files
    min_cache_hit_rate: float = 0.7  # 70%
    enable_performance_monitoring: bool = True
    performance_logging_enabled: bool = True


@dataclass
class SafetyConfig:
    """Safety configuration settings."""

    enable_rollback: bool = True
    enable_backup: bool = True
    max_recursive_passes: int = 3
    session_timeout: int = 300  # seconds
    max_backup_points: int = 10
    backup_retention_hours: int = 24
    enable_error_recovery: bool = True
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds


@dataclass
class QualityConfig:
    """Quality configuration settings."""

    min_rule_confidence: float = 0.7
    min_safety_score: float = 0.8
    min_quality_score: float = 0.85
    enable_validation: bool = True
    enable_preview: bool = True
    validation_strict_mode: bool = False
    quality_threshold_enforcement: bool = True


@dataclass
class UserControlConfig:
    """User control configuration settings."""

    enable_auto_generation: bool = True
    enable_git_hooks: bool = False  # Start disabled for safety
    enable_notifications: bool = True
    enable_logging: bool = True
    enable_interactive_mode: bool = False
    require_user_confirmation: bool = True
    enable_dry_run_mode: bool = False
    enable_debug_mode: bool = False


@dataclass
class BulletproofingConfig:
    """Complete bulletproofing configuration."""

    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    user_control: UserControlConfig = field(default_factory=UserControlConfig)

    # Metadata
    config_version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    description: str = "Bulletproofing configuration for auto rules generation system"


class BulletproofingConfigManager:
    """Configuration manager for bulletproofing settings."""

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize the configuration manager."""
        setup_logger(LogConfig())
        self.logger = get_logger()

        self.config_file = config_file or Path("bulletproofing_config.yaml")
        self.config = BulletproofingConfig()

        # Load configuration if file exists
        if self.config_file.exists():
            self.load_config()
        else:
            self.save_config()

        self.logger.log_info("Bulletproofing configuration manager initialized")

    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if self.config_file.suffix.lower() == ".json":
                with open(self.config_file) as f:
                    config_data = json.load(f)
            else:
                with open(self.config_file) as f:
                    config_data = yaml.safe_load(f)

            # Update configuration
            self._update_config_from_dict(config_data)
            self.logger.log_info(f"Configuration loaded from: {self.config_file}")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to load configuration: {e}")
            return False

    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            # Update last modified timestamp
            self.config.last_modified = datetime.now()

            # Convert to dictionary
            config_data = asdict(self.config)

            # Save based on file extension
            if self.config_file.suffix.lower() == ".json":
                with open(self.config_file, "w") as f:
                    json.dump(config_data, f, indent=2, default=str)
            else:
                with open(self.config_file, "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)

            self.logger.log_info(f"Configuration saved to: {self.config_file}")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to save configuration: {e}")
            return False

    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary."""
        # Update performance config
        if "performance" in config_data:
            perf_data = config_data["performance"]
            self.config.performance = PerformanceConfig(**perf_data)

        # Update safety config
        if "safety" in config_data:
            safety_data = config_data["safety"]
            self.config.safety = SafetyConfig(**safety_data)

        # Update quality config
        if "quality" in config_data:
            quality_data = config_data["quality"]
            self.config.quality = QualityConfig(**quality_data)

        # Update user control config
        if "user_control" in config_data:
            user_data = config_data["user_control"]
            self.config.user_control = UserControlConfig(**user_data)

        # Update metadata
        if "config_version" in config_data:
            self.config.config_version = config_data["config_version"]
        if "description" in config_data:
            self.config.description = config_data["description"]

    def get_config(self) -> BulletproofingConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values."""
        try:
            # Update performance settings
            if "performance" in updates:
                for key, value in updates["performance"].items():
                    if hasattr(self.config.performance, key):
                        setattr(self.config.performance, key, value)

            # Update safety settings
            if "safety" in updates:
                for key, value in updates["safety"].items():
                    if hasattr(self.config.safety, key):
                        setattr(self.config.safety, key, value)

            # Update quality settings
            if "quality" in updates:
                for key, value in updates["quality"].items():
                    if hasattr(self.config.quality, key):
                        setattr(self.config.quality, key, value)

            # Update user control settings
            if "user_control" in updates:
                for key, value in updates["user_control"].items():
                    if hasattr(self.config.user_control, key):
                        setattr(self.config.user_control, key, value)

            # Save updated configuration
            return self.save_config()

        except Exception as e:
            self.logger.log_error(f"Failed to update configuration: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values."""
        try:
            self.config = BulletproofingConfig()
            return self.save_config()
        except Exception as e:
            self.logger.log_error(f"Failed to reset configuration: {e}")
            return False

    def validate_config(self) -> List[str]:
        """Validate configuration settings."""
        errors = []

        # Validate performance settings
        if self.config.performance.max_execution_time <= 0:
            errors.append("max_execution_time must be positive")
        if self.config.performance.max_memory_usage <= 0:
            errors.append("max_memory_usage must be positive")
        if (
            self.config.performance.max_cpu_usage <= 0
            or self.config.performance.max_cpu_usage > 100
        ):
            errors.append("max_cpu_usage must be between 0 and 100")
        if self.config.performance.max_file_count <= 0:
            errors.append("max_file_count must be positive")
        if (
            self.config.performance.min_cache_hit_rate < 0
            or self.config.performance.min_cache_hit_rate > 1
        ):
            errors.append("min_cache_hit_rate must be between 0 and 1")

        # Validate safety settings
        if self.config.safety.max_recursive_passes <= 0:
            errors.append("max_recursive_passes must be positive")
        if self.config.safety.session_timeout <= 0:
            errors.append("session_timeout must be positive")
        if self.config.safety.max_backup_points <= 0:
            errors.append("max_backup_points must be positive")
        if self.config.safety.backup_retention_hours <= 0:
            errors.append("backup_retention_hours must be positive")
        if self.config.safety.retry_attempts <= 0:
            errors.append("retry_attempts must be positive")
        if self.config.safety.retry_delay <= 0:
            errors.append("retry_delay must be positive")

        # Validate quality settings
        if (
            self.config.quality.min_rule_confidence < 0
            or self.config.quality.min_rule_confidence > 1
        ):
            errors.append("min_rule_confidence must be between 0 and 1")
        if (
            self.config.quality.min_safety_score < 0
            or self.config.quality.min_safety_score > 1
        ):
            errors.append("min_safety_score must be between 0 and 1")
        if (
            self.config.quality.min_quality_score < 0
            or self.config.quality.min_quality_score > 1
        ):
            errors.append("min_quality_score must be between 0 and 1")

        return errors

    def is_config_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate_config()) == 0

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return {
            "config_version": self.config.config_version,
            "created_at": self.config.created_at.isoformat(),
            "last_modified": self.config.last_modified.isoformat(),
            "description": self.config.description,
            "performance": {
                "max_execution_time": self.config.performance.max_execution_time,
                "max_memory_usage": self.config.performance.max_memory_usage,
                "max_cpu_usage": self.config.performance.max_cpu_usage,
                "max_file_count": self.config.performance.max_file_count,
                "enable_performance_monitoring": self.config.performance.enable_performance_monitoring,
            },
            "safety": {
                "enable_rollback": self.config.safety.enable_rollback,
                "enable_backup": self.config.safety.enable_backup,
                "max_recursive_passes": self.config.safety.max_recursive_passes,
                "enable_error_recovery": self.config.safety.enable_error_recovery,
            },
            "quality": {
                "min_rule_confidence": self.config.quality.min_rule_confidence,
                "min_safety_score": self.config.quality.min_safety_score,
                "min_quality_score": self.config.quality.min_quality_score,
                "enable_validation": self.config.quality.enable_validation,
            },
            "user_control": {
                "enable_auto_generation": self.config.user_control.enable_auto_generation,
                "enable_git_hooks": self.config.user_control.enable_git_hooks,
                "require_user_confirmation": self.config.user_control.require_user_confirmation,
                "enable_dry_run_mode": self.config.user_control.enable_dry_run_mode,
            },
        }

    def generate_config_report(self) -> str:
        """Generate a configuration report."""
        summary = self.get_config_summary()
        validation_errors = self.validate_config()

        report = f"""
🔧 BULLETPROOFING CONFIGURATION REPORT
{'='*60}

📋 CONFIGURATION SUMMARY:
- Version: {summary['config_version']}
- Created: {summary['created_at']}
- Last Modified: {summary['last_modified']}
- Description: {summary['description']}

{'='*60}

⚡ PERFORMANCE SETTINGS:
- Max Execution Time: {summary['performance']['max_execution_time']}s
- Max Memory Usage: {summary['performance']['max_memory_usage']}MB
- Max CPU Usage: {summary['performance']['max_cpu_usage']}%
- Max File Count: {summary['performance']['max_file_count']}
- Performance Monitoring: {'✅ Enabled' if summary['performance']['enable_performance_monitoring'] else '❌ Disabled'}

{'='*60}

🛡️ SAFETY SETTINGS:
- Rollback: {'✅ Enabled' if summary['safety']['enable_rollback'] else '❌ Disabled'}
- Backup: {'✅ Enabled' if summary['safety']['enable_backup'] else '❌ Disabled'}
- Max Recursive Passes: {summary['safety']['max_recursive_passes']}
- Error Recovery: {'✅ Enabled' if summary['safety']['enable_error_recovery'] else '❌ Disabled'}

{'='*60}

🎯 QUALITY SETTINGS:
- Min Rule Confidence: {summary['quality']['min_rule_confidence']:.2f}
- Min Safety Score: {summary['quality']['min_safety_score']:.2f}
- Min Quality Score: {summary['quality']['min_quality_score']:.2f}
- Validation: {'✅ Enabled' if summary['quality']['enable_validation'] else '❌ Disabled'}

{'='*60}

👤 USER CONTROL SETTINGS:
- Auto Generation: {'✅ Enabled' if summary['user_control']['enable_auto_generation'] else '❌ Disabled'}
- Git Hooks: {'✅ Enabled' if summary['user_control']['enable_git_hooks'] else '❌ Disabled'}
- User Confirmation: {'✅ Required' if summary['user_control']['require_user_confirmation'] else '❌ Not Required'}
- Dry Run Mode: {'✅ Enabled' if summary['user_control']['enable_dry_run_mode'] else '❌ Disabled'}

{'='*60}
"""

        if validation_errors:
            report += """
❌ CONFIGURATION ERRORS:
"""
            for error in validation_errors:
                report += f"- {error}\n"
        else:
            report += """
✅ CONFIGURATION VALIDATION: PASSED
"""

        return report

    def export_config(self, filepath: Path, format: str = "yaml") -> bool:
        """Export configuration to a file."""
        try:
            config_data = asdict(self.config)

            if format.lower() == "json":
                with open(filepath, "w") as f:
                    json.dump(config_data, f, indent=2, default=str)
            else:
                with open(filepath, "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)

            self.logger.log_info(f"Configuration exported to: {filepath}")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to export configuration: {e}")
            return False

    def import_config(self, filepath: Path) -> bool:
        """Import configuration from a file."""
        try:
            if filepath.suffix.lower() == ".json":
                with open(filepath) as f:
                    config_data = json.load(f)
            else:
                with open(filepath) as f:
                    config_data = yaml.safe_load(f)

            self._update_config_from_dict(config_data)
            return self.save_config()

        except Exception as e:
            self.logger.log_error(f"Failed to import configuration: {e}")
            return False


# Global configuration manager instance
_global_config_manager: Optional[BulletproofingConfigManager] = None


def get_config_manager() -> BulletproofingConfigManager:
    """Get the global configuration manager instance."""
    global global_config_manager
    if global_config_manager is None:
        global_config_manager = BulletproofingConfigManager()
    return global_config_manager


def get_config() -> BulletproofingConfig:
    """Get the current bulletproofing configuration."""
    return get_config_manager().get_config()


def update_config(updates: Dict[str, Any]) -> bool:
    """Update the bulletproofing configuration."""
    return get_config_manager().update_config(updates)


def validate_config() -> List[str]:
    """Validate the current configuration."""
    return get_config_manager().validate_config()


def is_config_valid() -> bool:
    """Check if the current configuration is valid."""
    return get_config_manager().is_config_valid()


if __name__ == "__main__":
    # Example usage
    config_manager = BulletproofingConfigManager()

    # Generate and print configuration report
    report = config_manager.generate_config_report()
    print(report)

    # Example configuration update
    updates = {
        "performance": {"max_execution_time": 45.0, "max_memory_usage": 768.0},
        "user_control": {"enable_dry_run_mode": True},
    }

    success = config_manager.update_config(updates)
    if success:
        print("Configuration updated successfully")
        print(config_manager.generate_config_report())
    else:
        print("Failed to update configuration")
