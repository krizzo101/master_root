#!/usr/bin/env python3
"""
Error Recovery and Rollback System for Auto Rules Generation

This module provides comprehensive error recovery and rollback capabilities
for the auto rules generation system to handle failures gracefully.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)


@dataclass
class BackupPoint:
    """A backup point for rollback operations."""

    id: str
    timestamp: datetime
    description: str
    file_paths: List[Path]
    backup_dir: Path
    metadata: Dict[str, Any]


@dataclass
class RecoveryAction:
    """A recovery action to be performed."""

    action_type: str  # 'rollback', 'retry', 'fallback', 'cleanup'
    description: str
    target: Any
    parameters: Dict[str, Any]
    priority: int  # Higher number = higher priority


@dataclass
class ErrorContext:
    """Context information for error recovery."""

    error_type: str
    error_message: str
    timestamp: datetime
    operation_name: str
    file_paths: List[Path]
    backup_points: List[BackupPoint]
    recovery_actions: List[RecoveryAction]


class ErrorRecoverySystem:
    """Comprehensive error recovery and rollback system."""

    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize the error recovery system."""
        setup_logger(LogConfig())
        self.logger = get_logger()

        self.backup_dir = backup_dir or Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

        self.backup_points: List[BackupPoint] = []
        self.recovery_strategies: Dict[str, List[RecoveryAction]] = {}
        self.max_backups = 10
        self.retry_attempts = 3
        self.retry_delay = 1.0  # seconds

        # Thread safety
        self._lock = threading.Lock()

        self.logger.log_info("Error recovery system initialized")

    def create_backup_point(
        self,
        description: str,
        file_paths: List[Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BackupPoint:
        """Create a backup point for potential rollback."""
        with self._lock:
            backup_id = f"backup_{int(time.time())}_{len(self.backup_points)}"
            backup_dir = self.backup_dir / backup_id
            backup_dir.mkdir(exist_ok=True)

            # Copy files to backup directory
            backed_up_files = []
            for file_path in file_paths:
                if file_path.exists():
                    backup_file = backup_dir / file_path.name
                    shutil.copy2(file_path, backup_file)
                    backed_up_files.append(file_path)

            backup_point = BackupPoint(
                id=backup_id,
                timestamp=datetime.now(),
                description=description,
                file_paths=backed_up_files,
                backup_dir=backup_dir,
                metadata=metadata or {},
            )

            self.backup_points.append(backup_point)

            # Clean up old backups if we have too many
            if len(self.backup_points) > self.max_backups:
                oldest_backup = self.backup_points.pop(0)
                self._cleanup_backup(oldest_backup)

            self.logger.log_info(f"Created backup point: {backup_id} - {description}")
            return backup_point

    def _cleanup_backup(self, backup_point: BackupPoint):
        """Clean up a backup point."""
        try:
            if backup_point.backup_dir.exists():
                shutil.rmtree(backup_point.backup_dir)
            self.logger.log_info(f"Cleaned up backup point: {backup_point.id}")
        except Exception as e:
            self.logger.log_warning(
                f"Failed to cleanup backup point {backup_point.id}: {e}"
            )

    def rollback_to_backup(self, backup_point: BackupPoint) -> bool:
        """Rollback to a specific backup point."""
        try:
            self.logger.log_info(f"Rolling back to backup point: {backup_point.id}")

            # Restore files from backup
            restored_files = []
            for file_path in backup_point.file_paths:
                backup_file = backup_point.backup_dir / file_path.name
                if backup_file.exists():
                    shutil.copy2(backup_file, file_path)
                    restored_files.append(file_path)

            self.logger.log_info(
                f"Successfully restored {len(restored_files)} files from backup {backup_point.id}"
            )
            return True

        except Exception as e:
            self.logger.log_error(
                f"Failed to rollback to backup {backup_point.id}: {e}"
            )
            return False

    def rollback_latest(self) -> Optional[BackupPoint]:
        """Rollback to the latest backup point."""
        if not self.backup_points:
            self.logger.log_warning("No backup points available for rollback")
            return None

        latest_backup = self.backup_points[-1]
        success = self.rollback_to_backup(latest_backup)

        if success:
            return latest_backup
        else:
            return None

    def add_recovery_strategy(self, error_type: str, actions: List[RecoveryAction]):
        """Add a recovery strategy for a specific error type."""
        self.recovery_strategies[error_type] = sorted(
            actions, key=lambda x: x.priority, reverse=True
        )
        self.logger.log_info(f"Added recovery strategy for error type: {error_type}")

    def execute_recovery_strategy(self, error_context: ErrorContext) -> bool:
        """Execute recovery strategy for an error."""
        self.logger.log_info(
            f"Executing recovery strategy for error: {error_context.error_type}"
        )

        strategy = self.recovery_strategies.get(error_context.error_type, [])

        for action in strategy:
            try:
                self.logger.log_info(
                    f"Executing recovery action: {action.action_type} - {action.description}"
                )

                if action.action_type == "rollback":
                    success = self._execute_rollback_action(action, error_context)
                elif action.action_type == "retry":
                    success = self._execute_retry_action(action, error_context)
                elif action.action_type == "fallback":
                    success = self._execute_fallback_action(action, error_context)
                elif action.action_type == "cleanup":
                    success = self._execute_cleanup_action(action, error_context)
                else:
                    self.logger.log_warning(
                        f"Unknown recovery action type: {action.action_type}"
                    )
                    success = False

                if success:
                    self.logger.log_info(
                        f"Recovery action {action.action_type} succeeded"
                    )
                    return True
                else:
                    self.logger.log_warning(
                        f"Recovery action {action.action_type} failed"
                    )

            except Exception as e:
                self.logger.log_error(
                    f"Error executing recovery action {action.action_type}: {e}"
                )

        self.logger.log_error("All recovery strategies failed")
        return False

    def _execute_rollback_action(
        self, action: RecoveryAction, error_context: ErrorContext
    ) -> bool:
        """Execute a rollback action."""
        if action.target == "latest":
            return self.rollback_latest() is not None
        elif isinstance(action.target, BackupPoint):
            return self.rollback_to_backup(action.target)
        else:
            self.logger.log_warning(f"Invalid rollback target: {action.target}")
            return False

    def _execute_retry_action(
        self, action: RecoveryAction, error_context: ErrorContext
    ) -> bool:
        """Execute a retry action."""
        func = action.parameters.get("function")
        max_attempts = action.parameters.get("max_attempts", self.retry_attempts)
        delay = action.parameters.get("delay", self.retry_delay)

        if not func or not callable(func):
            self.logger.log_warning("Retry action requires a callable function")
            return False

        for attempt in range(max_attempts):
            try:
                self.logger.log_info(f"Retry attempt {attempt + 1}/{max_attempts}")
                result = func()
                if result:
                    self.logger.log_info(f"Retry attempt {attempt + 1} succeeded")
                    return True
            except Exception as e:
                self.logger.log_warning(f"Retry attempt {attempt + 1} failed: {e}")

            if attempt < max_attempts - 1:
                time.sleep(delay)

        return False

    def _execute_fallback_action(
        self, action: RecoveryAction, error_context: ErrorContext
    ) -> bool:
        """Execute a fallback action."""
        fallback_func = action.parameters.get("fallback_function")

        if not fallback_func or not callable(fallback_func):
            self.logger.log_warning("Fallback action requires a callable function")
            return False

        try:
            result = fallback_func()
            self.logger.log_info("Fallback action executed successfully")
            return True
        except Exception as e:
            self.logger.log_error(f"Fallback action failed: {e}")
            return False

    def _execute_cleanup_action(
        self, action: RecoveryAction, error_context: ErrorContext
    ) -> bool:
        """Execute a cleanup action."""
        try:
            # Clean up temporary files
            temp_files = action.parameters.get("temp_files", [])
            for temp_file in temp_files:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()

            # Clean up temporary directories
            temp_dirs = action.parameters.get("temp_dirs", [])
            for temp_dir in temp_dirs:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)

            self.logger.log_info("Cleanup action executed successfully")
            return True
        except Exception as e:
            self.logger.log_error(f"Cleanup action failed: {e}")
            return False

    @contextmanager
    def error_recovery_context(
        self,
        operation_name: str,
        file_paths: List[Path],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for error recovery."""
        backup_point = None
        error_context = None

        try:
            # Create backup point
            backup_point = self.create_backup_point(
                f"Before {operation_name}", file_paths, metadata
            )

            yield backup_point

        except Exception as e:
            # Create error context
            error_context = ErrorContext(
                error_type=type(e).__name__,
                error_message=str(e),
                timestamp=datetime.now(),
                operation_name=operation_name,
                file_paths=file_paths,
                backup_points=[backup_point] if backup_point else [],
                recovery_actions=[],
            )

            # Execute recovery strategy
            recovery_success = self.execute_recovery_strategy(error_context)

            if not recovery_success:
                self.logger.log_error(
                    f"Error recovery failed for operation: {operation_name}"
                )
                raise
            else:
                self.logger.log_info(
                    f"Error recovery succeeded for operation: {operation_name}"
                )

    def get_backup_points(self) -> List[BackupPoint]:
        """Get all backup points."""
        with self._lock:
            return self.backup_points.copy()

    def cleanup_old_backups(self, max_age_hours: int = 24):
        """Clean up backup points older than specified age."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        with self._lock:
            old_backups = [
                backup
                for backup in self.backup_points
                if backup.timestamp.timestamp() < cutoff_time
            ]

            for backup in old_backups:
                self.backup_points.remove(backup)
                self._cleanup_backup(backup)

            self.logger.log_info(f"Cleaned up {len(old_backups)} old backup points")

    def export_backup_info(self, filepath: Path):
        """Export backup information to a file."""
        backup_info = {
            "export_timestamp": datetime.now().isoformat(),
            "backup_points": [
                {
                    "id": bp.id,
                    "timestamp": bp.timestamp.isoformat(),
                    "description": bp.description,
                    "file_paths": [str(fp) for fp in bp.file_paths],
                    "backup_dir": str(bp.backup_dir),
                    "metadata": bp.metadata,
                }
                for bp in self.backup_points
            ],
        }

        with open(filepath, "w") as f:
            json.dump(backup_info, f, indent=2)

        self.logger.log_info(f"Backup information exported to: {filepath}")

    def generate_recovery_report(self) -> str:
        """Generate a recovery system report."""
        report = f"""
🛡️ ERROR RECOVERY SYSTEM REPORT
{'='*50}

📊 BACKUP POINTS:
- Total Backup Points: {len(self.backup_points)}
- Oldest Backup: {self.backup_points[0].timestamp if self.backup_points else 'None'}
- Newest Backup: {self.backup_points[-1].timestamp if self.backup_points else 'None'}

{'='*50}

📋 RECOVERY STRATEGIES:
"""

        for error_type, actions in self.recovery_strategies.items():
            report += f"\nError Type: {error_type}\n"
            for action in actions:
                report += f"  - {action.action_type}: {action.description} (Priority: {action.priority})\n"

        report += f"\n{'='*50}"

        if self.backup_points:
            report += "\n📁 RECENT BACKUP POINTS:\n"
            for backup in self.backup_points[-5:]:  # Last 5 backups
                report += f"\n- {backup.id}: {backup.description}"
                report += (
                    f"\n  Timestamp: {backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                report += f"\n  Files: {len(backup.file_paths)}"

        return report


# Global error recovery system instance
_global_recovery_system: Optional[ErrorRecoverySystem] = None


def get_error_recovery_system() -> ErrorRecoverySystem:
    """Get the global error recovery system instance."""
    global global_recovery_system
    if global_recovery_system is None:
        global_recovery_system = ErrorRecoverySystem()
    return global_recovery_system


def with_error_recovery(
    operation_name: str,
    file_paths: List[Path],
    metadata: Optional[Dict[str, Any]] = None,
):
    """Decorator for adding error recovery to functions."""

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            recovery_system = get_error_recovery_system()

            with recovery_system.error_recovery_context(
                operation_name, file_paths, metadata
            ):
                return func(*args, **kwargs)

        return wrapper

    return decorator


if __name__ == "__main__":
    # Example usage
    recovery_system = ErrorRecoverySystem()

    # Add recovery strategies
    recovery_system.add_recovery_strategy(
        "FileNotFoundError",
        [
            RecoveryAction("rollback", "Rollback to latest backup", "latest", {}, 1),
            RecoveryAction("retry", "Retry operation", "retry", {"max_attempts": 3}, 2),
        ],
    )

    recovery_system.add_recovery_strategy(
        "PermissionError",
        [
            RecoveryAction(
                "cleanup", "Clean up temporary files", "cleanup", {"temp_files": []}, 1
            ),
            RecoveryAction(
                "fallback",
                "Use fallback method",
                "fallback",
                {"fallback_function": lambda: True},
                2,
            ),
        ],
    )

    # Example function with error recovery
    @with_error_recovery("test_operation", [Path("test_file.txt")])
    def test_function():
        # Simulate some operation
        time.sleep(1)
        return "success"

    # Run the function
    result = test_function()
    print(f"Result: {result}")

    # Generate report
    report = recovery_system.generate_recovery_report()
    print(report)
