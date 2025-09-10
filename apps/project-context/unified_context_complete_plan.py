#!/usr/bin/env python3
"""
Complete Unified Context System ExecutionPlan
Single comprehensive plan with design, build, test, and document phases
Uses advanced ExecutionPlan features including phases, parallel execution, and quality gates
"""
import os
import sys

sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")

from execution_plan_schema import QualityGateType, TaskPriority, TaskType
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_validation import validate_execution_plan


def create_unified_context_complete_plan():
    """
    Create complete ExecutionPlan for Unified Context System
    Single plan with proper phasing: Foundation → Ingestion → Correlation → Validation → Documentation
    """

    builder = ExecutionPlanBuilder("Unified Context System: Complete Implementation")

    # === PHASE 1: FOUNDATION ===

    builder.add_phase(
        "foundation",
        "Foundation & Architecture",
        "Core database setup, schema design, and architectural foundation",
        max_parallel=8,  # High parallelization for foundation work
        timeout_seconds=7200,  # 2 hours for complex tasks
    )

    # Foundation research tasks (parallel)
    foundation_research = [
        {
            "task_id": "research_timescale_pgvector",
            "task_type": TaskType.RESEARCH_GENIUS,
            "prompt": "Research TimescaleDB and pgvector integration patterns, performance characteristics, and best practices for time-series + vector data",
            "phase_id": "foundation",
            "estimated_duration_minutes": 45,
        },
        {
            "task_id": "research_correlation_algorithms",
            "task_type": TaskType.RESEARCH_GENIUS,
            "prompt": "Research advanced correlation algorithms, temporal analysis patterns, and causal chain detection methods",
            "phase_id": "foundation",
            "estimated_duration_minutes": 60,
        },
        {
            "task_id": "research_git_integration",
            "task_type": TaskType.RESEARCH_GENIUS,
            "prompt": "Research Git history analysis patterns, commit parsing libraries, and integration strategies for extracting code evolution data",
            "phase_id": "foundation",
            "estimated_duration_minutes": 40,
        },
    ]

    builder.add_parallel_tasks(foundation_research)

    # Architecture and analysis (parallel)
    foundation_analysis = [
        {
            "task_id": "analyze_existing_systems",
            "task_type": TaskType.SOLUTION_ARCHITECT,
            "prompt": "Analyze existing database systems (PostgreSQL, Neo4j, SQLite chat logs) and their schemas to understand current state and integration points",
            "phase_id": "foundation",
            "estimated_duration_minutes": 90,
        },
        {
            "task_id": "design_system_architecture",
            "task_type": TaskType.SOLUTION_ARCHITECT,
            "prompt": "Design complete system architecture including ingestion pipelines, correlation engine, and query layer integration",
            "dependencies": [
                "research_timescale_pgvector",
                "research_correlation_algorithms",
            ],
            "phase_id": "foundation",
            "estimated_duration_minutes": 120,
            "priority": TaskPriority.HIGH,
        },
    ]

    builder.add_parallel_tasks(foundation_analysis)

    # Database foundation (sequential after analysis)
    foundation_database = [
        {
            "task_id": "design_unified_schema",
            "task_type": TaskType.DATABASE_SPECIALIST,
            "prompt": "Design the complete unified context database schema based on research and analysis, incorporating context_items, relationships, and metrics tables",
            "dependencies": ["analyze_existing_systems", "design_system_architecture"],
            "phase_id": "foundation",
            "estimated_duration_minutes": 180,
            "priority": TaskPriority.CRITICAL,
        },
        {
            "task_id": "implement_core_schema",
            "task_type": TaskType.DATABASE_SPECIALIST,
            "prompt": "Implement the unified context schema in PostgreSQL with TimescaleDB and pgvector extensions, including all indexes and constraints",
            "dependencies": ["design_unified_schema"],
            "phase_id": "foundation",
            "estimated_duration_minutes": 120,
            "priority": TaskPriority.CRITICAL,
        },
    ]

    builder.add_sequential_tasks(foundation_database)

    # === PHASE 2: INGESTION PIPELINE ===

    builder.add_phase(
        "ingestion",
        "Data Ingestion Pipeline",
        "Complete ingestion system with all adapters and processing",
        depends_on_phases=["foundation"],
        max_parallel=10,  # Maximum parallelization for ingestion
        timeout_seconds=5400,  # 1.5 hours
    )

    # Ingestion design (parallel after foundation)
    ingestion_design = [
        {
            "task_id": "design_ingestion_pipeline",
            "task_type": TaskType.SOLUTION_ARCHITECT,
            "prompt": "Design the base ingestion pipeline architecture with pluggable adapters for different data sources (chat, code, git, errors)",
            "phase_id": "ingestion",
            "estimated_duration_minutes": 90,
        },
        {
            "task_id": "design_deduplication_engine",
            "task_type": TaskType.SOLUTION_ARCHITECT,
            "prompt": "Design comprehensive deduplication system with content hashing, similarity detection, and intelligent merging",
            "phase_id": "ingestion",
            "estimated_duration_minutes": 75,
        },
        {
            "task_id": "design_relationship_extractor",
            "task_type": TaskType.SOLUTION_ARCHITECT,
            "prompt": "Design intelligent relationship extraction system with pattern recognition and automatic correlation detection",
            "phase_id": "ingestion",
            "estimated_duration_minutes": 90,
        },
    ]

    builder.add_parallel_tasks(ingestion_design)

    # Core pipeline implementation (sequential after design)
    ingestion_core = [
        {
            "task_id": "implement_base_pipeline",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement the core ingestion pipeline with async processing, error handling, and pluggable adapter architecture",
            "dependencies": ["design_ingestion_pipeline"],
            "phase_id": "ingestion",
            "estimated_duration_minutes": 150,
            "priority": TaskPriority.HIGH,
        },
        {
            "task_id": "implement_deduplication",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement deduplication engine with hash-based detection, similarity analysis, and automatic merge logic",
            "dependencies": ["design_deduplication_engine"],
            "phase_id": "ingestion",
            "estimated_duration_minutes": 120,
        },
        {
            "task_id": "implement_relationship_extraction",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement relationship extraction engine with NLP pattern matching and machine learning correlation detection",
            "dependencies": ["design_relationship_extractor"],
            "phase_id": "ingestion",
            "estimated_duration_minutes": 135,
        },
    ]

    builder.add_parallel_tasks(ingestion_core)

    # Adapter implementations (parallel after core)
    ingestion_adapters = [
        {
            "task_id": "implement_chat_adapter",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Build the chat log adapter to ingest JSONL chat logs into the unified context system with proper entity extraction and relationships",
            "dependencies": ["implement_base_pipeline"],
            "phase_id": "ingestion",
            "estimated_duration_minutes": 90,
        },
        {
            "task_id": "implement_code_adapter",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Build the code intelligence adapter to ingest .proj-intel data and AST analysis into the unified context system",
            "dependencies": ["implement_base_pipeline"],
            "phase_id": "ingestion",
            "estimated_duration_minutes": 90,
        },
        {
            "task_id": "implement_git_adapter",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement the Git history adapter with comprehensive commit analysis and efficient incremental processing",
            "dependencies": ["implement_base_pipeline", "research_git_integration"],
            "phase_id": "ingestion",
            "estimated_duration_minutes": 120,
        },
        {
            "task_id": "implement_error_adapter",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement error log adapter with intelligent parsing, severity classification, and automatic correlation triggers",
            "dependencies": ["implement_base_pipeline"],
            "phase_id": "ingestion",
            "estimated_duration_minutes": 100,
        },
        {
            "task_id": "implement_embedding_system",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement high-performance embedding generation system with batching, caching, and fallback strategies",
            "dependencies": ["implement_base_pipeline"],
            "phase_id": "ingestion",
            "estimated_duration_minutes": 110,
        },
    ]

    builder.add_parallel_tasks(ingestion_adapters)

    # === PHASE 3: CORRELATION ENGINE ===

    builder.add_phase(
        "correlation",
        "Correlation & Intelligence Engine",
        "Advanced correlation, pattern detection, and causal analysis",
        depends_on_phases=["ingestion"],
        max_parallel=8,
        timeout_seconds=6000,
    )

    # Correlation implementation (parallel)
    correlation_tasks = [
        {
            "task_id": "implement_temporal_correlation",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement temporal correlation engine with efficient time-series analysis and event pattern detection",
            "dependencies": ["research_correlation_algorithms"],
            "phase_id": "correlation",
            "estimated_duration_minutes": 150,
            "priority": TaskPriority.HIGH,
        },
        {
            "task_id": "implement_causal_chains",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement causal chain analysis with multi-hop relationship detection and confidence scoring",
            "phase_id": "correlation",
            "estimated_duration_minutes": 135,
        },
        {
            "task_id": "implement_pattern_detector",
            "task_type": TaskType.DEVELOPMENT_SPECIALIST,
            "prompt": "Implement intelligent pattern detection system with anomaly detection and automatic pattern discovery",
            "phase_id": "correlation",
            "estimated_duration_minutes": 120,
        },
        {
            "task_id": "implement_correlation_storage",
            "task_type": TaskType.DATABASE_SPECIALIST,
            "prompt": "Implement correlation storage system with high-performance indexes and intelligent caching",
            "phase_id": "correlation",
            "estimated_duration_minutes": 90,
        },
    ]

    builder.add_parallel_tasks(correlation_tasks)

    # === PHASE 4: INTEGRATION & OPTIMIZATION ===

    builder.add_phase(
        "integration",
        "System Integration & Optimization",
        "Complete system integration with performance optimization",
        depends_on_phases=["correlation"],
        max_parallel=6,
        timeout_seconds=4800,
    )

    # Integration tasks (parallel)
    integration_tasks = [
        {
            "task_id": "integrate_ingestion_pipeline",
            "task_type": TaskType.API_INTEGRATION_SPECIALIST,
            "prompt": "Integrate all ingestion adapters into unified pipeline with orchestration, monitoring, and error handling",
            "dependencies": [
                "implement_chat_adapter",
                "implement_code_adapter",
                "implement_git_adapter",
                "implement_error_adapter",
                "implement_embedding_system",
                "implement_deduplication",
                "implement_relationship_extraction",
            ],
            "phase_id": "integration",
            "estimated_duration_minutes": 120,
            "priority": TaskPriority.CRITICAL,
        },
        {
            "task_id": "integrate_correlation_engine",
            "task_type": TaskType.API_INTEGRATION_SPECIALIST,
            "prompt": "Integrate all correlation components into unified engine with orchestration and monitoring",
            "dependencies": [
                "implement_temporal_correlation",
                "implement_causal_chains",
                "implement_pattern_detector",
                "implement_correlation_storage",
            ],
            "phase_id": "integration",
            "estimated_duration_minutes": 100,
            "priority": TaskPriority.HIGH,
        },
        {
            "task_id": "integrate_with_mcp",
            "task_type": TaskType.API_INTEGRATION_SPECIALIST,
            "prompt": "Integrate the unified context system with the existing project-context MCP server, updating the 21 tools to use the new backend",
            "dependencies": [
                "integrate_ingestion_pipeline",
                "integrate_correlation_engine",
            ],
            "phase_id": "integration",
            "estimated_duration_minutes": 150,
            "priority": TaskPriority.CRITICAL,
        },
        {
            "task_id": "optimize_system_performance",
            "task_type": TaskType.PERFORMANCE_OPTIMIZER,
            "prompt": "Optimize complete system performance for high-throughput processing and concurrent operations across all components",
            "dependencies": ["integrate_with_mcp"],
            "phase_id": "integration",
            "estimated_duration_minutes": 120,
        },
    ]

    builder.add_parallel_tasks(integration_tasks)

    # === PHASE 5: VALIDATION & TESTING ===

    builder.add_phase(
        "validation",
        "Comprehensive Validation & Testing",
        "Complete system validation with accuracy, performance, and end-to-end testing",
        depends_on_phases=["integration"],
        max_parallel=5,
        timeout_seconds=5400,
    )

    # Validation tasks (parallel)
    validation_tasks = [
        {
            "task_id": "comprehensive_testing",
            "task_type": TaskType.QA_TESTING_GURU,
            "prompt": "Create and execute comprehensive test suite for the unified context system including unit tests, integration tests, and performance tests",
            "phase_id": "validation",
            "estimated_duration_minutes": 150,
            "priority": TaskPriority.HIGH,
        },
        {
            "task_id": "correlation_accuracy_testing",
            "task_type": TaskType.QA_TESTING_GURU,
            "prompt": "Comprehensive testing of correlation accuracy using known relationships and validation datasets",
            "phase_id": "validation",
            "estimated_duration_minutes": 120,
        },
        {
            "task_id": "performance_validation",
            "task_type": TaskType.PERFORMANCE_OPTIMIZER,
            "prompt": "Performance testing of complete system under load with optimization recommendations",
            "phase_id": "validation",
            "estimated_duration_minutes": 100,
        },
        {
            "task_id": "security_validation",
            "task_type": TaskType.SECURITY_ARCHITECT,
            "prompt": "Complete security review including data validation, injection prevention, access controls, and compliance",
            "phase_id": "validation",
            "estimated_duration_minutes": 90,
        },
        {
            "task_id": "end_to_end_validation",
            "task_type": TaskType.QA_TESTING_GURU,
            "prompt": "End-to-end validation of complete pipeline from ingestion through correlation with real-world scenarios",
            "dependencies": ["comprehensive_testing", "correlation_accuracy_testing"],
            "phase_id": "validation",
            "estimated_duration_minutes": 120,
            "priority": TaskPriority.CRITICAL,
        },
    ]

    builder.add_parallel_tasks(validation_tasks)

    # === PHASE 6: DOCUMENTATION ===

    builder.add_phase(
        "documentation",
        "Comprehensive Documentation",
        "Complete documentation including architecture, APIs, user guides, and tutorials",
        depends_on_phases=["validation"],
        max_parallel=4,
        timeout_seconds=3600,
    )

    # Documentation tasks (parallel)
    documentation_tasks = [
        {
            "task_id": "create_architecture_documentation",
            "task_type": TaskType.TECHNICAL_WRITER,
            "prompt": "Create comprehensive architecture documentation including system design, data flow, component relationships, and deployment guide",
            "phase_id": "documentation",
            "estimated_duration_minutes": 90,
        },
        {
            "task_id": "create_api_documentation",
            "task_type": TaskType.TECHNICAL_WRITER,
            "prompt": "Create detailed API reference documentation for MCP tools with usage examples and interactive tutorials",
            "phase_id": "documentation",
            "estimated_duration_minutes": 75,
        },
        {
            "task_id": "create_user_guides",
            "task_type": TaskType.TECHNICAL_WRITER,
            "prompt": "Create comprehensive user guides for developers, analysts, and administrators using the system",
            "phase_id": "documentation",
            "estimated_duration_minutes": 90,
        },
        {
            "task_id": "create_troubleshooting_guide",
            "task_type": TaskType.TECHNICAL_WRITER,
            "prompt": "Create comprehensive troubleshooting guide with common issues, solutions, diagnostic procedures, and performance tuning",
            "phase_id": "documentation",
            "estimated_duration_minutes": 60,
        },
    ]

    builder.add_parallel_tasks(documentation_tasks)

    # Final documentation integration
    builder.add_task(
        "finalize_documentation",
        TaskType.TECHNICAL_WRITER,
        "Integrate all documentation into comprehensive website with search, navigation, and interactive examples",
        dependencies=[
            "create_architecture_documentation",
            "create_api_documentation",
            "create_user_guides",
            "create_troubleshooting_guide",
        ],
        phase_id="documentation",
        estimated_duration_minutes=60,
        priority=TaskPriority.HIGH,
    )

    # === QUALITY GATES ===

    # Foundation completion gate
    builder.add_quality_gate(
        "foundation_complete",
        "Foundation Phase Completion",
        "Validate foundation phase is complete with working database and architecture",
        QualityGateType.DATABASE,
        {
            "schema_implemented": "Required tables created",
            "indexes_created": "All performance indexes active",
            "extensions_enabled": "TimescaleDB and pgvector operational",
        },
    )

    # Ingestion completion gate
    builder.add_quality_gate(
        "ingestion_complete",
        "Ingestion Pipeline Completion",
        "Validate all ingestion adapters are functional with quality processing",
        QualityGateType.CUSTOM,
        {
            "adapters_functional": "5+ adapters working",
            "pipeline_throughput": ">1000 items/second",
            "deduplication_accuracy": ">95%",
        },
    )

    # Correlation accuracy gate
    builder.add_quality_gate(
        "correlation_accuracy",
        "Correlation Engine Accuracy Standards",
        "Validate correlation engine meets accuracy and performance requirements",
        QualityGateType.CUSTOM,
        {
            "correlation_precision": ">85%",
            "correlation_recall": ">80%",
            "causal_chain_accuracy": ">75%",
            "real_time_performance": "<5 seconds",
        },
    )

    # System integration gate
    builder.add_quality_gate(
        "system_integration",
        "Complete System Integration Standards",
        "Validate complete system works end-to-end with all components integrated",
        QualityGateType.TEST_RESULTS,
        {
            "integration_tests": ">95% pass rate",
            "mcp_tools_updated": "All 21 tools functional",
            "performance_targets": "All benchmarks met",
            "security_review": "PASSED",
        },
    )

    # Documentation completeness gate
    builder.add_quality_gate(
        "documentation_complete",
        "Documentation Completeness Standards",
        "Validate all required documentation is complete and accurate",
        QualityGateType.CUSTOM,
        {
            "documentation_coverage": ">90%",
            "user_guide_complete": "All user types covered",
            "api_docs_complete": "All endpoints documented",
            "troubleshooting_comprehensive": "Common issues covered",
        },
    )

    return builder.build()


def main():
    """Create and validate the complete execution plan"""
    print("🚀 Creating Unified Context System COMPLETE ExecutionPlan...")

    plan = create_unified_context_complete_plan()

    print(
        f"📋 Complete plan created with {len(plan.tasks)} tasks, {len(plan.phases)} phases, and {len(plan.quality_gates)} quality gates"
    )

    # Validate the plan
    print("\n🔍 Validating complete execution plan...")
    result = validate_execution_plan(plan)

    if result.success:
        print("✅ Complete ExecutionPlan validation PASSED!")
        print(f"   Tasks: {len(plan.tasks)}")
        print(f"   Phases: {len(plan.phases)}")
        print(f"   Quality Gates: {len(plan.quality_gates)}")
        print(f"   Dependencies: {sum(len(task.dependencies) for task in plan.tasks)}")

        print("\n📊 Execution phases:")
        for phase in plan.phases:
            phase_tasks = [t for t in plan.tasks if t.phase_id == phase.phase_id]
            print(
                f"   {phase.name}: {len(phase_tasks)} tasks (max_parallel={phase.max_parallel})"
            )

        print("\n📊 Task breakdown by agent type:")
        task_types = {}
        for task in plan.tasks:
            agent_type = task.task_type.value
            task_types[agent_type] = task_types.get(agent_type, 0) + 1

        for agent_type, count in sorted(task_types.items()):
            print(f"   {agent_type}: {count} tasks")

        total_duration = sum(
            task.estimated_duration_minutes or 60 for task in plan.tasks
        )
        print(f"\n⏱️  Estimated duration:")
        print(
            f"   Sequential: {total_duration} minutes ({total_duration/60:.1f} hours)"
        )
        print(
            f"   Parallel optimized: ~{total_duration/8:.0f} minutes ({total_duration/480:.1f} hours)"
        )

        print("\n🎯 COMPLETE UNIFIED CONTEXT SYSTEM READY FOR EXECUTION!")
        print("   ✅ Single comprehensive plan with proper phasing")
        print("   ✅ Design → Build → Test → Document all integrated")
        print("   ✅ Maximum parallelization with dependency management")
        print("   ✅ Comprehensive quality gates for each phase")

        return plan

    else:
        print("❌ Complete ExecutionPlan validation FAILED!")
        print(f"   Errors: {result.error_count}")
        for error in result.errors:
            print(f"   - {error}")
        return None


if __name__ == "__main__":
    main()
