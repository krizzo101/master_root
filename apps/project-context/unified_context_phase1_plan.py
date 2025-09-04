#!/usr/bin/env python3
"""
ExecutionPlan for Unified Context System Phase 1 Implementation
Using the ExecutionPlan system for high-velocity parallel development
"""
import os
import sys

sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")

from execution_plan_schema import QualityGateType, TaskType
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_validation import validate_execution_plan


def create_unified_context_phase1_plan():
    """
    Create ExecutionPlan for Unified Context System Phase 1: Foundation (Week 1-2)
    Based on the design document at docs/unified-context-system-design.md
    """

    builder = ExecutionPlanBuilder("Unified Context System Phase 1: Foundation")

    # === ANALYSIS & ARCHITECTURE PHASE ===

    builder.add_task(
        "analyze_existing_systems",
        TaskType.SOLUTION_ARCHITECT,
        "Analyze existing database systems (PostgreSQL, Neo4j, SQLite chat logs) and their schemas to understand current state and integration points",
        context={
            "files_to_analyze": [
                "/home/opsvi/master_root/apps/project-context/src/project_context/db/connections.py",
                "/home/opsvi/master_root/chat_logs.db",
                "Neo4j knowledge graph structure",
            ]
        },
    )

    builder.add_task(
        "research_timescale_pgvector",
        TaskType.RESEARCH_GENIUS,
        "Research TimescaleDB and pgvector integration patterns, performance characteristics, and best practices for time-series + vector data",
        context={
            "focus_areas": [
                "TimescaleDB hypertables for chat logs",
                "pgvector for semantic search",
                "Performance optimization",
                "Integration patterns",
            ]
        },
    )

    # === DATABASE ARCHITECTURE PHASE ===

    builder.add_task(
        "design_unified_schema",
        TaskType.DATABASE_SPECIALIST,
        "Design the complete unified context database schema based on the design document, incorporating context_items, relationships, and metrics tables",
        dependencies=["analyze_existing_systems", "research_timescale_pgvector"],
        context={
            "schema_requirements": [
                "context_items table with polymorphic design",
                "context_relationships for graph connections",
                "correlation_patterns for learned patterns",
                "context_metrics_hourly for aggregations",
                "TimescaleDB hypertables",
                "pgvector indexes",
            ]
        },
    )

    builder.add_task(
        "implement_core_schema",
        TaskType.DATABASE_SPECIALIST,
        "Implement the unified context schema in PostgreSQL with TimescaleDB and pgvector extensions, including all indexes and constraints",
        dependencies=["design_unified_schema"],
        context={
            "deliverables": [
                "SQL migration scripts",
                "Index creation scripts",
                "Hypertable setup",
                "Vector index configuration",
            ]
        },
    )

    # === INGESTION PIPELINE ARCHITECTURE ===

    builder.add_task(
        "design_ingestion_pipeline",
        TaskType.SOLUTION_ARCHITECT,
        "Design the base ingestion pipeline architecture with pluggable adapters for different data sources (chat, code, git, errors)",
        dependencies=["design_unified_schema"],
        context={
            "pipeline_components": [
                "Base IngestionPipeline class",
                "Source-specific adapters",
                "Validation and normalization",
                "Deduplication logic",
                "Embedding generation",
                "Relationship extraction",
            ]
        },
    )

    builder.add_task(
        "implement_base_pipeline",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Implement the core ingestion pipeline with async processing, error handling, and pluggable adapter architecture",
        dependencies=["design_ingestion_pipeline", "implement_core_schema"],
        context={
            "implementation_files": [
                "src/ingestion/base_pipeline.py",
                "src/ingestion/adapters/__init__.py",
                "src/ingestion/processors.py",
                "src/ingestion/validators.py",
            ]
        },
    )

    # === CHAT LOG ADAPTER ===

    builder.add_task(
        "implement_chat_adapter",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Build the chat log adapter to ingest JSONL chat logs into the unified context system with proper entity extraction and relationships",
        dependencies=["implement_base_pipeline"],
        context={
            "adapter_features": [
                "JSONL parsing",
                "Message normalization",
                "File/function/symbol extraction",
                "Tool usage tracking",
                "Actor identification",
                "Embedding generation",
            ]
        },
    )

    # === CODE INTELLIGENCE ADAPTER ===

    builder.add_task(
        "implement_code_adapter",
        TaskType.DEVELOPMENT_SPECIALIST,
        "Build the code intelligence adapter to ingest .proj-intel data and AST analysis into the unified context system",
        dependencies=["implement_base_pipeline"],
        context={
            "adapter_features": [
                ".proj-intel integration",
                "Symbol indexing",
                "File-level context",
                "Function-level context",
                "Dependency relationships",
                "Code metrics extraction",
            ]
        },
    )

    # === INTEGRATION & TESTING ===

    builder.add_task(
        "integrate_with_mcp",
        TaskType.API_INTEGRATION_SPECIALIST,
        "Integrate the unified context system with the existing project-context MCP server, updating the 21 tools to use the new backend",
        dependencies=["implement_chat_adapter", "implement_code_adapter"],
        context={
            "integration_points": [
                "Update MCP tool implementations",
                "Connection pooling",
                "Query optimization",
                "Error handling",
                "Backward compatibility",
            ]
        },
    )

    builder.add_task(
        "comprehensive_testing",
        TaskType.QA_TESTING_GURU,
        "Create and execute comprehensive test suite for the unified context system including unit tests, integration tests, and performance tests",
        dependencies=["integrate_with_mcp"],
        context={
            "test_coverage": [
                "Ingestion pipeline tests",
                "Database schema validation",
                "Adapter functionality",
                "MCP tool integration",
                "Performance benchmarks",
                "Load testing",
            ]
        },
    )

    builder.add_task(
        "create_documentation",
        TaskType.TECHNICAL_WRITER,
        "Create comprehensive documentation for the unified context system including architecture overview, API docs, and developer guides",
        dependencies=["comprehensive_testing"],
        context={
            "documentation_types": [
                "Architecture documentation",
                "API reference",
                "Developer setup guide",
                "Usage examples",
                "Performance tuning guide",
            ]
        },
    )

    # === QUALITY GATES ===

    # Database quality gate
    builder.add_quality_gate(
        "database_validation",
        "Database Schema Validation",
        "Validate database schema is properly created with all indexes and constraints",
        QualityGateType.DATABASE,
        {
            "required_tables": [
                "context_items",
                "context_relationships",
                "correlation_patterns",
            ],
            "required_extensions": ["timescaledb", "vector"],
            "required_indexes": True,
        },
    )

    # Code quality gate
    builder.add_quality_gate(
        "code_quality_check",
        "Code Quality Standards",
        "Validate code meets quality standards with proper testing coverage",
        QualityGateType.CODE_QUALITY,
        {"min_coverage": 80, "max_complexity": 15, "type_checking": True},
    )

    # Integration testing gate
    builder.add_quality_gate(
        "integration_validation",
        "Integration Testing Validation",
        "Validate all components integrate properly with existing systems",
        QualityGateType.TEST_RESULTS,
        {
            "required_test_types": ["unit", "integration", "performance"],
            "min_pass_rate": 95,
        },
    )

    # Performance validation gate
    builder.add_quality_gate(
        "performance_validation",
        "Performance Standards Validation",
        "Validate system meets performance requirements for ingestion and queries",
        QualityGateType.CUSTOM,
        {
            "ingestion_rate": "1000+ items/second",
            "query_response": "< 100ms for simple queries",
            "concurrent_users": "10+ simultaneous",
        },
    )

    return builder.build()


def main():
    """Create and validate the execution plan"""
    print("🚀 Creating Unified Context System Phase 1 ExecutionPlan...")

    plan = create_unified_context_phase1_plan()

    print(
        f"📋 Plan created with {len(plan.tasks)} tasks and {len(plan.quality_gates)} quality gates"
    )

    # Validate the plan
    print("\n🔍 Validating execution plan...")
    result = validate_execution_plan(plan)

    if result.success:
        print("✅ ExecutionPlan validation PASSED!")
        print(f"   Tasks: {len(plan.tasks)}")
        print(f"   Quality Gates: {len(plan.quality_gates)}")
        print(f"   Dependencies: {sum(len(task.dependencies) for task in plan.tasks)}")

        print("\n📊 Task breakdown by agent type:")
        task_types = {}
        for task in plan.tasks:
            agent_type = task.task_type.value
            task_types[agent_type] = task_types.get(agent_type, 0) + 1

        for agent_type, count in sorted(task_types.items()):
            print(f"   {agent_type}: {count} tasks")

        print("\n🎯 Ready to execute with GenericOrchestrator!")
        return plan

    else:
        print("❌ ExecutionPlan validation FAILED!")
        print(f"   Errors: {result.error_count}")
        for error in result.errors:
            print(f"   - {error}")
        return None


if __name__ == "__main__":
    main()
