#!/usr/bin/env python3
"""
Standardized Resume - Universal checkpoint resumption for any orchestrator workflow
Handles both checkpoint files and task status, with UnifiedOrchestrator support
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.generic_orchestrator import AgentTask, GenericOrchestrator
from src.unified.unified_orchestrator import (
    FeatureFlag,
    UnifiedConfig,
    UnifiedOrchestrator,
)


class StandardizedResume:
    """Universal checkpoint resume handler"""

    def __init__(self, checkpoint_path: str = None, output_dir: str = None):
        """Initialize with either checkpoint file or output directory"""
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.output_dir = Path(output_dir) if output_dir else None

        # Auto-detect checkpoint if only output_dir provided
        if not self.checkpoint_path and self.output_dir:
            self._find_latest_checkpoint()

    def _find_latest_checkpoint(self):
        """Find the most recent checkpoint in output directory"""
        checkpoint_dir = self.output_dir / "checkpoints"
        if checkpoint_dir.exists():
            # Try latest_checkpoint.json first
            latest = checkpoint_dir / "latest_checkpoint.json"
            if latest.exists():
                self.checkpoint_path = latest
            else:
                # Find most recent checkpoint_*.json
                checkpoints = sorted(checkpoint_dir.glob("checkpoint_*.json"))
                if checkpoints:
                    self.checkpoint_path = checkpoints[-1]

    def analyze_checkpoint(self):
        """Analyze checkpoint to determine resume strategy"""
        if not self.checkpoint_path or not self.checkpoint_path.exists():
            return None

        with open(self.checkpoint_path) as f:
            checkpoint = json.load(f)

        return {
            "workflow_id": checkpoint.get("workflow_id"),
            "workflow_source": checkpoint.get("workflow_source", "generic"),
            "completed_tasks": checkpoint.get("completed_tasks", []),
            "failed_tasks": checkpoint.get("failed_tasks", []),
            "running_tasks": checkpoint.get("running_tasks", []),
            "total_tasks": checkpoint.get("metrics", {}).get("total", 0),
            "completed_count": checkpoint.get("metrics", {}).get("completed", 0),
            "output_dir": self.checkpoint_path.parent.parent,
        }

    async def resume_unified(self, analysis):
        """Resume using UnifiedOrchestrator with all features"""
        print(f"🔄 Resuming UnifiedOrchestrator workflow: {analysis['workflow_id']}")

        # Find the workflow file used (checking for various patterns)
        workflow_files = [
            "orchestrator_self_improvement_resume_task12.json",
            "orchestrator_self_improvement_flat_parallel.json",
            "orchestrator_self_improvement.json",
            "workflow.json",
        ]

        workflow_file = None
        for wf in workflow_files:
            if Path(wf).exists():
                workflow_file = wf
                break

        if not workflow_file:
            print("❌ Could not find workflow file to resume")
            return False

        # Load workflow and filter to uncompleted tasks
        with open(workflow_file) as f:
            workflow = json.load(f)

        # Filter tasks to only those not completed
        remaining_tasks = []
        for task in workflow.get("tasks", []):
            if task["task_id"] not in analysis["completed_tasks"]:
                # Clear dependencies to completed tasks
                new_deps = [
                    d
                    for d in task.get("dependencies", [])
                    if d not in analysis["completed_tasks"]
                ]
                task["dependencies"] = new_deps
                remaining_tasks.append(task)

        if not remaining_tasks:
            print("✅ All tasks already completed!")
            return True

        print(f"📋 Resuming {len(remaining_tasks)} remaining tasks")

        # Create new workflow with remaining tasks
        resume_workflow = {
            "workflow_name": f"resume_{analysis['workflow_id']}",
            "description": f"Resuming from checkpoint with {len(remaining_tasks)} tasks",
            "tasks": remaining_tasks,
        }

        # Save resume workflow
        resume_file = f"resume_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(resume_file, "w") as f:
            json.dump(resume_workflow, f, indent=2)

        print(f"💾 Saved resume workflow to: {resume_file}")

        # Configure UnifiedOrchestrator
        config = UnifiedConfig(
            output_dir=analysis["output_dir"],
            max_parallel=15,  # Optimized for 28GB RAM
            enabled_features={
                FeatureFlag.QUALITY_GATES,
                FeatureFlag.AGENT_MONITORING,
                FeatureFlag.COLLABORATION,
                FeatureFlag.EXECUTION_PLAN,
                FeatureFlag.ENHANCED_METRICS,
                FeatureFlag.BACKGROUND_EXECUTION,
                FeatureFlag.AUTO_RECOVERY,
                FeatureFlag.STATE_PERSISTENCE,
            },
            enable_monitoring=True,
            enable_quality_gates=True,
            enable_collaboration=True,
        )

        # Create and run orchestrator
        orchestrator = UnifiedOrchestrator(config)

        # Convert tasks to AgentTask objects
        agent_tasks = []
        for task in remaining_tasks:
            agent_task = AgentTask(
                task_id=task["task_id"],
                task_type=task["task_type"],
                prompt=task["prompt"],
                context=task.get("context", {}),
                dependencies=task.get("dependencies", []),
                quality_gates=task.get("quality_gates", []),
            )
            agent_tasks.append(agent_task)

        print("🚀 Starting UnifiedOrchestrator execution...")
        await orchestrator.execute(agent_tasks)

        return True

    async def resume_generic(self, analysis):
        """Resume using GenericOrchestrator"""
        print(f"🔄 Resuming GenericOrchestrator workflow")

        orchestrator = GenericOrchestrator(
            output_dir=analysis["output_dir"], max_parallel=10
        )

        # Load tasks from directory
        tasks_dir = analysis["output_dir"] / "tasks"
        if tasks_dir.exists():
            pending_tasks = []
            for task_file in tasks_dir.glob("*.json"):
                with open(task_file) as f:
                    task_data = json.load(f)
                if task_data.get("status") != "completed":
                    pending_tasks.append(task_file.stem)

            if pending_tasks:
                print(f"📋 Found {len(pending_tasks)} pending tasks")
                await orchestrator.run()

        return True

    async def resume(self):
        """Main resume method - auto-detects and resumes appropriately"""
        # Analyze checkpoint
        analysis = self.analyze_checkpoint()
        if not analysis:
            print("❌ No valid checkpoint found")
            return False

        # Print status
        print("\n" + "=" * 60)
        print("CHECKPOINT ANALYSIS")
        print("=" * 60)
        print(f"Workflow ID: {analysis['workflow_id']}")
        print(f"Source: {analysis['workflow_source']}")
        print(
            f"Progress: {analysis['completed_count']}/{analysis['total_tasks']} tasks"
        )
        print(
            f"Completed: {', '.join(analysis['completed_tasks'][:3])}{'...' if len(analysis['completed_tasks']) > 3 else ''}"
        )
        if analysis["failed_tasks"]:
            print(f"Failed: {', '.join(analysis['failed_tasks'])}")
        if analysis["running_tasks"]:
            print(f"Running: {', '.join(analysis['running_tasks'])}")
        print("=" * 60 + "\n")

        # Choose resume strategy based on workflow source
        if "unified" in analysis["workflow_source"]:
            return await self.resume_unified(analysis)
        else:
            return await self.resume_generic(analysis)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Standardized checkpoint resume")
    parser.add_argument("path", help="Checkpoint file or output directory")
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=15,
        help="Maximum parallel agents (default: 15)",
    )

    args = parser.parse_args()

    # Determine if path is checkpoint or directory
    path = Path(args.path)
    if path.is_file():
        resumer = StandardizedResume(checkpoint_path=args.path)
    else:
        resumer = StandardizedResume(output_dir=args.path)

    # Run resume
    success = asyncio.run(resumer.resume())

    if success:
        print("\n✅ Resume completed successfully!")
    else:
        print("\n❌ Resume failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
