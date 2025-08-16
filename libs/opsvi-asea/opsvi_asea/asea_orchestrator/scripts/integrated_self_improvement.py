#!/usr/bin/env python3
"""
Integrated Self-Improvement Workflow

This workflow properly integrates with the existing database ecosystem:
- Uses main database (port 8529) with existing collections
- Leverages core_memory for foundational knowledge
- Adds workflow states to existing knowledge management system
- No data silos or isolated instances
"""

import asyncio
import sys
import os

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


def create_integrated_workflow():
    """Creates a workflow that integrates with existing database ecosystem."""
    return {
        "integrated_self_improvement": {
            "steps": [
                {
                    "plugin_name": "arango_db_plugin",
                    "inputs": {},
                    "outputs": {"failure_analysis": "failure_patterns"},
                    "parameters": {
                        "operation": "query",
                        "database": "_system",  # Use existing database
                        "query": """
                        FOR doc IN core_memory
                        FILTER doc.foundational == true
                        AND (doc.type LIKE '%failure%' OR doc.type LIKE '%critical%')
                        SORT doc.created DESC
                        LIMIT 5
                        RETURN {
                            title: doc.title,
                            type: doc.type,
                            core_insight: doc.core_realization || doc.summary || doc.key_insights,
                            priority: doc.priority || 'normal'
                        }
                        """,
                    },
                },
                {
                    "plugin_name": "arango_db_plugin",
                    "inputs": {},
                    "outputs": {"capability_analysis": "capabilities"},
                    "parameters": {
                        "operation": "query",
                        "database": "_system",
                        "query": """
                        FOR doc IN core_memory
                        FILTER doc.foundational == true
                        AND doc.type == 'technical_breakthrough_completion'
                        SORT doc.created DESC
                        LIMIT 3
                        RETURN {
                            achievement: doc.title,
                            impact: doc.autonomous_intelligence_impact,
                            status: doc.status
                        }
                        """,
                    },
                },
                {
                    "plugin_name": "file_system_plugin",
                    "inputs": {
                        "failure_patterns": "failures",
                        "capabilities": "achievements",
                    },
                    "outputs": {"improvement_plan": "plan"},
                    "parameters": {
                        "operation": "create_improvement_plan",
                        "output_file": "/home/opsvi/asea/integrated_improvement_plan.md",
                    },
                },
                {
                    "plugin_name": "arango_db_plugin",
                    "inputs": {"plan": "improvement_plan"},
                    "outputs": {"stored_plan": "plan_id"},
                    "parameters": {
                        "operation": "insert",
                        "collection": "cognitive_patterns",  # Use existing collection
                        "document": {
                            "type": "self_improvement_plan",
                            "plan_content": "{{plan}}",
                            "generated_at": "{{timestamp}}",
                            "status": "ready_for_implementation",
                        },
                    },
                },
            ]
        }
    }


async def main():
    """Execute the integrated self-improvement workflow."""

    print("🔗 Starting INTEGRATED Self-Improvement Workflow")
    print("   Using existing database ecosystem and collections")
    print("=" * 60)

    # Initialize with correct architecture
    workflow_defs = create_integrated_workflow()
    workflow_manager = WorkflowManager(workflow_definitions=workflow_defs)

    orchestrator = Orchestrator(
        plugin_dir=PLUGIN_DIR, workflow_manager=workflow_manager
    )

    # Connect to existing database
    orchestrator.db_client = ArangoDBClient(
        host="http://localhost:8529",  # Main database
        database="_system",  # Use existing _system database
        username="root",
        password="",
    )

    # Configure plugins for the workflow
    plugin_configs = {
        "arango_db_plugin": PluginConfig(name="arango_db_plugin"),
        "file_system_plugin": PluginConfig(name="file_system_plugin"),
    }
    orchestrator.temp_configure_plugins(plugin_configs)

    # Execute workflow with integration focus
    initial_state = {
        "integration_mode": True,
        "use_existing_collections": True,
        "timestamp": "2025-06-21T20:30:00Z",
        "improvement_focus": [
            "Database failure detection enhancement",
            "Behavioral rule compliance monitoring",
            "Tool orchestration optimization",
            "Knowledge integration improvement",
        ],
    }

    try:
        print("🚀 Executing integrated workflow using existing collections...")
        print(
            f"   📊 Available collections: {len([c for c in ['core_memory', 'cognitive_patterns', 'knowledge_graph']])}"
        )

        result = await orchestrator.run_workflow(
            workflow_name="integrated_self_improvement",
            initial_state=initial_state,
            run_id="integrated-improvement-001",
        )

        print("✅ Integrated workflow completed!")
        print(f"📊 Status: {result.get('status', 'Unknown')}")
        print(f"🔍 Failure Patterns Analyzed: {len(result.get('failure_patterns', []))}")
        print(f"🎯 Capabilities Reviewed: {len(result.get('capabilities', []))}")
        print(f"📋 Plan Generated: {result.get('plan_id', 'Available')}")

        return result

    except Exception as e:
        print(f"❌ Integrated workflow failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
