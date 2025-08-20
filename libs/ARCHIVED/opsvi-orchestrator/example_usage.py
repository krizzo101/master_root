#!/usr/bin/env python3
"""
Example usage of the SDLC Orchestration System for a real project.
This shows how to integrate the orchestrator into your development workflow.
"""

import json
from datetime import datetime
from pathlib import Path

from decomposer import MicroTask

# Import orchestration components
from real_executor import (
    RealWorldExecutor,
    create_mcp_callback,
    create_task_tool_callback,
)


def create_custom_cli_project():
    """
    Example: Using the orchestrator to build a CLI application.
    """
    print("=" * 70)
    print("EXAMPLE: Building a CLI Application with Orchestration")
    print("=" * 70)

    project_name = "my-awesome-cli"
    project_root = Path(f"/home/opsvi/master_root/apps/{project_name}")

    print(f"\nProject: {project_name}")
    print(f"Location: {project_root}")
    print("\n" + "-" * 70)

    # Step 1: Create custom micro-tasks for the project
    custom_tasks = {
        "discovery": [
            MicroTask(
                id="cli_requirements",
                name="Gather CLI Requirements",
                phase="discovery",
                wave=1,
                tools=["file_reader", "mcp__knowledge__knowledge_query"],
                outputs=["docs/requirements.md", "docs/user_stories.md"],
                timeout_seconds=180,
                metadata={"focus": "CLI command structure and user workflows"},
            ),
            MicroTask(
                id="cli_research",
                name="Research CLI Best Practices",
                phase="discovery",
                wave=1,
                tools=["brave_web_search", "mcp__tech_docs__get-library-docs"],
                outputs=["docs/research.md", "docs/libraries.json"],
                timeout_seconds=240,
                metadata={"focus": "Click, Typer, Rich libraries for Python CLIs"},
            ),
        ],
        "development": [
            # Wave 1: Setup
            MicroTask(
                id="project_structure",
                name="Create Project Structure",
                phase="development",
                wave=1,
                tools=["file_writer", "directory_creator"],
                outputs=["src/__init__.py", "tests/__init__.py", "setup.py"],
                timeout_seconds=120,
                metadata={"template": "python-cli"},
            ),
            MicroTask(
                id="cli_interface",
                name="Define CLI Interface",
                phase="development",
                wave=1,
                tools=["file_writer"],
                outputs=["src/cli.py", "src/commands/__init__.py"],
                timeout_seconds=180,
                metadata={"library": "click"},
            ),
            # Wave 2: Implementation
            MicroTask(
                id="core_commands",
                name="Implement Core Commands",
                phase="development",
                wave=2,
                dependencies=["cli_interface"],
                tools=["file_writer", "mcp__thinking__sequentialthinking"],
                outputs=[
                    "src/commands/init.py",
                    "src/commands/run.py",
                    "src/commands/config.py",
                ],
                timeout_seconds=300,
                metadata={"commands": ["init", "run", "config"]},
            ),
            MicroTask(
                id="utilities",
                name="Create Utility Functions",
                phase="development",
                wave=2,
                dependencies=["project_structure"],
                tools=["file_writer"],
                outputs=["src/utils.py", "src/validators.py"],
                timeout_seconds=240,
            ),
            # Wave 3: Testing
            MicroTask(
                id="unit_tests",
                name="Write Unit Tests",
                phase="development",
                wave=3,
                dependencies=["core_commands", "utilities"],
                tools=["file_writer", "test_runner"],
                outputs=["tests/test_commands.py", "tests/test_utils.py"],
                timeout_seconds=300,
                metadata={"framework": "pytest"},
            ),
            MicroTask(
                id="integration_tests",
                name="Write Integration Tests",
                phase="development",
                wave=3,
                dependencies=["core_commands"],
                tools=["file_writer", "test_runner"],
                outputs=["tests/test_integration.py"],
                timeout_seconds=240,
            ),
        ],
    }

    # Step 2: Initialize the executor with callbacks
    print("\n🔧 Initializing Executor...")

    executor = RealWorldExecutor(
        max_parallel=3,
        task_tool_callback=create_task_tool_callback(),
        mcp_tool_callback=create_mcp_callback(),
        session_export_dir=project_root / ".sdlc-sessions",
    )

    # Step 3: Execute Discovery Phase
    print("\n📋 DISCOVERY PHASE")
    print("-" * 40)

    discovery_results = {}
    for task in custom_tasks["discovery"]:
        print(f"\nExecuting: {task.name}")
        prompt = f"""
        Project: {project_name}
        Task: {task.name}
        Focus: {task.metadata.get('focus', 'General discovery')}

        Create the following outputs:
        {', '.join(task.outputs)}
        """

        context = executor.execute_with_monitoring(
            task=task, mode="task", prompt=prompt  # Use Task tool for discovery
        )

        if context.error:
            print(f"  ❌ Failed: {context.error}")
        else:
            print(f"  ✅ Success in {context.duration:.1f}s")
            discovery_results[task.id] = context.output

    # Step 4: Execute Development Phase with waves
    print("\n\n⚙️ DEVELOPMENT PHASE")
    print("-" * 40)

    # Group tasks by wave
    dev_waves = {}
    for task in custom_tasks["development"]:
        wave = task.wave
        if wave not in dev_waves:
            dev_waves[wave] = []
        dev_waves[wave].append(task)

    development_results = {}

    for wave_num in sorted(dev_waves.keys()):
        print(f"\n🌊 Wave {wave_num}: {len(dev_waves[wave_num])} parallel tasks")

        # Execute wave tasks in parallel
        wave_contexts = []
        for task in dev_waves[wave_num]:
            mode = "mcp" if task.timeout_seconds > 240 else "task"

            prompt = f"""
            Project: {project_name}
            Task: {task.name}
            Wave: {wave_num}

            Create the following outputs:
            {', '.join(task.outputs)}

            {'Library: ' + task.metadata.get('library', '') if 'library' in task.metadata else ''}
            {'Framework: ' + task.metadata.get('framework', '')
             if 'framework' in task.metadata else ''}
            """

            # Add dependency context
            deps = {}
            for dep_id in task.dependencies:
                if dep_id in development_results:
                    deps[dep_id] = development_results[dep_id]

            print(f"  • {task.name} [{mode}]...")
            context = executor.execute_with_monitoring(
                task=task, mode=mode, prompt=prompt, dependencies=deps
            )

            wave_contexts.append(context)

            if not context.error:
                development_results[task.id] = context.output

        # Report wave results
        successful = sum(1 for c in wave_contexts if not c.error)
        print(
            f"\n  Wave {wave_num} Complete: {successful}/{len(wave_contexts)} successful"
        )

    # Step 5: Generate final report
    print("\n\n📊 EXECUTION REPORT")
    print("=" * 70)

    total_tasks = len(custom_tasks["discovery"]) + len(custom_tasks["development"])
    successful_tasks = len(discovery_results) + len(development_results)

    report = {
        "project": project_name,
        "timestamp": datetime.now().isoformat(),
        "phases_executed": ["discovery", "development"],
        "statistics": {
            "total_tasks": total_tasks,
            "successful": successful_tasks,
            "success_rate": f"{(successful_tasks/total_tasks)*100:.1f}%",
        },
        "outputs": {
            "discovery": list(discovery_results.keys()),
            "development": list(development_results.keys()),
        },
        "session_exports": str(project_root / ".sdlc-sessions"),
    }

    print(json.dumps(report, indent=2))

    # Step 6: Show how to access session data
    print("\n\n💾 SESSION DATA")
    print("-" * 70)
    print("All session data has been exported to:")
    print(f"  {project_root / '.sdlc-sessions'}")
    print("\nYou can analyze these sessions to:")
    print("  • Debug failures")
    print("  • Optimize task timing")
    print("  • Track costs and token usage")
    print("  • Resume incomplete work")

    # Cleanup
    executor.shutdown()

    print("\n✅ Example complete!")
    return report


def integrate_with_existing_project():
    """
    Example: Integrating orchestration into an existing project.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Integrating with Existing Project")
    print("=" * 70)

    print(
        """
    To integrate orchestration into your existing project:

    1. Install the orchestrator:
       pip install opsvi-orchestrator

    2. Create your task definitions:

       from opsvi_orchestrator import MicroTask

       tasks = [
           MicroTask(
               id="refactor_module",
               name="Refactor User Module",
               phase="refactoring",
               wave=1,
               tools=["file_editor", "test_runner"],
               outputs=["src/user.py", "tests/test_user.py"],
               timeout_seconds=300
           )
       ]

    3. Set up callbacks for your tools:

       def my_task_callback(description, subagent_type, prompt):
           # Your Task tool integration
           return execute_task(...)

       def my_mcp_callback(task, **kwargs):
           # Your MCP integration
           return execute_mcp(...)

    4. Execute with monitoring:

       executor = RealWorldExecutor(
           task_tool_callback=my_task_callback,
           mcp_tool_callback=my_mcp_callback
       )

       context = executor.execute_with_monitoring(
           task=task,
           mode="task",
           prompt="Refactor for better performance"
       )

    5. Analyze results:

       if context.error:
           print(f"Failed: {context.error}")
           # Check logs for details
           for log in context.logs:
               print(log)
       else:
           print(f"Success in {context.duration}s")
    """
    )


def show_advanced_features():
    """
    Show advanced features of the orchestration system.
    """
    print("\n" + "=" * 70)
    print("ADVANCED FEATURES")
    print("=" * 70)

    print(
        """
    🔄 AUTOMATIC RETRY WITH BACKOFF
    --------------------------------
    task = MicroTask(
        id="flaky_task",
        retry_count=3,  # Retry up to 3 times
        metadata={"backoff_multiplier": 2}  # Double timeout each retry
    )

    📊 COST OPTIMIZATION
    --------------------
    # Set cost limits per task
    task.metadata["max_cost_usd"] = 0.10

    # Track cumulative costs
    executor.metrics["total_cost_usd"]

    🔍 CUSTOM VALIDATORS
    --------------------
    from validators import MicroTaskValidator

    class MyValidator(MicroTaskValidator):
        def validate_my_output(self, output):
            # Custom validation logic
            return ValidationResult(...)

    📈 PERFORMANCE MONITORING
    -------------------------
    # Real-time monitoring
    active = executor.get_active_sessions()
    for session in active:
        print(f"{session['task_name']}: {session['duration_so_far']}s")

    🔗 DEPENDENCY CHAINS
    --------------------
    # Complex dependency graphs
    task = MicroTask(
        dependencies=["task1", "task2", "task3"],
        metadata={"wait_for_all": True}
    )

    🎯 TARGETED CORRECTIONS
    -----------------------
    # Specific error corrections
    if "import error" in context.error:
        correction_task = MicroTask(
            id=f"{task.id}_fix_imports",
            metadata={"correction_type": "imports"}
        )

    📝 CUSTOM TEMPLATES
    -------------------
    # Task templates for common patterns
    templates = {
        "crud_api": [tasks...],
        "data_pipeline": [tasks...],
        "ml_model": [tasks...]
    }
    """
    )


if __name__ == "__main__":
    # Run examples
    print("SDLC ORCHESTRATION SYSTEM - PRACTICAL EXAMPLES")
    print("=" * 70)
    print("\nChoose an example:")
    print("1. Build a new CLI project with orchestration")
    print("2. Integrate with existing project")
    print("3. Show advanced features")
    print("\nRunning example 1...\n")

    # Run the CLI project example
    create_custom_cli_project()

    # Show integration guide
    integrate_with_existing_project()

    # Show advanced features
    show_advanced_features()

    print("\n" + "=" * 70)
    print("Ready to revolutionize your development workflow!")
    print("=" * 70)
