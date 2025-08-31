"""
Task creation and routing for HECATON orchestration
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List

from ..orchestration.merger import ConflictReport, GatesReport


def create_fixit_tasks(
    conflicts: List[ConflictReport], gates_report: GatesReport = None, run_id: str = None
) -> List[Dict[str, Any]]:
    """
    Create Fix-It tasks for conflict resolution and gate failures

    Args:
        conflicts: List of conflict reports from patch application
        gates_report: Optional gates report with failures
        run_id: Run identifier for context

    Returns:
        List of Fix-It agent tasks
    """
    tasks = []

    # Create tasks for conflicts
    for i, conflict in enumerate(conflicts):
        # Build conflict context
        context_lines = []
        context_lines.append(f"Conflict in patch from agent: {conflict.agent_id}")
        context_lines.append(f"Affected files: {', '.join(conflict.conflicted_files)}")

        if conflict.conflict_diff:
            context_lines.append("\nConflict details:")
            # Limit diff to reasonable size
            diff_lines = conflict.conflict_diff.split("\n")[:50]
            context_lines.extend(diff_lines)

        prompt = f"""Fix merge conflict in integration branch.

Context:
{chr(10).join(context_lines)}

Instructions:
1. Analyze the conflict and understand what both versions are trying to achieve
2. Create a resolution that preserves the intent of both changes
3. Ensure the resolved code is syntactically correct and functional
4. Generate a clean patch that applies to integration/{run_id}
5. Include a brief explanation of the resolution strategy

Original patch: {conflict.patch_file}
Target branch: integration/{run_id}
"""

        task = {
            "id": f"fixit_conflict_{i}_{conflict.agent_id}",
            "agent_type": "code",  # Use code agent for conflict resolution
            "prompt": prompt,
            "run_id": run_id,
            "sequence": 100 + i,  # Higher sequence for fix-it tasks
            "export_patch": True,
            "worktree": None,  # Will be created from integration branch
            "metadata": {
                "task_type": "conflict_resolution",
                "original_agent": conflict.agent_id,
                "conflicted_files": conflict.conflicted_files,
            },
        }

        tasks.append(task)

    # Create tasks for gate failures
    if gates_report and not gates_report.success:
        for i, (cmd, error) in enumerate(gates_report.failed_gates):
            prompt = f"""Fix quality gate failure.

Failed command: {cmd}
Error output:
{error[:1000]}  # Limit error output

Instructions:
1. Analyze the failure and identify the root cause
2. Fix the issues causing the gate to fail
3. Ensure the fix doesn't break other functionality
4. Verify the gate would pass after your changes
5. Create a patch with your fixes

Target branch: integration/{run_id}
"""

            task = {
                "id": (
                    f"fixit_gate_{i}_"
                    f"{hashlib.md5(cmd.encode(), usedforsecurity=False).hexdigest()[:8]}"
                ),
                "agent_type": "code",
                "prompt": prompt,
                "run_id": run_id,
                "sequence": 200 + i,  # Even higher sequence for gate fixes
                "export_patch": True,
                "worktree": None,
                "metadata": {
                    "task_type": "gate_fix",
                    "failed_command": cmd,
                },
            }

            tasks.append(task)

    return tasks


def create_review_tasks(patches: List[Dict[str, Any]], run_id: str = None) -> List[Dict[str, Any]]:
    """
    Create review tasks for merged patches

    Args:
        patches: List of patch manifests
        run_id: Run identifier

    Returns:
        List of review agent tasks
    """
    tasks = []

    # Group patches by functional area
    grouped = {}
    for patch in patches:
        files = patch.get("files_changed", [])
        # Simple grouping by top-level directory
        for file in files:
            parts = Path(file).parts
            if parts:
                area = parts[0]
                if area not in grouped:
                    grouped[area] = []
                grouped[area].append(patch)

    # Create review task for each area
    for area, area_patches in grouped.items():
        patch_summaries = []
        for p in area_patches:
            patch_summaries.append(
                f"- {p['agent_role']}/{p['agent_id']}: "
                f"{p['insertions']}+ {p['deletions']}- in {len(p['files_changed'])} files"
            )

        prompt = f"""Review merged changes in {area}.

Patches included:
{chr(10).join(patch_summaries)}

Review checklist:
1. Code quality and style consistency
2. Potential bugs or logic errors
3. Security vulnerabilities
4. Performance implications
5. Test coverage adequacy
6. Documentation completeness

Provide a detailed review with:
- Summary of changes
- Issues found (if any)
- Recommendations for improvement
- Overall assessment

Target: integration/{run_id}
"""

        task = {
            "id": (
                f"review_{area}_"
                f"{hashlib.md5(area.encode(), usedforsecurity=False).hexdigest()[:8]}"
            ),
            "agent_type": "review",
            "prompt": prompt,
            "run_id": run_id,
            "sequence": 300,  # Review tasks run last
            "export_patch": False,  # Reviews don't create patches
            "metadata": {
                "task_type": "review",
                "area": area,
                "patch_count": len(area_patches),
            },
        }

        tasks.append(task)

    return tasks
