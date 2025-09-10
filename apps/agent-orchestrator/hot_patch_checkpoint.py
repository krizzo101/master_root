#!/usr/bin/env python3
"""
Hot-patch running checkpoint to enable parallelization
"""

import json
import shutil
from datetime import datetime
from pathlib import Path


def patch_checkpoint(checkpoint_file):
    """Modify checkpoint to parallelize remaining tasks"""

    # Backup original
    backup = f"{checkpoint_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(checkpoint_file, backup)
    print(f"✅ Backed up to: {backup}")

    # Load checkpoint
    checkpoint = json.loads(Path(checkpoint_file).read_text())

    # Modify dependencies for remaining tasks
    patched = False
    for task in checkpoint.get("all_tasks", []):
        task_id = task["task_id"]

        # Check if task is not yet completed
        completed_ids = [t["task_id"] for t in checkpoint.get("completed_tasks", [])]
        if task_id not in completed_ids:
            # Apply parallelization optimizations
            if task_id in [
                "014_break_god_object",
                "015_dependency_injection",
                "016_domain_driven_design",
            ]:
                task["dependencies"] = ["013_commit_resources"]
                patched = True
                print(f"  • Parallelized: {task_id}")

            elif task_id == "017_integration_tests":
                task["dependencies"] = [
                    "014_break_god_object",
                    "015_dependency_injection",
                    "016_domain_driven_design",
                ]
                patched = True
                print(f"  • Updated deps: {task_id}")

            elif task_id in ["020_update_documentation", "021_security_audit"]:
                task["dependencies"] = ["019_performance_comparison"]
                patched = True
                print(f"  • Parallelized: {task_id}")

            elif task_id == "022_final_validation":
                task["dependencies"] = [
                    "020_update_documentation",
                    "021_security_audit",
                ]
                patched = True
                print(f"  • Updated deps: {task_id}")

    if patched:
        # Save patched checkpoint
        Path(checkpoint_file).write_text(json.dumps(checkpoint, indent=2))
        print(f"\n✅ Hot-patched checkpoint: {checkpoint_file}")
        print("   Workflow will use parallel execution for:")
        print("   - Tasks 14-16 (architecture refactoring)")
        print("   - Tasks 20-21 (docs & security)")
    else:
        print("⚠️  No tasks to patch (already completed or not found)")

    return patched


if __name__ == "__main__":
    checkpoint_file = (
        "output/self_improvement_resumed/checkpoints/latest_checkpoint.json"
    )
    patch_checkpoint(checkpoint_file)
