#!/usr/bin/env python3
"""
Agent Orchestrator Task Runner

Command-line interface for running orchestrated agent tasks including
system documentation workflows with checkpointing and resumption.

Usage:
    python run_orchestrator_task.py --task-type system-documentation --app-name my-app --app-root /path/to/app
    python run_orchestrator_task.py --resume-checkpoint checkpoint_12345
    python run_orchestrator_task.py --list-checkpoints --app-name my-app
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.workflows.resumable_orchestrator import ResumableDocumentationOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'orchestrator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
    ],
)

logger = logging.getLogger(__name__)


class OrchestratorCLI:
    """Command-line interface for orchestrator tasks"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser"""

        parser = argparse.ArgumentParser(
            description="Agent Orchestrator Task Runner",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run comprehensive documentation workflow
  %(prog)s --task-type system-documentation --app-name my-app --app-root /path/to/app

  # Run with custom template and output directory
  %(prog)s --task-type system-documentation --app-name my-app --app-root /path/to/app \\
           --template standard --output-dir /custom/docs/path

  # Resume from checkpoint
  %(prog)s --resume-checkpoint checkpoint_sysdoc_myapp_20231201_143022

  # List available checkpoints
  %(prog)s --list-checkpoints --app-name my-app

  # Get checkpoint details
  %(prog)s --checkpoint-details checkpoint_id_here
            """,
        )

        # Main task arguments
        parser.add_argument(
            "--task-type",
            choices=["system-documentation"],
            help="Type of orchestrator task to run",
        )

        parser.add_argument("--app-name", help="Name of the application to document")

        parser.add_argument("--app-root", help="Root directory of the application")

        parser.add_argument(
            "--output-dir",
            help="Output directory for generated files (default: {app_root}/docs)",
        )

        # Documentation-specific arguments
        parser.add_argument(
            "--template",
            choices=["comprehensive", "standard", "minimal", "api-focused"],
            default="comprehensive",
            help="Documentation template to use (default: comprehensive)",
        )

        parser.add_argument(
            "--include-api-docs",
            action="store_true",
            default=True,
            help="Include API reference documentation",
        )

        parser.add_argument(
            "--include-architecture",
            action="store_true",
            default=True,
            help="Include architecture documentation",
        )

        parser.add_argument(
            "--include-deployment",
            action="store_true",
            default=True,
            help="Include deployment documentation",
        )

        parser.add_argument(
            "--include-user-guide",
            action="store_true",
            default=True,
            help="Include user guide documentation",
        )

        parser.add_argument(
            "--detail-level",
            choices=["minimal", "standard", "comprehensive"],
            default="comprehensive",
            help="Level of detail for documentation (default: comprehensive)",
        )

        # Execution control
        parser.add_argument(
            "--max-parallel",
            type=int,
            default=5,
            help="Maximum number of parallel agent executions (default: 5)",
        )

        parser.add_argument(
            "--checkpoint-interval",
            type=int,
            default=3,
            help="Create checkpoint every N completed tasks (default: 3)",
        )

        # Resume and checkpoint management
        parser.add_argument(
            "--resume-checkpoint", help="Resume execution from specified checkpoint ID"
        )

        parser.add_argument(
            "--list-checkpoints",
            action="store_true",
            help="List available checkpoints for resumption",
        )

        parser.add_argument(
            "--checkpoint-details",
            help="Show detailed information about a specific checkpoint",
        )

        # Output and workspace
        parser.add_argument(
            "--workspace-dir",
            help="Base workspace directory for orchestrator (default: ./orchestrator_output)",
        )

        parser.add_argument(
            "--keep-workspace",
            action="store_true",
            help="Keep workspace directory after completion",
        )

        # Debug and logging
        parser.add_argument(
            "--verbose", action="store_true", help="Enable verbose logging"
        )

        parser.add_argument("--debug", action="store_true", help="Enable debug logging")

        return parser

    async def run(self, args: argparse.Namespace) -> int:
        """Run orchestrator task based on arguments"""

        # Set logging level
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        elif args.verbose:
            logging.getLogger().setLevel(logging.INFO)

        # Determine workspace directory
        if args.workspace_dir:
            workspace_dir = Path(args.workspace_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workspace_dir = Path("./orchestrator_output") / timestamp

        workspace_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using workspace: {workspace_dir}")

        # Initialize orchestrator
        orchestrator = ResumableDocumentationOrchestrator(
            output_dir=workspace_dir,
            max_parallel=args.max_parallel,
            checkpoint_interval=args.checkpoint_interval,
        )

        try:
            # Handle different command types
            if args.list_checkpoints:
                return self._list_checkpoints(orchestrator, args)

            elif args.checkpoint_details:
                return self._show_checkpoint_details(orchestrator, args)

            elif args.resume_checkpoint:
                return await self._resume_checkpoint(orchestrator, args)

            elif args.task_type == "system-documentation":
                return await self._run_system_documentation(orchestrator, args)

            else:
                logger.error(
                    "No valid task specified. Use --help for usage information."
                )
                return 1

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            if args.debug:
                import traceback

                logger.error(traceback.format_exc())
            return 1

        finally:
            # Cleanup workspace if requested
            if not args.keep_workspace and not args.resume_checkpoint:
                logger.info(f"Cleaning up workspace: {workspace_dir}")
                # Note: In practice, you might want to keep logs and results

    def _list_checkpoints(
        self, orchestrator: ResumableDocumentationOrchestrator, args: argparse.Namespace
    ) -> int:
        """List available checkpoints"""

        checkpoints = orchestrator.list_checkpoints(app_name=args.app_name)

        if not checkpoints:
            print("No checkpoints found.")
            return 0

        print(
            f"\nAvailable checkpoints{' for ' + args.app_name if args.app_name else ''}:"
        )
        print("-" * 80)

        for cp in checkpoints:
            status = "✓ Ready to resume" if cp["can_resume"] else "✗ Already completed"
            print(f"ID: {cp['checkpoint_id']}")
            print(f"  App: {cp['app_name']}")
            print(f"  Date: {cp['timestamp']}")
            print(
                f"  Progress: {cp['completed_tasks']} completed, {cp['failed_tasks']} failed, {cp['pending_tasks']} pending"
            )
            print(f"  Status: {status}")
            print()

        return 0

    def _show_checkpoint_details(
        self, orchestrator: ResumableDocumentationOrchestrator, args: argparse.Namespace
    ) -> int:
        """Show detailed checkpoint information"""

        details = orchestrator.get_checkpoint_details(args.checkpoint_details)

        if not details:
            print(f"Checkpoint not found: {args.checkpoint_details}")
            return 1

        checkpoint = details["checkpoint"]
        progress = details["progress"]

        print(f"\nCheckpoint Details: {args.checkpoint_details}")
        print("-" * 80)
        print(f"App Name: {checkpoint['app_name']}")
        print(f"Workflow: {checkpoint['workflow_type']}")
        print(f"Created: {checkpoint['timestamp']}")
        print(f"Can Resume: {'Yes' if details['can_resume'] else 'No'}")
        print(
            f"\nProgress: {progress['completed']}/{progress['total']} tasks completed"
        )
        print(f"  ✓ Completed: {progress['completed']}")
        print(f"  ✗ Failed: {progress['failed']}")
        print(f"  ⏳ Pending: {progress['pending']}")

        if checkpoint["completed_tasks"]:
            print(f"\nCompleted Tasks:")
            for task in checkpoint["completed_tasks"]:
                print(f"  ✓ {task}")

        if checkpoint["failed_tasks"]:
            print(f"\nFailed Tasks:")
            for task in checkpoint["failed_tasks"]:
                print(f"  ✗ {task}")

        if checkpoint["pending_tasks"]:
            print(f"\nPending Tasks:")
            for task in checkpoint["pending_tasks"]:
                print(f"  ⏳ {task}")

        return 0

    async def _resume_checkpoint(
        self, orchestrator: ResumableDocumentationOrchestrator, args: argparse.Namespace
    ) -> int:
        """Resume execution from checkpoint"""

        logger.info(f"Resuming from checkpoint: {args.resume_checkpoint}")

        try:
            summary = await orchestrator._resume_from_checkpoint(args.resume_checkpoint)

            print(f"\nResume execution completed!")
            print("-" * 50)
            print(f"App: {summary['app_name']}")
            print(
                f"Tasks completed: {summary['completed_tasks']}/{summary['total_tasks']}"
            )
            print(f"Success rate: {summary['success_rate']:.1f}%")
            print(f"Output directory: {summary['output_dir']}")

            if summary["failed_tasks"] > 0:
                print(f"⚠️  {summary['failed_tasks']} tasks failed")
                return 1

            return 0

        except Exception as e:
            logger.error(f"Resume failed: {e}")
            return 1

    async def _run_system_documentation(
        self, orchestrator: ResumableDocumentationOrchestrator, args: argparse.Namespace
    ) -> int:
        """Run system documentation workflow"""

        # Validate required arguments
        if not args.app_name:
            logger.error("--app-name is required for system-documentation")
            return 1

        if not args.app_root:
            logger.error("--app-root is required for system-documentation")
            return 1

        app_root = Path(args.app_root)
        if not app_root.exists():
            logger.error(f"App root directory does not exist: {app_root}")
            return 1

        logger.info(f"Starting system documentation workflow for {args.app_name}")

        # Prepare configuration kwargs
        config_kwargs = {}
        if hasattr(args, "include_api_docs"):
            config_kwargs["include_api_docs"] = args.include_api_docs
        if hasattr(args, "include_architecture"):
            config_kwargs["include_architecture"] = args.include_architecture
        if hasattr(args, "include_deployment"):
            config_kwargs["include_deployment"] = args.include_deployment
        if hasattr(args, "include_user_guide"):
            config_kwargs["include_user_guide"] = args.include_user_guide
        if hasattr(args, "detail_level"):
            config_kwargs["detail_level"] = args.detail_level

        try:
            summary = await orchestrator.execute_system_documentation(
                app_name=args.app_name,
                app_root=str(app_root),
                output_dir=args.output_dir,
                template=args.template,
                **config_kwargs,
            )

            print(f"\nSystem documentation workflow completed!")
            print("-" * 50)
            print(f"App: {summary['app_name']}")
            print(f"Template: {args.template}")
            print(
                f"Tasks completed: {summary['completed_tasks']}/{summary['total_tasks']}"
            )
            print(f"Success rate: {summary['success_rate']:.1f}%")
            print(f"Output directory: {summary['output_dir']}")

            if summary["failed_tasks"] > 0:
                print(f"⚠️  {summary['failed_tasks']} tasks failed")
                print(
                    f"You can resume with: --resume-checkpoint {summary['final_checkpoint']}"
                )
                return 1

            print(f"\n✓ Documentation generated successfully!")
            print(f"📝 View results in: {summary['output_dir']}")

            return 0

        except Exception as e:
            logger.error(f"Documentation workflow failed: {e}")
            return 1


async def main():
    """Main entry point"""

    cli = OrchestratorCLI()
    args = cli.parser.parse_args()

    return await cli.run(args)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
