#!/usr/bin/env python3
"""
SDLC Phase Executor V2 - Optimized for parallel execution and focus
"""

import json
import sys
from datetime import datetime


def get_discovery_task():
    """Get optimized Discovery phase task."""
    return """Execute SDLC Discovery Phase ONLY.

FOCUS: Requirements gathering and research
DELIVERABLES:
- /home/opsvi/master_root/apps/hello-cli/docs/1-requirements.md
- /home/opsvi/master_root/apps/hello-cli/.sdlc/discovery-complete.json

REQUIRED ACTIONS:
1. Read /home/opsvi/master_root/.claude/agents/sdlc-discovery.md
2. Use mcp__knowledge__knowledge_query to check for existing solutions
3. Research with brave_web_search for "Python CLI best practices 2025"
4. Create requirements document
5. Create gate file

DO NOT: Fix unrelated issues, modify .gitignore, or work on other phases."""


def get_design_task():
    """Get optimized Design phase task."""
    return """Execute SDLC Design Phase ONLY.

FOCUS: Architecture design based on requirements
DELIVERABLES:
- /home/opsvi/master_root/apps/hello-cli/docs/2-design.md
- /home/opsvi/master_root/apps/hello-cli/.sdlc/design-complete.json

REQUIRED ACTIONS:
1. Read /home/opsvi/master_root/.claude/agents/sdlc-design.md
2. Read existing requirements from docs/1-requirements.md
3. Create architecture with mermaid diagrams
4. Define technology stack
5. Create design document and gate file

DO NOT: Implement code, fix project setup issues, or modify other files."""


def get_planning_task():
    """Get optimized Planning phase task."""
    return """Execute SDLC Planning Phase ONLY.

FOCUS: Task breakdown and scheduling
DELIVERABLES:
- /home/opsvi/master_root/apps/hello-cli/docs/3-planning.md
- /home/opsvi/master_root/apps/hello-cli/.sdlc/planning-complete.json

Create task breakdown with <2 hour tasks.
Include dependencies and effort estimates.

DO NOT: Start implementation or fix other issues."""


def get_development_task():
    """Get optimized Development phase task with PARALLEL execution."""
    return """Execute SDLC Development Phase with PARALLEL agents.

USE THE TASK TOOL to spawn parallel agents for faster execution:

Task(
    description="Implement core modules",
    subagent_type="development-specialist",
    prompt="Implement hello_cli/core.py, config.py, greeter.py based on design"
)

Task(
    description="Implement CLI interface",
    subagent_type="development-specialist",
    prompt="Implement hello_cli/cli.py and __main__.py based on design"
)

Task(
    description="Write unit tests",
    subagent_type="qa-testing-guru",
    prompt="Write comprehensive unit tests for all modules"
)

FOCUS: TDD implementation with parallel execution
DELIVERABLES:
- Complete hello_cli implementation in /home/opsvi/master_root/apps/hello-cli/src/
- Unit tests in /home/opsvi/master_root/apps/hello-cli/tests/
- /home/opsvi/master_root/apps/hello-cli/.sdlc/development-complete.json

CRITICAL: Use Task tool for parallel work. Commit after each component."""


def get_testing_task():
    """Get optimized Testing phase task."""
    return """Execute SDLC Testing Phase with PARALLEL test execution.

USE PARALLEL AGENTS:
- One for unit tests
- One for integration tests
- One for coverage analysis

FOCUS: Test execution and validation
DELIVERABLES:
- Test execution results
- Coverage report (>80%)
- /home/opsvi/master_root/apps/hello-cli/docs/4-testing.md
- /home/opsvi/master_root/apps/hello-cli/.sdlc/testing-complete.json

REQUIRED: Actually RUN tests, not just write them. Show output."""


def get_deployment_task():
    """Get optimized Deployment phase task."""
    return """Execute SDLC Deployment Phase ONLY.

FOCUS: Deployment preparation
DELIVERABLES:
- /home/opsvi/master_root/apps/hello-cli/docs/5-deployment.md
- Dockerfile if applicable
- CI/CD configuration
- /home/opsvi/master_root/apps/hello-cli/.sdlc/deployment-complete.json"""


def get_production_task():
    """Get optimized Production phase task."""
    return """Execute SDLC Production Phase ONLY.

FOCUS: Final review and handover
DELIVERABLES:
- /home/opsvi/master_root/apps/hello-cli/docs/6-production.md
- /home/opsvi/master_root/apps/hello-cli/.sdlc/production-complete.json"""


def get_postmortem_task():
    """Get optimized Postmortem phase task."""
    return """Execute SDLC Postmortem Phase ONLY.

FOCUS: Review and lessons learned
DELIVERABLES:
- /home/opsvi/master_root/apps/hello-cli/docs/6-postmortem.md
- /home/opsvi/master_root/apps/hello-cli/.sdlc/postmortem-complete.json

Analyze what was done vs what was planned.
Identify violations and lessons learned."""


# Phase task mapping
PHASE_TASKS = {
    "discovery": get_discovery_task,
    "design": get_design_task,
    "planning": get_planning_task,
    "development": get_development_task,
    "testing": get_testing_task,
    "deployment": get_deployment_task,
    "production": get_production_task,
    "postmortem": get_postmortem_task,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python sdlc-phase-executor-v2.py <phase>")
        print(
            "Phases: discovery, design, planning, development, testing, deployment, "
            "production, postmortem"
        )
        sys.exit(1)

    phase = sys.argv[1].lower()

    if phase not in PHASE_TASKS:
        print(f"Error: Unknown phase '{phase}'")
        print(f"Valid phases: {', '.join(PHASE_TASKS.keys())}")
        sys.exit(1)

    # Get the optimized task for this phase
    task = PHASE_TASKS[phase]()

    # Create execution parameters
    params = {
        "task": task,
        "phase": phase,
        "timestamp": datetime.now().isoformat(),
        "timeout_recommendation": "600 seconds for simple phases, 1200 for development/testing",
        "parallel_execution": phase in ["development", "testing"],
        "focus": f"ONLY {phase} phase deliverables",
    }

    # Output for debugging
    print(f"\n{'='*60}")
    print(f"SDLC PHASE EXECUTOR V2 - {phase.upper()}")
    print(f"{'='*60}")
    print("\nTask to execute:")
    print(task)
    print(f"\n{'='*60}")
    print("Execution parameters:")
    print(json.dumps(params, indent=2))
    print(f"{'='*60}\n")

    # Here you would call the MCP tool
    print("To execute, use:")
    print("mcp__claude-code-wrapper__claude_run(")
    print(f'    task="""{task}""",')
    print('    outputFormat="json",')
    print('    permissionMode="bypassPermissions",')
    print("    verbose=True")
    print(")")


if __name__ == "__main__":
    main()
