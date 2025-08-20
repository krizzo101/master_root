#!/usr/bin/env python3
"""
SDLC Execute Phase - Runs claude-code MCP with full session export
Combines phase execution with comprehensive logging and export
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def execute_phase_with_export(phase: str) -> None:
    """
    Execute SDLC phase using claude-code MCP with session export.

    Args:
        phase: The SDLC phase to execute
    """
    # Import the phase task definitions
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sdlc_phase_executor_v2", Path(__file__).parent / "sdlc-phase-executor-v2.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    PHASE_TASKS = module.PHASE_TASKS

    if phase not in PHASE_TASKS:
        print(f"Error: Unknown phase '{phase}'")
        print(f"Valid phases: {', '.join(PHASE_TASKS.keys())}")
        sys.exit(1)

    # Get the task for this phase
    task = PHASE_TASKS[phase]()

    # Setup export directory
    export_dir = Path("/home/opsvi/master_root/.sdlc-sessions")
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create pre-execution snapshot
    pre_snapshot = {
        "phase": phase,
        "timestamp": timestamp,
        "task": task,
        "environment": {
            "cwd": os.getcwd(),
            "user": os.environ.get("USER", "unknown"),
            "python_version": sys.version,
        },
    }

    snapshot_file = export_dir / f"{phase}_{timestamp}_pre.json"
    with open(snapshot_file, "w") as f:
        json.dump(pre_snapshot, f, indent=2)

    print(f"{'='*60}")
    print(f"EXECUTING {phase.upper()} PHASE WITH SESSION EXPORT")
    print(f"{'='*60}")
    print(f"Export directory: {export_dir}")
    print(f"Pre-execution snapshot: {snapshot_file}")
    print()

    # Here's where we would call the MCP tool
    # For now, showing the structure
    print("Executing via MCP:")
    print("mcp__claude-code-wrapper__claude_run(")
    print(f'    task="""{task}""",')
    print('    outputFormat="json",')
    print('    permissionMode="bypassPermissions",')
    print("    verbose=True")
    print(")")
    print()

    # The actual execution would be:
    """
    try:
        result = mcp__claude-code-wrapper__claude_run(
            task=task,
            outputFormat="json",
            permissionMode="bypassPermissions",
            verbose=True
        )

        # Save the result
        result_file = export_dir / f"{phase}_{timestamp}_result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"Result saved to: {result_file}")

        # Create post-execution summary
        summary = {
            "phase": phase,
            "timestamp": timestamp,
            "status": "success" if not result.get("is_error") else "error",
            "duration_ms": result.get("duration_ms", 0),
            "cost_usd": result.get("total_cost_usd", 0),
            "session_id": result.get("session_id", "unknown"),
            "files": {
                "pre_snapshot": str(snapshot_file),
                "result": str(result_file)
            }
        }

        summary_file = export_dir / f"{phase}_{timestamp}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"Summary saved to: {summary_file}")

    except Exception as e:
        error_file = export_dir / f"{phase}_{timestamp}_error.json"
        with open(error_file, 'w') as f:
            json.dump({
                "phase": phase,
                "timestamp": timestamp,
                "error": str(e),
                "traceback": traceback.format_exc()
            }, f, indent=2)

        print(f"Error saved to: {error_file}")
        raise
    """

    # For demonstration, create a mock result
    mock_result = {
        "phase": phase,
        "timestamp": timestamp,
        "status": "mock_execution",
        "note": "This is where actual MCP execution would occur",
        "export_files": {
            "pre_snapshot": str(snapshot_file),
            "session": f"{export_dir}/{phase}_{timestamp}_session.json",
            "result": f"{export_dir}/{phase}_{timestamp}_result.json",
        },
    }

    result_file = export_dir / f"{phase}_{timestamp}_mock_result.json"
    with open(result_file, "w") as f:
        json.dump(mock_result, f, indent=2)

    print(f"Mock result saved to: {result_file}")
    print()
    print("Session export complete!")
    print(f"All files saved to: {export_dir}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python sdlc-execute-phase.py <phase>")
        print(
            "Phases: discovery, design, planning, development, testing, deployment, "
            "production, postmortem"
        )
        sys.exit(1)

    phase = sys.argv[1].lower()
    execute_phase_with_export(phase)


if __name__ == "__main__":
    main()
