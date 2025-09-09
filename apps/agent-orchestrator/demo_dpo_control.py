#!/usr/bin/env python3
"""
Demo: Controlling DPO Enhancement Levels

Shows how to control how much DPO enhances your workflows.
"""

import asyncio
from pathlib import Path

# Import DPO with enhancement config
from src.dpo.enhancement_config import (
    DPOEnhancementConfig,
    EnhancementLevel,
    EnhancementScope,
)
from src.dpo.request_analyzer import RequestAnalyzer
from src.generic_orchestrator import AgentTask, GenericOrchestrator


def generate_workflow(request: str, config: DPOEnhancementConfig) -> list:
    """Generate workflow with specified enhancement level."""
    tasks = []

    if not config.enabled:
        # DPO OFF - just basic orchestrator task
        tasks.append(
            AgentTask(
                task_id="basic_task", task_type="development-specialist", prompt=request
            )
        )
        return tasks

    # Analyze request
    analyzer = RequestAnalyzer()
    analysis = analyzer.analyze(request)

    # Add agents based on config
    if config.should_enhance(EnhancementScope.AGENTS):
        if config.sturdy_box_mode:
            # Sturdy box - just essential agents
            agents = [
                "requirements-analyst",
                "development-specialist",
                "qa-testing-guru",
            ]
        elif config.level == EnhancementLevel.MAXIMUM:
            # Maximum - all relevant agents
            agents = [
                "requirements-analyst",
                "business-analyst",
                "solution-architect",
                "database-specialist",
                "api-integration-specialist",
                "development-specialist",
                "security-architect",
                "performance-optimizer",
                "qa-testing-guru",
                "technical-writer",
                "devops-automation",
            ]
        else:
            # Balanced
            agents = [
                "requirements-analyst",
                "development-specialist",
                "database-specialist",
                "qa-testing-guru",
                "technical-writer",
            ]

        # Limit agents based on config
        agents = agents[: config.max_agents]
    else:
        agents = ["development-specialist"]

    # Generate tasks
    task_count = 0

    # Requirements phase
    if "requirements-analyst" in agents:
        tasks.append(
            AgentTask(
                task_id="analyze_requirements",
                task_type="requirements-analyst",
                prompt=f"Analyze requirements for: {request}",
            )
        )
        task_count += 1

    # Development phase
    if task_count < config.max_tasks_per_phase * 3:  # Rough limit
        tasks.append(
            AgentTask(
                task_id="implement_solution",
                task_type="development-specialist",
                prompt=f"Implement: {request}",
                dependencies=["analyze_requirements"]
                if "requirements-analyst" in agents
                else [],
            )
        )
        task_count += 1

    # Quality gates
    if config.add_quality_gates and config.should_enhance(EnhancementScope.QUALITY):
        if config.sturdy_box_mode:
            quality_gates = ["functionality"]  # Just ensure it works
        else:
            quality_gates = ["functionality", "performance", "security"]
    else:
        quality_gates = []

    # Testing
    if config.add_testing and config.should_enhance(EnhancementScope.TESTING):
        tasks.append(
            AgentTask(
                task_id="test_solution",
                task_type="qa-testing-guru",
                prompt="Test the implementation",
                dependencies=["implement_solution"],
                quality_gates=quality_gates,
            )
        )
        task_count += 1

    # Documentation
    if config.add_documentation and config.should_enhance(
        EnhancementScope.DOCUMENTATION
    ):
        tasks.append(
            AgentTask(
                task_id="document_solution",
                task_type="technical-writer",
                prompt="Document the solution",
                dependencies=["test_solution"]
                if config.add_testing
                else ["implement_solution"],
            )
        )
        task_count += 1

    return tasks


def compare_enhancement_levels():
    """Compare different enhancement levels."""
    request = "Build a user authentication system"

    print("=" * 70)
    print("DPO ENHANCEMENT LEVEL COMPARISON")
    print("=" * 70)
    print(f"\n📝 Request: '{request}'")
    print("=" * 70)

    configs = {
        "🚫 OFF (No DPO)": DPOEnhancementConfig(enabled=False),
        "📦 STURDY BOX": DPOEnhancementConfig.sturdy_box(),
        "⚖️ SMART/BALANCED": DPOEnhancementConfig.smart_default(),
        "🚀 MAXIMUM": DPOEnhancementConfig.maximum_enhancement(),
    }

    for name, config in configs.items():
        tasks = generate_workflow(request, config)

        print(f"\n{name}:")
        print(f"  Enabled: {config.enabled}")
        if config.enabled:
            print(f"  Level: {config.level.value}")
            print(f"  Max agents: {config.max_agents}")
            print(f"  Sturdy box mode: {config.sturdy_box_mode}")
        print(f"  Tasks generated: {len(tasks)}")
        print(f"  Agents used: {len(set(t.task_type for t in tasks))}")
        print(f"  Quality gates: {sum(len(t.quality_gates) for t in tasks)}")

        print("  Workflow:")
        for task in tasks:
            deps = (
                f" (depends: {', '.join(task.dependencies)})"
                if task.dependencies
                else ""
            )
            gates = (
                f" [QG: {', '.join(task.quality_gates)}]" if task.quality_gates else ""
            )
            print(f"    • {task.task_id}{deps}{gates}")


def demo_programmatic_control():
    """Show programmatic control of DPO."""
    print("\n" + "=" * 70)
    print("PROGRAMMATIC DPO CONTROL")
    print("=" * 70)

    # Create custom config
    custom_config = DPOEnhancementConfig(
        enabled=True,
        level=EnhancementLevel.BALANCED,
        scopes=[
            EnhancementScope.AGENTS,
            EnhancementScope.TASKS,
            EnhancementScope.TESTING
            # Specifically excluding DOCUMENTATION, DEPLOYMENT, etc.
        ],
        max_agents=6,
        max_tasks_per_phase=3,
        add_quality_gates=True,
        add_documentation=False,  # Don't want docs this time
        add_testing=True,
        infer_requirements=False,
        add_best_practices=False,
    )

    print("\n🎛️ Custom Configuration:")
    print(f"  Enabled: {custom_config.enabled}")
    print(f"  Level: {custom_config.level.value}")
    print(f"  Active scopes: {[s.value for s in custom_config.get_scopes_for_level()]}")
    print(f"  Max agents: {custom_config.max_agents}")
    print(f"  Add docs: {custom_config.add_documentation}")
    print(f"  Infer requirements: {custom_config.infer_requirements}")

    # Generate workflow with custom config
    request = "Create a simple REST API"
    tasks = generate_workflow(request, custom_config)

    print(f"\n📊 Generated workflow for: '{request}'")
    print(f"  Tasks: {len(tasks)}")
    print(f"  Workflow: {' → '.join(t.task_id for t in tasks)}")


def demo_config_from_string():
    """Show string-based configuration."""
    print("\n" + "=" * 70)
    print("STRING-BASED DPO CONFIGURATION")
    print("=" * 70)

    print("\n📝 Available presets:")
    presets = ["off", "sturdy", "smart", "max", "minimal", "essential", "comprehensive"]

    for preset in presets:
        config = DPOEnhancementConfig.from_string(preset)
        print(
            f"  '{preset}': enabled={config.enabled}, level={config.level.value if config.enabled else 'N/A'}"
        )

    print("\n💡 Usage in orchestrator:")
    print('  orchestrator = EnhancedOrchestrator(dpo_enhancement="sturdy")')
    print('  orchestrator = EnhancedOrchestrator(dpo_enhancement="off")  # Default')
    print(
        '  orchestrator = EnhancedOrchestrator(dpo_enhancement="max")   # All features'
    )


def main():
    """Run all demos."""
    print("\n" + "🎮 " * 35)
    print("DPO ENHANCEMENT CONTROL DEMO")
    print("🎮 " * 35)

    # Compare enhancement levels
    compare_enhancement_levels()

    # Show programmatic control
    demo_programmatic_control()

    # Show string-based config
    demo_config_from_string()

    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print(
        """
✅ DPO is OFF by default - must explicitly enable
✅ Multiple enhancement levels from 'sturdy box' to 'maximum'
✅ Fine-grained control over what gets enhanced
✅ Can limit agents and tasks to stay practical
✅ 'Sturdy box' mode = just what's needed for success
✅ 'Maximum' mode = all the crazy cool stuff
✅ Easy string-based config: "off", "sturdy", "smart", "max"
    """
    )


if __name__ == "__main__":
    main()
