#!/usr/bin/env python3
"""
Resume Orchestrator Script

Enhanced script for resuming interrupted orchestrator workflows from checkpoints,
with support for documentation workflows and checkpoint management.

Usage:
    python resume_orchestrator.py checkpoint_id
    python resume_orchestrator.py --list-checkpoints
    python resume_orchestrator.py --details checkpoint_id
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.workflows.resumable_orchestrator import ResumableDocumentationOrchestrator

    DOCUMENTATION_WORKFLOWS_AVAILABLE = True
except ImportError:
    DOCUMENTATION_WORKFLOWS_AVAILABLE = False

try:
    from src.unified.unified_orchestrator import UnifiedConfig, UnifiedOrchestrator

    UNIFIED_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    UNIFIED_ORCHESTRATOR_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def resume_from_checkpoint(checkpoint_id: str, workspace_dir: Path = None) -> int:
    """Resume workflow from checkpoint"""

    if DOCUMENTATION_WORKFLOWS_AVAILABLE:
        return await _resume_documentation_workflow(checkpoint_id, workspace_dir)
    elif UNIFIED_ORCHESTRATOR_AVAILABLE:
        return await _resume_unified_workflow(checkpoint_id, workspace_dir)
    else:
        logger.error("No resumable orchestrator implementation available")
        return 1


async def _resume_documentation_workflow(
    checkpoint_id: str, workspace_dir: Path = None
) -> int:
    """Resume documentation workflow from checkpoint"""

    if workspace_dir is None:
        # Try to find workspace from checkpoint
        possible_files = list(
            Path("orchestrator_output").glob(
                f"**/checkpoints/checkpoint_{checkpoint_id}.json"
            )
        )

        if not possible_files:
            logger.error(f"Checkpoint file not found: checkpoint_{checkpoint_id}.json")
            logger.info("Available checkpoints:")
            await list_checkpoints()
            return 1

        workspace_dir = possible_files[0].parent.parent
        logger.info(f"Found workspace: {workspace_dir}")

    orchestrator = ResumableDocumentationOrchestrator(
        output_dir=workspace_dir, max_parallel=5
    )

    try:
        logger.info(f"Resuming from checkpoint: {checkpoint_id}")
        summary = await orchestrator._resume_from_checkpoint(checkpoint_id)

        print(f"\n✅ Resume execution completed!")
        print("-" * 50)
        print(f"App: {summary['app_name']}")
        print(f"Tasks completed: {summary['completed_tasks']}/{summary['total_tasks']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Output directory: {summary['output_dir']}")

        if summary["failed_tasks"] > 0:
            print(f"⚠️  {summary['failed_tasks']} tasks failed")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Resume failed: {e}")
        return 1


async def _resume_unified_workflow(
    checkpoint_path: str, workspace_dir: Path = None
) -> int:
    """Resume unified orchestrator workflow from checkpoint file path"""

    checkpoint_file = Path(checkpoint_path)
    if not checkpoint_file.exists():
        # Try to find by ID
        possible_files = list(
            Path(".").glob(f"**/checkpoints/checkpoint_{checkpoint_path}.json")
        )
        if possible_files:
            checkpoint_file = possible_files[0]
        else:
            logger.error(f"Checkpoint file not found: {checkpoint_path}")
            return 1

    # Extract output directory from checkpoint path
    output_dir = checkpoint_file.parent.parent

    logger.info(f"Resuming unified orchestrator from checkpoint...")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Checkpoint: {checkpoint_file.name}")

    # Create orchestrator instance with same config
    config = UnifiedConfig(
        output_dir=output_dir,
        max_parallel=10,
        master_mcp_registry_path=Path("../../.mcp.json"),
        features=[
            "state_persistence",
            "auto_recovery",
            "background_execution",
            "enhanced_metrics",
            "collaboration",
            "quality_gates",
            "execution_plan",
            "agent_monitoring",
        ],
    )
    orchestrator = UnifiedOrchestrator(config)

    # Load from checkpoint
    success = await orchestrator.load_checkpoint(checkpoint_file)
    if not success:
        logger.error("Failed to load checkpoint")
        return 1

    logger.info("Checkpoint loaded successfully")

    # Resume execution
    logger.info("Resuming orchestrator execution...")

    # The orchestrator should automatically continue from where it left off
    await orchestrator.run()

    logger.info("Orchestrator execution completed")
    return 0


async def list_checkpoints(app_name: str = None) -> int:
    """List all available checkpoints"""

    if DOCUMENTATION_WORKFLOWS_AVAILABLE:
        return await _list_documentation_checkpoints(app_name)
    else:
        return await _list_unified_checkpoints()


async def _list_documentation_checkpoints(app_name: str = None) -> int:
    """List documentation workflow checkpoints"""

    checkpoint_dirs = list(Path("orchestrator_output").glob("**/checkpoints"))

    if not checkpoint_dirs:
        print("No orchestrator workspaces found.")
        return 0

    all_checkpoints = []

    for checkpoint_dir in checkpoint_dirs:
        workspace_dir = checkpoint_dir.parent
        orchestrator = ResumableDocumentationOrchestrator(output_dir=workspace_dir)

        checkpoints = orchestrator.list_checkpoints(app_name=app_name)
        for cp in checkpoints:
            cp["workspace"] = str(workspace_dir)
            all_checkpoints.append(cp)

    if not all_checkpoints:
        print(f"No checkpoints found{' for ' + app_name if app_name else ''}.")
        return 0

    # Sort by timestamp
    all_checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)

    print(f"\n📋 Available checkpoints{' for ' + app_name if app_name else ''}:")
    print("-" * 80)

    for cp in all_checkpoints:
        status = "✅ Ready to resume" if cp["can_resume"] else "✅ Completed"
        print(f"🆔 {cp['checkpoint_id']}")
        print(f"   📱 App: {cp['app_name']}")
        print(f"   📅 Date: {cp['timestamp']}")
        print(
            f"   📊 Progress: {cp['completed_tasks']} ✅ {cp['failed_tasks']} ❌ {cp['pending_tasks']} ⏳"
        )
        print(f"   📁 Workspace: {cp['workspace']}")
        print(f"   📋 Status: {status}")
        print()

    return 0


async def _list_unified_checkpoints() -> int:
    """List unified orchestrator checkpoints"""

    checkpoint_files = list(Path(".").glob("**/checkpoints/checkpoint_*.json"))

    if not checkpoint_files:
        print("No checkpoints found.")
        return 0

    print("\n📋 Available checkpoints:")
    print("-" * 80)

    for checkpoint_file in sorted(
        checkpoint_files, key=lambda x: x.stat().st_mtime, reverse=True
    ):
        print(f"📄 {checkpoint_file}")
        print(f"   📅 Modified: {checkpoint_file.stat().st_mtime}")
        print(f"   📁 Directory: {checkpoint_file.parent.parent}")
        print()

    return 0


async def show_checkpoint_details(checkpoint_id: str) -> int:
    """Show detailed checkpoint information"""

    if DOCUMENTATION_WORKFLOWS_AVAILABLE:
        checkpoint_files = list(
            Path("orchestrator_output").glob(
                f"**/checkpoints/checkpoint_{checkpoint_id}.json"
            )
        )

        if not checkpoint_files:
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return 1

        workspace_dir = checkpoint_files[0].parent.parent
        orchestrator = ResumableDocumentationOrchestrator(output_dir=workspace_dir)

        details = orchestrator.get_checkpoint_details(checkpoint_id)

        if not details:
            print(f"Checkpoint not found: {checkpoint_id}")
            return 1

        checkpoint = details["checkpoint"]
        progress = details["progress"]

        print(f"\n📋 Checkpoint Details: {checkpoint_id}")
        print("=" * 80)
        print(f"📱 App Name: {checkpoint['app_name']}")
        print(f"🔄 Workflow: {checkpoint['workflow_type']}")
        print(f"📅 Created: {checkpoint['timestamp']}")
        print(f"▶️  Can Resume: {'Yes' if details['can_resume'] else 'No'}")
        print(f"📁 Workspace: {workspace_dir}")

        print(
            f"\n📊 Progress: {progress['completed']}/{progress['total']} tasks completed"
        )
        print(f"  ✅ Completed: {progress['completed']}")
        print(f"  ❌ Failed: {progress['failed']}")
        print(f"  ⏳ Pending: {progress['pending']}")

        if checkpoint["completed_tasks"]:
            print(f"\n✅ Completed Tasks:")
            for task in checkpoint["completed_tasks"]:
                print(f"  ✓ {task}")

        if checkpoint["failed_tasks"]:
            print(f"\n❌ Failed Tasks:")
            for task in checkpoint["failed_tasks"]:
                print(f"  ✗ {task}")

        if checkpoint["pending_tasks"]:
            print(f"\n⏳ Pending Tasks:")
            for task in checkpoint["pending_tasks"]:
                print(f"  ⏳ {task}")

        if details["can_resume"]:
            print(f"\n▶️  To resume: python resume_orchestrator.py {checkpoint_id}")

        return 0

    else:
        print(f"Checkpoint details not available for: {checkpoint_id}")
        return 1


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description="Resume interrupted orchestrator workflows"
    )

    parser.add_argument(
        "checkpoint_id", nargs="?", help="Checkpoint ID or file path to resume from"
    )

    parser.add_argument(
        "--list-checkpoints", action="store_true", help="List available checkpoints"
    )

    parser.add_argument(
        "--details", help="Show detailed information about a checkpoint"
    )

    parser.add_argument("--app-name", help="Filter checkpoints by app name")

    parser.add_argument("--workspace-dir", help="Specific workspace directory to use")

    args = parser.parse_args()

    async def run():
        if args.list_checkpoints:
            return await list_checkpoints(args.app_name)
        elif args.details:
            return await show_checkpoint_details(args.details)
        elif args.checkpoint_id:
            workspace_dir = Path(args.workspace_dir) if args.workspace_dir else None
            return await resume_from_checkpoint(args.checkpoint_id, workspace_dir)
        else:
            parser.print_help()
            return 0

    try:
        exit_code = asyncio.run(run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
