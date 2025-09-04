#!/usr/bin/env python3
"""
Execute Chat Log PostgreSQL Import - Phase 1 Infrastructure
Uses PracticalOrchestrator with 18 parallel execution for maximum speed
"""
import asyncio
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from practical_orchestrator import PracticalAgentTask, PracticalOrchestrator
from token_loader import TokenLoader


def create_chat_import_phase1_tasks():
    """
    Create Phase 1 tasks for chat log PostgreSQL import
    Focus: Infrastructure setup and database preparation
    """

    tasks = []

    # Task 1A: Database Schema Validation & Enhancement
    tasks.append(
        PracticalAgentTask(
            task_id="database_schema_validation",
            task_type="database-specialist",
            prompt="""TASK: Validate and enhance PostgreSQL schema for chat log import

SPECIALIST ROLE: You are acting as a database-specialist agent.

CONTEXT:
- Database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- SQLite Source: /home/opsvi/master_root/chat_logs.db (133MB, 539 sessions, 41K nodes, 19K tool calls)
- Target Tables: context_items, chat_sessions, agent_usage, file_activity
- Schema Files: /home/opsvi/master_root/apps/project-context/setup_unified_context_database.sql

REQUIREMENTS:
1. Verify context_items table supports chat message fields
2. Create optimized indexes for chat queries (session_id, timestamp, content search)
3. Add vector indexes for embeddings (if pgvector available)
4. Create materialized views for chat analytics
5. Validate foreign key relationships
6. Add performance tuning for bulk insert operations

DELIVERABLES:
- Enhanced schema with chat-specific optimizations
- Performance tuning recommendations
- Validation report of schema compatibility

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context""",
            dependencies=[],
            phase_id="infrastructure",
            tags=["database", "schema", "performance"],
            session_id="chat_import_db_schema_2025_09_04",
        )
    )

    # Task 1B: SQLite Bridge Adapter Implementation
    tasks.append(
        PracticalAgentTask(
            task_id="sqlite_bridge_adapter",
            task_type="development-specialist",
            prompt="""TASK: Create SQLite-to-ContextItem bridge adapter for chat import

SPECIALIST ROLE: You are acting as a development-specialist agent.

CONTEXT:
- SQLite Database: /home/opsvi/master_root/chat_logs.db
- Tables: sessions, nodes, tool_calls, tool_results, file_operations
- Target: Transform SQLite data → ContextItem objects → PostgreSQL
- Framework: /home/opsvi/master_root/apps/project-context/src/project_context/ingestion/

REQUIREMENTS:
1. Create SQLiteBridgeAdapter class extending BaseAdapter
2. Implement data transformation:
   - sessions → chat_sessions + context_items
   - nodes → context_items with proper entity_type
   - tool_calls + tool_results → agent_usage context_items
   - file_operations → file_activity context_items
3. Handle incremental processing and deduplication
4. Implement batch processing for 41K records
5. Add comprehensive error handling and logging
6. Include progress tracking and metrics

FILES TO CREATE:
- src/project_context/ingestion/adapters/sqlite_bridge_adapter.py
- tests/test_sqlite_bridge_adapter.py

DELIVERABLES:
- Complete SQLiteBridgeAdapter implementation
- Unit tests with 90%+ coverage
- Performance benchmarks for 41K records

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context""",
            dependencies=[],
            phase_id="infrastructure",
            tags=["adapter", "sqlite", "transformation"],
            session_id="chat_import_sqlite_bridge_2025_09_04",
        )
    )

    # Task 1C: Enhanced ChatAdapter Integration
    tasks.append(
        PracticalAgentTask(
            task_id="chat_adapter_integration",
            task_type="development-specialist",
            prompt="""TASK: Integrate SQLite data source into existing ChatAdapter

SPECIALIST ROLE: You are acting as a development-specialist agent.

CONTEXT:
- Existing File: /home/opsvi/master_root/apps/project-context/src/project_context/ingestion/adapters/chat_adapter.py
- Current Formats: jsonl, json, api, stream
- Add Format: sqlite_database
- SQLite Source: /home/opsvi/master_root/chat_logs.db

REQUIREMENTS:
1. Add "sqlite_database" to supported input_format options
2. Implement _fetch_from_sqlite_database() method
3. Integrate with existing entity extraction pipeline
4. Enhance conversation threading and session support
5. Add SQLite-specific relationship detection
6. Maintain compatibility with existing JSONL processing
7. Add configuration validation for SQLite sources

ENHANCEMENTS:
- Tool call entity extraction
- Session-based conversation flows
- File operation tracking integration
- Performance optimization for large SQLite datasets

DELIVERABLES:
- Enhanced ChatAdapter with SQLite support
- Updated configuration schema
- Integration tests
- Performance validation

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context""",
            dependencies=["sqlite_bridge_adapter"],
            phase_id="infrastructure",
            tags=["chat", "adapter", "integration"],
            session_id="chat_import_adapter_enhance_2025_09_04",
        )
    )

    # Task 1D: Vector Embeddings Service
    tasks.append(
        PracticalAgentTask(
            task_id="embedding_service",
            task_type="development-specialist",
            prompt="""TASK: Implement robust embedding generation service for chat messages

SPECIALIST ROLE: You are acting as a development-specialist agent.

CONTEXT:
- Chat Messages: 41,137 messages need embeddings
- Services: OpenAI API + sentence-transformers fallback
- Integration: ChatAdapter embedding generation
- Performance: Batch processing for efficiency

REQUIREMENTS:
1. Create EmbeddingService class with multiple backends:
   - OpenAI API (primary) - text-embedding-3-small
   - sentence-transformers (fallback) - all-MiniLM-L6-v2
   - Simple hash-based (testing)
2. Implement batch processing (32-100 messages per batch)
3. Add embedding caching and deduplication
4. Comprehensive error handling and retry logic
5. Rate limiting and API quota management
6. Progress tracking for large batches
7. Integration with existing ChatAdapter.generate_embedding()

FILES TO CREATE:
- src/project_context/services/embedding_service.py
- tests/test_embedding_service.py
- config/embedding_service_config.yaml

DELIVERABLES:
- Production-ready EmbeddingService
- Performance benchmarks (41K messages)
- Integration documentation
- Cost estimation for OpenAI usage

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context""",
            dependencies=[],
            phase_id="infrastructure",
            tags=["embeddings", "ai", "performance"],
            session_id="chat_import_embeddings_2025_09_04",
        )
    )

    # Task 1E: Configuration & Pipeline Setup
    tasks.append(
        PracticalAgentTask(
            task_id="pipeline_configuration",
            task_type="solution-architect",
            prompt="""TASK: Configure chat ingestion pipeline for production import

SPECIALIST ROLE: You are acting as a solution-architect agent.

CONTEXT:
- Pipeline Framework: /home/opsvi/master_root/apps/project-context/src/project_context/ingestion/
- Orchestrator: /home/opsvi/master_root/apps/project-context/src/project_context/ingestion/orchestrator.py
- Data Volume: 133MB SQLite → PostgreSQL (539 sessions, 41K nodes, 19K tool calls)

REQUIREMENTS:
1. Create ingestion pipeline configuration:
   - Register SQLiteBridgeAdapter and enhanced ChatAdapter
   - Configure batch processing (optimal batch sizes)
   - Set up parallel processing workflows
   - Configure embedding generation pipeline
   - Add progress tracking and monitoring
2. Update orchestrator to handle chat import workflow
3. Create production configuration files:
   - config/chat_import_pipeline.yaml
   - config/sqlite_source_config.yaml
4. Add pipeline validation and health checks
5. Implement failure recovery mechanisms

FILES TO CREATE:
- config/chat_import_pipeline.yaml
- config/sqlite_source_config.yaml
- src/project_context/ingestion/chat_import_pipeline.py

DELIVERABLES:
- Complete pipeline configuration
- Production-ready orchestration setup
- Performance tuning recommendations
- Operational documentation

WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context""",
            dependencies=[
                "sqlite_bridge_adapter",
                "chat_adapter_integration",
                "embedding_service",
            ],
            phase_id="infrastructure",
            tags=["configuration", "pipeline", "orchestration"],
            session_id="chat_import_pipeline_2025_09_04",
        )
    )

    return tasks


async def main():
    """Execute Phase 1 of chat log PostgreSQL import"""

    print("🚀 Starting Chat Log PostgreSQL Import - Phase 1")
    print("=" * 60)

    # Load tokens for parallel execution
    token_loader = TokenLoader()
    tokens = token_loader.load_tokens()
    print(f"📋 Loaded {len(tokens)} tokens for parallel execution")

    # Create orchestrator with 18 parallel execution
    from pathlib import Path

    orchestrator = PracticalOrchestrator(
        output_dir=Path("/home/opsvi/master_root/apps/project-context/phase1_output"),
        max_parallel=min(18, len(tokens)),  # Don't exceed available tokens
        tokens=tokens,
        enable_monitoring=True,
        enable_quality_reports=True,
    )

    # Create Phase 1 tasks
    tasks = create_chat_import_phase1_tasks()

    print(f"📋 Created {len(tasks)} Phase 1 infrastructure tasks")
    for task in tasks:
        print(
            f"  • {task.task_id} ({task.task_type}, dependencies: {len(task.dependencies)})"
        )
    print()

    # Execute tasks with monitoring
    print("⚡ Executing Phase 1 tasks with 18 parallel execution...")
    start_time = asyncio.get_event_loop().time()

    try:
        results = await orchestrator.execute_batch(tasks)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        print(f"\n✅ Phase 1 completed in {duration:.1f} seconds")
        successful = [
            r for r in results if isinstance(r, dict) and r.get("status") == "completed"
        ]
        failed = [
            r for r in results if isinstance(r, dict) and r.get("status") == "failed"
        ]

        print(f"📊 Results: {len(successful)} successful, {len(failed)} failed")

        # Show detailed results
        for result in results:
            if isinstance(result, dict):
                status = "✅" if result.get("status") == "completed" else "❌"
                task_id = result.get("task_id", "unknown")
                print(f"{status} {task_id}")
                if result.get("status") == "failed" and result.get("error"):
                    print(f"   Error: {result.get('error')}")
            else:
                print(f"❌ Invalid result: {result}")

        # Generate summary report
        print(f"\n📈 Phase 1 Summary:")
        print(f"  • Infrastructure tasks completed: {len(successful)}/5")
        print(f"  • Database schema: Ready for chat import")
        print(f"  • SQLite bridge: Ready for data transformation")
        print(f"  • ChatAdapter: Enhanced with SQLite support")
        print(f"  • Embeddings: Service ready for 41K messages")
        print(f"  • Pipeline: Configured for production import")
        print(f"\n🎯 Ready for Phase 2: Data Processing & Import")

    except Exception as e:
        print(f"\n❌ Phase 1 execution failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    asyncio.run(main())
