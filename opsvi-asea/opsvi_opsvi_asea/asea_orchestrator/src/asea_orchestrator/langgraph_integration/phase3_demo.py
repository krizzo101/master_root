"""
Phase 3 Complete Demo - Multi-Agent Orchestration + Advanced Monitoring

Demonstrates the full Phase 3 capabilities:
1. Multi-Agent Orchestration with different execution modes
2. Advanced Monitoring and Metrics Collection
3. Real-time Alerting and Health Assessment
4. Performance Analytics and Resource Tracking
"""

import sys
import time
import uuid
from pathlib import Path

# Add the ASEA orchestrator to the path
sys.path.append(str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ASEAState, create_initial_state
from .multi_agent_orchestration import (
    MultiAgentWorkflowBuilder,
    AgentRole,
    ExecutionMode,
    AgentCoordinator,
    AgentDefinition,
)
from .advanced_monitoring import (
    create_default_monitoring_setup,
    MetricsCollector,
    WorkflowMonitor,
    AlertManager,
    AlertSeverity,
)
from ..plugins.available.cognitive_reminder_plugin import CognitiveReminderPlugin
from ..plugins.available.cognitive_pre_analysis_plugin import CognitivePreAnalysisPlugin
from ..plugins.available.ai_reasoning_plugin import AIReasoningPlugin
from ..plugins.available.cognitive_critic_plugin import CognitiveCriticPlugin


def create_multi_agent_research_team():
    """
    Create a multi-agent research team with different specializations.

    Team Structure:
    - Research Coordinator (orchestrates the research process)
    - Domain Specialists (parallel analysis from different angles)
    - Quality Critics (competitive evaluation of outputs)
    - Synthesis Agent (collaborative result combination)
    """

    builder = MultiAgentWorkflowBuilder()

    # Add Research Coordinator
    builder.add_agent(
        agent_id="research_coordinator",
        role=AgentRole.COORDINATOR,
        plugin_class=CognitiveReminderPlugin,
        input_mapping={
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "task_type": "research_coordination",
        },
        output_mapping={"reminders": "coordination_framework"},
        description="Coordinates research approach and methodology",
    )

    # Add Domain Specialists (parallel execution)
    builder.add_agent(
        agent_id="technical_specialist",
        role=AgentRole.SPECIALIST,
        plugin_class=CognitivePreAnalysisPlugin,
        input_mapping={
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "context": "Technical and scientific analysis perspective",
        },
        output_mapping={"enhanced_understanding": "technical_analysis"},
        description="Provides technical and scientific analysis",
    )

    builder.add_agent(
        agent_id="business_specialist",
        role=AgentRole.SPECIALIST,
        plugin_class=CognitivePreAnalysisPlugin,
        input_mapping={
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "context": "Business and economic impact perspective",
        },
        output_mapping={"enhanced_understanding": "business_analysis"},
        description="Provides business and economic analysis",
    )

    builder.add_agent(
        agent_id="social_specialist",
        role=AgentRole.SPECIALIST,
        plugin_class=CognitivePreAnalysisPlugin,
        input_mapping={
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "context": "Social and ethical implications perspective",
        },
        output_mapping={"enhanced_understanding": "social_analysis"},
        description="Provides social and ethical analysis",
    )

    # Add Quality Critics (competitive evaluation)
    builder.add_agent(
        agent_id="quality_critic_1",
        role=AgentRole.CRITIC,
        plugin_class=CognitiveCriticPlugin,
        input_mapping={
            "response": "{{ workflow.state.technical_analysis }}",
            "original_prompt": "{{ workflow.input.user_prompt }}",
        },
        output_mapping={"critique": "technical_critique"},
        description="Critiques technical analysis quality",
    )

    builder.add_agent(
        agent_id="quality_critic_2",
        role=AgentRole.CRITIC,
        plugin_class=CognitiveCriticPlugin,
        input_mapping={
            "response": "{{ workflow.state.business_analysis }}",
            "original_prompt": "{{ workflow.input.user_prompt }}",
        },
        output_mapping={"critique": "business_critique"},
        description="Critiques business analysis quality",
    )

    # Add Synthesis Agent (collaborative combination)
    builder.add_agent(
        agent_id="synthesis_agent",
        role=AgentRole.SYNTHESIZER,
        plugin_class=AIReasoningPlugin,
        input_mapping={
            "prompt": "Synthesize research findings from multiple perspectives",
            "user_prompt": "{{ workflow.input.user_prompt }}",
        },
        output_mapping={"response": "synthesized_research"},
        description="Synthesizes findings from all specialists",
    )

    # Define execution groups
    builder.add_execution_group(
        agent_ids=["research_coordinator"],
        execution_mode=ExecutionMode.SEQUENTIAL,
        name="coordination_phase",
    )

    builder.add_execution_group(
        agent_ids=["technical_specialist", "business_specialist", "social_specialist"],
        execution_mode=ExecutionMode.PARALLEL,
        name="specialist_analysis",
    )

    builder.add_execution_group(
        agent_ids=["quality_critic_1", "quality_critic_2"],
        execution_mode=ExecutionMode.COMPETITIVE,
        name="quality_evaluation",
    )

    builder.add_execution_group(
        agent_ids=["synthesis_agent"],
        execution_mode=ExecutionMode.COLLABORATIVE,
        name="synthesis_phase",
    )

    builder.set_aggregation_strategy("collaborative")

    return builder


def create_monitored_workflow():
    """Create a workflow with comprehensive monitoring."""

    # Initialize monitoring
    (
        metrics_collector,
        workflow_monitor,
        alert_manager,
    ) = create_default_monitoring_setup()

    # Add custom alerts for demo
    alert_manager.create_threshold_alert(
        "demo_slow_workflow",
        "workflow_duration",
        10,  # 10 seconds
        "greater",
        AlertSeverity.WARNING,
        1,  # 1 minute window
    )

    alert_manager.create_threshold_alert(
        "demo_high_agent_count",
        "active_workflows",
        2,  # More than 2 active workflows
        "greater",
        AlertSeverity.INFO,
        1,
    )

    # Create multi-agent workflow
    multi_agent_builder = create_multi_agent_research_team()

    # Create LangGraph workflow
    workflow = StateGraph(ASEAState)

    # Add the multi-agent node
    multi_agent_node = multi_agent_builder.build_multi_agent_node()

    def monitored_multi_agent_node(state: ASEAState) -> ASEAState:
        """Multi-agent node with monitoring."""
        run_id = state.get("run_id", str(uuid.uuid4()))
        workflow_name = state.get("workflow_name", "multi_agent_research")

        # Start monitoring
        workflow_monitor.start_workflow_monitoring(workflow_name, run_id, state)

        start_time = time.time()

        try:
            # Execute multi-agent workflow
            result_state = multi_agent_node(state)

            # Record success metrics
            duration = time.time() - start_time
            metrics_collector.record_timer("multi_agent_execution", duration)
            metrics_collector.record_counter("multi_agent_success", 1)

            # Update monitoring
            workflow_monitor.update_workflow_state(run_id, result_state)
            workflow_monitor.finish_workflow_monitoring(run_id, result_state, True)

            return result_state

        except Exception as e:
            # Record failure metrics
            duration = time.time() - start_time
            metrics_collector.record_timer("multi_agent_execution", duration)
            metrics_collector.record_counter("multi_agent_failure", 1)

            # Update monitoring
            error_state = state.copy()
            error_state["errors"].append(str(e))
            workflow_monitor.update_workflow_state(run_id, error_state)
            workflow_monitor.finish_workflow_monitoring(run_id, error_state, False)

            raise

    workflow.add_node("multi_agent_research", monitored_multi_agent_node)
    workflow.set_entry_point("multi_agent_research")
    workflow.add_edge("multi_agent_research", END)

    return workflow, metrics_collector, workflow_monitor, alert_manager


def demo_phase3_capabilities():
    """Comprehensive demo of Phase 3 capabilities."""

    print("=" * 80)
    print("🚀 PHASE 3 COMPLETE DEMO - Multi-Agent Orchestration + Advanced Monitoring")
    print("=" * 80)
    print("Features Demonstrated:")
    print(
        "✅ Multi-Agent Orchestration (Coordinator + Specialists + Critics + Synthesizer)"
    )
    print(
        "✅ Multiple Execution Modes (Sequential + Parallel + Competitive + Collaborative)"
    )
    print("✅ Real-time Metrics Collection and Performance Analytics")
    print("✅ Advanced Workflow Health Monitoring")
    print("✅ Intelligent Alerting and Notification Systems")
    print("✅ Cross-Agent Communication and State Sharing")
    print()

    # Create monitored workflow
    print("🏗️  Building multi-agent workflow with comprehensive monitoring...")
    workflow, metrics, monitor, alerts = create_monitored_workflow()

    # Compile workflow
    checkpointer = MemorySaver()
    compiled_workflow = workflow.compile(checkpointer=checkpointer)

    print("✅ Multi-agent workflow built successfully!")
    print(f"📊 Monitoring components initialized:")
    print(f"   - Metrics Collector: Active")
    print(f"   - Workflow Monitor: Active")
    print(f"   - Alert Manager: {len(alerts.alerts)} alerts configured")
    print()

    # Test scenarios
    research_scenarios = [
        {
            "name": "AI Ethics Research",
            "prompt": "Analyze the ethical implications of AI decision-making in healthcare, considering technical capabilities, business impacts, and social consequences.",
            "expected_agents": 6,
        },
        {
            "name": "Quantum Computing Impact",
            "prompt": "Evaluate the potential impact of quantum computing on cybersecurity, including technical challenges, economic implications, and societal effects.",
            "expected_agents": 6,
        },
        {
            "name": "Climate Tech Innovation",
            "prompt": "Research innovative technologies for carbon capture and storage, analyzing technical feasibility, business viability, and social adoption challenges.",
            "expected_agents": 6,
        },
    ]

    for i, scenario in enumerate(research_scenarios, 1):
        print(f"🧪 RESEARCH SCENARIO {i}: {scenario['name']}")
        print(f"📝 Research Question: {scenario['prompt']}")
        print()

        # Create initial state
        run_id = str(uuid.uuid4())
        initial_state = create_initial_state(
            workflow_name="multi_agent_research",
            run_id=run_id,
            user_input={
                "user_prompt": scenario["prompt"],
                "research_type": "comprehensive_analysis",
            },
            workflow_config={"enable_monitoring": True, "enable_multi_agent": True},
        )

        # Execute workflow with monitoring
        start_time = time.time()
        config = {"configurable": {"thread_id": run_id}}

        try:
            print("🚀 Executing multi-agent research workflow...")

            # Show real-time monitoring
            print("📊 Real-time Monitoring:")
            health_before = monitor.get_workflow_health()
            print(f"   Health Status: {health_before['status']}")
            print(f"   Active Workflows: {health_before['active_workflows']}")

            # Execute workflow
            final_state = compiled_workflow.invoke(initial_state, config=config)
            execution_time = time.time() - start_time

            print()
            print("📊 === MULTI-AGENT EXECUTION RESULTS ===")
            print(f"⏱️  Total execution time: {execution_time:.2f} seconds")

            # Show multi-agent results
            multi_agent_results = final_state.get("workflow_state", {}).get(
                "multi_agent_results", {}
            )
            if multi_agent_results:
                print()
                print("🤖 MULTI-AGENT TEAM RESULTS:")

                if "individual_contributions" in multi_agent_results:
                    contributions = multi_agent_results["individual_contributions"]
                    for group_name, group_results in contributions.items():
                        print(f"\n   📋 {group_name.upper()}:")
                        for agent_id, result in group_results.items():
                            if "error" in result:
                                print(f"      ❌ {agent_id}: {result['error']}")
                            else:
                                print(f"      ✅ {agent_id}: Analysis completed")

                if "synthesized_result" in multi_agent_results:
                    synthesis = multi_agent_results["synthesized_result"]
                    print(f"\n   🎯 SYNTHESIS SUMMARY:")
                    print(
                        f"      Key Insights: {len(synthesis.get('key_insights', []))}"
                    )
                    print(
                        f"      Diverse Perspectives: {len(synthesis.get('diverse_perspectives', []))}"
                    )
                    print(
                        f"      Combined Recommendations: {len(synthesis.get('combined_recommendations', []))}"
                    )

            # Show monitoring metrics
            print()
            print("📈 PERFORMANCE METRICS:")
            metrics_summary = metrics.get_all_metrics_summary()

            key_metrics = [
                "multi_agent_execution",
                "multi_agent_success",
                "workflows_started",
                "workflows_completed",
            ]

            for metric_name in key_metrics:
                if metric_name in metrics_summary:
                    summary = metrics_summary[metric_name]
                    if summary:
                        print(
                            f"   {metric_name}: {summary.get('latest', 0)} (avg: {summary.get('mean', 0):.2f})"
                        )

            # Show workflow health
            health_after = monitor.get_workflow_health()
            print()
            print("🏥 WORKFLOW HEALTH STATUS:")
            print(f"   Status: {health_after['status']}")
            print(f"   Active Workflows: {health_after['active_workflows']}")
            print(f"   Error Rate (last hour): {health_after['error_rate_last_hour']}")
            print(
                f"   Avg Duration (last hour): {health_after['avg_duration_last_hour']:.2f}s"
            )

            # Show active alerts
            active_alerts = alerts.get_active_alerts()
            if active_alerts:
                print()
                print("🚨 ACTIVE ALERTS:")
                for alert in active_alerts:
                    severity = alert["severity"].upper()
                    print(f"   [{severity}] {alert['name']}: {alert['message']}")
            else:
                print()
                print("✅ No active alerts - system healthy")

            # Show errors (if any)
            errors = final_state.get("errors", [])
            if errors:
                print()
                print("⚠️  ERRORS ENCOUNTERED:")
                for error in errors:
                    print(f"   - {error}")

        except Exception as e:
            print(f"❌ Multi-agent workflow execution failed: {e}")
            import traceback

            traceback.print_exc()

        print()
        print("=" * 80)
        print()

        # Brief pause between scenarios
        if i < len(research_scenarios):
            print("⏸️  Pausing 2 seconds before next scenario...")
            time.sleep(2)

    # Final monitoring summary
    print("📊 FINAL MONITORING SUMMARY")
    print("=" * 40)

    # Export metrics
    print("\n📈 Metrics Export (JSON format):")
    print(metrics.export_metrics("json"))

    # Alert history
    alert_history = alerts.get_alert_history(10)
    if alert_history:
        print(f"\n🚨 Recent Alert History ({len(alert_history)} events):")
        for event in alert_history[-5:]:  # Show last 5
            timestamp = time.strftime("%H:%M:%S", time.localtime(event["timestamp"]))
            action = event.get("action", "triggered")
            print(f"   [{timestamp}] {event['name']}: {action}")

    # System health summary
    final_health = monitor.get_workflow_health()
    print(f"\n🏥 Final System Health: {final_health['status'].upper()}")

    print()
    print("🎉 PHASE 3 COMPLETE DEMO FINISHED!")
    print("All advanced capabilities successfully demonstrated:")
    print("   ✅ Multi-agent orchestration with 6 specialized agents")
    print(
        "   ✅ 4 different execution modes (sequential, parallel, competitive, collaborative)"
    )
    print("   ✅ Real-time metrics collection and performance analytics")
    print("   ✅ Comprehensive workflow health monitoring")
    print("   ✅ Intelligent alerting with multiple severity levels")
    print("   ✅ Cross-agent communication and result synthesis")
    print()


if __name__ == "__main__":
    demo_phase3_capabilities()
