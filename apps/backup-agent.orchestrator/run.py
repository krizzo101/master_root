#!/usr/bin/env python3
"""
Agent Orchestrator - Main entry point
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.generic_orchestrator import AgentTask, GenericOrchestrator


async def example_simple():
    """Simple example with 3 sequential tasks"""

    orchestrator = GenericOrchestrator(
        output_dir=Path("./output"), max_parallel=3, use_optimizations=True
    )

    def generate_tasks():
        return [
            AgentTask(
                task_id="research",
                task_type="research",
                prompt="Research the benefits of async programming in Python",
            ),
            AgentTask(
                task_id="design",
                task_type="design",
                prompt="Design a simple async web server architecture",
                dependencies=["research"],
            ),
            AgentTask(
                task_id="implement",
                task_type="code",
                prompt="Write a hello world async FastAPI server",
                dependencies=["design"],
            ),
        ]

    print("Running simple example...")
    await orchestrator.run(task_generator=generate_tasks)


async def example_parallel():
    """Example with parallel execution"""

    orchestrator = GenericOrchestrator(
        output_dir=Path("./output"), max_parallel=5, use_optimizations=True
    )

    def generate_tasks():
        tasks = []

        # Create 5 independent research tasks (will run in parallel)
        topics = ["microservices", "REST APIs", "GraphQL", "gRPC", "WebSockets"]
        for topic in topics:
            tasks.append(
                AgentTask(
                    task_id=f"research_{topic}",
                    task_type="research",
                    prompt=f"Research {topic} and list 3 key advantages",
                )
            )

        # Summary task depends on all research
        tasks.append(
            AgentTask(
                task_id="summary",
                task_type="summary",
                prompt="Summarize all the research findings",
                dependencies=[f"research_{t}" for t in topics],
            )
        )

        return tasks

    print("Running parallel example...")
    await orchestrator.run(task_generator=generate_tasks)


def main():
    """Main entry point"""

    print("\nAgent Orchestrator Framework")
    print("=" * 40)
    print("1. Simple example (3 sequential tasks)")
    print("2. Parallel example (5 parallel + 1 summary)")
    print("3. Exit")

    choice = input("\nSelect option (1-3): ")

    if choice == "1":
        asyncio.run(example_simple())
    elif choice == "2":
        asyncio.run(example_parallel())
    else:
        print("Exiting...")


if __name__ == "__main__":
    main()
