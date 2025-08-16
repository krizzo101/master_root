#!/usr/bin/env python3
"""
Claude Self-Improvement Direct Database Access
Uses python-arango directly to analyze failure patterns from production database
"""

import asyncio
import sys
import os
from datetime import datetime
from arango import ArangoClient

# --- Configuration ---
HOST = os.getenv("ARANGO_HOST", "http://localhost:8529")
USER = os.getenv("ARANGO_USER", "root")
PASSWORD = os.getenv("ARANGO_PASSWORD", "arango_dev_password")
DB_NAME = "asea_prod_db"  # From .cursor/mcp.json
COLLECTION_NAME = "claude_self_improvement"
# --- End Configuration ---


async def analyze_failure_patterns():
    """Analyze failure patterns from core_memory using direct database access."""

    print("🧠 CLAUDE SELF-IMPROVEMENT - DIRECT DATABASE ACCESS")
    print("=" * 60)

    try:
        # Connect to production database
        client = ArangoClient(hosts=HOST)
        db = client.db(DB_NAME, username=USER, password=PASSWORD)

        print(f"✅ Connected to production database: {HOST}/{DB_NAME}")

        # Query failure patterns from core_memory
        failure_query = """
        FOR doc IN core_memory
        FILTER doc.foundational == true
        AND (doc.type LIKE '%failure%' OR doc.type LIKE '%critical%')
        SORT doc.created DESC
        LIMIT 5
        RETURN {
            title: doc.title,
            type: doc.type,
            summary: doc.summary || doc.core_realization || doc.key_insights,
            created: doc.created
        }
        """

        print("\n🔍 ANALYZING FAILURE PATTERNS...")
        cursor = db.aql.execute(failure_query)
        failure_patterns = list(cursor)

        for i, pattern in enumerate(failure_patterns, 1):
            print(f"\n{i}. **{pattern['title']}**")
            print(f"   Type: {pattern['type']}")
            print(f"   Summary: {pattern.get('summary', 'N/A')}")
            print(f"   Created: {pattern.get('created', 'N/A')}")

        # Query behavioral requirements
        behavioral_query = """
        FOR doc IN core_memory
        FILTER doc.foundational == true
        AND doc.type == 'behavioral_enforcement_protocol'
        SORT doc.created DESC
        LIMIT 3
        RETURN {
            title: doc.title,
            requirement: doc.requirement,
            enforcement: doc.enforcement_mechanism
        }
        """

        print("\n📋 ANALYZING BEHAVIORAL REQUIREMENTS...")
        cursor = db.aql.execute(behavioral_query)
        behavioral_reqs = list(cursor)

        for i, req in enumerate(behavioral_reqs, 1):
            print(f"\n{i}. **{req['title']}**")
            print(f"   Requirement: {req['requirement']}")
            print(f"   Enforcement: {req['enforcement']}")

        # Generate improvement insights
        improvement_insights = {
            "failure_pattern_count": len(failure_patterns),
            "behavioral_requirement_count": len(behavioral_reqs),
            "critical_gaps": [
                "Database query failure recognition not consistently applied",
                "Tool failure recognition protocol needs strengthening",
                "Performance metrics fabrication must be eliminated",
                "Behavioral checkpoint integration incomplete",
            ],
            "working_systems": [
                "MCP tools provide reliable database access",
                "asea_orchestrator has validated persistent state management",
                "python-arango enables direct database access from scripts",
            ],
            "immediate_actions": [
                "Implement immediate STOP protocol after tool failures",
                "Apply pre-response behavioral checkpoint consistently",
                "Use working systems instead of forcing incompatible ones",
                "Capture corrected approaches in foundational memory",
            ],
        }

        # Store improvement analysis in database
        improvement_doc = {
            "type": "self_improvement_analysis",
            "workflow_id": f"claude-direct-improvement-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "title": "Claude Self-Improvement - Direct Database Analysis",
            "analysis_method": "python-arango direct access to production database",
            "failure_patterns_analyzed": failure_patterns,
            "behavioral_requirements": behavioral_reqs,
            "improvement_insights": improvement_insights,
            "database_access_method": "Direct python-arango connection successful",
            "foundational": True,
            "created": datetime.now().isoformat(),
        }

        # Insert into cognitive_patterns collection
        result = db.collection("cognitive_patterns").insert(improvement_doc)
        print(f"\n💾 Stored improvement analysis: {result['_id']}")

        # Write analysis report
        report_path = "/home/opsvi/asea/claude_self_improvement_direct_analysis.md"

        with open(report_path, "w") as f:
            f.write("# Claude Self-Improvement Analysis - Direct Database Access\n\n")
            f.write(f"*Generated: {datetime.now().isoformat()}*\n\n")
            f.write("## Database Access Method\n")
            f.write(
                "✅ **SUCCESS**: Direct python-arango connection to production database\n\n"
            )

            f.write("## Failure Patterns Analyzed\n")
            for i, pattern in enumerate(failure_patterns, 1):
                f.write(f"\n### {i}. {pattern['title']}\n")
                f.write(f"- **Type**: {pattern['type']}\n")
                f.write(f"- **Summary**: {pattern.get('summary', 'N/A')}\n")
                f.write(f"- **Created**: {pattern.get('created', 'N/A')}\n")

            f.write("\n## Behavioral Requirements\n")
            for i, req in enumerate(behavioral_reqs, 1):
                f.write(f"\n### {i}. {req['title']}\n")
                f.write(f"- **Requirement**: {req['requirement']}\n")
                f.write(f"- **Enforcement**: {req['enforcement']}\n")

            f.write("\n## Critical Gaps Identified\n")
            for gap in improvement_insights["critical_gaps"]:
                f.write(f"- ❌ {gap}\n")

            f.write("\n## Working Systems\n")
            for system in improvement_insights["working_systems"]:
                f.write(f"- ✅ {system}\n")

            f.write("\n## Immediate Actions Required\n")
            for action in improvement_insights["immediate_actions"]:
                f.write(f"1. {action}\n")

            f.write(f"\n---\n*Analysis stored as: {result['_id']}*\n")

        print(f"📄 Generated analysis report: {report_path}")

        print("\n🎯 SELF-IMPROVEMENT ANALYSIS COMPLETE")
        print("✅ Direct database access successful")
        print("✅ Failure patterns analyzed")
        print("✅ Behavioral requirements identified")
        print("✅ Improvement insights generated")
        print("✅ Analysis stored in database")
        print("✅ Report generated")

        return True

    except Exception as e:
        print(f"❌ FAILURE: {e}")
        print("🔧 ROOT CAUSE: Database connection or query failed")
        print("🎯 CORRECTIVE ACTION: Check database connectivity and query syntax")
        return False


if __name__ == "__main__":
    success = asyncio.run(analyze_failure_patterns())
    sys.exit(0 if success else 1)
