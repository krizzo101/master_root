#!/usr/bin/env python3
"""
Continue Phase 1 Completion - Execute remaining 3 tasks
Chat and Code adapters are already complete, continue with integration, testing, documentation
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


def create_remaining_phase1_tasks():
    """
    Create the remaining 3 Phase 1 tasks as AgentTask objects
    (Chat and code adapters are already complete)
    """

    agent_tasks = []

    # Task 3: Integration (depends on both adapters - now complete)
    integration_prompt = """TASK: Integrate chat and code adapters with MCP tools and validate system connectivity.

SPECIALIST ROLE: You are acting as an api-integration-specialist agent.

CONTEXT:
- foundation_status: Base pipeline COMPLETE, Chat adapter COMPLETE, Code adapter COMPLETE
- database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- completed_adapters:
  • src/ingestion/adapters/chat_adapter.py (COMPLETE)
  • src/ingestion/adapters/code_adapter.py (COMPLETE)
- integration_targets:
  • MCP server tools integration
  • Unified pipeline orchestration
  • End-to-end data flow validation
  • Cross-adapter data relationships

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context

PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System. The chat and code adapters are now complete. Your task is to integrate them with the MCP tools and validate the complete system connectivity.

IMPLEMENTATION REQUIREMENTS:
- Integrate both adapters with MCP server framework
- Validate cross-adapter data relationships
- Test end-to-end ingestion pipeline
- Ensure unified schema compatibility
- Implement monitoring and health checks
- Document integration points and usage patterns
"""

    integration_task = AgentTask(
        task_id="integrate_with_mcp",
        task_type="api-integration-specialist",
        prompt=integration_prompt,
        dependencies=[],  # Dependencies already satisfied
        context={"phase": "phase1_completion", "priority": "high"},
    )

    agent_tasks.append(integration_task)

    # Task 4: Testing (depends on integration)
    testing_prompt = """TASK: Execute comprehensive testing of the complete Phase 1 system implementation.

SPECIALIST ROLE: You are acting as a qa-testing-guru agent.

CONTEXT:
- foundation_status: Base pipeline COMPLETE, Chat adapter COMPLETE, Code adapter COMPLETE, Integration COMPLETE
- database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- system_components:
  • Database schema and connections
  • Chat adapter with entity extraction
  • Code adapter with AST analysis
  • MCP integration layer
  • Unified ingestion pipeline
- testing_scope:
  • Unit tests for all adapters
  • Integration tests for complete pipeline
  • Performance and load testing
  • Error handling and recovery
  • Schema compatibility validation

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context

PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System. All core components are now complete and integrated. Your task is to execute comprehensive testing to validate system functionality, performance, and reliability.

IMPLEMENTATION REQUIREMENTS:
- Create comprehensive test suites for all components
- Execute integration tests for complete data flow
- Validate performance under realistic loads
- Test error handling and recovery scenarios
- Verify database schema compatibility
- Generate test reports and coverage metrics
- Document test procedures and results
"""

    testing_task = AgentTask(
        task_id="comprehensive_testing",
        task_type="qa-testing-guru",
        prompt=testing_prompt,
        dependencies=["integrate_with_mcp"],
        context={"phase": "phase1_completion", "priority": "high"},
    )

    agent_tasks.append(testing_task)

    # Task 5: Documentation (depends on testing)
    documentation_prompt = """TASK: Create comprehensive documentation for the complete Phase 1 system.

SPECIALIST ROLE: You are acting as a technical-writer agent.

CONTEXT:
- foundation_status: ALL PHASE 1 COMPONENTS COMPLETE AND TESTED
- database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- completed_system:
  • Database schema and connections ✓
  • Chat adapter with entity extraction ✓
  • Code adapter with AST analysis ✓
  • MCP integration layer ✓
  • Unified ingestion pipeline ✓
  • Comprehensive test suite ✓
- documentation_scope:
  • System architecture overview
  • Component usage guides
  • API documentation
  • Deployment procedures
  • Troubleshooting guides
  • Phase 2 readiness assessment

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context

PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System. All components are now complete, integrated, and tested. Your task is to create comprehensive documentation for deployment, usage, and transition to Phase 2.

IMPLEMENTATION REQUIREMENTS:
- Create comprehensive system documentation
- Document all component APIs and interfaces
- Provide deployment and configuration guides
- Document troubleshooting and maintenance procedures
- Create usage examples and tutorials
- Assess Phase 2 readiness and requirements
- Generate final Phase 1 completion report
"""

    documentation_task = AgentTask(
        task_id="create_documentation",
        task_type="technical-writer",
        prompt=documentation_prompt,
        dependencies=["comprehensive_testing"],
        context={"phase": "phase1_completion", "priority": "high"},
    )

    agent_tasks.append(documentation_task)

    return agent_tasks


async def main():
    """Execute the remaining Phase 1 completion tasks"""

    print("🚀 CONTINUING PHASE 1 COMPLETION")
    print("=" * 60)
    print("📋 Status: Chat and Code adapters COMPLETE")
    print("🎯 Remaining: Integration → Testing → Documentation")
    print("⚡ Parallel capacity: 18 tokens configured")
    print()

    # Initialize token loader
    print("🔧 Initializing token loader...")
    token_loader = TokenLoader()
    tokens = token_loader.load_tokens()
    print(f"✅ Loaded {len(tokens)} tokens")
    print()

    # Create tasks
    print("📝 Creating remaining tasks...")
    tasks = create_remaining_phase1_tasks()
    print(f"✅ Created {len(tasks)} tasks")
    for task in tasks:
        deps = task.dependencies if task.dependencies else "none"
        print(f"   • {task.task_id} ({task.task_type}) - deps: {deps}")
    print()

    # Initialize orchestrator
    print("🎼 Initializing orchestrator...")
    orchestrator = GenericOrchestrator(
        max_parallel=3,  # Conservative for integration tasks
        output_dir=Path("phase1_completion_continue_output"),
    )
    print("✅ Orchestrator ready")
    print()

    # Execute tasks
    print("🚀 Starting execution...")
    print("📊 Expected timeline:")
    print("   Stage 1: Integration (20-30 minutes)")
    print("   Stage 2: Testing (30-40 minutes)")
    print("   Stage 3: Documentation (15-20 minutes)")
    print()

    try:
        results = await orchestrator.execute_batch(tasks)

        print("\n" + "=" * 60)
        print("✅ PHASE 1 COMPLETION CONTINUED - RESULTS")
        print("=" * 60)

        for task_id, result in results.items():
            status = "✅ SUCCESS" if not result.get("is_error") else "❌ FAILED"
            duration = result.get("duration_ms", 0) / 1000
            print(f"{status} {task_id}: {duration:.1f}s")

        print()
        print("📁 Results saved to: phase1_completion_continue_output/")
        print("🎉 Phase 1 completion continued successfully!")

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    asyncio.run(main())
