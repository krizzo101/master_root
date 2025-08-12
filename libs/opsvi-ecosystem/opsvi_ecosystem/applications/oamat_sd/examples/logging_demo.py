"""
Logging System Demonstration

Shows how the Smart Decomposition logging system provides transparency
without overwhelming users with technical details.
"""

import asyncio
import time
from typing import Any, Dict

from sd_logging import (
    ConsoleInterface,
    LogConfig,
    LoggerFactory,
    create_correlation_context,
)

from src.applications.oamat_sd.src.config.config_manager import ConfigManager


async def simulate_complexity_analysis() -> Dict[str, Any]:
    """Simulate the 6-factor complexity analysis"""

    # Get specialized loggers
    factory = LoggerFactory(LogConfig())
    complexity_logger = factory.get_complexity_logger()
    debug_logger = factory.get_debug_logger()

    debug_logger.info("Starting complexity analysis", operation="complexity_analysis")

    # Simulate factor analysis
    factors = {
        "Skill Diversity": 7.5,
        "Coordination Complexity": 8.2,
        "Parallelizability": 6.0,
        "Time Sensitivity": 3.5,  # Inverse scoring
        "Cost Tolerance": 7.0,
        "Domain Suitability": 8.5,
    }

    # Calculate weighted score
    weights = [0.2, 0.25, 0.15, 0.1, 0.15, 0.15]
    overall_score = (
        sum(score * weight for score, weight in zip(factors.values(), weights)) * 10
    )

    decision = "DAG Orchestration" if overall_score >= 60 else "Linear Workflow"
    reasoning = (
        f"Score {overall_score:.1f}/100 - Multiple high-complexity factors detected"
    )

    # Log the analysis
    factory.log_complexity_analysis(
        user_request="Build a comprehensive market research report with competitive analysis",
        factors=factors,
        overall_score=overall_score,
        decision=decision,
        reasoning=reasoning,
    )

    debug_logger.info(
        "Complexity analysis completed",
        operation="complexity_analysis",
        score=overall_score,
        decision=decision,
    )

    return {
        "score": overall_score,
        "factors": factors,
        "decision": decision,
        "reasoning": reasoning,
    }


async def simulate_dag_execution(console: ConsoleInterface):
    """Simulate DAG workflow execution with logging"""

    factory = LoggerFactory(LogConfig())
    workflow_logger = factory.get_workflow_logger()
    performance_logger = factory.get_performance_logger()
    api_logger = factory.get_api_logger()

    # Define DAG structure
    agents = ["researcher", "analyst", "writer", "reviewer"]
    dependencies = {
        "researcher": [],
        "analyst": ["researcher"],
        "writer": ["researcher", "analyst"],
        "reviewer": ["writer"],
    }

    console.show_dag_structure(agents, dependencies)

    # Log workflow start
    workflow_logger.info(
        "Starting DAG workflow execution",
        event="workflow_start",
        workflow_type="dag",
        agents=agents,
        dependencies=dependencies,
    )

    # Simulate agent execution
    results = {}
    start_time = time.time()

    for agent in agents:
        task_id = console.start_task(agent.title(), f"Executing {agent} agent", 4)

        # Simulate agent work with logging
        for step in range(4):
            await asyncio.sleep(0.5)  # Simulate work

            # Log API calls
            if step == 1:
                factory.log_api_call(
                    method="POST",
                    url="https://api.openai.com/v1/chat/completions",
                    request_data={
                        "model": "gpt-4.1-mini",
                        "messages": [{"role": "user", "content": f"{agent} prompt"}],
                    },
                    response_data={
                        "choices": [{"message": {"content": f"{agent} response"}}]
                    },
                    status_code=200,
                    duration_ms=1200.5,
                )

            console.update_task(task_id, f"{agent.title()}: Step {step + 1}/4")

        # Log agent completion
        agent_result = f"{agent} completed successfully"
        results[agent] = agent_result

        factory.log_agent_interaction(
            agent_id=agent,
            action="execute",
            input_data={"dependencies": dependencies.get(agent, [])},
            output_data={"result": agent_result},
            duration_ms=2000.0,
            metadata={"step_count": 4},
        )

        console.complete_task(task_id, agent_result)

    total_duration = (time.time() - start_time) * 1000

    # Log workflow completion
    factory.log_workflow_execution(
        workflow_type="dag",
        agents=agents,
        dependencies=dependencies,
        results=results,
        total_duration_ms=total_duration,
    )

    # Log performance metrics
    factory.log_performance_metrics(
        operation="dag_workflow_execution",
        duration_ms=total_duration,
        resource_usage={
            "agents_executed": len(agents),
            "api_calls": 4,
            "memory_peak_mb": 156.7,
        },
        metadata={"complexity_justified": True},
    )

    return results


async def simulate_error_scenario():
    """Simulate error handling and recovery logging"""

    factory = LoggerFactory(LogConfig())
    error_logger = factory.get_error_logger()
    debug_logger = factory.get_debug_logger()

    try:
        # Simulate an error
        debug_logger.info("Attempting risky operation", operation="api_call")

        # Simulate API failure
        factory.log_api_call(
            method="POST",
            url="https://api.example.com/failing-endpoint",
            request_data={"data": "test"},
            status_code=500,
            duration_ms=5000.0,
            error="Internal Server Error - Rate limit exceeded",
        )

        raise Exception("API rate limit exceeded")

    except Exception as e:
        error_logger.error(
            "Operation failed with recovery",
            event="error_with_recovery",
            error_type=type(e).__name__,
            error_message=str(e),
            recovery_action="exponential_backoff",
            retry_count=3,
        )

        # Simulate successful recovery
        await asyncio.sleep(1)

        factory.log_api_call(
            method="POST",
            url="https://api.example.com/failing-endpoint",
            request_data={"data": "test"},
            response_data={"status": "success"},
            status_code=200,
            duration_ms=800.0,
        )

        debug_logger.info(
            "Operation recovered successfully",
            operation="api_call",
            recovery_successful=True,
        )


async def main():
    """Run comprehensive logging demonstration"""

    # Setup logging configuration
    config = LogConfig(
        console_rich=True,
        console_progress=True,
        truncate_prompts_console=200,
        full_prompts_in_api_log=True,
    )

    # Create correlation context
    context = create_correlation_context(
        user_request="Build a comprehensive market research report with competitive analysis",
        execution_mode="dag",
    )

    # Initialize console interface
    console = ConsoleInterface(config)
    factory = LoggerFactory(config)

    try:
        # Start session
        console.start_session(
            user_request="Build a comprehensive market research report with competitive analysis"
        )

        print("\n" + "=" * 80)
        print("🔍 DEMONSTRATING SMART DECOMPOSITION LOGGING SYSTEM")
        print("=" * 80)

        # 1. Complexity Analysis
        print("\n1️⃣ Complexity Analysis Phase")
        complexity_result = await simulate_complexity_analysis()

        console.show_complexity_decision(
            score=complexity_result["score"],
            factors=complexity_result["factors"],
            decision=complexity_result["decision"],
        )

        # 2. DAG Execution
        print("\n2️⃣ DAG Workflow Execution")
        execution_results = await simulate_dag_execution(console)

        # 3. Error Handling Demo
        print("\n3️⃣ Error Handling and Recovery")
        await simulate_error_scenario()

        # 4. Final Results
        console.show_final_results(execution_results, 8.5)

        print("\n" + "=" * 80)
        print("📊 LOG FILES GENERATED:")
        print("=" * 80)

        for category, file_config in ConfigManager().get_log_files().items():
            log_path = ConfigManager().log_dir / file_config.filename
            if log_path.exists():
                size_kb = log_path.stat().st_size / 1024
                print(
                    f"📁 {category.value:12} → {file_config.filename} ({size_kb:.1f} KB)"
                )

        print("\n✨ Logging demonstration completed!")
        print("📋 Review individual log files for targeted investigation")
        print("🎯 Console provided user-friendly progress without technical overwhelm")

    finally:
        console.end_session()


if __name__ == "__main__":
    asyncio.run(main())
