#!/usr/bin/env python3
"""
SQLite Priority Chat Import Execution
Execute high-priority batch import from SQLite source using existing orchestrator
"""

import asyncio
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add orchestrator path
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
sys.path.append("/home/opsvi/master_root/apps/project-context")

# Import after path modification  # noqa: E402
from practical_orchestrator import PracticalAgentTask, PracticalOrchestrator


async def analyze_sqlite_priorities():
    """Analyze SQLite database to identify priority sessions"""

    source_db = "/home/opsvi/master_root/chat_logs.db"

    if not Path(source_db).exists():
        print(f"❌ Source database not found: {source_db}")
        return None

    print(f"📊 Analyzing SQLite database: {source_db}")

    conn = sqlite3.connect(source_db)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        # Get overall statistics
        cursor.execute("SELECT COUNT(*) as total_sessions FROM sessions")
        total_sessions = cursor.fetchone()["total_sessions"]

        cursor.execute(
            "SELECT COUNT(*) as total_messages FROM nodes WHERE node_type LIKE '%message%'"
        )
        total_messages = cursor.fetchone()["total_messages"]

        cursor.execute("SELECT COUNT(*) as total_tools FROM nodes WHERE node_type = 'tool_call'")
        total_tools = cursor.fetchone()["total_tools"]

        # Get priority sessions (recent, with tool usage, substantial conversations)
        cursor.execute(
            """
            SELECT s.session_id, s.cwd, s.git_branch, s.created_at,
                   COUNT(n.uuid) as message_count,
                   COUNT(CASE WHEN n.node_type = 'tool_call' THEN 1 END) as tool_count,
                   MAX(n.timestamp) as last_activity,
                   CASE
                       WHEN s.created_at > datetime('now', '-30 days') AND
                            COUNT(n.uuid) > 10 THEN 'high'
                       WHEN s.created_at > datetime('now', '-90 days') AND
                            COUNT(n.uuid) > 5 THEN 'medium'
                       ELSE 'low'
                   END as priority
            FROM sessions s
            JOIN nodes n ON s.session_id = n.session_id
            GROUP BY s.session_id, s.cwd, s.git_branch, s.created_at
            ORDER BY
                CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                tool_count DESC,
                message_count DESC,
                s.created_at DESC
        """
        )

        prioritized_sessions = [dict(row) for row in cursor.fetchall()]

        # Count by priority
        high_priority = [s for s in prioritized_sessions if s["priority"] == "high"]
        medium_priority = [s for s in prioritized_sessions if s["priority"] == "medium"]
        low_priority = [s for s in prioritized_sessions if s["priority"] == "low"]

        analysis = {
            "source_database": source_db,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_tool_calls": total_tools,
            "priority_breakdown": {
                "high": len(high_priority),
                "medium": len(medium_priority),
                "low": len(low_priority),
            },
            "high_priority_sessions": high_priority[:50],  # Top 50 high-priority
            "sample_sessions": prioritized_sessions[:10],
        }

        print("📈 Analysis complete:")
        print(f"   • Total Sessions: {total_sessions}")
        print(f"   • Total Messages: {total_messages}")
        print(f"   • Total Tool Calls: {total_tools}")
        print(f"   • High Priority: {len(high_priority)} sessions")
        print(f"   • Medium Priority: {len(medium_priority)} sessions")
        print(f"   • Low Priority: {len(low_priority)} sessions")

        return analysis

    finally:
        conn.close()


async def execute_priority_import():
    """Execute prioritized import using orchestrator framework"""

    print("🚀 SQLITE PRIORITY CHAT IMPORT")
    print("=" * 60)
    print("📊 Source: SQLite chat database")
    print("🎯 Strategy: High-priority sessions with orchestrated execution")
    print()

    # Step 1: Analyze data priorities
    analysis = await analyze_sqlite_priorities()
    if not analysis:
        print("❌ Failed to analyze source data")
        return 1

    # Step 2: Create orchestrator with import-specific configuration
    orchestrator = PracticalOrchestrator(
        output_dir="/home/opsvi/master_root/apps/project-context/chat_import_output",
        max_parallel=5,  # Moderate parallelism for data import
        enable_monitoring=True,
        enable_quality_reports=True,
        orchestrator_type="sqlite_chat_import",
    )

    print("✅ Orchestrator initialized for SQLite import")

    # Step 3: Create prioritized import tasks
    import_tasks = [
        # Task 1: Database schema preparation
        PracticalAgentTask(
            task_id="prepare_database_schema",
            task_type="development-specialist",
            prompt=f"""
TASK: Prepare PostgreSQL database schema for SQLite chat import.

CONTEXT:
- Source: {analysis['source_database']} with {analysis['total_sessions']} sessions
- Target: PostgreSQL unified_context database
- Data volume: {analysis['total_messages']} messages, {analysis['total_tool_calls']} tool calls

REQUIREMENTS:
1. Verify unified_context database schema is ready for chat import
2. Create indexes optimized for chat data (session_id, timestamp, content)
3. Prepare staging tables if needed for bulk import
4. Validate connection pools and performance settings

DELIVERABLES: Database preparation report with schema validation and performance optimization.
""",
            phase_id="infrastructure",
            priority="high",
            dependencies=[],
            tags=["database", "schema", "preparation"],
        ),
        # Task 2: SQLite adapter implementation
        PracticalAgentTask(
            task_id="implement_sqlite_adapter",
            task_type="development-specialist",
            prompt=f"""
TASK: Implement SQLite chat adapter for unified context system.

CONTEXT:
- Source database: {analysis['source_database']}
- Priority sessions: {analysis['priority_breakdown']['high']} high-priority
- Existing ChatAdapter framework available

REQUIREMENTS:
1. Extend existing ChatAdapter to support "sqlite_database" input format
2. Implement SQLite query logic for sessions, nodes, and tool calls
3. Map SQLite schema to ContextItem objects
4. Add batch processing and error handling
5. Support priority-based session selection

DELIVERABLES: Complete SQLite adapter with session processing capabilities.
""",
            phase_id="adapter",
            priority="high",
            dependencies=["prepare_database_schema"],
            tags=["adapter", "sqlite", "implementation"],
        ),
        # Task 3: Priority session processing
        PracticalAgentTask(
            task_id="process_priority_sessions",
            task_type="development-specialist",
            prompt=f"""
TASK: Execute priority session import with monitoring and validation.

CONTEXT:
- High-priority sessions: {analysis['priority_breakdown']['high']} identified
- Target processing: Top 50 sessions from analysis
- Expected data: ~{sum(s['message_count'] for s in analysis['high_priority_sessions'])} messages

REQUIREMENTS:
1. Process high-priority sessions through SQLite adapter
2. Generate embeddings and extract entities for chat content
3. Detect relationships between messages and tool calls
4. Implement progress monitoring and error recovery
5. Validate data quality during import

DELIVERABLES: Successful import of priority sessions with quality validation report.
""",
            phase_id="processing",
            priority="high",
            dependencies=["implement_sqlite_adapter"],
            tags=["processing", "import", "validation"],
        ),
        # Task 4: Quality assurance and metrics
        PracticalAgentTask(
            task_id="validate_import_quality",
            task_type="development-specialist",
            prompt=f"""
TASK: Comprehensive quality validation of imported chat data.

CONTEXT:
- Import target: {analysis['priority_breakdown']['high']} high-priority sessions
- Database: PostgreSQL unified_context with chat data
- Quality metrics needed for production readiness

REQUIREMENTS:
1. Validate message deduplication and integrity
2. Check entity extraction accuracy and coverage
3. Verify relationship detection between conversations
4. Test embedding generation and semantic search
5. Generate comprehensive import metrics and quality report

DELIVERABLES: Quality validation report with metrics and recommendations for full import.
""",
            phase_id="validation",
            priority="high",
            dependencies=["process_priority_sessions"],
            tags=["validation", "quality", "metrics"],
        ),
        # Task 5: Integration testing and next steps
        PracticalAgentTask(
            task_id="integration_testing",
            task_type="development-specialist",
            prompt=f"""
TASK: Test integration with MCP server and prepare for full import.

CONTEXT:
- Priority import completed: {analysis['priority_breakdown']['high']} sessions
- Remaining data: {analysis['priority_breakdown']['medium']} medium + "
                + f"{analysis['priority_breakdown']['low']} low priority
- Production system integration required

REQUIREMENTS:
1. Test MCP server integration with imported chat data
2. Validate semantic search and context retrieval
3. Create execution plan for remaining medium/low priority sessions
4. Document lessons learned and optimization recommendations
5. Prepare monitoring dashboard for full import

DELIVERABLES: Integration test results and comprehensive plan for full-scale import execution.
""",
            phase_id="integration",
            priority="medium",
            dependencies=["validate_import_quality"],
            tags=["integration", "testing", "planning"],
        ),
    ]

    print(f"📋 Created {len(import_tasks)} prioritized import tasks")

    # Step 4: Execute tasks with monitoring
    start_time = datetime.now()
    print(f"🔄 Starting task execution at {start_time.strftime('%H:%M:%S')}")

    try:
        results = await orchestrator.execute_batch(import_tasks)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ Task execution completed in {duration/60:.1f} minutes!")

        # Process results
        successful_tasks = 0
        failed_tasks = 0

        for i, result in enumerate(results):
            task_id = import_tasks[i].task_id

            if isinstance(result, dict):
                status = result.get("status", "unknown")
                success = status == "completed"
            else:
                success = False
                status = "error"

            if success:
                successful_tasks += 1
                print(f"  ✅ {task_id}: {status}")
            else:
                failed_tasks += 1
                print(f"  ❌ {task_id}: {status}")

        # Generate summary
        summary = {
            "execution_time": duration,
            "execution_minutes": duration / 60,
            "total_tasks": len(import_tasks),
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (successful_tasks / len(import_tasks)) * 100,
            "source_analysis": analysis,
            "task_results": results,
        }

        # Save summary
        summary_file = Path("sqlite_priority_import_summary.json")
        summary_file.write_text(json.dumps(summary, indent=2, default=str))

        print("\n📊 EXECUTION SUMMARY")
        print(f"⏱️  Duration: {duration/60:.1f} minutes")
        print(
            f"✅ Success Rate: {successful_tasks}/{len(import_tasks)} "
            f"({summary['success_rate']:.1f}%)"
        )
        print(f"📄 Summary saved: {summary_file}")

        if successful_tasks == len(import_tasks):
            print("\n🎉 PRIORITY IMPORT COMPLETED SUCCESSFULLY!")
            print("📈 Ready for medium/low priority import phases")
            return 0
        else:
            print(f"\n⚠️  PARTIAL SUCCESS - {failed_tasks} tasks failed")
            print("🔄 Review failed tasks and re-execute as needed")
            return 1

    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(execute_priority_import())
    sys.exit(exit_code)
