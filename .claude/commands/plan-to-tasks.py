#!/usr/bin/env python3
"""
Convert SDLC planning document into TodoWrite tasks.
Ensures plan is followed by creating trackable tasks.
"""

import json
import re
from pathlib import Path
from typing import Dict, List


def parse_planning_document(planning_file: Path) -> List[Dict]:
    """Extract tasks from planning markdown."""
    tasks = []

    with open(planning_file) as f:
        content = f.read()

    # Find task tables using regex
    # Format: | Task ID | Task | Effort | Dependencies | Acceptance Criteria |
    task_pattern = r"\|\s*([\w-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"

    for match in re.finditer(task_pattern, content):
        task_id = match.group(1).strip()
        task_name = match.group(2).strip()
        effort = match.group(3).strip()
        deps = match.group(4).strip()
        criteria = match.group(5).strip()

        # Skip header rows
        if task_id == "Task ID" or task_id.startswith("-"):
            continue

        tasks.append(
            {
                "id": task_id,
                "content": f"{task_id}: {task_name} ({effort})",
                "status": "pending",
                "metadata": {
                    "effort": effort,
                    "dependencies": deps,
                    "acceptance_criteria": criteria,
                },
            }
        )

    return tasks


def generate_todo_commands(tasks: List[Dict]) -> str:
    """Generate TodoWrite command for all tasks."""

    # Group tasks by phase
    phases = {}
    for task in tasks:
        phase = task["id"].split("-")[0]
        if phase not in phases:
            phases[phase] = []
        phases[phase].append(task)

    # Generate TodoWrite command
    todo_items = []
    for phase, phase_tasks in phases.items():
        # Add phase header
        todo_items.append(
            {
                "id": f"{phase}-PHASE",
                "content": f"===== {phase} PHASE =====",
                "status": "pending",
            }
        )
        # Add tasks
        for task in phase_tasks:
            todo_items.append(
                {"id": task["id"], "content": task["content"], "status": "pending"}
            )

    return f"""TodoWrite(todos={json.dumps(todo_items, indent=2)})"""


def create_task_validation_script(tasks: List[Dict], project_name: str) -> str:
    """Create script to validate task completion."""

    script = f"""#!/usr/bin/env python3
'''
Validate that all planned tasks have been completed for {project_name}.
Auto-generated from planning document.
'''

import json
from pathlib import Path

REQUIRED_TASKS = {json.dumps([t['id'] for t in tasks], indent=2)}

def validate_task_completion(project_path: Path) -> bool:
    '''Check if all tasks are marked complete.'''

    # Read development artifact
    dev_complete = project_path / '.sdlc' / 'development-complete.json'
    if not dev_complete.exists():
        print("❌ Development artifact not found")
        return False

    with open(dev_complete) as f:
        data = json.load(f)

    completed = set(data.get('tasks_completed', []))
    required = set(REQUIRED_TASKS)

    missing = required - completed
    if missing:
        print(f"❌ Missing tasks: {{missing}}")
        return False

    print(f"✅ All {{len(required)}} tasks completed")
    return True

if __name__ == "__main__":
    import sys
    project = Path(sys.argv[1])
    if not validate_task_completion(project):
        sys.exit(1)
"""

    return script


# Usage example
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python plan-to-tasks.py <planning-doc.md> [project-name]")
        sys.exit(1)

    planning_file = Path(sys.argv[1])
    project_name = sys.argv[2] if len(sys.argv) > 2 else "project"

    # Parse tasks
    tasks = parse_planning_document(planning_file)
    print(f"Found {len(tasks)} tasks in planning document\n")

    # Generate TodoWrite command
    print("TodoWrite Command:")
    print("=" * 50)
    print(generate_todo_commands(tasks))
    print("=" * 50)

    # Save validation script
    validation_script = create_task_validation_script(tasks, project_name)
    validation_file = Path(f"validate_{project_name}_tasks.py")
    validation_file.write_text(validation_script)
    print(f"\nValidation script saved to: {validation_file}")

    # Create task tracking file
    tracking = {"project": project_name, "total_tasks": len(tasks), "tasks": tasks}
    tracking_file = Path(".sdlc/task_tracking.json")
    tracking_file.parent.mkdir(exist_ok=True)
    tracking_file.write_text(json.dumps(tracking, indent=2))
    print(f"Task tracking saved to: {tracking_file}")
