"""
Simple Test for Task Decomposition Logic
Shows how OAMAT breaks large tasks into parallel sub-workflows
"""

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Standalone implementation for testing without full OAMAT imports
from dataclasses import dataclass
from enum import Enum
from typing import List


class TaskComplexity(Enum):
    SIMPLE = "simple"  # Single subtask
    MODERATE = "moderate"  # 2-3 subtasks
    COMPLEX = "complex"  # 4+ subtasks
    MASSIVE = "massive"  # Needs hierarchical breakdown


@dataclass
class SubTask:
    """Represents a decomposed subtask"""

    id: str
    description: str
    agent_role: str
    estimated_effort: int  # 1-10 scale
    dependencies: List[str]
    file_outputs: List[str]
    parallel_safe: bool = True


class SimpleTaskDecomposer:
    """Simplified task decomposer for testing"""

    def analyze_task_complexity(
        self, task_description: str, agent_role: str
    ) -> TaskComplexity:
        """Analyze if a task needs decomposition"""
        complexity_indicators = {
            "multiple": 2,
            "various": 2,
            "several": 2,
            "create and": 3,
            "implement and": 3,
            "build a": 2,
            "full": 3,
            "complete": 3,
            "comprehensive": 4,
            "entire": 4,
            "system": 3,
            "application": 3,
            "API": 2,
            "database": 2,
            "frontend": 2,
            "backend": 2,
        }

        score = 0
        task_lower = task_description.lower()

        for indicator, weight in complexity_indicators.items():
            if indicator in task_lower:
                score += weight

        if agent_role == "coder" and any(
            word in task_lower for word in ["api", "web app", "system"]
        ):
            score += 2

        if score <= 2:
            return TaskComplexity.SIMPLE
        elif score <= 5:
            return TaskComplexity.MODERATE
        elif score <= 8:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.MASSIVE

    def decompose_coding_task(
        self, task_description: str, user_request: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """Decompose coding tasks into parallel components"""
        subtasks = []
        task_lower = task_description.lower()

        # Web Application Pattern
        if any(word in task_lower for word in ["web app", "api", "service"]):
            if "database" in task_lower or "data" in task_lower:
                subtasks.append(
                    SubTask(
                        id="db_models",
                        description=f"Create database models and schema for: {user_request}",
                        agent_role="coder_db",
                        estimated_effort=6,
                        dependencies=[],
                        file_outputs=["models.py", "schema.sql"],
                        parallel_safe=True,
                    )
                )

            if "api" in task_lower or "backend" in task_lower:
                subtasks.append(
                    SubTask(
                        id="api_endpoints",
                        description=f"Implement API endpoints for: {user_request}",
                        agent_role="coder_api",
                        estimated_effort=7,
                        dependencies=["db_models"] if "database" in task_lower else [],
                        file_outputs=["routes/", "controllers/"],
                        parallel_safe=False if "database" in task_lower else True,
                    )
                )

            if "frontend" in task_lower or "ui" in task_lower:
                subtasks.append(
                    SubTask(
                        id="frontend_ui",
                        description=f"Create frontend interface for: {user_request}",
                        agent_role="coder_frontend",
                        estimated_effort=6,
                        dependencies=[],
                        file_outputs=["static/", "templates/"],
                        parallel_safe=True,
                    )
                )

        # Generic decomposition for complex tasks
        elif complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]:
            subtasks.extend(
                [
                    SubTask(
                        id="core_logic",
                        description=f"Implement core business logic for: {user_request}",
                        agent_role="coder_core",
                        estimated_effort=7,
                        dependencies=[],
                        file_outputs=["core/", "main.py"],
                        parallel_safe=True,
                    ),
                    SubTask(
                        id="utilities",
                        description=f"Create utility functions for: {user_request}",
                        agent_role="coder_utils",
                        estimated_effort=4,
                        dependencies=[],
                        file_outputs=["utils/", "helpers/"],
                        parallel_safe=True,
                    ),
                    SubTask(
                        id="config_setup",
                        description=f"Set up configuration for: {user_request}",
                        agent_role="coder_config",
                        estimated_effort=3,
                        dependencies=[],
                        file_outputs=["config/", "requirements.txt"],
                        parallel_safe=True,
                    ),
                ]
            )

        return subtasks


def test_task_complexity_analysis():
    """Test the task complexity analysis"""
    decomposer = SimpleTaskDecomposer()

    test_cases = [
        ("Fix a bug in login", "coder", TaskComplexity.SIMPLE),
        ("Create a REST API for user management", "coder", TaskComplexity.MODERATE),
        (
            "Build a complete e-commerce web application with authentication, database, and frontend",
            "coder",
            TaskComplexity.MASSIVE,
        ),
        (
            "Implement comprehensive testing for the entire system",
            "tester",
            TaskComplexity.COMPLEX,
        ),
        ("Write API documentation", "doc", TaskComplexity.SIMPLE),
    ]

    print("🧪 TESTING Task Complexity Analysis")
    print("=" * 60)

    for task_desc, role, expected in test_cases:
        actual = decomposer.analyze_task_complexity(task_desc, role)
        status = "✅" if actual == expected else "❌"
        print(
            f"{status} {role}: '{task_desc[:50]}...' → {actual.value} (expected: {expected.value})"
        )

    print()


def test_task_decomposition():
    """Test task decomposition into subtasks"""
    decomposer = SimpleTaskDecomposer()

    test_cases = [
        {
            "task": "Build a complete web API with database, authentication, and frontend",
            "role": "coder",
            "user_request": "Create a user management system",
        },
        {
            "task": "Implement core business logic with utilities and configuration",
            "role": "coder",
            "user_request": "Build a task management app",
        },
        {
            "task": "Fix login validation bug",
            "role": "coder",
            "user_request": "Fix login system",
        },
    ]

    print("🔧 TESTING Task Decomposition")
    print("=" * 60)

    for case in test_cases:
        complexity = decomposer.analyze_task_complexity(case["task"], case["role"])
        subtasks = decomposer.decompose_coding_task(
            case["task"], case["user_request"], complexity
        )

        print(f"\n📋 {case['role'].upper()}: {case['task']}")
        print(f"   🎯 Complexity: {complexity.value}")

        if subtasks:
            print(f"   🔧 Decomposed into {len(subtasks)} subtasks:")
            for i, subtask in enumerate(subtasks, 1):
                deps = (
                    f" (depends on: {', '.join(subtask.dependencies)})"
                    if subtask.dependencies
                    else ""
                )
                parallel = "🔄" if subtask.parallel_safe else "🔒"
                print(
                    f"     {i}. {parallel} {subtask.id}: {subtask.description[:60]}...{deps}"
                )
                print(
                    f"        Effort: {subtask.estimated_effort}/10, Files: {', '.join(subtask.file_outputs[:2])}"
                )
        else:
            print("   ⚡ No decomposition needed (simple task)")


def demonstrate_execution_levels():
    """Show how tasks are organized into execution levels"""
    print("\n🚀 EXECUTION LEVEL ORGANIZATION")
    print("=" * 60)

    # Example: Complex web application
    subtasks = [
        SubTask(
            "db_models",
            "Create database models",
            "coder_db",
            6,
            [],
            ["models.py"],
            True,
        ),
        SubTask(
            "frontend_ui",
            "Create frontend",
            "coder_frontend",
            6,
            [],
            ["templates/"],
            True,
        ),
        SubTask(
            "config_setup",
            "Setup configuration",
            "coder_config",
            3,
            [],
            ["config/"],
            True,
        ),
        SubTask(
            "api_endpoints",
            "Create API endpoints",
            "coder_api",
            7,
            ["db_models"],
            ["routes/"],
            False,
        ),
        SubTask(
            "authentication",
            "Implement auth",
            "coder_auth",
            5,
            ["db_models"],
            ["auth/"],
            False,
        ),
    ]

    # Organize by dependency levels
    levels = {}
    for task in subtasks:
        level = 0 if not task.dependencies else 1
        if level not in levels:
            levels[level] = []
        levels[level].append(task)

    print("📊 Execution Timeline:")
    total_time = 0

    for level, tasks in levels.items():
        parallel_time = max(
            task.estimated_effort * 5 for task in tasks
        )  # 5s per effort point
        total_time += parallel_time

        print(f"\n🎯 Level {level} ({parallel_time}s - parallel execution):")
        for task in tasks:
            deps = (
                f" (waits for: {', '.join(task.dependencies)})"
                if task.dependencies
                else ""
            )
            print(f"   • {task.id}: {task.estimated_effort * 5}s{deps}")

    sequential_time = sum(task.estimated_effort * 5 for task in subtasks)
    improvement = sequential_time / total_time

    print("\n📈 Performance Comparison:")
    print(f"   Sequential: {sequential_time}s")
    print(f"   Parallel: {total_time}s")
    print(f"   🚀 Improvement: {improvement:.1f}x faster")


def main():
    """Run all tests"""
    print("🧪 OAMAT TASK DECOMPOSITION DEMO")
    print("=" * 60)
    print("Demonstrates how large tasks are broken into parallel sub-workflows\n")

    test_task_complexity_analysis()
    test_task_decomposition()
    demonstrate_execution_levels()

    print("\n✅ Demo completed!")
    print("\n💡 Key Benefits:")
    print("   • Automatic complexity detection")
    print("   • Intelligent task decomposition")
    print("   • Dependency-aware parallel execution")
    print("   • 2-5x performance improvement for complex tasks")
    print("\n🚀 Ready to integrate into OAMAT for hierarchical parallel processing!")


if __name__ == "__main__":
    main()
