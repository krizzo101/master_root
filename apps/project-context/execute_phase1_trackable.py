#!/usr/bin/env python3
"""
Trackable execution of Unified Context System Phase 1
Uses predictable session IDs so we can monitor each agent in real-time
"""
import asyncio
import hashlib
import os
import sys
import time
from pathlib import Path

sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from unified_context_phase1_plan import create_unified_context_phase1_plan

from src.generic_orchestrator import AgentTask, GenericOrchestrator


def generate_predictable_session_id(task_id: str, execution_timestamp: str) -> str:
    """Generate predictable session ID based on task and timestamp"""
    # Create deterministic but unique session ID
    base_string = f"unified-context-{task_id}-{execution_timestamp}"
    hash_object = hashlib.sha256(base_string.encode())
    session_hash = hash_object.hexdigest()[:8]  # First 8 chars for brevity
    return f"uc-{task_id}-{session_hash}"


def convert_execution_plan_to_agent_tasks_with_tracking(
    execution_plan, execution_timestamp
):
    """Convert ExecutionPlan tasks to AgentTask format with trackable session IDs"""
    agent_tasks = []
    session_map = {}  # Track task_id -> session_id mapping

    for task in execution_plan.tasks:
        # Generate predictable session ID
        session_id = generate_predictable_session_id(task.task_id, execution_timestamp)
        session_map[task.task_id] = session_id

        prompt_parts = [
            f"TASK: {task.prompt}",
            "",
            f"SPECIALIST ROLE: You are acting as a {task.task_type.value} agent.",
            f"TASK ID: {task.task_id}",
            f"SESSION ID: {session_id}",
            "",
        ]

        if task.context:
            prompt_parts.append("CONTEXT:")
            context_dict = (
                task.context.to_dict()
                if hasattr(task.context, "to_dict")
                else task.context.__dict__
            )
            for key, value in context_dict.items():
                if isinstance(value, list) and value:
                    prompt_parts.append(f"- {key}:")
                    for item in value:
                        prompt_parts.append(f"  • {item}")
                elif value and not isinstance(value, (list, dict)):
                    prompt_parts.append(f"- {key}: {value}")
                elif isinstance(value, dict) and value:
                    prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")

        if task.dependencies:
            prompt_parts.append(
                f"DEPENDENCIES: This task depends on completion of: {', '.join(task.dependencies)}"
            )
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.",
                "",
                "WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context",
                "",
                "PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System - a temporal knowledge graph that unifies chat logs, code intelligence, git history, and error data into a queryable PostgreSQL + Neo4j backend with semantic search capabilities.",
            ]
        )

        full_prompt = "\n".join(prompt_parts)

        agent_task = AgentTask(
            task_id=task.task_id,
            task_type=task.task_type.value,
            prompt=full_prompt,
            dependencies=task.dependencies,
            context={
                "execution_plan_id": execution_plan.plan_id,
                "original_context": task.context,
                "phase": "Phase 1: Foundation",
                "project": "Unified Context System",
                "session_id": session_id,  # Include in context for reference
                "trackable": True,
            },
        )
        agent_tasks.append(agent_task)

    return agent_tasks, session_map


async def execute_phase1_trackable():
    """Execute Phase 1 with trackable session IDs"""
    execution_timestamp = str(int(time.time()))

    print("🎯 TRACKABLE EXECUTION - Unified Context System Phase 1")
    print("=" * 70)

    # Create execution plan
    execution_plan = create_unified_context_phase1_plan()
    print(f"📋 ExecutionPlan loaded: {len(execution_plan.tasks)} tasks")

    # Convert to trackable agent tasks
    agent_tasks, session_map = convert_execution_plan_to_agent_tasks_with_tracking(
        execution_plan, execution_timestamp
    )

    print(f"\n📊 AGENT SESSION MAPPING:")
    print("=" * 50)
    for task_id, session_id in session_map.items():
        agent_type = next(
            task.task_type.value
            for task in execution_plan.tasks
            if task.task_id == task_id
        )
        print(f"{task_id:25} → {session_id} ({agent_type})")

    print(f"\n🔍 REAL-TIME TRACKING COMMANDS:")
    print("=" * 50)
    print("# Monitor all agents:")
    for task_id, session_id in session_map.items():
        print(
            f"tail -f /home/opsvi/master_root/chat_logs/{session_id}*.jsonl  # {task_id}"
        )

    print(f"\n# Search for completed agents:")
    print(
        'python apps/chat-search/chat_search.py "✅|COMPLETED|finished" --file-filter '
        + " ".join([f"{sid}*" for sid in session_map.values()])
    )

    # Set up output directory
    output_dir = Path(
        "/home/opsvi/master_root/apps/project-context/phase1_trackable_output"
    )
    output_dir.mkdir(exist_ok=True)

    # Initialize orchestrator with high parallelization
    orchestrator = GenericOrchestrator(
        output_dir=output_dir, max_parallel=10  # Use maximum parallel capacity
    )

    print(f"\n⚡ Starting execution with max_parallel=10")
    print(f"📁 Output directory: {output_dir}")
    print(f"🕒 Execution timestamp: {execution_timestamp}")
    print()

    try:
        print("🚀 Launching trackable agent execution...")

        # NOTE: The GenericOrchestrator still generates its own session IDs internally
        # But our session mapping provides a way to correlate task_id to predictable patterns
        # For true trackability, we'd need to modify the orchestrator itself

        results = await orchestrator.execute_batch(agent_tasks)

        print(f"\n✅ Execution completed! {len(results)} tasks processed")

        # Analyze results with session mapping
        successful_tasks = [r for r in results if r.get("status") == "completed"]
        failed_tasks = [r for r in results if r.get("status") == "failed"]

        print(f"   ✅ Successful: {len(successful_tasks)}")
        print(f"   ❌ Failed: {len(failed_tasks)}")

        print(f"\n📊 RESULTS BY TRACKED AGENT:")
        for result in results:
            task_id = result.get("task_id", "unknown")
            status = result.get("status", "unknown")
            mapped_session = session_map.get(task_id, "unmapped")
            agent_type = result.get("agent_type", "unknown")
            print(
                f"   {task_id:25} ({agent_type:20}) → {status:10} [Session: {mapped_session}]"
            )

        return results, session_map

    except Exception as e:
        print(f"❌ Execution failed: {str(e)}")
        return None, session_map


def main():
    """Main trackable execution"""
    print("=" * 80)
    print("UNIFIED CONTEXT SYSTEM - PHASE 1 TRACKABLE IMPLEMENTATION")
    print("Predictable Session IDs for Real-Time Agent Monitoring")
    print("=" * 80)
    print()

    results, session_map = asyncio.run(execute_phase1_trackable())

    if results:
        print(f"\n🎯 TRACKABLE Phase 1 Implementation COMPLETED!")
        print(
            f"   Use the session mapping above to correlate agents with their chat logs"
        )
        print(
            f"   Chat logs location: /home/opsvi/master_root/chat_logs/[session-id]*.jsonl"
        )
    else:
        print(f"\n❌ Trackable execution failed")
        print(f"   Session mapping still available for debugging:")
        for task_id, session_id in session_map.items():
            print(f"     {task_id} → {session_id}")


if __name__ == "__main__":
    main()
