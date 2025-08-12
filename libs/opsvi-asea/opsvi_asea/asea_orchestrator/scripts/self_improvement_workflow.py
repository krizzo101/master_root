#!/usr/bin/env python3
"""
Self-Improvement Workflow for Autonomous Agent Enhancement

This workflow analyzes the agent's current capabilities, identifies improvement
opportunities, and implements enhancements to further autonomous evolution.

Focus areas:
1. Failure pattern analysis and prevention
2. Tool orchestration optimization
3. Knowledge integration enhancement
4. Behavioral rule effectiveness
5. Token efficiency optimization
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.database import ArangoDBClient
from asea_orchestrator.plugins.plugin_manager import PluginManager


def create_self_improvement_workflow():
    """Creates a workflow for autonomous self-improvement."""
    return {
        "self_improvement_analysis": {
            "steps": [
                {
                    "plugin_name": "arango_db_plugin",
                    "inputs": {},
                    "outputs": {"analysis_data": "failure_patterns"},
                    "parameters": {
                        "operation": "query",
                        "query": """
                        FOR doc IN core_memory
                        FILTER doc.foundational == true
                        AND (doc.type LIKE '%failure%' OR doc.type LIKE '%critical%')
                        RETURN {
                            title: doc.title,
                            type: doc.type,
                            key_insights: doc.key_insights || doc.core_realization || doc.summary,
                            created: doc.created
                        }
                        """,
                    },
                },
                {
                    "plugin_name": "code_analysis_plugin",
                    "inputs": {"failure_patterns": "patterns"},
                    "outputs": {"improvement_opportunities": "opportunities"},
                    "parameters": {
                        "analysis_type": "capability_gaps",
                        "focus": "behavioral_enforcement",
                    },
                },
                {
                    "plugin_name": "arango_db_plugin",
                    "inputs": {},
                    "outputs": {"rule_effectiveness": "rule_analysis"},
                    "parameters": {
                        "operation": "query",
                        "query": """
                        FOR doc IN core_memory
                        FILTER doc.foundational == true
                        AND doc.title CONTAINS 'rule'
                        COLLECT type = doc.type WITH COUNT INTO count
                        SORT count DESC
                        RETURN {rule_type: type, frequency: count}
                        """,
                    },
                },
                {
                    "plugin_name": "file_system_plugin",
                    "inputs": {
                        "opportunities": "improvement_data",
                        "rule_analysis": "rule_data",
                    },
                    "outputs": {"implementation_plan": "plan"},
                    "parameters": {
                        "operation": "create_improvement_plan",
                        "output_file": "/home/opsvi/asea/self_improvement_plan.md",
                    },
                },
                {
                    "plugin_name": "shell_plugin",
                    "inputs": {"plan": "implementation_plan"},
                    "outputs": {"execution_result": "result"},
                    "parameters": {
                        "command": "cd /home/opsvi/asea && python -c \"print('Self-improvement analysis complete')\"",
                        "capture_output": True,
                    },
                },
            ]
        }
    }


async def main():
    """Execute the self-improvement workflow."""

    print("🧠 Starting Autonomous Self-Improvement Workflow")
    print("=" * 60)

    # Initialize components
    db_client = ArangoDBClient(
        host="localhost",
        port=8529,  # Use main database
        username="root",
        password="",
        database_name="_system",
    )

    await db_client.connect()

    plugin_manager = PluginManager()
    await plugin_manager.load_plugins()

    orchestrator = Orchestrator(db_client=db_client, plugin_manager=plugin_manager)

    # Create workflow definition
    workflow_def = create_self_improvement_workflow()

    # Execute workflow
    initial_state = {
        "analysis_focus": "behavioral_enhancement",
        "token_constraints": {"premium_limit": 1000000, "efficient_limit": 10000000},
        "improvement_goals": [
            "Eliminate failure recognition gaps",
            "Optimize tool orchestration patterns",
            "Enhance behavioral rule compliance",
            "Improve token efficiency",
        ],
    }

    try:
        print(f"🚀 Executing self-improvement workflow...")

        result = await orchestrator.run_workflow(
            workflow_name="self_improvement_analysis",
            workflow_definition=workflow_def,
            initial_state=initial_state,
            run_id="self-improvement-" + str(hash(str(initial_state)))[-8:],
        )

        print(f"✅ Self-improvement workflow completed!")
        print(f"📊 Final Status: {result.get('status', 'Unknown')}")
        print(
            f"📈 Improvement Opportunities Identified: {result.get('opportunities', 'Analysis in progress')}"
        )
        print(f"🎯 Implementation Plan: {result.get('plan', 'Generated')}")

        # Display key insights
        if "failure_patterns" in result:
            print(f"\n🔍 Failure Pattern Analysis:")
            patterns = result["failure_patterns"]
            if isinstance(patterns, list):
                for i, pattern in enumerate(patterns[:3], 1):
                    print(f"   {i}. {pattern.get('title', 'Unknown pattern')}")

        return result

    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        raise
    finally:
        await db_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
