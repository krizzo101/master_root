#!/usr/bin/env python3
"""
Parallel completion of unified context system using agent orchestrator.
Distributes remaining tasks across 15 parallel agents for maximum efficiency.
"""

import asyncio
import sys
from pathlib import Path

# Add orchestrator to path
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
from generic_orchestrator import AgentTask, GenericOrchestrator


async def complete_unified_context_system():
    """Execute all remaining unified context system tasks in parallel."""

    print("🚀 Starting parallel execution of unified context system tasks...")
    print("📊 Using 15 parallel Claude agents for maximum efficiency")

    orchestrator = GenericOrchestrator(
        output_dir=Path("/tmp/unified_context_completion"), max_parallel=15
    )

    # Define all remaining tasks with proper dependencies
    tasks = [
        # PHASE 1: Core Infrastructure (Independent - can run in parallel)
        AgentTask(
            task_id="context_items_population",
            task_type="development",
            prompt="""
            Task: Implement context_items table population from all sources

            Context: You are working on the unified context system that combines PostgreSQL + Neo4j + chat analytics.

            Requirements:
            1. Create a comprehensive data ingestion script for the context_items table
            2. Populate from ALL sources: .proj-intel data, chat logs, monitoring metrics, code elements
            3. Use the existing PostgreSQL schema with JSONB fields for flexible data storage
            4. Implement batch processing for large datasets (similar to Neo4j approach)
            5. Add data validation and deduplication logic
            6. Create progress tracking and error handling

            Files to work with:
            - /home/opsvi/master_root/init-scripts/01-create-schema.sql (context_items table schema)
            - /home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/proj_intel_ingester.py (reference for ingestion patterns)
            - /home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/dual_write_adapter.py (database connections)

            Expected output: A complete context_items_populator.py script that ingests all available data sources into the unified context_items table.
            """,
            context={
                "database_schema": "/home/opsvi/master_root/init-scripts/01-create-schema.sql",
                "reference_files": [
                    "/home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/proj_intel_ingester.py",
                    "/home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/dual_write_adapter.py",
                ],
                "work_location": "/home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/",
            },
            dependencies=[],
        ),
        AgentTask(
            task_id="materialized_views_testing",
            task_type="testing",
            prompt="""
            Task: Test materialized views and refresh functions

            Context: The unified context system uses PostgreSQL materialized views for performance optimization.

            Requirements:
            1. Test all materialized views defined in the schema
            2. Verify refresh functions work correctly and improve performance
            3. Create performance benchmarks (before/after view creation)
            4. Test automatic refresh triggers and manual refresh procedures
            5. Validate data consistency between base tables and materialized views
            6. Create monitoring for view staleness and refresh performance

            Files to examine:
            - /home/opsvi/master_root/init-scripts/01-create-schema.sql (materialized views definitions)
            - PostgreSQL database: unified_context (connection: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context)

            Expected output: A comprehensive testing script and performance report for all materialized views.
            """,
            context={
                "database_url": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
                "schema_file": "/home/opsvi/master_root/init-scripts/01-create-schema.sql",
            },
            dependencies=[],
        ),
        AgentTask(
            task_id="pgvector_extension",
            task_type="development",
            prompt="""
            Task: Add pgvector extension for semantic search

            Context: The unified context system needs semantic search capabilities for intelligent code and chat analytics.

            Requirements:
            1. Install and configure pgvector extension in PostgreSQL
            2. Add vector columns to context_items table for embeddings
            3. Create vector similarity search functions and indexes
            4. Integrate with existing embedding service at localhost:8001
            5. Create semantic search API endpoints
            6. Add vector operations for code similarity, chat context matching
            7. Create benchmarks for vector search performance

            Integration points:
            - PostgreSQL database: unified_context
            - Embedding service: http://localhost:8001 (already running)
            - Existing schema: /home/opsvi/master_root/init-scripts/01-create-schema.sql

            Expected output: Complete pgvector integration with semantic search capabilities ready for production use.
            """,
            context={
                "database_url": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
                "embedding_service": "http://localhost:8001",
                "schema_file": "/home/opsvi/master_root/init-scripts/01-create-schema.sql",
            },
            dependencies=[],
        ),
        AgentTask(
            task_id="sqlite_migration_script",
            task_type="development",
            prompt="""
            Task: Create migration script for existing SQLite data

            Context: The system is migrating from SQLite to PostgreSQL with dual-write pattern. Need to migrate historical data.

            Requirements:
            1. Create comprehensive SQLite to PostgreSQL migration script
            2. Migrate all existing chat logs, analytics, and intelligence data
            3. Preserve data integrity and relationships during migration
            4. Handle data type conversions (SQLite to PostgreSQL)
            5. Create validation and rollback mechanisms
            6. Support incremental migration for large datasets
            7. Generate migration reports and statistics

            Source data:
            - SQLite database: /home/opsvi/master_root/chat_logs.db
            - Target: PostgreSQL unified_context database
            - Reference dual-write adapter: /home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/dual_write_adapter.py

            Expected output: Production-ready migration script with validation and reporting capabilities.
            """,
            context={
                "sqlite_path": "/home/opsvi/master_root/chat_logs.db",
                "postgres_url": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
                "dual_write_adapter": "/home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/dual_write_adapter.py",
            },
            dependencies=[],
        ),
        AgentTask(
            task_id="realtime_chat_ingestion",
            task_type="development",
            prompt="""
            Task: Set up real-time chat log ingestion

            Context: Need real-time ingestion of Claude chat logs into the unified context system for immediate correlation and analytics.

            Requirements:
            1. Create real-time chat log monitoring and ingestion system
            2. Watch for new chat logs and ingest them immediately
            3. Integrate with correlator for real-time code correlation
            4. Support multiple chat log formats and sources
            5. Add buffering and batch processing for high throughput
            6. Create monitoring and alerting for ingestion health
            7. Ensure fault tolerance and recovery mechanisms

            Integration points:
            - Chat log sources: various locations in /home/opsvi/master_root/
            - Correlator: /home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/correlator.py
            - Database: PostgreSQL unified_context with dual-write to SQLite

            Expected output: Production-ready real-time chat log ingestion service with monitoring.
            """,
            context={
                "chat_log_paths": [
                    "/home/opsvi/master_root/chat_logs.db",
                    "/home/opsvi/master_root/.claude/",
                ],
                "correlator_path": "/home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/correlator.py",
                "database_url": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
            },
            dependencies=[],
        ),
        # PHASE 2: Integration & Bridge (Depends on core components)
        AgentTask(
            task_id="ide_context_bridge",
            task_type="development",
            prompt="""
            Task: Implement IDE context bridge integration

            Context: Create bridge between IDE/editor context and the unified context system for intelligent code assistance.

            Requirements:
            1. Create IDE context bridge that captures current file, cursor position, selection
            2. Integrate with unified context system to provide relevant code intelligence
            3. Support multiple IDEs: VSCode, Vim, Emacs through standardized protocol
            4. Provide real-time code suggestions based on context_items data
            5. Create semantic search integration for finding relevant code examples
            6. Add chat history integration for contextual assistance
            7. Implement caching and performance optimization

            Dependencies:
            - Must use populated context_items table for relevant suggestions
            - Requires pgvector for semantic search capabilities
            - Needs real-time ingestion for up-to-date context

            Expected output: IDE bridge system with standardized protocol for intelligent code assistance.
            """,
            context={
                "context_system": "unified_context PostgreSQL database",
                "semantic_search": "pgvector extension required",
                "target_ides": ["vscode", "vim", "emacs"],
            },
            dependencies=[
                "context_items_population",
                "pgvector_extension",
                "realtime_chat_ingestion",
            ],
        ),
        # PHASE 3: Monitoring & Optimization (Final phase)
        AgentTask(
            task_id="monitoring_performance_optimization",
            task_type="devops",
            prompt="""
            Task: Set up monitoring and performance optimization

            Context: Create comprehensive monitoring and optimization for the completed unified context system.

            Requirements:
            1. Create comprehensive monitoring dashboard for all system components
            2. Set up performance metrics collection for PostgreSQL, Neo4j, ingestion pipelines
            3. Create alerting for system health, performance degradation, data quality issues
            4. Implement automated performance optimization recommendations
            5. Create system health checks and diagnostic tools
            6. Set up log aggregation and analysis
            7. Create capacity planning and scaling recommendations

            Components to monitor:
            - PostgreSQL with TimescaleDB (unified_context database)
            - Neo4j graph database
            - Real-time ingestion pipelines
            - Chat correlation engine
            - IDE context bridge
            - Semantic search performance

            Expected output: Production-ready monitoring and optimization suite with dashboards and alerting.
            """,
            context={
                "postgres_url": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
                "neo4j_uri": "bolt://localhost:7687",
                "components": [
                    "correlator",
                    "ingestion",
                    "ide_bridge",
                    "semantic_search",
                ],
            },
            dependencies=[
                "context_items_population",
                "materialized_views_testing",
                "pgvector_extension",
                "sqlite_migration_script",
                "realtime_chat_ingestion",
                "ide_context_bridge",
            ],
        ),
        # BONUS: Documentation & Validation
        AgentTask(
            task_id="system_validation_documentation",
            task_type="documentation",
            prompt="""
            Task: Create comprehensive system validation and documentation

            Context: Document and validate the completed unified context system for production readiness.

            Requirements:
            1. Create end-to-end system validation tests
            2. Generate comprehensive system documentation
            3. Create deployment and operations guide
            4. Document all APIs, data flows, and integration points
            5. Create troubleshooting and maintenance guides
            6. Validate all components work together correctly
            7. Create performance benchmarks and SLA documentation

            System components to document:
            - PostgreSQL + TimescaleDB + pgvector setup
            - Neo4j relationship graph
            - Real-time ingestion pipelines
            - Chat correlation engine
            - IDE context bridge
            - Monitoring and alerting systems

            Expected output: Production-ready documentation suite and validation report.
            """,
            context={
                "system_components": [
                    "postgresql",
                    "neo4j",
                    "ingestion",
                    "correlation",
                    "ide_bridge",
                    "monitoring",
                ],
                "validation_scope": "end-to-end system integration",
            },
            dependencies=["monitoring_performance_optimization"],
        ),
    ]

    print(f"📋 Created {len(tasks)} parallel tasks:")
    for task in tasks:
        deps_str = (
            f" (depends on: {', '.join(task.dependencies)})"
            if task.dependencies
            else " (independent)"
        )
        print(f"   • {task.task_id}{deps_str}")

    print(f"\n🔄 Executing tasks with up to 15 parallel agents...")

    # Execute all tasks (orchestrator handles dependencies automatically)
    results = await orchestrator.execute_batch(tasks)

    print(f"\n✅ Parallel execution complete!")

    # Report results
    completed = [r for r in results if r["status"] == "completed"]
    failed = [r for r in results if r["status"] == "failed"]

    print(f"📊 Results summary:")
    print(f"   ✅ Completed: {len(completed)}")
    print(f"   ❌ Failed: {len(failed)}")

    if failed:
        print(f"\n❌ Failed tasks:")
        for result in failed:
            print(f"   • {result['task_id']}: {result.get('error', 'Unknown error')}")

    if completed:
        print(f"\n🎉 Successfully completed tasks:")
        for result in completed:
            duration = result.get("duration_ms", 0) / 1000
            print(f"   • {result['task_id']} ({duration:.1f}s)")

    print(f"\n📁 Task outputs saved to: /tmp/unified_context_completion/tasks/")
    print(f"🔍 Review individual task results for detailed implementation.")

    return results


async def main():
    """Main execution function."""
    try:
        results = await complete_unified_context_system()

        # Additional summary
        total_duration = sum(r.get("duration_ms", 0) for r in results) / 1000
        parallel_duration = max(r.get("duration_ms", 0) for r in results) / 1000
        speedup = total_duration / parallel_duration if parallel_duration > 0 else 1

        print(f"\n⚡ Performance summary:")
        print(f"   Total work: {total_duration:.1f} seconds")
        print(f"   Parallel time: {parallel_duration:.1f} seconds")
        print(f"   Speedup: {speedup:.1f}x")
        print(f"\n🚀 Unified Context System implementation complete!")

    except Exception as e:
        print(f"❌ Orchestration failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
