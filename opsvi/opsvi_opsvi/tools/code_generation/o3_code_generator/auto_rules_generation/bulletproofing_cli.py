#!/usr/bin/env python3
"""
Command Line Interface for Bulletproofing System

This module provides a simple CLI for running bulletproofing validation
and managing the auto rules generation system.
"""

import argparse
from pathlib import Path
import sys

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)

from .bulletproofing_config import (
    get_config_manager,
    validate_config,
)
from .bulletproofing_orchestrator import (
    enable_git_hooks_safely,
    generate_bulletproofing_report,
    get_bulletproofing_orchestrator,
    is_system_bulletproof,
    run_bulletproofing_validation,
)


def setup_logging():
    """Setup logging for CLI."""
    setup_logger(LogConfig())
    return get_logger()


def validate_command(args):
    """Run bulletproofing validation."""
    logger = setup_logging()
    logger.log_info("Running bulletproofing validation")

    test_path = Path(args.codebase_path)
    if not test_path.exists():
        print(f"❌ Error: Codebase path does not exist: {test_path}")
        sys.exit(1)

    try:
        result = run_bulletproofing_validation(test_path)

        if result.is_bulletproof:
            print("✅ System is BULLETPROOF")
            print("✅ Ready for git hook integration")
        else:
            print("❌ System is NOT BULLETPROOF")
            print("❌ NOT ready for git hook integration")

        if args.verbose:
            print("\n" + "=" * 80)
            print("DETAILED REPORT:")
            print("=" * 80)
            print(result.validation_report)
            print(result.performance_report)
            print(result.recovery_report)
            print(result.config_report)

        print("\n📋 RECOMMENDATIONS:")
        for i, recommendation in enumerate(result.recommendations, 1):
            print(f"{i}. {recommendation}")

        sys.exit(0 if result.is_bulletproof else 1)

    except Exception as e:
        logger.log_error(f"Validation failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


def report_command(args):
    """Generate comprehensive bulletproofing report."""
    logger = setup_logging()
    logger.log_info("Generating bulletproofing report")

    test_path = Path(args.codebase_path)
    if not test_path.exists():
        print(f"❌ Error: Codebase path does not exist: {test_path}")
        sys.exit(1)

    try:
        report = generate_bulletproofing_report(test_path)
        print(report)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.write_text(report, encoding="utf-8")
            print(f"\n📄 Report saved to: {output_path}")

        sys.exit(0)

    except Exception as e:
        logger.log_error(f"Report generation failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


def check_command(args):
    """Quick check if system is bulletproof."""
    logger = setup_logging()
    logger.log_info("Checking if system is bulletproof")

    test_path = Path(args.codebase_path)
    if not test_path.exists():
        print(f"❌ Error: Codebase path does not exist: {test_path}")
        sys.exit(1)

    try:
        is_bulletproof = is_system_bulletproof(test_path)

        if is_bulletproof:
            print("✅ System is BULLETPROOF")
            sys.exit(0)
        else:
            print("❌ System is NOT BULLETPROOF")
            sys.exit(1)

    except Exception as e:
        logger.log_error(f"Check failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


def enable_git_hooks_command(args):
    """Enable git hooks if system is bulletproof."""
    logger = setup_logging()
    logger.log_info("Attempting to enable git hooks")

    try:
        success = enable_git_hooks_safely()

        if success:
            print("✅ Git hooks enabled successfully")
            print("✅ System is bulletproof and ready for production")
            sys.exit(0)
        else:
            print("❌ Git hooks cannot be enabled")
            print("❌ System is not bulletproof")
            sys.exit(1)

    except Exception as e:
        logger.log_error(f"Failed to enable git hooks: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


def config_command(args):
    """Manage bulletproofing configuration."""
    logger = setup_logging()
    config_manager = get_config_manager()

    if args.show:
        report = config_manager.generate_config_report()
        print(report)

    elif args.validate:
        errors = validate_config()
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("✅ Configuration is valid")

    elif args.reset:
        success = config_manager.reset_to_defaults()
        if success:
            print("✅ Configuration reset to defaults")
        else:
            print("❌ Failed to reset configuration")
            sys.exit(1)

    elif args.export:
        output_path = Path(args.export)
        success = config_manager.export_config(output_path)
        if success:
            print(f"✅ Configuration exported to: {output_path}")
        else:
            print("❌ Failed to export configuration")
            sys.exit(1)

    elif args.import_file:
        input_path = Path(args.import_file)
        if not input_path.exists():
            print(f"❌ Error: Import file does not exist: {input_path}")
            sys.exit(1)

        success = config_manager.import_config(input_path)
        if success:
            print(f"✅ Configuration imported from: {input_path}")
        else:
            print("❌ Failed to import configuration")
            sys.exit(1)


def dry_run_command(args):
    """Run bulletproofing validation in dry-run mode."""
    logger = setup_logging()
    logger.log_info("Running bulletproofing validation in dry-run mode")

    test_path = Path(args.codebase_path)
    if not test_path.exists():
        print(f"❌ Error: Codebase path does not exist: {test_path}")
        sys.exit(1)

    try:
        orchestrator = get_bulletproofing_orchestrator()
        result = orchestrator.run_dry_run(test_path)

        print("🧪 DRY RUN MODE - No changes will be made")

        if result.is_bulletproof:
            print("✅ System would be BULLETPROOF in production")
        else:
            print("❌ System would NOT be bulletproof in production")

        if args.verbose:
            print("\n" + "=" * 80)
            print("DETAILED DRY RUN REPORT:")
            print("=" * 80)
            print(result.validation_report)
            print(result.performance_report)
            print(result.recovery_report)
            print(result.config_report)

        print("\n📋 RECOMMENDATIONS:")
        for i, recommendation in enumerate(result.recommendations, 1):
            print(f"{i}. {recommendation}")

        sys.exit(0)

    except Exception as e:
        logger.log_error(f"Dry run failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bulletproofing CLI for Auto Rules Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run validation on oamat_sd codebase
  python bulletproofing_cli.py validate src/applications/oamat_sd

  # Generate detailed report
  python bulletproofing_cli.py report src/applications/oamat_sd --verbose

  # Quick check if system is bulletproof
  python bulletproofing_cli.py check src/applications/oamat_sd

  # Enable git hooks (only if bulletproof)
  python bulletproofing_cli.py enable-git-hooks

  # Show configuration
  python bulletproofing_cli.py config --show

  # Run dry-run validation
  python bulletproofing_cli.py dry-run src/applications/oamat_sd --verbose
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Run bulletproofing validation"
    )
    validate_parser.add_argument("codebase_path", help="Path to codebase to validate")
    validate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed report"
    )
    validate_parser.set_defaults(func=validate_command)

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate comprehensive report"
    )
    report_parser.add_argument("codebase_path", help="Path to codebase to analyze")
    report_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed report"
    )
    report_parser.add_argument("--output-file", "-o", help="Save report to file")
    report_parser.set_defaults(func=report_command)

    # Check command
    check_parser = subparsers.add_parser(
        "check", help="Quick check if system is bulletproof"
    )
    check_parser.add_argument("codebase_path", help="Path to codebase to check")
    check_parser.set_defaults(func=check_command)

    # Enable git hooks command
    enable_parser = subparsers.add_parser(
        "enable-git-hooks", help="Enable git hooks if system is bulletproof"
    )
    enable_parser.set_defaults(func=enable_git_hooks_command)

    # Config command
    config_parser = subparsers.add_parser(
        "config", help="Manage bulletproofing configuration"
    )
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument(
        "--show", action="store_true", help="Show current configuration"
    )
    config_group.add_argument(
        "--validate", action="store_true", help="Validate configuration"
    )
    config_group.add_argument(
        "--reset", action="store_true", help="Reset to default configuration"
    )
    config_group.add_argument("--export", help="Export configuration to file")
    config_group.add_argument(
        "--import", dest="import_file", help="Import configuration from file"
    )
    config_parser.set_defaults(func=config_command)

    # Dry run command
    dry_run_parser = subparsers.add_parser(
        "dry-run", help="Run validation in dry-run mode"
    )
    dry_run_parser.add_argument("codebase_path", help="Path to codebase to validate")
    dry_run_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed report"
    )
    dry_run_parser.set_defaults(func=dry_run_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
