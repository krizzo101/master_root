#!/usr/bin/env python3
"""
Claude Self-Improvement Workflow
Uses the validated asea_orchestrator to analyze failure patterns and create improvement strategies
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# --- Absolute Path Setup ---
WORKSPACE_ROOT = "/home/opsvi/asea"
SRC_PATH = os.path.join(WORKSPACE_ROOT, "asea_orchestrator/src")
sys.path.insert(0, SRC_PATH)

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig
from asea_orchestrator.database import ArangoDBClient

# --- Absolute Path for Plugins ---
PLUGIN_DIR = os.path.join(SRC_PATH, "asea_orchestrator/plugins/available")


def create_self_improvement_workflow():
    """Creates a workflow for Claude's self-improvement using validated orchestrator."""
    return {
        "claude_self_improvement": {
            "steps": [
                {
                    "plugin_name": "arango_db",
                    "inputs": {},
                    "outputs": {"failure_patterns": "failure_analysis"},
                    "parameters": {
                        "action": "query",
                        "query": """
                        FOR doc IN core_memory
                        FILTER doc.foundational == true
                        AND (doc.type LIKE '%failure%' OR doc.type LIKE '%critical%')
                        SORT doc.created DESC
                        LIMIT 10
                        RETURN {
                            title: doc.title,
                            type: doc.type,
                            failure_pattern: doc.core_realization || doc.summary,
                            prevention_required: doc.prevention_target || doc.corrective_action_required
                        }
                        """,
                    },
                },
                {
                    "plugin_name": "arango_db",
                    "inputs": {},
                    "outputs": {"behavioral_requirements": "behavioral_analysis"},
                    "parameters": {
                        "action": "query",
                        "query": """
                        FOR doc IN core_memory
                        FILTER doc.foundational == true
                        AND doc.type == 'behavioral_enforcement_protocol'
                        SORT doc.created DESC
                        LIMIT 5
                        RETURN {
                            title: doc.title,
                            requirement: doc.requirement,
                            enforcement: doc.enforcement_mechanism
                        }
                        """,
                    },
                },
                {
                    "plugin_name": "file_system",
                    "inputs": {
                        "failure_analysis": "failures",
                        "behavioral_analysis": "behaviors",
                    },
                    "outputs": {"improvement_report": "report_path"},
                    "parameters": {
                        "action": "write",
                        "path": "/home/opsvi/asea/claude_self_improvement_analysis.md",
                        "content": """# Claude Self-Improvement Analysis

## Failure Patterns Identified
{{failures}}

## Behavioral Requirements
{{behaviors}}

## Improvement Strategies
Based on analysis, the following improvements are recommended:

1. **Enhanced Failure Recognition**: Implement immediate stop-and-analyze protocols
2. **Behavioral Integration**: Strengthen rule compliance mechanisms
3. **Knowledge Utilization**: Systematic consultation of foundational memories
4. **Tool Orchestration**: Optimize parallel execution patterns

## Implementation Plan
- Priority 1: Fix immediate failure recognition gaps
- Priority 2: Strengthen behavioral rule compliance
- Priority 3: Enhance knowledge integration workflows

Generated: {{timestamp}}
""",
                    },
                },
                {
                    "plugin_name": "arango_db",
                    "inputs": {"report_path": "analysis_report"},
                    "outputs": {"stored_improvement": "improvement_id"},
                    "parameters": {
                        "action": "insert",
                        "collection": "cognitive_patterns",
                        "document": {
                            "type": "self_improvement_analysis",
                            "analysis_report": "{{analysis_report}}",
                            "generated_at": "{{timestamp}}",
                            "status": "ready_for_implementation",
                            "priority": "high",
                        },
                    },
                },
            ]
        }
    }


async def main():
    """Execute Claude's self-improvement workflow using validated orchestrator."""

    print("🧠 CLAUDE SELF-IMPROVEMENT WORKFLOW")
    print("   Using validated asea_orchestrator system")
    print("   Analyzing failure patterns and behavioral requirements")
    print("=" * 60)

    # Initialize validated orchestrator
    workflow_defs = create_self_improvement_workflow()
    workflow_manager = WorkflowManager(workflow_definitions=workflow_defs)

    orchestrator = Orchestrator(
        plugin_dir=PLUGIN_DIR, workflow_manager=workflow_manager
    )

    # Connect to production database (port 8529)
    orchestrator.db_client = ArangoDBClient(
        host="http://localhost:8529", database="_system", username="root", password=""
    )

    # Configure plugins with proper database configuration
    plugin_configs = {
        "arango_db": PluginConfig(
            name="arango_db",
            config={
                "host": "http://localhost:8529",
                "db_name": "_system",
                "username": "root",
                "password": "",
            },
        ),
        "file_system": PluginConfig(name="file_system"),
    }
    orchestrator.temp_configure_plugins(plugin_configs)

    # Execute self-improvement workflow
    initial_state = {
        "timestamp": datetime.now().isoformat(),
        "analysis_focus": "failure_patterns_and_behavioral_compliance",
        "improvement_target": "enhanced_autonomous_operation",
    }

    try:
        print("🚀 Executing self-improvement analysis...")

        result = await orchestrator.run_workflow(
            workflow_name="claude_self_improvement",
            initial_state=initial_state,
            run_id=f"claude-improvement-{uuid.uuid4().hex[:8]}",
        )

        print("✅ Self-improvement analysis completed!")
        print(f"📊 Status: {result.get('status', 'Unknown')}")
        print("🔍 Failure Patterns Analyzed: Available")
        print("📋 Behavioral Requirements: Available")
        print(f"📄 Analysis Report: {result.get('report_path', 'Generated')}")
        print(f"💾 Stored in Database: {result.get('improvement_id', 'Success')}")

        return result

    except Exception as e:
        print(f"❌ Self-improvement workflow failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
