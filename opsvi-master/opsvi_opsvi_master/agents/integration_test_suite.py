"""
Comprehensive integration test suite for enhanced agent systems.

This module provides extensive integration testing capabilities including:
- End-to-end agent communication testing
- Performance benchmarking and profiling
- Load testing and stress testing
- Error handling and recovery validation
- Message bus reliability testing
- Multi-agent coordination scenarios
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import Mock, AsyncMock

from src.agents.enhanced_base_agent import EnhancedBaseAgent
from src.agents.base_agent import AgentCapabilityType, AgentCapability
from src.agents.error_handling import ErrorSeverity
from src.agents.monitoring import get_agent_monitor
from src.coordination.enhanced_message_bus import (
    EnhancedMessageBus,
    MessagePriority,
    DeliveryMode,
    RoutingStrategy,
)
from src.agents.base_agent import AgentMessage, MessageType, AgentCapability

logger = logging.getLogger(__name__)


class MockTool:
    """Mock tool for testing agent functionality."""

    def __init__(
        self, name: str, execution_time: float = 0.1, failure_rate: float = 0.0
    ):
        """Initialize mock tool.

        Args:
            name: Tool name
            execution_time: Simulated execution time in seconds
            failure_rate: Probability of failure (0.0 to 1.0)
        """
        self.name = name
        self.execution_time = execution_time
        self.failure_rate = failure_rate
        self.call_count = 0

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mock tool."""
        self.call_count += 1

        # Simulate execution time
        await asyncio.sleep(self.execution_time)

        # Simulate failures
        import random

        if random.random() < self.failure_rate:
            raise Exception(f"Simulated failure in tool {self.name}")

        return {
            "tool": self.name,
            "result": f"success_{self.call_count}",
            "parameters": parameters,
            "execution_time": self.execution_time,
        }


class TestAgent(EnhancedBaseAgent):
    """Test agent implementation for integration testing."""

    async def _initialize_agent(self):
        """Minimal implementation for abstract method."""
        pass

    def __init__(self, agent_id: str, test_config: Optional[Dict[str, Any]] = None):
        """Initialize test agent."""
        config = {
            "tool_cache_enabled": True,
            "tool_cache_ttl": 300,
            "retry_max_attempts": 3,
            "retry_base_delay": 0.1,
            "retry_max_delay": 10.0,
            **(test_config or {}),
        }

        super().__init__(
            agent_id=agent_id,
            name=f"TestAgent-{agent_id}",
            description="Agent for integration testing",
            capabilities=[
                AgentCapability(
                    name=AgentCapabilityType.TASK_PROCESSING.value,
                    description="Task processing capability",
                    version="1.0",
                ),
                AgentCapability(
                    name=AgentCapabilityType.COMMUNICATION.value,
                    description="Communication capability",
                    version="1.0",
                ),
                AgentCapability(
                    name=AgentCapabilityType.ERROR_HANDLING.value,
                    description="Error handling capability",
                    version="1.0",
                ),
            ],
            config=config,
        )

        # Test-specific attributes
        self.processed_tasks = []
        self.received_messages = []
        self.test_tools = {}

    def add_test_tool(self, tool: MockTool) -> None:
        """Add a mock tool for testing."""
        self.test_tools[tool.name] = tool

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool (mock implementation for testing)."""
        if tool_name in self.test_tools:
            return await self.test_tools[tool_name].execute(parameters)

        # Fallback to parent implementation
        return await super().execute_tool(tool_name, parameters)

    async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task implementation for testing."""
        task_id = task.get("id", "unknown")
        task_type = task.get("type", "generic")

        self.processed_tasks.append(task)

        # Simulate different task types
        if task_type == "simple":
            await asyncio.sleep(0.1)
            return {
                "status": "completed",
                "task_id": task_id,
                "result": "simple_task_done",
            }

        elif task_type == "tool_usage":
            tool_name = task.get("tool", "default_tool")
            tool_params = task.get("parameters", {})
            tool_result = await self.execute_tool(tool_name, tool_params)
            return {
                "status": "completed",
                "task_id": task_id,
                "tool_result": tool_result,
            }

        elif task_type == "error_prone":
            if task.get("should_fail", False):
                raise Exception(f"Intentional failure for task {task_id}")
            return {
                "status": "completed",
                "task_id": task_id,
                "result": "error_prone_task_done",
            }

        elif task_type == "long_running":
            duration = task.get("duration", 1.0)
            await asyncio.sleep(duration)
            return {"status": "completed", "task_id": task_id, "duration": duration}

        else:
            return {
                "status": "completed",
                "task_id": task_id,
                "result": "generic_task_done",
            }

    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle message with recording for testing."""
        self.received_messages.append(message)
        await super()._handle_message(message)


class IntegrationTestSuite:
    """Comprehensive integration test suite for enhanced agent systems."""

    def __init__(self, test_config: Optional[Dict[str, Any]] = None):
        """Initialize test suite."""
        self.test_config = test_config or {}
        self.test_results = {}
        self.performance_metrics = {}
        self.test_agents = {}
        self.message_bus = None
        self.logger = logging.getLogger(f"{__name__}.IntegrationTestSuite")

    async def setup(self) -> None:
        """Set up test environment."""
        self.logger.info("Setting up integration test environment")

        # Create enhanced message bus
        self.message_bus = EnhancedMessageBus(
            routing_strategy=RoutingStrategy.LEAST_BUSY, enable_compression=True
        )
        await self.message_bus.start()

        # Create test agents
        for i in range(3):
            agent_id = f"test_agent_{i}"
            agent = TestAgent(agent_id, self.test_config)

            # Add mock tools
            agent.add_test_tool(MockTool("fast_tool", 0.1, 0.0))
            agent.add_test_tool(MockTool("slow_tool", 1.0, 0.0))
            agent.add_test_tool(MockTool("unreliable_tool", 0.2, 0.3))

            # Initialize and start agent
            await agent.initialize()
            await agent.start()

            # Register with message bus
            await self.message_bus.register_agent(
                agent_id, agent._handle_message, ["task_processing", "communication"]
            )

            self.test_agents[agent_id] = agent

        self.logger.info("Test environment setup complete")

    async def teardown(self) -> None:
        """Clean up test environment."""
        self.logger.info("Tearing down test environment")

        # Stop agents
        for agent in self.test_agents.values():
            try:
                await agent.stop()
            except Exception as e:
                self.logger.warning(f"Error stopping agent: {e}")

        # Stop message bus
        if self.message_bus:
            await self.message_bus.stop()

        self.test_agents.clear()
        self.logger.info("Test environment teardown complete")

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        self.logger.info("Starting comprehensive integration test suite")
        start_time = time.time()

        try:
            await self.setup()

            # Run test categories
            await self.test_basic_agent_functionality()
            await self.test_message_bus_reliability()
            await self.test_error_handling_and_recovery()
            await self.test_performance_and_scaling()
            await self.test_multi_agent_coordination()
            await self.test_load_and_stress_scenarios()

            total_time = time.time() - start_time

            # Generate summary
            summary = self._generate_test_summary(total_time)
            self.logger.info(
                f"Integration test suite completed in {total_time:.2f} seconds"
            )

            return summary

        finally:
            await self.teardown()

    async def test_basic_agent_functionality(self) -> None:
        """Test basic agent functionality."""
        self.logger.info("Testing basic agent functionality")
        test_results = {}

        agent = list(self.test_agents.values())[0]

        # Test 1: Simple task processing
        task = {"id": "basic_1", "type": "simple"}
        result = await agent.process_task(task)
        test_results["simple_task"] = {
            "success": result["status"] == "completed",
            "result": result,
        }

        # Test 2: Tool execution with caching
        task = {
            "id": "basic_2",
            "type": "tool_usage",
            "tool": "fast_tool",
            "parameters": {"test": "value"},
        }

        # First execution (cache miss)
        start_time = time.time()
        result1 = await agent.process_task(task)
        first_time = time.time() - start_time

        # Second execution (cache hit)
        start_time = time.time()
        result2 = await agent.process_task(task)
        second_time = time.time() - start_time

        test_results["tool_caching"] = {
            "success": result1["status"] == "completed"
            and result2["status"] == "completed",
            "cache_performance_improvement": first_time > second_time,
            "first_execution_time": first_time,
            "second_execution_time": second_time,
        }

        # Test 3: Agent status and monitoring
        status = agent.get_enhanced_status()
        test_results["status_monitoring"] = {
            "success": "performance" in status and "error_handling" in status,
            "status_keys": list(status.keys()),
        }

        self.test_results["basic_functionality"] = test_results

    async def test_message_bus_reliability(self) -> None:
        """Test message bus reliability and delivery guarantees."""
        self.logger.info("Testing message bus reliability")
        test_results = {}

        agent1 = self.test_agents["test_agent_0"]
        agent2 = self.test_agents["test_agent_1"]

        # Test 1: Direct message delivery
        message = AgentMessage(
            type=MessageType.TASK_REQUEST,
            content={"test": "direct_delivery"},
            sender_id=agent1.agent_id,
            recipient_id=agent2.agent_id,
        )

        initial_count = len(agent2.received_messages)
        success = await self.message_bus.send_message(
            message, delivery_mode=DeliveryMode.AT_LEAST_ONCE
        )

        # Wait for delivery
        await asyncio.sleep(0.5)

        test_results["direct_delivery"] = {
            "success": success and len(agent2.received_messages) > initial_count,
            "message_received": len(agent2.received_messages) > initial_count,
        }

        # Test 2: Load balancing
        messages_sent = 0
        for i in range(10):
            message = AgentMessage(
                type=MessageType.TASK_REQUEST,
                content={"test": f"load_balance_{i}"},
                sender_id=agent1.agent_id,
            )

            success = await self.message_bus.send_message(
                message, required_capabilities=["task_processing"]
            )
            if success:
                messages_sent += 1

        await asyncio.sleep(1.0)  # Allow time for delivery

        # Check distribution across agents
        message_counts = {
            agent_id: len(agent.received_messages)
            for agent_id, agent in self.test_agents.items()
        }

        test_results["load_balancing"] = {
            "success": messages_sent > 0,
            "messages_sent": messages_sent,
            "distribution": message_counts,
        }

        # Test 3: Event publishing
        subscribers = ["test_agent_0", "test_agent_1", "test_agent_2"]
        for agent_id in subscribers:
            await self.message_bus.subscribe(agent_id, "test_events")

        published_count = await self.message_bus.publish_event(
            "test_events",
            {"event_type": "test", "data": "event_data"},
            MessagePriority.HIGH,
        )

        await asyncio.sleep(0.5)

        test_results["event_publishing"] = {
            "success": published_count == len(subscribers),
            "published_count": published_count,
            "expected_count": len(subscribers),
        }

        self.test_results["message_bus_reliability"] = test_results

    async def test_error_handling_and_recovery(self) -> None:
        """Test error handling and recovery mechanisms."""
        self.logger.info("Testing error handling and recovery")
        test_results = {}

        agent = self.test_agents["test_agent_0"]

        # Test 1: Tool execution errors with retry
        task = {
            "id": "error_1",
            "type": "tool_usage",
            "tool": "unreliable_tool",
            "parameters": {"test": "retry_test"},
        }

        # Execute multiple times to test retry logic
        success_count = 0
        error_count = 0

        for i in range(10):
            try:
                result = await agent.process_task(task)
                if result["status"] == "completed":
                    success_count += 1
            except Exception:
                error_count += 1

        test_results["tool_error_recovery"] = {
            "success": success_count > 0,  # Some should succeed due to retries
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / (success_count + error_count),
        }

        # Test 2: Task processing errors
        error_task = {"id": "error_2", "type": "error_prone", "should_fail": True}

        try:
            result = await agent.process_task(error_task)
            error_handled = False
        except Exception:
            error_handled = True

        # Check error handler state
        error_health = agent.error_handler.get_health_status()

        test_results["task_error_handling"] = {
            "success": error_handled,
            "error_health": error_health,
            "circuit_breaker_active": any(
                cb.state != "CLOSED"
                for cb in agent.error_handler.circuit_breakers.values()
            ),
        }

        # Test 3: Performance degradation handling
        monitor = agent.monitor
        performance_summary = monitor.get_performance_summary()

        test_results["performance_monitoring"] = {
            "success": "tasks" in performance_summary,
            "metrics_available": list(performance_summary.keys()),
            "has_error_metrics": "errors" in performance_summary,
        }

        self.test_results["error_handling_recovery"] = test_results

    async def test_performance_and_scaling(self) -> None:
        """Test performance characteristics and scaling behavior."""
        self.logger.info("Testing performance and scaling")
        test_results = {}

        # Test 1: Concurrent task processing
        agent = self.test_agents["test_agent_0"]

        concurrent_tasks = []
        task_count = 20

        start_time = time.time()

        for i in range(task_count):
            task = {"id": f"perf_{i}", "type": "simple"}
            concurrent_tasks.append(agent.process_task(task))

        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

        end_time = time.time()

        successful_tasks = sum(
            1
            for result in results
            if not isinstance(result, Exception) and result.get("status") == "completed"
        )

        test_results["concurrent_processing"] = {
            "success": successful_tasks == task_count,
            "task_count": task_count,
            "successful_tasks": successful_tasks,
            "total_time": end_time - start_time,
            "tasks_per_second": task_count / (end_time - start_time),
        }

        # Test 2: Message throughput
        agent1 = self.test_agents["test_agent_0"]
        agent2 = self.test_agents["test_agent_1"]

        message_count = 100

        start_time = time.time()

        message_tasks = []
        for i in range(message_count):
            message = AgentMessage(
                type=MessageType.NOTIFICATION,
                content={"test": f"throughput_{i}"},
                sender_id=agent1.agent_id,
                recipient_id=agent2.agent_id,
            )

            message_tasks.append(
                self.message_bus.send_message(message, DeliveryMode.FIRE_AND_FORGET)
            )

        send_results = await asyncio.gather(*message_tasks)
        send_time = time.time() - start_time

        # Wait for delivery
        await asyncio.sleep(1.0)

        successful_sends = sum(1 for result in send_results if result)

        test_results["message_throughput"] = {
            "success": successful_sends > message_count * 0.9,  # Allow 10% failure
            "message_count": message_count,
            "successful_sends": successful_sends,
            "send_time": send_time,
            "messages_per_second": message_count / send_time,
        }

        # Test 3: Memory usage monitoring
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        test_results["resource_usage"] = {
            "success": True,  # Always successful, just monitoring
            "memory_mb": memory_info.rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "open_files": len(process.open_files()),
        }

        self.test_results["performance_scaling"] = test_results

    async def test_multi_agent_coordination(self) -> None:
        """Test multi-agent coordination scenarios."""
        self.logger.info("Testing multi-agent coordination")
        test_results = {}

        agents = list(self.test_agents.values())

        # Test 1: Agent-to-agent task delegation
        coordinator = agents[0]
        worker1 = agents[1]
        worker2 = agents[2]

        # Coordinator sends task to worker
        delegation_message = AgentMessage(
            type=MessageType.TASK_REQUEST,
            content={
                "task_id": "delegation_1",
                "task_type": "simple",
                "delegated_by": coordinator.agent_id,
            },
            sender_id=coordinator.agent_id,
            recipient_id=worker1.agent_id,
        )

        initial_task_count = len(worker1.processed_tasks)
        success = await self.message_bus.send_message(delegation_message)

        await asyncio.sleep(0.5)

        test_results["task_delegation"] = {
            "success": success and len(worker1.processed_tasks) > initial_task_count,
            "message_sent": success,
            "task_processed": len(worker1.processed_tasks) > initial_task_count,
        }

        # Test 2: Broadcast coordination
        coordination_tasks = []

        for i, agent in enumerate(agents):
            task = {
                "id": f"coordination_{i}",
                "type": "simple",
                "coordination_round": 1,
            }
            coordination_tasks.append(agent.process_task(task))

        coordination_results = await asyncio.gather(*coordination_tasks)

        successful_coordination = sum(
            1 for result in coordination_results if result.get("status") == "completed"
        )

        test_results["broadcast_coordination"] = {
            "success": successful_coordination == len(agents),
            "agent_count": len(agents),
            "successful_agents": successful_coordination,
        }

        # Test 3: Load distribution verification
        bus_stats = self.message_bus.get_statistics()

        test_results["load_distribution"] = {
            "success": bus_stats["active_agents"] == len(agents),
            "active_agents": bus_stats["active_agents"],
            "total_agents": bus_stats["total_agents"],
            "average_load": bus_stats["average_load"],
        }

        self.test_results["multi_agent_coordination"] = test_results

    async def test_load_and_stress_scenarios(self) -> None:
        """Test system behavior under load and stress conditions."""
        self.logger.info("Testing load and stress scenarios")
        test_results = {}

        # Test 1: High-frequency message sending
        agent1 = self.test_agents["test_agent_0"]

        burst_count = 200
        burst_tasks = []

        start_time = time.time()

        for i in range(burst_count):
            message = AgentMessage(
                type=MessageType.NOTIFICATION,
                content={"burst_id": i, "timestamp": time.time()},
                sender_id=agent1.agent_id,
            )

            burst_tasks.append(
                self.message_bus.send_message(
                    message,
                    priority=MessagePriority.HIGH,
                    required_capabilities=["communication"],
                )
            )

        burst_results = await asyncio.gather(*burst_tasks, return_exceptions=True)
        burst_time = time.time() - start_time

        successful_bursts = sum(
            1
            for result in burst_results
            if not isinstance(result, Exception) and result
        )

        test_results["high_frequency_messaging"] = {
            "success": successful_bursts
            > burst_count * 0.8,  # Allow 20% failure under stress
            "burst_count": burst_count,
            "successful_bursts": successful_bursts,
            "burst_time": burst_time,
            "burst_rate": burst_count / burst_time,
        }

        # Test 2: Long-running task stress
        long_tasks = []
        long_task_count = 10

        start_time = time.time()

        for i in range(long_task_count):
            task = {
                "id": f"long_{i}",
                "type": "long_running",
                "duration": 2.0,  # 2 second tasks
            }

            agent = self.test_agents[f"test_agent_{i % len(self.test_agents)}"]
            long_tasks.append(agent.process_task(task))

        long_results = await asyncio.gather(*long_tasks, return_exceptions=True)
        long_time = time.time() - start_time

        successful_long_tasks = sum(
            1
            for result in long_results
            if not isinstance(result, Exception) and result.get("status") == "completed"
        )

        test_results["long_running_stress"] = {
            "success": successful_long_tasks == long_task_count,
            "task_count": long_task_count,
            "successful_tasks": successful_long_tasks,
            "total_time": long_time,
            "expected_min_time": 2.0,  # Should take at least 2 seconds due to parallel execution
            "parallel_efficiency": 2.0 / long_time if long_time > 0 else 0,
        }

        # Test 3: System recovery after stress
        await asyncio.sleep(2.0)  # Allow system to settle

        # Check system health after stress
        final_stats = self.message_bus.get_statistics()

        all_agents_healthy = True
        agent_health = {}

        for agent_id, agent in self.test_agents.items():
            status = agent.get_enhanced_status()
            health = {
                "state": status["state"],
                "error_count": status["error_count"],
                "performance_available": "performance" in status,
            }
            agent_health[agent_id] = health

            if status["state"] != "running" or status["error_count"] > 10:
                all_agents_healthy = False

        test_results["post_stress_recovery"] = {
            "success": all_agents_healthy
            and final_stats["active_agents"] == len(self.test_agents),
            "all_agents_healthy": all_agents_healthy,
            "active_agents": final_stats["active_agents"],
            "agent_health": agent_health,
            "final_bus_stats": final_stats,
        }

        self.test_results["load_stress_scenarios"] = test_results

    def _generate_test_summary(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        summary = {
            "test_execution": {
                "total_time": total_time,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_categories": len(self.test_results),
            },
            "results_by_category": {},
            "overall_statistics": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
            },
            "performance_highlights": {},
            "detailed_results": self.test_results,
        }

        # Analyze results by category
        total_tests = 0
        passed_tests = 0

        for category, tests in self.test_results.items():
            category_passed = 0
            category_total = 0

            for test_name, test_result in tests.items():
                category_total += 1
                total_tests += 1

                if test_result.get("success", False):
                    category_passed += 1
                    passed_tests += 1

            summary["results_by_category"][category] = {
                "passed": category_passed,
                "total": category_total,
                "success_rate": category_passed / category_total
                if category_total > 0
                else 0,
            }

        # Overall statistics
        summary["overall_statistics"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
        }

        # Extract performance highlights
        if "performance_scaling" in self.test_results:
            perf_tests = self.test_results["performance_scaling"]

            if "concurrent_processing" in perf_tests:
                summary["performance_highlights"][
                    "concurrent_tasks_per_second"
                ] = perf_tests["concurrent_processing"].get("tasks_per_second", 0)

            if "message_throughput" in perf_tests:
                summary["performance_highlights"]["messages_per_second"] = perf_tests[
                    "message_throughput"
                ].get("messages_per_second", 0)

        return summary

    async def save_test_report(self, output_path: str) -> None:
        """Save detailed test report to file."""
        report = {
            "test_suite": "Enhanced Agent Systems Integration Tests",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "configuration": self.test_config,
            "summary": self._generate_test_summary(0),
            "detailed_results": self.test_results,
            "system_info": {
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
                "agent_count": len(self.test_agents),
                "test_environment": "integration_test_suite",
            },
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Test report saved to {output_path}")


# Convenience function for running integration tests
async def run_integration_tests(
    config: Optional[Dict[str, Any]] = None,
    save_report: bool = True,
    report_path: str = "/tmp/agent_integration_test_report.json",
) -> Dict[str, Any]:
    """Run complete integration test suite.

    Args:
        config: Test configuration
        save_report: Whether to save detailed report
        report_path: Path to save report

    Returns:
        Test summary results
    """
    suite = IntegrationTestSuite(config)

    try:
        summary = await suite.run_all_tests()

        if save_report:
            await suite.save_test_report(report_path)

        return summary

    except Exception as e:
        logger.error(f"Integration test suite failed: {e}")
        raise


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_integration_tests())
