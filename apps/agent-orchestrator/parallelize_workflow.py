#!/usr/bin/env python3
"""
Parallelize workflow by optimizing task dependencies
"""

import json
import sys
from pathlib import Path


def optimize_dependencies(workflow_file):
    """Remove unnecessary sequential dependencies to enable parallelization"""

    workflow = json.loads(Path(workflow_file).read_text())
    tasks = workflow["tasks"]

    # Create optimized workflow
    optimized = workflow.copy()

    # Parallel optimization opportunities:
    # 1. Tasks 14-16 (architecture refactoring) can run in parallel after 13
    # 2. Tasks 20-21 (docs & security) can run in parallel after 19

    for task in optimized["tasks"]:
        task_id = task["task_id"]

        # Architecture refactoring tasks - all depend on 13 instead of each other
        if task_id in [
            "014_break_god_object",
            "015_dependency_injection",
            "016_domain_driven_design",
        ]:
            task["dependencies"] = ["013_commit_resources"]

        # Integration tests wait for all architecture tasks
        elif task_id == "017_integration_tests":
            task["dependencies"] = [
                "014_break_god_object",
                "015_dependency_injection",
                "016_domain_driven_design",
            ]

        # Docs and security can run in parallel
        elif task_id in ["020_update_documentation", "021_security_audit"]:
            task["dependencies"] = ["019_performance_comparison"]

        # Final validation waits for both
        elif task_id == "022_final_validation":
            task["dependencies"] = ["020_update_documentation", "021_security_audit"]

    # Save optimized workflow
    output_file = workflow_file.replace(".json", "_parallel.json")
    Path(output_file).write_text(json.dumps(optimized, indent=2))

    print(f"✅ Created parallelized workflow: {output_file}")
    print("\nOptimizations made:")
    print("  • Tasks 14-16 (architecture) now run in parallel")
    print("  • Tasks 20-21 (docs/security) now run in parallel")
    print(f"  • Potential time savings: ~40% reduction")

    return output_file


if __name__ == "__main__":
    if len(sys.argv) > 1:
        optimize_dependencies(sys.argv[1])
    else:
        # Default to self-improvement workflow
        optimize_dependencies("orchestrator_self_improvement_flat.json")
