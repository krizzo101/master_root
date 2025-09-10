#!/usr/bin/env python3
"""
Execute Phase 1 Completion with PracticalOrchestrator - Maximum Parallel + Deterministic Session IDs

Combines the best aspects:
- Working GenericOrchestrator foundation (reliable)
- PracticalOrchestrator enhancements (monitoring + session IDs)
- 18 parallel execution (maximum speed)
- Phase 1 completion tasks (final 5 tasks)
"""
import asyncio
import json
import sys
import time
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from practical_orchestrator import PracticalAgentTask, PracticalOrchestrator


def create_phase1_completion_tasks():
    """
    Create the final 5 Phase 1 tasks with deterministic session IDs

    Foundation Status: ✅ 6/11 tasks COMPLETE
    - research_timescale_pgvector ✅
    - analyze_existing_systems ✅
    - design_unified_schema ✅
    - implement_core_schema ✅
    - design_ingestion_pipeline ✅
    - implement_base_pipeline ✅

    Remaining: 5 tasks in dependency chain
    """

    tasks = [
        # STAGE 1: Parallel adapter implementation (no dependencies)
        PracticalAgentTask(
            task_id="implement_chat_adapter",
            task_type="development-specialist",
            prompt="""Implement chat log adapter for JSONL ingestion with entity extraction and embeddings.

FOUNDATION STATUS: ✅ Base pipeline implemented and ready in src/ingestion/

IMPLEMENTATION REQUIREMENTS:
- Build on existing base pipeline in src/ingestion/
- Parse JSONL chat logs with message extraction
- Extract entities, topics, and generate embeddings
- Support incremental ingestion with deduplication
- Implement async processing with proper error handling
- Create ChatAdapter class extending BaseAdapter

KEY DELIVERABLES:
1. src/project_context/ingestion/adapters/chat_adapter.py - Complete ChatAdapter implementation
2. Full async methods: fetch_items(), transform_item(), validate_item()
3. JSONL parsing with message deduplication
4. Entity extraction and topic analysis
5. Integration with existing pipeline framework
6. Comprehensive error handling and logging
7. Unit tests for adapter functionality

SUCCESS CRITERIA:
- ChatAdapter processes JSONL files successfully
- Deduplication prevents duplicate ingestion
- Entities and embeddings are properly extracted
- Integrates seamlessly with base pipeline
- All tests pass""",
            dependencies=[],  # Base pipeline is complete
            phase_id="adapters",
            priority="high",
            tags=["adapter", "chat", "jsonl", "ingestion"],
        ),
        PracticalAgentTask(
            task_id="implement_code_adapter",
            task_type="development-specialist",
            prompt="""Implement code analysis adapter for repository scanning with function/class extraction.

FOUNDATION STATUS: ✅ Base pipeline ready for code adapter integration

IMPLEMENTATION REQUIREMENTS:
- Build CodeAdapter extending BaseAdapter framework
- Scan repository files for code analysis
- Extract functions, classes, modules, and dependencies
- Support multiple programming languages (Python, JavaScript, etc.)
- Generate embeddings for code semantic search
- Implement file watching and incremental updates

KEY DELIVERABLES:
1. src/project_context/ingestion/adapters/code_adapter.py - Complete CodeAdapter
2. Multi-language code parsing and analysis
3. Function/class extraction with signatures and docstrings
4. Dependency graph analysis and import tracking
5. Code embeddings for semantic search
6. Incremental file monitoring and updates
7. Integration with base pipeline architecture

SUCCESS CRITERIA:
- CodeAdapter successfully scans repository
- Extracts functions, classes with proper metadata
- Supports incremental updates on file changes
- Generates meaningful code embeddings
- Integrates with pipeline framework
- Performance is acceptable for large codebases""",
            dependencies=[],  # Can run parallel with chat_adapter
            phase_id="adapters",
            priority="high",
            tags=["adapter", "code", "analysis", "repository"],
        ),
        # STAGE 2: Integration (depends on both adapters)
        PracticalAgentTask(
            task_id="integrate_with_mcp",
            task_type="api-integration-specialist",
            prompt="""Integrate chat and code adapters with MCP (Model Context Protocol) tools.

DEPENDENCIES: ✅ Both adapters implemented and tested

INTEGRATION REQUIREMENTS:
- Update existing 21 MCP tools to use new backend
- Ensure chat adapter integration with MCP chat tools
- Integrate code adapter with MCP code analysis tools
- Maintain backwards compatibility with existing tools
- Test all integrations thoroughly
- Update tool documentation and examples

KEY DELIVERABLES:
1. MCP tool updates for new adapter integration
2. Chat tool integration with ChatAdapter backend
3. Code tool integration with CodeAdapter backend
4. Backwards compatibility preservation
5. Updated tool documentation and examples
6. Integration test suite
7. Performance validation

SUCCESS CRITERIA:
- All 21 MCP tools work with new backend
- Chat tools properly use ChatAdapter
- Code tools properly use CodeAdapter
- No breaking changes in tool APIs
- Documentation is complete and accurate
- Performance meets or exceeds previous version""",
            dependencies=["implement_chat_adapter", "implement_code_adapter"],
            phase_id="integration",
            priority="normal",
            tags=["mcp", "integration", "api", "tools"],
        ),
        # STAGE 3: Testing (depends on integration)
        PracticalAgentTask(
            task_id="comprehensive_testing",
            task_type="qa-testing-guru",
            prompt="""Create comprehensive test suite for Phase 1 unified context system.

DEPENDENCIES: ✅ All adapters and MCP integration complete

TESTING REQUIREMENTS:
- Unit tests for ChatAdapter and CodeAdapter
- Integration tests for complete ingestion pipeline
- MCP tool integration tests
- Database validation and performance tests
- End-to-end system validation
- Error handling and edge case testing

KEY DELIVERABLES:
1. Complete unit test suite for all adapters
2. Integration tests for pipeline end-to-end
3. MCP tool integration test coverage
4. Database validation tests
5. Performance benchmarks and stress tests
6. Error handling validation
7. Test automation and CI integration
8. Test documentation and coverage reports

SUCCESS CRITERIA:
- >90% test coverage on all new components
- All unit tests pass reliably
- Integration tests validate complete workflows
- Performance meets baseline requirements
- Error handling is robust and tested
- Tests can run in CI/CD pipeline
- Clear test documentation and reports""",
            dependencies=["integrate_with_mcp"],
            phase_id="testing",
            priority="normal",
            tags=["testing", "qa", "validation", "coverage"],
        ),
        # STAGE 4: Documentation (depends on testing)
        PracticalAgentTask(
            task_id="create_documentation",
            task_type="technical-writer",
            prompt="""Create comprehensive documentation for Phase 1 implementation.

DEPENDENCIES: ✅ All implementation and testing complete

DOCUMENTATION REQUIREMENTS:
- Architecture overview and design decisions
- Complete API reference for all adapters
- Installation and setup guide
- Usage examples and tutorials
- Troubleshooting and FAQ
- Developer guide for extensions

KEY DELIVERABLES:
1. Architecture documentation with diagrams
2. Complete API reference documentation
3. Installation and setup guide
4. Usage tutorials with examples
5. Troubleshooting guide and FAQ
6. Developer guide for extending the system
7. Performance tuning guide
8. Migration guide from previous version

SUCCESS CRITERIA:
- Documentation covers all new functionality
- Clear examples and tutorials
- Architecture is well-explained with diagrams
- API reference is complete and accurate
- Installation guide works for new users
- Troubleshooting covers common issues
- Developer guide enables extensions""",
            dependencies=["comprehensive_testing"],
            phase_id="documentation",
            priority="low",
            tags=["documentation", "api", "tutorials", "guide"],
        ),
    ]

    return tasks


def print_execution_plan(tasks):
    """Print the execution plan with dependencies and session IDs"""

    print("📋 PHASE 1 COMPLETION EXECUTION PLAN")
    print("=" * 50)

    # Group by phase
    phases = {}
    for task in tasks:
        phase = task.phase_id or "no_phase"
        if phase not in phases:
            phases[phase] = []
        phases[phase].append(task)

    for phase_name, phase_tasks in phases.items():
        print(f"\n🔄 PHASE: {phase_name.upper()}")
        print("-" * 30)

        for task in phase_tasks:
            deps_str = (
                f" (depends: {', '.join(task.dependencies)})"
                if task.dependencies
                else " (no dependencies)"
            )
            print(f"  📌 {task.task_id}{deps_str}")
            print(f"     Session ID: {task.session_id}")
            print(f"     Priority: {task.priority}")
            print(f"     Monitor: tail -f {task.get_log_path()}")
            print()


async def execute_phase1_completion():
    """Execute Phase 1 completion with maximum parallel execution"""

    print("🚀 PHASE 1 COMPLETION - PRACTICAL ORCHESTRATOR")
    print("=" * 60)
    print("✅ Foundation: 6/11 tasks complete - database and pipeline ready")
    print("🎯 Remaining: 5 tasks in optimized dependency chain")
    print("⚡ Execution: Up to 18 parallel tasks with deterministic session IDs")
    print()

    # Create orchestrator with maximum parallel execution
    orchestrator = PracticalOrchestrator(
        output_dir="./phase1_completion_practical_output",
        max_parallel=18,  # Use all available tokens
        enable_monitoring=True,
        enable_quality_reports=True,
    )

    print(f"🔧 Token pool size: {orchestrator.token_pool.size()}")
    print(f"⚡ Max parallel: {orchestrator.max_parallel}")

    # Set up progress monitoring
    def progress_monitor(event_type: str, data: dict):
        timestamp = time.strftime("%H:%M:%S")
        print(
            f"[{timestamp}] 📊 {event_type}: {json.dumps(data, indent=2) if isinstance(data, dict) else data}"
        )

    orchestrator.set_progress_callback(progress_monitor)

    # Create Phase 1 completion tasks
    tasks = create_phase1_completion_tasks()

    # Print execution plan
    print_execution_plan(tasks)

    # Confirm execution
    print(f"\n🚀 READY TO EXECUTE")
    print("=" * 30)
    print(f"📊 Tasks: {len(tasks)}")
    print(f"⚡ Parallel: Up to {orchestrator.max_parallel}")
    print(f"🔍 Monitoring: Deterministic session IDs enabled")
    print(f"📁 Output: {orchestrator.output_dir}")

    # Execute tasks
    print(f"\n⏱️  Starting execution at {time.strftime('%H:%M:%S')}")
    start_time = time.time()

    try:
        results = await orchestrator.execute_batch(tasks)
        end_time = time.time()

        # Analyze results
        completed = len(
            [
                r
                for r in results
                if isinstance(r, dict) and r.get("status") == "completed"
            ]
        )
        failed = len(
            [r for r in results if isinstance(r, dict) and r.get("status") == "failed"]
        )
        errors = len([r for r in results if isinstance(r, Exception)])

        total_duration = end_time - start_time

        print(f"\n📊 EXECUTION COMPLETE")
        print("=" * 30)
        print(
            f"⏱️  Duration: {total_duration//3600:.0f}h {(total_duration%3600)//60:.0f}m {total_duration%60:.0f}s"
        )
        print(f"✅ Completed: {completed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")
        print(f"📈 Success rate: {completed/len(tasks):.1%}")

        # Show outputs
        print(f"\n📁 GENERATED OUTPUT")
        print("=" * 30)
        print(f"📊 Quality report: {orchestrator.output_dir}/quality_report.json")
        print(f"📋 Task outputs: {orchestrator.output_dir}/tasks/")

        # Show session monitoring
        print(f"\n🔍 SESSION MONITORING")
        print("=" * 30)
        orchestrator.print_session_map()

        if completed == len(tasks):
            print(f"\n🎉 SUCCESS! Phase 1 completion finished successfully!")
            print(f"✅ All {len(tasks)} tasks completed")
            print(f"🚀 Ready to proceed to Phase 2")
            return True
        else:
            print(f"\n⚠️  Phase 1 completion had issues:")
            print(f"   {completed}/{len(tasks)} tasks completed")
            print(f"   Check individual task outputs for details")
            return False

    except Exception as e:
        print(f"\n💥 EXECUTION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Phase 1 Completion - PracticalOrchestrator Edition")
    print("Combines reliability, speed, and monitoring")
    print("=" * 60)

    success = asyncio.run(execute_phase1_completion())

    if success:
        print(f"\n✅ Phase 1 completion successful!")
        print(f"🎯 System ready for Phase 2 execution")
    else:
        print(f"\n❌ Phase 1 completion needs attention")
        print(f"📋 Check the output above for specific issues")

    print(f"\nExecution complete. Check logs and outputs for details.")
    sys.exit(0 if success else 1)
