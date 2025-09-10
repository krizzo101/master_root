#!/usr/bin/env python3
"""
Integration Example: Using Context-Isolated Orchestrator
Shows how to integrate the context isolation features with existing orchestrator workflows.
"""

import asyncio
import os
from pathlib import Path
from typing import List

# Import the context-isolated orchestrator
from context_isolated_orchestrator import ContextIsolatedOrchestrator, AgentTask


def create_production_tasks() -> List[AgentTask]:
    """Create tasks that demonstrate real-world isolation needs."""
    
    tasks = [
        # Research agent that needs web access
        AgentTask(
            task_id="research_agent",
            task_type="research",
            prompt="Research the latest developments in container orchestration technologies",
            context={
                "focus_area": "kubernetes",
                "output_format": "markdown",
            },
            mcp_needs=["mcp_web_search", "research_papers"],
        ),
        
        # Analysis agent that processes data
        AgentTask(
            task_id="analysis_agent", 
            task_type="analysis",
            prompt="Analyze the system logs and identify patterns",
            context={
                "log_path": "/var/log/system.log",
                "analysis_type": "anomaly_detection",
            },
            mcp_needs=["shell_exec"],
            dependencies=["research_agent"],  # Depends on research
        ),
        
        # Code generation agent
        AgentTask(
            task_id="code_gen_agent",
            task_type="implementation",
            prompt="Generate Python code for a REST API service",
            context={
                "framework": "fastapi",
                "database": "postgresql",
            },
            mcp_needs=["shell_exec"],
        ),
        
        # Documentation agent
        AgentTask(
            task_id="doc_agent",
            task_type="documentation",
            prompt="Create comprehensive documentation for the generated code",
            context={
                "format": "mkdocs",
                "include_examples": True,
            },
            dependencies=["code_gen_agent"],  # Depends on code generation
        ),
    ]
    
    return tasks


async def run_with_isolation():
    """Run tasks with full context isolation."""
    
    print("=" * 60)
    print("PRODUCTION ORCHESTRATOR WITH CONTEXT ISOLATION")
    print("=" * 60)
    
    # Create orchestrator with isolation enabled
    orchestrator = ContextIsolatedOrchestrator(
        output_dir=Path("production_output"),
        max_parallel=3,
        enable_context_isolation=True,  # Enable isolation
        cleanup_on_completion=True,     # Auto-cleanup after completion
        agent_execution_profile="standard",  # Use standard MCP profile
        enable_optimizations=True,
        use_dynamic_configs=True,
    )
    
    # Set tokens (in production, load from secure storage)
    if "CLAUDE_CODE_TOKEN" in os.environ:
        orchestrator.token_pool.tokens = [
            os.environ["CLAUDE_CODE_TOKEN"]
        ]
    else:
        # For demo purposes only
        orchestrator.token_pool.tokens = ["demo_token_1", "demo_token_2"]
    
    # Create and execute tasks
    tasks = create_production_tasks()
    
    print(f"\nExecuting {len(tasks)} tasks with context isolation:")
    for task in tasks:
        print(f"  - {task.task_id}: {task.task_type}")
        if task.dependencies:
            print(f"    Dependencies: {', '.join(task.dependencies)}")
    
    # Execute batch with isolation
    results = await orchestrator.execute_batch(tasks)
    
    # Report results
    print("\n" + "=" * 60)
    print("EXECUTION RESULTS")
    print("=" * 60)
    
    print(f"\nMetrics:")
    print(f"  Total tasks: {orchestrator.metrics['total']}")
    print(f"  Completed: {orchestrator.metrics['completed']}")
    print(f"  Failed: {orchestrator.metrics['failed']}")
    print(f"  Avg time: {orchestrator.metrics['avg_execution_time']:.2f}s")
    
    print(f"\nIsolated Contexts Created: {len(orchestrator.isolated_contexts)}")
    if orchestrator.cleanup_on_completion:
        print("  (All contexts cleaned up after completion)")
    
    # Check artifacts
    artifacts_dir = Path("production_output/artifacts")
    if artifacts_dir.exists():
        print(f"\nPreserved Artifacts:")
        for agent_dir in artifacts_dir.iterdir():
            print(f"  - {agent_dir.name}/")
            files = list(agent_dir.rglob("*"))
            if files:
                for f in files[:3]:  # Show first 3 files
                    print(f"    • {f.relative_to(agent_dir)}")
    
    return results


async def run_without_isolation():
    """Run tasks without isolation for comparison."""
    
    print("\n" + "=" * 60)
    print("TRADITIONAL ORCHESTRATOR (NO ISOLATION)")
    print("=" * 60)
    
    orchestrator = ContextIsolatedOrchestrator(
        output_dir=Path("traditional_output"),
        max_parallel=3,
        enable_context_isolation=False,  # Disable isolation
        cleanup_on_completion=False,
        agent_execution_profile="standard",
    )
    
    # Set tokens
    orchestrator.token_pool.tokens = ["demo_token"]
    
    tasks = create_production_tasks()
    
    print(f"\nExecuting {len(tasks)} tasks WITHOUT isolation:")
    print("⚠️  Warning: Agents may interfere with each other!")
    
    results = await orchestrator.execute_batch(tasks)
    
    print(f"\nCompleted: {orchestrator.metrics['completed']}/{orchestrator.metrics['total']}")
    
    return results


async def main():
    """Main entry point."""
    
    print("\n🚀 Context Isolation Integration Example\n")
    
    # Run with isolation
    await run_with_isolation()
    
    # Optionally run without isolation for comparison
    # await run_without_isolation()
    
    print("\n✅ Integration example completed!\n")


if __name__ == "__main__":
    asyncio.run(main())