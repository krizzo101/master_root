#!/usr/bin/env python3
"""
Execute Chat Import using GenericOrchestrator (Known Working Pattern)
Uses the same reliable pattern as execute_phase1_generic.py
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


def create_chat_import_agent_tasks():
    """
    Create chat import tasks as AgentTask objects
    Following the original working pattern from execute_phase1_generic.py
    """

    agent_tasks = []

    # Task 1: Chat Log Analysis and Preparation (no dependencies)
    analysis_prompt = """TASK: Analyze existing chat logs and prepare them for import into the unified context system.

SPECIALIST ROLE: You are acting as a development-specialist agent.

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Data Source: ~/.claude/projects/*/*.jsonl files
- Target Database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- Existing Infrastructure: ChatAdapter and base pipeline ready

REQUIREMENTS:
1. Survey existing chat log files:
   - Scan ~/.claude/projects/*/*.jsonl for importable sessions
   - Identify file sizes, date ranges, and content types
   - Calculate total data volume and estimated processing time
   - Flag any problematic or corrupted files

2. Create import strategy:
   - Prioritize recent and important sessions
   - Batch files by size for optimal processing
   - Identify sessions with high value content
   - Plan incremental vs full import approach

3. Prepare import configuration:
   - Update chat_adapter.py with optimized settings
   - Configure batch sizes and memory limits
   - Set up progress tracking and error handling
   - Create import scheduling recommendations

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing chat log import for the Unified Context System - a temporal knowledge graph that processes conversation data for semantic search and knowledge extraction.
"""

    agent_tasks.append(
        AgentTask(
            task_id="chat_analysis_preparation",
            task_type="development-specialist",
            prompt=analysis_prompt,
            context={"phase": "chat_import", "priority": "high"},
        )
    )

    # Task 2: Batch Import Execution (depends on analysis)
    batch_import_prompt = """TASK: Execute batch import of prioritized chat logs into the unified context system.

SPECIALIST ROLE: You are acting as a development-specialist agent.

DEPENDENCIES: This task depends on completion of: chat_analysis_preparation

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Import Strategy: Use findings from chat_analysis_preparation task
- Database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- Pipeline: src/project_context/ingestion/adapters/chat_adapter.py

REQUIREMENTS:
1. Execute high-priority batch imports:
   - Import recent high-value sessions first
   - Use optimal batch sizes from preparation analysis
   - Monitor memory usage and processing speed
   - Handle errors gracefully with retry logic

2. Data quality validation:
   - Verify message deduplication is working
   - Check entity extraction and embedding generation
   - Validate temporal ordering and session boundaries
   - Ensure proper metadata preservation

3. Progress monitoring and reporting:
   - Track import progress with real-time status
   - Generate quality metrics and statistics
   - Identify and report any data issues
   - Create completion summary with next steps

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing chat log import for the Unified Context System - a temporal knowledge graph that processes conversation data for semantic search and knowledge extraction.
"""

    agent_tasks.append(
        AgentTask(
            task_id="batch_import_execution",
            task_type="development-specialist",
            prompt=batch_import_prompt,
            dependencies=["chat_analysis_preparation"],
            context={"phase": "chat_import", "priority": "high"},
        )
    )

    # Task 3: Data Validation and Quality Assurance (depends on import)
    validation_prompt = """TASK: Validate imported chat data and ensure quality standards are met.

SPECIALIST ROLE: You are acting as a qa-testing-guru agent.

DEPENDENCIES: This task depends on completion of: batch_import_execution

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context
- Imported Data: Results from batch_import_execution task
- Quality Standards: >95% successful import rate, proper entity extraction

REQUIREMENTS:
1. Data integrity validation:
   - Verify all messages are properly imported
   - Check for duplicate detection effectiveness
   - Validate entity extraction accuracy
   - Confirm embedding generation success

2. Performance and quality metrics:
   - Measure import speed and throughput
   - Calculate data completeness percentages
   - Assess semantic search functionality
   - Test temporal query accuracy

3. Issue identification and reporting:
   - Flag any data quality problems
   - Identify performance bottlenecks
   - Recommend optimizations for future imports
   - Create comprehensive quality report

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing chat log import for the Unified Context System - a temporal knowledge graph that processes conversation data for semantic search and knowledge extraction.
"""

    agent_tasks.append(
        AgentTask(
            task_id="data_validation_qa",
            task_type="qa-testing-guru",
            prompt=validation_prompt,
            dependencies=["batch_import_execution"],
            context={"phase": "chat_import", "priority": "normal"},
        )
    )

    # Task 4: Performance Optimization (depends on validation)
    optimization_prompt = """TASK: Optimize chat import performance and prepare for production-scale operations.

SPECIALIST ROLE: You are acting as a performance-optimizer agent.

DEPENDENCIES: This task depends on completion of: data_validation_qa

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context
- Performance Data: Results from data_validation_qa task
- Target: Production-ready import system for large-scale chat data
- Infrastructure: PostgreSQL + embeddings + entity extraction pipeline

REQUIREMENTS:
1. Performance optimization:
   - Optimize database queries and indexing
   - Tune batch sizes for maximum throughput
   - Implement connection pooling and caching
   - Configure parallel processing settings

2. Scalability enhancements:
   - Design for handling GB-scale chat logs
   - Implement incremental import capabilities
   - Add resume functionality for interrupted imports
   - Create monitoring and alerting systems

3. Production readiness:
   - Add comprehensive error handling and recovery
   - Implement import scheduling and automation
   - Create maintenance and cleanup procedures
   - Document operational procedures

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are implementing chat log import for the Unified Context System - a temporal knowledge graph that processes conversation data for semantic search and knowledge extraction.
"""

    agent_tasks.append(
        AgentTask(
            task_id="performance_optimization",
            task_type="performance-optimizer",
            prompt=optimization_prompt,
            dependencies=["data_validation_qa"],
            context={"phase": "chat_import", "priority": "normal"},
        )
    )

    return agent_tasks


async def main():
    """Execute chat import using the original GenericOrchestrator pattern"""

    print("🚀 CHAT IMPORT - GENERIC ORCHESTRATOR")
    print("=" * 60)
    print("✅ Foundation: ChatAdapter and ingestion pipeline ready")
    print("🎯 Mission: Import chat logs into unified context system")
    print(
        "⚡ Execution: Up to 7 parallel tasks using GenericOrchestrator + chat_import tokens"
    )
    print()

    # Create tasks using original pattern
    tasks = create_chat_import_agent_tasks()

    # Load chat import tokens (should get 7 tokens from chat_import pool)
    loader = TokenLoader()
    loader._orchestrator_type = "chat_import"  # Set type for chat_import token pool
    tokens = loader.load_tokens()

    # Create orchestrator with chat import coordination (like the original)
    orchestrator = GenericOrchestrator(
        output_dir=Path("./chat_import_output"),
        max_parallel=min(len(tokens), 7),  # Use chat import tokens, up to 7
        tokens=tokens,
        use_optimizations=True,
    )

    print(f"🔧 Token count: {len(tokens)}")
    print(f"⚡ Max parallel: {orchestrator.max_parallel}")
    print()

    # Print task plan
    print("📋 EXECUTION PLAN")
    print("-" * 30)
    for task in tasks:
        deps = (
            f" → depends on: {', '.join(task.dependencies)}"
            if task.dependencies
            else ""
        )
        print(f"  {task.task_id} ({task.task_type}){deps}")
    print()

    # Execute tasks
    print("🎯 Starting chat import...")
    results = await orchestrator.execute_batch(tasks)

    # Analyze results
    successful = [r for r in results if r.get("status") == "completed"]
    failed = [r for r in results if r.get("status") == "failed"]

    print("\n✅ CHAT IMPORT COMPLETED!")
    print("=" * 50)
    print(f"✅ Successful tasks: {len(successful)}")
    print(f"❌ Failed tasks: {len(failed)}")

    if failed:
        print("\n❌ Failed Tasks:")
        for task in failed:
            print(f"   - {task['task_id']}: {task.get('error', 'Unknown error')}")

    if len(successful) >= 3:  # Core import tasks complete
        print(f"\n🎉 SUCCESS: Chat import complete!")
        print(
            f"💾 Database: postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
        )
        print(f"🔍 Query chat data using semantic search capabilities")
    else:
        print(f"\n⚠️  Some tasks failed. Check results in ./chat_import_output/")

    print(f"\n📄 Full results saved to: ./chat_import_output/")
    print(f"📊 Import metrics will be available in quality reports")

    return results


if __name__ == "__main__":
    print("💬 Chat Import - GenericOrchestrator Pattern")
    print("=" * 60)
    print()

    asyncio.run(main())
