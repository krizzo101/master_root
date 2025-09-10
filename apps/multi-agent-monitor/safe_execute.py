#!/usr/bin/env python3
"""
Safe Execution CLI for Multi-Agent Teams
Main entry point for safe multi-agent orchestration
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.team_orchestrator import ProjectType
from src.safety import ExecutionMode, SafeOrchestrator, SafetyLevel


async def main():
    """Main entry point for safe execution"""

    parser = argparse.ArgumentParser(
        description="Safe Multi-Agent Execution System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python safe_execute.py my_project --type web --dry-run

  # Safe execution with medium safety
  python safe_execute.py my_project --type refactor --safety medium

  # Review mode with high safety
  python safe_execute.py my_project --type microservices --mode review --safety high

  # Emergency mode (use with caution!)
  python safe_execute.py hotfix --type web --mode emergency --phases "bug-fix"

Safety Levels:
  low      - Basic checks, suitable for documentation changes
  medium   - Standard checks, suitable for feature development
  high     - Strict checks, suitable for core changes
  critical - Maximum safety, suitable for production changes

Execution Modes:
  dry-run   - Preview changes without executing
  safe      - Execute with safety features (default)
  review    - Execute with mandatory review
  emergency - Bypass safety for urgent fixes
        """,
    )

    # Required arguments
    parser.add_argument("project_name", help="Name of the project")

    parser.add_argument(
        "--type",
        "-t",
        type=str,
        choices=[pt.value for pt in ProjectType],
        required=True,
        help="Type of project",
    )

    # Safety options
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=[m.value for m in ExecutionMode],
        default="safe",
        help="Execution mode (default: safe)",
    )

    parser.add_argument(
        "--safety",
        "-s",
        type=str,
        choices=[sl.value for sl in SafetyLevel],
        default="medium",
        help="Safety level (default: medium)",
    )

    # Execution options
    parser.add_argument(
        "--requirements",
        "-r",
        type=str,
        default="",
        help="Project requirements or description",
    )

    parser.add_argument(
        "--phases", "-p", type=str, nargs="+", help="Specific phases to execute"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing (same as --mode dry-run)",
    )

    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")

    parser.add_argument(
        "--no-rollback", action="store_true", help="Disable auto-rollback on error"
    )

    parser.add_argument(
        "--approve", action="store_true", help="Auto-approve changes (skip review)"
    )

    args = parser.parse_args()

    # Handle dry-run flag
    if args.dry_run:
        args.mode = "dry_run"

    # Convert string enums
    mode = ExecutionMode[args.mode.upper().replace("-", "_")]
    safety = SafetyLevel[args.safety.upper()]
    project_type = ProjectType[args.type.upper().replace("-", "_")]

    # Initialize orchestrator
    orchestrator = SafeOrchestrator()

    # Configure safety options
    if args.no_backup:
        orchestrator.safety_config["create_backup"] = False

    if args.no_rollback:
        orchestrator.safety_config["auto_rollback_on_error"] = False

    if args.approve:
        orchestrator.safety_config["require_approval"] = False

    # Show configuration
    print(
        f"""
╔══════════════════════════════════════════════════════════════╗
║           SAFE MULTI-AGENT EXECUTION SYSTEM                  ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
  Project:      {args.project_name}
  Type:         {project_type.value}
  Mode:         {mode.value}
  Safety:       {safety.value}
  Phases:       {args.phases or 'all'}
  Auto-rollback: {not args.no_rollback}
  Create backup: {not args.no_backup}
"""
    )

    # Confirm execution
    if mode != ExecutionMode.DRY_RUN and not args.approve:
        response = input("\n⚠️  Proceed with execution? (y/N): ")
        if response.lower() != "y":
            print("Execution cancelled")
            return

    # Execute
    try:
        result = await orchestrator.safe_execute(
            project_name=args.project_name,
            project_type=project_type,
            requirements=args.requirements or f"Execute {project_type.value} workflow",
            mode=mode,
            safety_level=safety,
            phases=args.phases,
        )

        # Show results
        if result["success"]:
            print("\n✅ Execution completed successfully!")

            if mode == ExecutionMode.DRY_RUN:
                print("\nDry run complete. No changes were made.")
                print("Run without --dry-run to execute.")
            elif "review_required" in result and result["review_required"]:
                print(
                    f"\n📝 Review required: {result.get('report', 'review_report.json')}"
                )
                print("\nNext steps:")
                print("  1. Review the changes")
                print("  2. Run: python src/safety/git_safety_manager.py review")
                print("  3. If approved: python src/safety/git_safety_manager.py merge")
            else:
                print("\nChanges have been committed to git.")
                print("Check the branch for details.")
        else:
            print(f"\n❌ Execution failed: {result.get('error', 'Unknown error')}")

            if not args.no_rollback:
                print("Changes have been rolled back.")

            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted!")
        print("Rolling back changes...")
        orchestrator.safety_manager.rollback_to_checkpoint()
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

        if not args.no_rollback:
            print("Attempting rollback...")
            try:
                orchestrator.safety_manager.rollback_to_checkpoint()
                print("✅ Rollback successful")
            except:
                print("❌ Rollback failed - manual intervention required")

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
