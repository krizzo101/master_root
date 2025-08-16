#!/usr/bin/env python3
"""
Bulletproofing Orchestrator for Auto Rules Generation

This module orchestrates all bulletproofing components to ensure the auto rules
generation system is truly bulletproof before git hook integration.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import time
from typing import List, Optional

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)

from .bulletproofing_config import (
    get_config,
    get_config_manager,
)
from .bulletproofing_validation import BulletproofingValidator
from .error_recovery import (
    get_error_recovery_system,
)
from .performance_monitor import (
    get_performance_monitor,
)


@dataclass
class BulletproofingResult:
    """Result of bulletproofing validation."""

    is_bulletproof: bool
    validation_report: str
    performance_report: str
    recovery_report: str
    config_report: str
    recommendations: List[str]
    timestamp: datetime


class BulletproofingOrchestrator:
    """Main orchestrator for bulletproofing the auto rules generation system."""

    def __init__(self):
        """Initialize the bulletproofing orchestrator."""
        setup_logger(LogConfig())
        self.logger = get_logger()

        # Initialize all components
        self.validator = BulletproofingValidator()
        self.performance_monitor = get_performance_monitor()
        self.recovery_system = get_error_recovery_system()
        self.config_manager = get_config_manager()

        self.logger.log_info("Bulletproofing orchestrator initialized")

    def run_comprehensive_validation(
        self, test_codebase_path: Path
    ) -> BulletproofingResult:
        """Run comprehensive bulletproofing validation."""
        self.logger.log_info("Starting comprehensive bulletproofing validation")

        start_time = time.time()

        try:
            # 1. Configuration validation
            config_errors = self.config_manager.validate_config()
            if config_errors:
                self.logger.log_warning(
                    f"Configuration validation errors: {config_errors}"
                )

            # 2. Performance validation
            with self.performance_monitor.monitor_performance(
                "bulletproofing_validation"
            ):
                validation_results = self.validator.validate_system(test_codebase_path)

            # 3. Generate reports
            validation_report = self.validator.generate_validation_report()
            performance_report = self.performance_monitor.generate_performance_report()
            recovery_report = self.recovery_system.generate_recovery_report()
            config_report = self.config_manager.generate_config_report()

            # 4. Determine if system is bulletproof
            is_bulletproof = (
                self.validator.is_bulletproof()
                and len(config_errors) == 0
                and self._check_performance_thresholds()
                and self._check_recovery_capabilities()
            )

            # 5. Generate recommendations
            recommendations = self._generate_recommendations(
                is_bulletproof, validation_results, config_errors
            )

            execution_time = time.time() - start_time

            result = BulletproofingResult(
                is_bulletproof=is_bulletproof,
                validation_report=validation_report,
                performance_report=performance_report,
                recovery_report=recovery_report,
                config_report=config_report,
                recommendations=recommendations,
                timestamp=datetime.now(),
            )

            self.logger.log_info(
                f"Bulletproofing validation completed in {execution_time:.2f}s"
            )
            self.logger.log_info(
                f"System is {'BULLETPROOF' if is_bulletproof else 'NOT BULLETPROOF'}"
            )

            return result

        except Exception as e:
            self.logger.log_error(f"Bulletproofing validation failed: {e}")

            # Return failure result
            return BulletproofingResult(
                is_bulletproof=False,
                validation_report=f"Validation failed: {e}",
                performance_report="Performance monitoring failed",
                recovery_report="Recovery system report unavailable",
                config_report="Configuration report unavailable",
                recommendations=["Fix the error that caused validation to fail"],
                timestamp=datetime.now(),
            )

    def _check_performance_thresholds(self) -> bool:
        """Check if performance meets thresholds."""
        config = get_config()
        summary = self.performance_monitor.get_performance_summary()

        if "message" in summary:
            return False  # No performance data available

        # Check against configured thresholds
        performance_checks = [
            summary["average_execution_time"] <= config.performance.max_execution_time,
            summary["average_memory_usage"] <= config.performance.max_memory_usage,
            summary["cache_hit_rate"] >= config.performance.min_cache_hit_rate,
        ]

        return all(performance_checks)

    def _check_recovery_capabilities(self) -> bool:
        """Check if recovery capabilities are adequate."""
        config = get_config()

        recovery_checks = [
            config.safety.enable_error_recovery,
            config.safety.enable_backup,
            config.safety.enable_rollback,
        ]

        return all(recovery_checks)

    def _generate_recommendations(
        self, is_bulletproof: bool, validation_results: List, config_errors: List[str]
    ) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        if not is_bulletproof:
            recommendations.append(
                "System is not bulletproof - address all validation issues before git hook integration"
            )

        # Configuration recommendations
        if config_errors:
            recommendations.append("Fix configuration validation errors")

        # Performance recommendations
        performance_suggestions = self.performance_monitor.optimize_performance()
        recommendations.extend(performance_suggestions)

        # Validation-specific recommendations
        failed_validations = [r for r in validation_results if not r.passed]
        if failed_validations:
            recommendations.append(
                f"Address {len(failed_validations)} failed validation tests"
            )

        # Safety recommendations
        config = get_config()
        if not config.safety.enable_git_hooks:
            recommendations.append(
                "Git hooks are disabled - enable only after system is bulletproof"
            )

        if config.user_control.require_user_confirmation:
            recommendations.append(
                "User confirmation is required - consider automated mode for production"
            )

        # Quality recommendations
        if config.quality.validation_strict_mode:
            recommendations.append(
                "Strict validation mode is enabled - ensure all quality thresholds are met"
            )

        return recommendations

    def enable_git_hooks(self) -> bool:
        """Enable git hooks only if system is bulletproof."""
        config = get_config()

        if not config.user_control.enable_git_hooks:
            self.logger.log_warning("Git hooks are disabled in configuration")
            return False

        # Run validation before enabling
        test_path = Path("src/applications/oamat_sd")
        result = self.run_comprehensive_validation(test_path)

        if result.is_bulletproof:
            self.logger.log_info("System is bulletproof - git hooks can be enabled")
            return True
        else:
            self.logger.log_error(
                "System is not bulletproof - git hooks cannot be enabled"
            )
            self.logger.log_error("Address the following issues:")
            for recommendation in result.recommendations:
                self.logger.log_error(f"- {recommendation}")
            return False

    def disable_git_hooks(self) -> bool:
        """Disable git hooks for safety."""
        try:
            updates = {"user_control": {"enable_git_hooks": False}}
            success = self.config_manager.update_config(updates)

            if success:
                self.logger.log_info("Git hooks disabled for safety")
            else:
                self.logger.log_error("Failed to disable git hooks")

            return success

        except Exception as e:
            self.logger.log_error(f"Error disabling git hooks: {e}")
            return False

    def run_dry_run(self, test_codebase_path: Path) -> BulletproofingResult:
        """Run bulletproofing validation in dry-run mode."""
        self.logger.log_info("Running bulletproofing validation in dry-run mode")

        # Enable dry-run mode
        updates = {"user_control": {"enable_dry_run_mode": True}}
        self.config_manager.update_config(updates)

        # Run validation
        result = self.run_comprehensive_validation(test_codebase_path)

        # Disable dry-run mode
        updates["user_control"]["enable_dry_run_mode"] = False
        self.config_manager.update_config(updates)

        return result

    def generate_comprehensive_report(self, test_codebase_path: Path) -> str:
        """Generate a comprehensive bulletproofing report."""
        result = self.run_comprehensive_validation(test_codebase_path)

        report = f"""
🛡️ COMPREHENSIVE BULLETPROOFING REPORT
{'='*80}

📊 EXECUTIVE SUMMARY:
- System Status: {'✅ BULLETPROOF' if result.is_bulletproof else '❌ NOT BULLETPROOF'}
- Validation Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- Git Hook Ready: {'✅ YES' if result.is_bulletproof else '❌ NO'}

{'='*80}

{result.validation_report}

{'='*80}

{result.performance_report}

{'='*80}

{result.recovery_report}

{'='*80}

{result.config_report}

{'='*80}

📋 RECOMMENDATIONS:
"""

        for i, recommendation in enumerate(result.recommendations, 1):
            report += f"{i}. {recommendation}\n"

        report += f"\n{'='*80}\n"

        if result.is_bulletproof:
            report += """
🎉 CONCLUSION: SYSTEM IS BULLETPROOF
✅ Ready for git hook integration
✅ All validation tests passed
✅ Performance meets requirements
✅ Error recovery mechanisms in place
✅ Configuration is valid
"""
        else:
            report += """
⚠️  CONCLUSION: SYSTEM IS NOT BULLETPROOF
❌ NOT ready for git hook integration
❌ Address all recommendations above
❌ Re-run validation after fixes
❌ Ensure all components are tested
"""

        return report

    def setup_default_recovery_strategies(self):
        """Setup default recovery strategies for common error types."""
        from .error_recovery import RecoveryAction

        # FileNotFoundError recovery
        self.recovery_system.add_recovery_strategy(
            "FileNotFoundError",
            [
                RecoveryAction(
                    "rollback", "Rollback to latest backup", "latest", {}, 1
                ),
                RecoveryAction(
                    "retry", "Retry operation", "retry", {"max_attempts": 3}, 2
                ),
            ],
        )

        # PermissionError recovery
        self.recovery_system.add_recovery_strategy(
            "PermissionError",
            [
                RecoveryAction(
                    "cleanup",
                    "Clean up temporary files",
                    "cleanup",
                    {"temp_files": []},
                    1,
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

        # MemoryError recovery
        self.recovery_system.add_recovery_strategy(
            "MemoryError",
            [
                RecoveryAction(
                    "cleanup", "Clean up memory", "cleanup", {"temp_dirs": []}, 1
                ),
                RecoveryAction("rollback", "Rollback to safe state", "latest", {}, 2),
            ],
        )

        # TimeoutError recovery
        self.recovery_system.add_recovery_strategy(
            "TimeoutError",
            [
                RecoveryAction(
                    "retry",
                    "Retry with shorter timeout",
                    "retry",
                    {"max_attempts": 2},
                    1,
                ),
                RecoveryAction(
                    "fallback",
                    "Use simplified processing",
                    "fallback",
                    {"fallback_function": lambda: True},
                    2,
                ),
            ],
        )

        self.logger.log_info("Default recovery strategies configured")

    def cleanup_old_data(self):
        """Clean up old performance and backup data."""
        # Clean up old performance logs
        self.performance_monitor.clear_history()

        # Clean up old backups
        self.recovery_system.cleanup_old_backups()

        self.logger.log_info("Old data cleaned up")


# Global orchestrator instance
_global_orchestrator: Optional[BulletproofingOrchestrator] = None


def get_bulletproofing_orchestrator() -> BulletproofingOrchestrator:
    """Get the global bulletproofing orchestrator instance."""
    global global_orchestrator
    if global_orchestrator is None:
        global_orchestrator = BulletproofingOrchestrator()
        global_orchestrator.setup_default_recovery_strategies()
    return global_orchestrator


def run_bulletproofing_validation(test_codebase_path: Path) -> BulletproofingResult:
    """Run comprehensive bulletproofing validation."""
    orchestrator = get_bulletproofing_orchestrator()
    return orchestrator.run_comprehensive_validation(test_codebase_path)


def generate_bulletproofing_report(test_codebase_path: Path) -> str:
    """Generate a comprehensive bulletproofing report."""
    orchestrator = get_bulletproofing_orchestrator()
    return orchestrator.generate_comprehensive_report(test_codebase_path)


def is_system_bulletproof(test_codebase_path: Path) -> bool:
    """Check if the system is bulletproof."""
    result = run_bulletproofing_validation(test_codebase_path)
    return result.is_bulletproof


def enable_git_hooks_safely() -> bool:
    """Enable git hooks only if system is bulletproof."""
    orchestrator = get_bulletproofing_orchestrator()
    return orchestrator.enable_git_hooks()


if __name__ == "__main__":
    # Example usage
    orchestrator = get_bulletproofing_orchestrator()

    # Test with oamat_sd codebase
    test_path = Path("src/applications/oamat_sd")

    if test_path.exists():
        # Generate comprehensive report
        report = orchestrator.generate_comprehensive_report(test_path)
        print(report)

        # Check if system is bulletproof
        is_bulletproof = orchestrator.run_comprehensive_validation(
            test_path
        ).is_bulletproof
        print(f"\nSystem is bulletproof: {'YES' if is_bulletproof else 'NO'}")

        # Try to enable git hooks
        if is_bulletproof:
            success = orchestrator.enable_git_hooks()
            print(f"Git hooks enabled: {'YES' if success else 'NO'}")
        else:
            print("Git hooks cannot be enabled - system is not bulletproof")
    else:
        print(f"Test codebase not found: {test_path}")
        print("Please run this script from the project root directory")
