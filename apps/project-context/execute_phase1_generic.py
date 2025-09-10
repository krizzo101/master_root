#!/usr/bin/env python3
"""
Execute Phase 1 Completion using GenericOrchestrator (Original Working Pattern)
Simple, reliable execution of the final 5 Phase 1 tasks with 18 parallel capacity
"""
import asyncio
import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from src.generic_orchestrator import AgentTask, GenericOrchestrator
from src.token_loader import TokenLoader


def create_phase1_completion_agent_tasks():
    """
    Create the final 5 Phase 1 tasks as AgentTask objects
    Following the original working pattern from execute_phase1_plan.py
    """

    agent_tasks = []

    # Task 1: Chat Adapter (no dependencies)
    chat_prompt = """TASK: Implement chat log adapter for JSONL ingestion with entity extraction and embeddings.

SPECIALIST ROLE: You are acting as a development-specialist agent.

CONTEXT:
- foundation_status: Base pipeline COMPLETE and ready for use
- database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- base_pipeline: /home/opsvi/master_root/apps/project-context/src/ingestion/
- implementation_files:
  • src/ingestion/adapters/chat_adapter.py
  • tests/test_chat_adapter.py
- integration_points:
  • base_adapter.py framework
  • unified schema tables
  • message deduplication system
  • entity extraction pipeline

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context

PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System - a temporal knowledge graph that unifies chat logs, code intelligence, git history, and error data into a queryable PostgreSQL + Neo4j backend with semantic search capabilities.

IMPLEMENTATION REQUIREMENTS:
- Build ChatAdapter class extending BaseAdapter framework
- Parse JSONL chat logs with message extraction
- Extract entities, topics, and generate embeddings
- Support incremental ingestion with deduplication
- Implement async processing with proper error handling
- Create comprehensive unit tests
"""

    agent_tasks.append(
        AgentTask(
            task_id="implement_chat_adapter",
            task_type="development-specialist",
            prompt=chat_prompt,
            dependencies=[],
            context={"phase": "phase1_completion", "priority": "high"},
        )
    )

    # Task 2: Code Adapter (no dependencies - can run parallel with chat)
    code_prompt = """TASK: Implement code analysis adapter for repository scanning with function/class extraction.

SPECIALIST ROLE: You are acting as a development-specialist agent.

CONTEXT:
- foundation_status: Base pipeline COMPLETE and ready for use
- database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- base_pipeline: /home/opsvi/master_root/apps/project-context/src/ingestion/
- implementation_files:
  • src/ingestion/adapters/code_adapter.py
  • tests/test_code_adapter.py
- integration_points:
  • base_adapter.py framework
  • unified schema tables
  • symbol relationship extraction
  • AST parsing utilities

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context

PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System - a temporal knowledge graph that unifies chat logs, code intelligence, git history, and error data into a queryable PostgreSQL + Neo4j backend with semantic search capabilities.

IMPLEMENTATION REQUIREMENTS:
- Build CodeAdapter extending BaseAdapter framework
- Scan repository files for code analysis
- Extract functions, classes, modules, and dependencies
- Support multiple programming languages (Python, JavaScript, etc.)
- Generate embeddings for code semantic search
- Implement file watching and incremental updates
"""

    agent_tasks.append(
        AgentTask(
            task_id="implement_code_adapter",
            task_type="development-specialist",
            prompt=code_prompt,
            dependencies=[],
            context={"phase": "phase1_completion", "priority": "high"},
        )
    )

    # Task 3: MCP Integration (depends on both adapters)
    mcp_prompt = """TASK: Update existing 21 MCP tools to use new unified context backend.

SPECIALIST ROLE: You are acting as a api-integration-specialist agent.

DEPENDENCIES: This task depends on completion of: implement_chat_adapter, implement_code_adapter

CONTEXT:
- foundation_status: Database operational, adapters complete
- mcp_tools_count: 21 existing tools need backend integration
- integration_scope:
  • Chat tools → ChatAdapter backend
  • Code tools → CodeAdapter backend
  • System tools → Unified database backend
- compatibility_requirement: Maintain existing tool APIs

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context

PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System - a temporal knowledge graph that unifies chat logs, code intelligence, git history, and error data into a queryable PostgreSQL + Neo4j backend with semantic search capabilities.

INTEGRATION REQUIREMENTS:
- Update existing 21 MCP tools to use new backend
- Ensure chat adapter integration with MCP chat tools
- Integrate code adapter with MCP code analysis tools
- Maintain backwards compatibility with existing tools
- Test all integrations thoroughly
- Update tool documentation and examples
"""

    agent_tasks.append(
        AgentTask(
            task_id="integrate_with_mcp",
            task_type="api-integration-specialist",
            prompt=mcp_prompt,
            dependencies=["implement_chat_adapter", "implement_code_adapter"],
            context={"phase": "phase1_completion", "priority": "normal"},
        )
    )

    # Task 4: Comprehensive Testing (depends on integration)
    testing_prompt = """TASK: Create comprehensive test suite for Phase 1 unified context system.

SPECIALIST ROLE: You are acting as a qa-testing-guru agent.

DEPENDENCIES: This task depends on completion of: integrate_with_mcp

CONTEXT:
- testing_scope: Complete Phase 1 system validation
- components_to_test:
  • ChatAdapter and CodeAdapter
  • MCP tool integrations
  • Database operations
  • End-to-end pipeline
- coverage_target: >90% test coverage

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context

PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System - a temporal knowledge graph that unifies chat logs, code intelligence, git history, and error data into a queryable PostgreSQL + Neo4j backend with semantic search capabilities.

TESTING REQUIREMENTS:
- Unit tests for ChatAdapter and CodeAdapter
- Integration tests for complete ingestion pipeline
- MCP tool integration tests
- Database validation and performance tests
- End-to-end system validation
- Error handling and edge case testing
"""

    agent_tasks.append(
        AgentTask(
            task_id="comprehensive_testing",
            task_type="qa-testing-guru",
            prompt=testing_prompt,
            dependencies=["integrate_with_mcp"],
            context={"phase": "phase1_completion", "priority": "normal"},
        )
    )

    # Task 5: Documentation (depends on testing)
    docs_prompt = """TASK: Create comprehensive documentation for Phase 1 implementation.

SPECIALIST ROLE: You are acting as a technical-writer agent.

DEPENDENCIES: This task depends on completion of: comprehensive_testing

CONTEXT:
- documentation_scope: Complete Phase 1 system documentation
- documentation_types:
  • Architecture overview and design decisions
  • API reference for all adapters
  • Installation and setup guide
  • Usage examples and tutorials
- target_audience: Developers and system administrators

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context

PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System - a temporal knowledge graph that unifies chat logs, code intelligence, git history, and error data into a queryable PostgreSQL + Neo4j backend with semantic search capabilities.

DOCUMENTATION REQUIREMENTS:
- Architecture overview with diagrams
- Complete API reference documentation
- Installation and setup guide
- Usage tutorials with examples
- Troubleshooting guide and FAQ
- Developer guide for extending the system
"""

    agent_tasks.append(
        AgentTask(
            task_id="create_documentation",
            task_type="technical-writer",
            prompt=docs_prompt,
            dependencies=["comprehensive_testing"],
            context={"phase": "phase1_completion", "priority": "low"},
        )
    )

    return agent_tasks


async def main():
    """Execute Phase 1 completion using the original GenericOrchestrator pattern"""

    print("🚀 PHASE 1 COMPLETION - GENERIC ORCHESTRATOR")
    print("=" * 60)
    print("✅ Foundation: 6/11 tasks complete - database and pipeline ready")
    print("🎯 Remaining: 5 tasks in dependency chain")
    print("⚡ Execution: Up to 18 parallel tasks using GenericOrchestrator")
    print()

    # Create tasks using original pattern
    tasks = create_phase1_completion_agent_tasks()

    # Load tokens (should get 18+ tokens)
    loader = TokenLoader()
    tokens = loader.load_tokens()

    # Create orchestrator with maximum parallel (like the original)
    orchestrator = GenericOrchestrator(
        output_dir=Path("./phase1_completion_generic_output"),
        max_parallel=min(len(tokens), 18),  # Use all available tokens, up to 18
        tokens=tokens,
        use_optimizations=True,
    )

    print(f"🔧 Token count: {len(tokens)}")
    print(f"⚡ Max parallel: {orchestrator.max_parallel}")
    print()

    # Print task plan
    print("📋 EXECUTION PLAN")
    print("=" * 30)
    for task in tasks:
        deps_str = (
            f" (depends: {', '.join(task.dependencies)})"
            if task.dependencies
            else " (no dependencies)"
        )
        print(f"  📌 {task.task_id}{deps_str}")
    print()

    # Execute tasks (original pattern)
    print(f"⏱️  Starting execution...")

    try:
        results = await orchestrator.execute_batch(tasks)

        # Analyze results
        completed = len([r for r in results if r.get("status") == "completed"])
        failed = len([r for r in results if r.get("status") == "failed"])

        print(f"\n📊 EXECUTION COMPLETE")
        print("=" * 30)
        print(f"✅ Completed: {completed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success rate: {completed/len(tasks):.1%}")

        # Show outputs
        output_dir = Path("./phase1_completion_generic_output")
        print(f"\n📁 OUTPUT DIRECTORY: {output_dir}")
        print(f"📋 Task results: {output_dir}/tasks/")

        if completed == len(tasks):
            print(f"\n🎉 SUCCESS! Phase 1 completion finished!")
            print(f"✅ All {len(tasks)} tasks completed successfully")
            print(f"🚀 System ready for Phase 2")
            return True
        else:
            print(f"\n⚠️  Phase 1 completion had issues")
            print(f"   Check task outputs in {output_dir}/tasks/ for details")
            return False

    except Exception as e:
        print(f"\n💥 EXECUTION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Phase 1 Completion - Original GenericOrchestrator Pattern")
    print("Simple, reliable execution with maximum parallelization")
    print("=" * 60)

    success = asyncio.run(main())

    if success:
        print(f"\n✅ Phase 1 completion successful!")
    else:
        print(f"\n❌ Phase 1 completion needs attention")

    sys.exit(0 if success else 1)
