#!/usr/bin/env python3
"""
Phase 1 Completion Plan: Optimized ExecutionPlan for Final 5 Tasks
Build on excellent foundation work to complete Phase 1 implementation
"""
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")

from execution_plan_schema import QualityGateType, TaskPriority, TaskType
from execution_plan_template import ExecutionPlanBuilder


def create_phase1_completion_plan():
    """
    Create optimized ExecutionPlan for Phase 1 completion (final 5 tasks)

    Foundation Status: ✅ 6/11 tasks COMPLETE
    - Database schema: OPERATIONAL
    - Base pipeline: PRODUCTION READY
    - All dependencies satisfied for remaining tasks
    """

    builder = ExecutionPlanBuilder("Phase 1 Completion: Final 5 Tasks")

    # === STAGE 1: ADAPTER IMPLEMENTATION (Parallel Execution) ===

    # Stage 1: Parallel adapter implementation - both can run simultaneously
    builder.add_phase(
        "adapter_implementation",
        "Adapter Implementation",
        "Implement chat and code adapters in parallel - foundation ready",
        max_parallel=2,  # Run both adapters simultaneously
        depends_on_phases=[],  # No dependencies - base pipeline is ready!
        gates=[],
    )

    # Chat adapter implementation
    builder.add_task(
        "implement_chat_adapter",
        TaskType.DEVELOPMENT_SPECIALIST,
        """Implement chat log adapter for JSONL ingestion with entity extraction and embeddings.

        FOUNDATION STATUS: ✅ Base pipeline implemented and ready

        IMPLEMENTATION REQUIREMENTS:
        - Build on existing base pipeline in src/ingestion/
        - Parse JSONL chat logs with message extraction
        - Entity recognition and relationship mapping
        - Generate embeddings for semantic search
        - Integrate with unified schema (already implemented)
        - Handle incremental ingestion and deduplication

        FILES TO CREATE:
        - src/ingestion/adapters/chat_adapter.py
        - tests/test_chat_adapter.py

        INTEGRATION POINTS:
        - Use base_adapter.py framework (already implemented)
        - Connect to unified_context database (operational)
        - Leverage existing embedding pipeline
        """,
        context={
            "foundation_status": "Base pipeline COMPLETE and ready for use",
            "database": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
            "base_pipeline": "/home/opsvi/master_root/apps/project-context/src/ingestion/",
            "implementation_files": [
                "src/ingestion/adapters/chat_adapter.py",
                "tests/test_chat_adapter.py",
            ],
            "integration_points": [
                "base_adapter.py framework",
                "unified schema tables",
                "embedding pipeline",
                "deduplication engine",
            ],
        },
        dependencies=[],  # No dependencies - base pipeline is complete!
        phase_id="adapter_implementation",
        priority=TaskPriority.HIGH,
        estimated_duration_minutes=60,
    )

    # Code adapter implementation
    builder.add_task(
        "implement_code_adapter",
        TaskType.DEVELOPMENT_SPECIALIST,
        """Implement code adapter for .proj-intel and AST analysis with symbol indexing.

        FOUNDATION STATUS: ✅ Base pipeline implemented and ready

        IMPLEMENTATION REQUIREMENTS:
        - Build on existing base pipeline in src/ingestion/
        - Parse .proj-intel files and perform AST analysis
        - Extract symbols, functions, classes, dependencies
        - Build relationship graph between code entities
        - Integrate with unified schema (already implemented)
        - Support incremental code analysis

        FILES TO CREATE:
        - src/ingestion/adapters/code_adapter.py
        - tests/test_code_adapter.py

        INTEGRATION POINTS:
        - Use base_adapter.py framework (already implemented)
        - Connect to unified_context database (operational)
        - Leverage relationship extraction pipeline
        """,
        context={
            "foundation_status": "Base pipeline COMPLETE and ready for use",
            "database": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
            "base_pipeline": "/home/opsvi/master_root/apps/project-context/src/ingestion/",
            "implementation_files": [
                "src/ingestion/adapters/code_adapter.py",
                "tests/test_code_adapter.py",
            ],
            "integration_points": [
                "base_adapter.py framework",
                "unified schema tables",
                "symbol relationship extraction",
                "AST parsing utilities",
            ],
        },
        dependencies=[],  # No dependencies - base pipeline is complete!
        phase_id="adapter_implementation",
        priority=TaskPriority.HIGH,
        estimated_duration_minutes=60,
    )

    # === STAGE 2: MCP INTEGRATION (Sequential After Adapters) ===

    builder.add_phase(
        "mcp_integration",
        "MCP Integration",
        "Update existing MCP tools to use new unified backend",
        max_parallel=1,  # Single integration task
        depends_on_phases=["adapter_implementation"],  # Wait for both adapters
        gates=[],
    )

    builder.add_task(
        "integrate_with_mcp",
        TaskType.API_INTEGRATION_SPECIALIST,
        """Update existing 21 MCP tools to use new unified context backend.

        FOUNDATION STATUS: ✅ Database operational, adapters will be complete

        INTEGRATION REQUIREMENTS:
        - Update existing MCP server implementations
        - Replace current backend with unified_context database
        - Implement connection pooling for performance
        - Add query optimization for large datasets
        - Maintain backward compatibility with existing APIs
        - Add new capabilities from unified schema

        MCP TOOLS TO UPDATE:
        - Chat search tools
        - Code analysis tools
        - Project context tools
        - Knowledge management tools

        INTEGRATION POINTS:
        - Database: unified_context (operational)
        - Chat data: via new chat_adapter
        - Code data: via new code_adapter
        - Existing MCP server framework
        """,
        context={
            "foundation_status": "Database operational, adapters in progress",
            "database": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
            "mcp_tools_directory": "/home/opsvi/master_root/apps/",
            "integration_targets": [
                "Chat search MCP tools",
                "Code analysis MCP tools",
                "Project context MCP tools",
                "Knowledge management tools",
            ],
            "performance_requirements": [
                "Connection pooling",
                "Query optimization",
                "Large dataset handling",
                "Response time <500ms",
            ],
        },
        dependencies=["implement_chat_adapter", "implement_code_adapter"],
        phase_id="mcp_integration",
        priority=TaskPriority.HIGH,
        estimated_duration_minutes=90,
    )

    # === STAGE 3: VALIDATION (Sequential After Integration) ===

    builder.add_phase(
        "validation_testing",
        "Validation & Testing",
        "Comprehensive testing of complete system",
        max_parallel=1,  # Single testing task
        depends_on_phases=["mcp_integration"],  # Wait for MCP integration
        gates=["phase1_quality_gate"],
    )

    builder.add_task(
        "comprehensive_testing",
        TaskType.QA_TESTING_GURU,
        """Execute comprehensive testing of complete Phase 1 implementation.

        FOUNDATION STATUS: ✅ Full system integration complete

        TESTING REQUIREMENTS:
        - Unit tests for all adapters and components
        - Integration tests across full pipeline
        - Performance tests with large datasets
        - Database validation and integrity checks
        - MCP tool integration testing
        - End-to-end workflow validation

        TEST COVERAGE:
        - Database schema and operations
        - Chat adapter functionality
        - Code adapter functionality
        - MCP integration points
        - Performance under load
        - Error handling and recovery

        SUCCESS CRITERIA:
        - All unit tests pass (>95% coverage)
        - Integration tests pass (100%)
        - Performance meets requirements
        - No data corruption or loss
        - MCP tools work seamlessly
        """,
        context={
            "foundation_status": "Complete system ready for testing",
            "database": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
            "test_scope": [
                "Unit tests (adapters, pipeline)",
                "Integration tests (end-to-end)",
                "Performance tests (load handling)",
                "Database integrity tests",
                "MCP integration tests",
            ],
            "success_criteria": [
                "Unit test coverage >95%",
                "All integration tests pass",
                "Performance requirements met",
                "Zero data integrity issues",
                "MCP backward compatibility maintained",
            ],
        },
        dependencies=["integrate_with_mcp"],
        phase_id="validation_testing",
        priority=TaskPriority.HIGH,
        estimated_duration_minutes=120,
    )

    # === STAGE 4: DOCUMENTATION (Final Stage) ===

    builder.add_phase(
        "documentation",
        "Documentation",
        "Create comprehensive documentation for Phase 1 system",
        max_parallel=1,  # Single documentation task
        depends_on_phases=["validation_testing"],  # Wait for testing completion
        gates=[],
    )

    builder.add_task(
        "create_documentation",
        TaskType.TECHNICAL_WRITER,
        """Create comprehensive documentation for complete Phase 1 implementation.

        FOUNDATION STATUS: ✅ System tested and validated

        DOCUMENTATION REQUIREMENTS:
        - Architecture documentation with diagrams
        - API reference for all MCP tools
        - Developer setup and deployment guides
        - User guides for system features
        - Troubleshooting and maintenance docs
        - Performance tuning guidelines

        DELIVERABLES:
        - README.md (main system overview)
        - ARCHITECTURE.md (system design)
        - API_REFERENCE.md (MCP tool APIs)
        - DEVELOPER_GUIDE.md (setup/deployment)
        - USER_GUIDE.md (feature usage)
        - TROUBLESHOOTING.md (common issues)
        - PERFORMANCE.md (optimization guide)

        INTEGRATION:
        - Document all Phase 1 achievements
        - Prepare handoff for Phase 2 execution
        - Include monitoring and observability
        """,
        context={
            "foundation_status": "Complete Phase 1 system validated and ready",
            "documentation_deliverables": [
                "README.md (system overview)",
                "ARCHITECTURE.md (design docs)",
                "API_REFERENCE.md (MCP APIs)",
                "DEVELOPER_GUIDE.md (setup)",
                "USER_GUIDE.md (usage)",
                "TROUBLESHOOTING.md (support)",
                "PERFORMANCE.md (optimization)",
            ],
            "system_components": [
                "Database: PostgreSQL + TimescaleDB + pgvector",
                "Base Pipeline: Async ingestion framework",
                "Chat Adapter: JSONL processing",
                "Code Adapter: AST analysis",
                "MCP Integration: 21 updated tools",
            ],
        },
        dependencies=["comprehensive_testing"],
        phase_id="documentation",
        priority=TaskPriority.NORMAL,
        estimated_duration_minutes=90,
    )

    # === QUALITY GATES ===

    # Phase 1 completion quality gate
    builder.add_quality_gate(
        "phase1_quality_gate",
        "Phase 1 Completion Validation",
        "Validate Phase 1 implementation is complete and production-ready",
        QualityGateType.CUSTOM,
        {
            "adapters_implemented": ["chat_adapter", "code_adapter"],
            "mcp_tools_updated": 21,
            "test_coverage": ">95%",
            "integration_tests_passed": "100%",
            "performance_validated": True,
            "documentation_complete": True,
        },
    )

    return builder.build()


def main():
    """Create and validate the Phase 1 completion plan"""
    print("🚀 Creating Phase 1 Completion ExecutionPlan...")
    print("Foundation Status: ✅ 6/11 tasks complete, all dependencies satisfied")
    print()

    # Create the plan
    plan = create_phase1_completion_plan()
    print(f"📋 ExecutionPlan created: {len(plan.tasks)} tasks")
    print(f"📊 Phases: {len(plan.phases)} stages")
    print(f"🎯 Quality Gates: {len(plan.quality_gates)} gates")

    # Show phase breakdown
    print("\n📊 PHASE BREAKDOWN:")
    for phase in plan.phases:
        tasks_in_phase = [t for t in plan.tasks if t.phase_id == phase.phase_id]
        print(
            f"   Stage {len([p for p in plan.phases if plan.phases.index(p) < plan.phases.index(phase)]) + 1}: {phase.name}"
        )
        print(f"      Tasks: {len(tasks_in_phase)} (max_parallel={phase.max_parallel})")
        print(f"      Dependencies: {phase.depends_on_phases or 'None'}")
        for task in tasks_in_phase:
            print(f"        - {task.task_id}")
        print()

    # Show execution strategy
    print("⚡ EXECUTION STRATEGY:")
    print("   Stage 1: Parallel adapter implementation (2 tasks simultaneously)")
    print("   Stage 2: Sequential MCP integration (depends on adapters)")
    print("   Stage 3: Sequential testing (depends on integration)")
    print("   Stage 4: Sequential documentation (depends on testing)")
    print()

    print("🎯 EXPECTED OUTCOME:")
    print("   Complete Phase 1 implementation (11/11 tasks)")
    print("   Production-ready unified context system")
    print("   Ready for Phase 2 execution")
    print()

    print("🚀 READY FOR EXECUTION:")
    print("   All foundation work complete ✅")
    print("   All dependencies satisfied ✅")
    print("   Optimized for maximum velocity ✅")


if __name__ == "__main__":
    main()
