"""
Comprehensive Tests for the Autonomous Claude Agent

This module contains comprehensive test coverage for the AutonomousAgent class,
including unit tests, integration tests, and stress tests.

Test Categories:
- Unit tests: Fast, isolated tests of individual methods
- Integration tests: Tests of component interactions
- Stress tests: Resource-intensive and performance tests

Usage:
    pytest tests/test_agent.py -m unit          # Run only unit tests
    pytest tests/test_agent.py -m integration   # Run only integration tests
    pytest tests/test_agent.py -m stress        # Run only stress tests
    pytest tests/test_agent.py --cov=src       # Run with coverage

Required fixtures are defined in conftest.py
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, call
import json

from src.core.agent import (
    AutonomousAgent, AgentState, ExecutionContext,
    ExecutionResult, GoalDecomposition
)
from src.core.claude_client import ClaudeTask


@pytest.mark.unit
class TestAutonomousAgent:
    """Unit tests for AutonomousAgent class"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_instance):
        """Test agent initializes correctly"""
        assert agent_instance.state == AgentState.IDLE
        assert agent_instance.iteration_count == 0
        assert agent_instance.claude_client is not None
        assert agent_instance.capability_registry is not None
    
    @pytest.mark.asyncio
    async def test_state_transitions(self, agent_instance):
        """Test agent state transitions"""
        # Test valid transitions
        await agent_instance.set_state(AgentState.PLANNING)
        assert agent_instance.state == AgentState.PLANNING
        
        await agent_instance.set_state(AgentState.EXECUTING)
        assert agent_instance.state == AgentState.EXECUTING
        
        await agent_instance.set_state(AgentState.LEARNING)
        assert agent_instance.state == AgentState.LEARNING
    
    @pytest.mark.asyncio
    async def test_goal_decomposition(self, agent_instance, mock_claude_client):
        """Test goal decomposition into subtasks"""
        goal = "Build a web scraper for news articles"
        
        # Mock Claude response for decomposition
        mock_claude_client.execute_task.return_value = {
            "status": "success",
            "result": {
                "subtasks": [
                    {"id": 1, "description": "Research news websites", "priority": 1},
                    {"id": 2, "description": "Design scraper architecture", "priority": 2},
                    {"id": 3, "description": "Implement scraper", "priority": 3},
                    {"id": 4, "description": "Test scraper", "priority": 4}
                ]
            }
        }
        
        decomposition = await agent_instance.decompose_goal(goal)
        
        assert decomposition is not None
        assert len(decomposition.subtasks) == 4
        assert decomposition.subtasks[0]["description"] == "Research news websites"
        mock_claude_client.execute_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_iteration(self, agent_instance, mock_claude_client):
        """Test single iteration execution"""
        context = ExecutionContext(
            iteration=1,
            goal="Test task",
            state=AgentState.EXECUTING
        )
        
        mock_claude_client.execute_task.return_value = {
            "status": "success",
            "result": "Task completed successfully",
            "metrics": {"tokens": 150}
        }
        
        result = await agent_instance.execute_iteration(context)
        
        assert result.success is True
        assert result.output == "Task completed successfully"
        assert "tokens" in result.metrics
        assert agent_instance.iteration_count == 1
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, agent_instance, mock_claude_client):
        """Test error recovery mechanism"""
        # Simulate an error
        mock_claude_client.execute_task.side_effect = [
            Exception("API Error"),
            {"status": "success", "result": "Recovered"}
        ]
        
        context = ExecutionContext(
            iteration=1,
            goal="Test with error",
            state=AgentState.EXECUTING
        )
        
        # First attempt should fail and trigger recovery
        result = await agent_instance.execute_iteration(context)
        
        # Should have recovered
        assert agent_instance.state != AgentState.ERROR
        assert mock_claude_client.execute_task.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_learning_from_execution(self, agent_instance, mock_knowledge_base):
        """Test that agent learns from execution results"""
        context = ExecutionContext(
            iteration=1,
            goal="Learn from this",
            state=AgentState.EXECUTING
        )
        
        result = ExecutionResult(
            success=True,
            output="Learned something new",
            metrics={"learning_rate": 0.01}
        )
        
        await agent_instance.learn_from_result(context, result)
        
        # Verify pattern was added to knowledge base
        mock_knowledge_base.add_pattern.assert_called()
        call_args = mock_knowledge_base.add_pattern.call_args[0][0]
        assert "goal" in call_args
        assert call_args["success"] is True
    
    @pytest.mark.asyncio
    async def test_resource_monitoring(self, agent_instance, mock_resource_monitor):
        """Test resource monitoring during execution"""
        mock_resource_monitor.check_limits.return_value = False  # Exceed limits
        
        context = ExecutionContext(
            iteration=1,
            goal="Resource intensive task",
            state=AgentState.EXECUTING
        )
        
        with pytest.raises(Exception, match="Resource limits exceeded"):
            await agent_instance.check_resources()
        
        mock_resource_monitor.check_limits.assert_called()
    
    @pytest.mark.asyncio
    async def test_capability_execution(self, agent_instance, mock_capability_registry):
        """Test capability execution"""
        capability_name = "code_analysis"
        task_data = {"code": "def test(): pass"}
        
        result = await agent_instance.execute_capability(capability_name, task_data)
        
        assert result is not None
        capability = mock_capability_registry.get_capability(capability_name)
        capability["handler"].assert_called_once_with(task_data)
    
    @pytest.mark.asyncio
    async def test_checkpoint_creation(self, agent_instance, mock_state_manager):
        """Test checkpoint creation and restoration"""
        # Create checkpoint
        checkpoint_id = await agent_instance.create_checkpoint()
        
        assert checkpoint_id == "checkpoint-123"
        mock_state_manager.create_checkpoint.assert_called_once()
        
        # Restore checkpoint
        success = await agent_instance.restore_checkpoint(checkpoint_id)
        
        assert success is True
        mock_state_manager.restore_checkpoint.assert_called_once_with(checkpoint_id)
    
    @pytest.mark.asyncio
    async def test_parallel_task_execution(self, agent_instance, mock_claude_client):
        """Test parallel execution of multiple tasks"""
        tasks = [
            ClaudeTask(prompt="Task 1"),
            ClaudeTask(prompt="Task 2"),
            ClaudeTask(prompt="Task 3")
        ]
        
        mock_claude_client.execute_batch.return_value = {
            "batch_id": "batch-789",
            "results": [
                {"status": "success", "result": "Result 1"},
                {"status": "success", "result": "Result 2"},
                {"status": "success", "result": "Result 3"}
            ]
        }
        
        results = await agent_instance.execute_parallel_tasks(tasks)
        
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
        mock_claude_client.execute_batch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_self_modification_safety(self, agent_instance, mock_safety_rules):
        """Test self-modification safety checks"""
        modification = {
            "type": "add_capability",
            "capability": "dangerous_operation",
            "code": "# potentially unsafe code"
        }
        
        mock_safety_rules.validate_modification.return_value = False
        
        with pytest.raises(Exception, match="Modification not allowed"):
            await agent_instance.apply_self_modification(modification)
        
        mock_safety_rules.validate_modification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, agent_instance):
        """Test proper cleanup on shutdown"""
        # Set agent to active state
        agent_instance.state = AgentState.EXECUTING
        
        await agent_instance.shutdown()
        
        assert agent_instance.state == AgentState.SHUTDOWN
        agent_instance.state_manager.save_state.assert_called()
        agent_instance.resource_monitor.stop_monitoring.assert_called()


@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for agent with components"""
    
    @pytest.mark.asyncio
    async def test_full_execution_cycle(self, agent_instance, mock_claude_client):
        """Test complete execution cycle from goal to result"""
        goal = "Analyze Python code quality"
        
        # Mock responses for full cycle
        mock_claude_client.execute_task.side_effect = [
            # Goal decomposition
            {"status": "success", "result": {"subtasks": [{"description": "Analyze code"}]}},
            # Task execution
            {"status": "success", "result": "Analysis complete", "metrics": {"quality_score": 85}}
        ]
        
        result = await agent_instance.execute_goal(goal, max_iterations=5)
        
        assert result.success is True
        assert agent_instance.iteration_count > 0
        assert "quality_score" in result.metrics
    
    @pytest.mark.asyncio
    async def test_learning_and_pattern_recognition(self, agent_instance, mock_knowledge_base):
        """Test learning system integration"""
        # Execute similar tasks
        similar_goals = [
            "Fix ImportError in module",
            "Resolve ImportError in package",
            "Handle ImportError exception"
        ]
        
        for goal in similar_goals:
            context = ExecutionContext(iteration=1, goal=goal, state=AgentState.EXECUTING)
            result = ExecutionResult(success=True, output="Fixed", metrics={})
            await agent_instance.learn_from_result(context, result)
        
        # Check if pattern was recognized
        patterns = await mock_knowledge_base.search_patterns("ImportError")
        assert mock_knowledge_base.add_pattern.call_count == 3
    
    @pytest.mark.asyncio
    async def test_capability_discovery_and_integration(self, agent_instance, mock_capability_registry):
        """Test dynamic capability discovery"""
        new_capability = {
            "name": "new_analysis",
            "description": "New analysis tool",
            "handler": AsyncMock(return_value={"status": "success"})
        }
        
        # Discover and register new capability
        await agent_instance.discover_and_register_capability(new_capability)
        
        mock_capability_registry.register.assert_called_once()
        
        # Use the new capability
        result = await agent_instance.execute_capability("new_analysis", {})
        assert result is not None
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_long_running_task_with_checkpoints(self, agent_instance, mock_state_manager):
        """Test long-running task with periodic checkpoints"""
        iterations = 10
        checkpoint_interval = 3
        
        for i in range(iterations):
            context = ExecutionContext(
                iteration=i+1,
                goal="Long task",
                state=AgentState.EXECUTING
            )
            
            result = await agent_instance.execute_iteration(context)
            
            if (i + 1) % checkpoint_interval == 0:
                await agent_instance.create_checkpoint()
        
        # Verify checkpoints were created
        expected_checkpoints = iterations // checkpoint_interval
        assert mock_state_manager.create_checkpoint.call_count == expected_checkpoints
    
    @pytest.mark.asyncio  
    async def test_error_cascade_handling(self, agent_instance, mock_claude_client):
        """Test handling of cascading errors"""
        # Simulate multiple consecutive errors
        mock_claude_client.execute_task.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3"),
            {"status": "success", "result": "Finally recovered"}
        ]
        
        context = ExecutionContext(
            iteration=1,
            goal="Error-prone task",
            state=AgentState.EXECUTING
        )
        
        result = await agent_instance.execute_iteration(context)
        
        # Should eventually recover
        assert mock_claude_client.execute_task.call_count == 4
        assert agent_instance.state != AgentState.ERROR


@pytest.mark.stress
class TestAgentStress:
    """Stress tests for the agent"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_high_iteration_count(self, agent_instance):
        """Test agent with high iteration count"""
        max_iterations = 100
        
        for i in range(max_iterations):
            context = ExecutionContext(
                iteration=i+1,
                goal=f"Task {i}",
                state=AgentState.EXECUTING
            )
            result = await agent_instance.execute_iteration(context)
            
            # Agent should handle high iteration counts
            assert agent_instance.iteration_count == i + 1
        
        assert agent_instance.iteration_count == max_iterations
    
    @pytest.mark.asyncio
    async def test_concurrent_capability_execution(self, agent_instance):
        """Test concurrent execution of multiple capabilities"""
        capability_tasks = [
            ("code_analysis", {"code": "test1"}),
            ("test_generation", {"code": "test2"}),
            ("code_analysis", {"code": "test3"})
        ]
        
        tasks = [
            agent_instance.execute_capability(name, data)
            for name, data in capability_tasks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete without exceptions
        assert len(results) == len(capability_tasks)
        assert not any(isinstance(r, Exception) for r in results)
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, agent_instance, mock_resource_monitor):
        """Test memory usage stays within limits under load"""
        initial_memory = 100
        memory_increment = 10
        
        def get_increasing_memory():
            nonlocal initial_memory
            initial_memory += memory_increment
            return {
                "memory_mb": initial_memory,
                "cpu_percent": 30,
                "disk_mb": 50,
                "api_calls": 5
            }
        
        mock_resource_monitor.get_metrics.side_effect = get_increasing_memory
        mock_resource_monitor.check_limits.side_effect = lambda: initial_memory < 500
        
        # Execute until memory limit
        iterations = 0
        while await agent_instance.check_resources():
            iterations += 1
            if iterations > 50:  # Safety limit
                break
        
        # Should stop before excessive memory use
        assert initial_memory < 600
        assert iterations > 0


@pytest.mark.claude
class TestAgentWithClaude:
    """Tests that require actual Claude API access"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_goal_execution(self, real_agent_instance):
        """Test with real Claude API (requires API key)"""
        pytest.skip("Requires Claude API key - enable manually for integration testing")
        
        goal = "Analyze a simple Python function for potential improvements"
        
        # This would test with real Claude API
        result = await real_agent_instance.execute_goal(goal, max_iterations=2)
        
        assert result is not None
        assert real_agent_instance.iteration_count > 0
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, real_agent_instance):
        """Test handling of real API errors"""
        pytest.skip("Requires Claude API key - enable manually for integration testing")
        
        # Test with invalid request that should trigger API error
        context = ExecutionContext(
            iteration=1,
            goal="Invalid request that exceeds token limits " * 1000,
            state=AgentState.EXECUTING
        )
        
        result = await real_agent_instance.execute_iteration(context)
        
        # Should handle API errors gracefully
        assert real_agent_instance.state != AgentState.ERROR


@pytest.mark.network
class TestAgentNetworkFeatures:
    """Tests for network-dependent features"""
    
    @pytest.mark.asyncio
    async def test_research_capability(self, agent_instance, mock_research_engine):
        """Test research functionality"""
        capabilities_needed = ["web_scraping", "data_analysis"]
        
        mock_research_engine.research_capability.return_value = {
            "techniques": ["BeautifulSoup", "Scrapy"],
            "examples": ["example code here"],
            "best_practices": ["respect robots.txt"]
        }
        
        opportunities = {"capabilities_needed": capabilities_needed}
        research = await agent_instance.research_solutions(opportunities)
        
        assert "web_scraping" in research
        assert research["web_scraping"] is not None
        mock_research_engine.research_capability.assert_called()
    
    @pytest.mark.asyncio
    async def test_capability_discovery(self, agent_instance, mock_capability_discovery):
        """Test dynamic capability discovery"""
        new_capabilities = [
            {"name": "json_parser", "handler": AsyncMock()},
            {"name": "file_processor", "handler": AsyncMock()}
        ]
        
        mock_capability_discovery.discover_capabilities.return_value = new_capabilities
        
        discovered = await agent_instance.capability_discovery.discover_capabilities()
        
        assert len(discovered) == 2
        assert any(cap["name"] == "json_parser" for cap in discovered)


@pytest.mark.experimental
class TestExperimentalFeatures:
    """Tests for experimental and advanced features"""
    
    @pytest.mark.asyncio
    async def test_self_reflection(self, agent_instance):
        """Test agent's ability to reflect on its own performance"""
        # Set up some execution history
        agent_instance.iteration = 20
        agent_instance.success_count = 15
        agent_instance.error_count = 5
        
        # Trigger self-reflection
        assessment = await agent_instance.assess_current_state()
        
        assert "progress" in assessment
        assert "bottlenecks" in assessment
        assert "recommendations" in assessment
        assert assessment["progress"] >= 0
        assert assessment["progress"] <= 100
    
    @pytest.mark.asyncio
    async def test_adaptive_behavior(self, agent_instance):
        """Test agent's adaptive behavior based on success rate"""
        # Simulate low success rate
        agent_instance.iteration = 50
        agent_instance.success_count = 20
        agent_instance.error_count = 30
        
        should_modify = await agent_instance.should_modify()
        
        # Should want to modify due to low success rate
        # Note: depends on iteration count being multiple of 20
        if agent_instance.iteration % 20 == 0:
            assert should_modify is True
    
    @pytest.mark.asyncio
    async def test_pattern_evolution(self, agent_instance, mock_pattern_engine):
        """Test how patterns evolve over time"""
        # Add some patterns
        patterns = [
            {"type": "error_recovery", "success_rate": 0.8},
            {"type": "optimization", "success_rate": 0.9},
            {"type": "debugging", "success_rate": 0.7}
        ]
        
        mock_pattern_engine.patterns = patterns
        mock_pattern_engine.get_top_patterns.return_value = patterns[:2]
        
        top_patterns = mock_pattern_engine.get_top_patterns(2)
        
        assert len(top_patterns) == 2
        assert top_patterns[0]["success_rate"] >= 0.8


@pytest.mark.critical
class TestCriticalFunctionality:
    """Tests for critical system functionality that must always work"""
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown_under_load(self, agent_instance):
        """Test graceful shutdown even when agent is busy"""
        # Simulate agent in busy state
        agent_instance.current_state = AgentState.EXECUTING
        agent_instance.iteration = 100
        
        # Request shutdown
        shutdown_task = asyncio.create_task(agent_instance.shutdown())
        
        # Should complete shutdown within reasonable time
        try:
            await asyncio.wait_for(shutdown_task, timeout=5.0)
        except asyncio.TimeoutError:
            pytest.fail("Shutdown took too long")
        
        assert agent_instance.current_state == AgentState.SHUTDOWN
    
    @pytest.mark.asyncio
    async def test_data_persistence_on_crash(self, agent_instance, mock_state_manager):
        """Test that important data is saved even if agent crashes"""
        # Simulate some progress
        agent_instance.iteration = 10
        agent_instance.success_count = 8
        
        # Simulate crash by raising exception
        with pytest.raises(Exception):
            raise Exception("Simulated crash")
        
        # Ensure shutdown still saves data
        await agent_instance.shutdown()
        
        # Verify checkpoint was saved
        mock_state_manager.save_checkpoint.assert_called()
    
    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self, agent_instance, mock_resource_monitor):
        """Test that resource limits are strictly enforced"""
        # Configure strict limits
        mock_resource_monitor.check_all_limits.return_value = False
        
        # Should not be able to continue execution
        can_continue = await agent_instance.check_resources()
        
        assert can_continue is False
        
        # Should trigger resource limit handling
        await agent_instance.handle_resource_limit()
        
        # Verify cleanup was attempted
        agent_instance.context_manager.compress_context.assert_called()
    
    @pytest.mark.asyncio
    async def test_safety_checks_prevent_dangerous_operations(self, agent_instance, mock_safety_rules):
        """Test that safety checks prevent dangerous self-modifications"""
        dangerous_modification = {
            "type": "replace_core_component",
            "target": "safety_rules",
            "code": "# Disable all safety checks"
        }
        
        mock_safety_rules.validate_modification.return_value = False
        
        with pytest.raises(Exception, match="Modification not allowed"):
            await agent_instance.apply_self_modification(dangerous_modification)
        
        # Ensure validation was called
        mock_safety_rules.validate_modification.assert_called_once_with(dangerous_modification)


@pytest.mark.performance
class TestPerformanceMetrics:
    """Tests focused on performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_iteration_performance(self, agent_instance):
        """Test that iterations complete within reasonable time"""
        context = ExecutionContext(
            iteration=1,
            goal="Simple test task",
            state=AgentState.EXECUTING
        )
        
        start_time = asyncio.get_event_loop().time()
        
        # Execute iteration
        result = await agent_instance.execute_iteration(context)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        # Should complete within 10 seconds for simple task
        assert duration < 10.0
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_memory_growth_over_iterations(self, agent_instance):
        """Test that memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run multiple iterations
        for i in range(10):
            context = ExecutionContext(
                iteration=i+1,
                goal=f"Test task {i}",
                state=AgentState.EXECUTING
            )
            await agent_instance.execute_iteration(context)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for 10 iterations)
        assert memory_growth < 100
    
    @pytest.mark.asyncio
    async def test_concurrent_operation_performance(self, agent_instance):
        """Test performance under concurrent operations"""
        # Create multiple concurrent tasks
        tasks = []
        for i in range(5):
            task = agent_instance.execute_capability(
                "test_capability", 
                {"data": f"test_{i}"}
            )
            tasks.append(task)
        
        start_time = asyncio.get_event_loop().time()
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        # Concurrent execution should be faster than sequential
        # and complete within reasonable time
        assert duration < 5.0
        assert len(results) == 5
        assert not any(isinstance(r, Exception) for r in results)


# Test utilities and helpers
def create_test_agent_config():
    """Create a test configuration for the agent"""
    return {
        'max_iterations': 10,
        'mode': 'test',
        'claude': {
            'max_concurrent': 2,
            'timeout': 30,
            'retry_max': 2
        },
        'context': {
            'max_tokens': 1000,
            'summarization_threshold': 800
        },
        'limits': {
            'memory_mb': 512,
            'cpu_percent': 50,
            'disk_mb': 1024
        },
        'safety': {
            'allow_file_modifications': False,
            'allow_network_requests': False,
            'require_approval_for': ['delete', 'system_command'],
            'max_recursion_depth': 3
        },
        'research': {
            'cache_ttl_hours': 1,
            'max_search_results': 5,
            'enable_web_search': False
        },
        'logging': {
            'level': 'DEBUG',
            'file': '/tmp/test_agent.log'
        }
    }


def assert_agent_state_valid(agent):
    """Assert that agent state is valid"""
    assert agent.id is not None
    assert len(agent.id) > 0
    assert agent.current_state in AgentState
    assert agent.iteration >= 0
    assert agent.success_count >= 0
    assert agent.error_count >= 0
    assert agent.max_iterations > 0


def create_mock_execution_result(success=True, improvements=1):
    """Create a mock execution result for testing"""
    from src.core.agent import ExecutionResult
    
    return ExecutionResult(
        success=success,
        output="Mock execution result",
        metrics={
            "duration": 1.5,
            "tokens_used": 150,
            "improvements": improvements
        }
    )


class MockClaudeResponse:
    """Mock Claude API response for testing"""
    
    def __init__(self, success=True, result=None, error=None):
        self.success = success
        self.result = result or "Mock successful result"
        self.error = error
        self.metrics = {
            "tokens": 100,
            "duration": 1.0
        }
    
    def to_dict(self):
        return {
            "status": "success" if self.success else "error",
            "result": self.result,
            "error": self.error,
            "metrics": self.metrics
        }