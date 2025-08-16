"""
Tests for Claude Code MCP Server
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from opsvi_mcp.servers.claude_code import (
    ClaudeCodeServer,
    JobManager,
    RecursionManager,
)
from opsvi_mcp.servers.claude_code.models import (
    JobStatus,
)


class TestJobManager:
    """Test JobManager functionality"""

    def test_create_job(self):
        """Test job creation"""
        manager = JobManager()

        job = manager.create_job(
            task="Test task",
            cwd="/tmp",
            output_format="json",
            permission_mode="bypassPermissions",
        )

        assert job.id is not None
        assert job.task == "Test task"
        assert job.cwd == "/tmp"
        assert job.status == JobStatus.RUNNING
        assert job.id in manager.active_jobs

    def test_job_lifecycle(self):
        """Test job state transitions"""
        manager = JobManager()

        job = manager.create_job(task="Test task")
        assert job.id in manager.active_jobs

        # Simulate completion
        manager._handle_job_success(job, '{"result": "success"}')
        assert job.id not in manager.active_jobs
        assert job.id in manager.completed_jobs
        assert job.status == JobStatus.COMPLETED

    def test_get_job_status(self):
        """Test getting job status"""
        manager = JobManager()

        job = manager.create_job(task="Test task")
        status = manager.get_job_status(job.id)

        assert status is not None
        assert status["jobId"] == job.id
        assert status["status"] == "running"
        assert status["task"] == "Test task"

    def test_list_jobs(self):
        """Test listing all jobs"""
        manager = JobManager()

        # Create multiple jobs
        job1 = manager.create_job(task="Task 1")
        job2 = manager.create_job(task="Task 2")

        jobs = manager.list_jobs()
        assert len(jobs) >= 2

        job_ids = [j["jobId"] for j in jobs]
        assert job1.id in job_ids
        assert job2.id in job_ids


class TestRecursionManager:
    """Test RecursionManager functionality"""

    def test_create_recursion_context(self):
        """Test creating recursion context"""
        manager = RecursionManager()

        context = manager.create_recursion_context(job_id="job1", task="Test task")

        assert context.job_id == "job1"
        assert context.depth == 0
        assert context.root_job_id == "job1"
        assert not context.is_recursive

    def test_nested_recursion(self):
        """Test nested recursion contexts"""
        manager = RecursionManager()

        # Create root context
        context1 = manager.create_recursion_context(job_id="job1", task="Root task")

        # Create child context
        context2 = manager.create_recursion_context(
            job_id="job2", parent_job_id="job1", task="Child task"
        )

        assert context2.depth == 1
        assert context2.root_job_id == "job1"
        assert context2.is_recursive
        assert "job1" in context2.call_stack

    def test_recursion_limits(self):
        """Test recursion limit enforcement"""
        manager = RecursionManager()

        # Create contexts up to the limit
        job_ids = []
        parent_id = None

        # Assuming default max_depth is 3
        for i in range(3):
            job_id = f"job{i}"
            context = manager.create_recursion_context(
                job_id=job_id, parent_job_id=parent_id, task=f"Task {i}"
            )
            job_ids.append(job_id)
            parent_id = job_id

        # Try to exceed the limit
        with pytest.raises(ValueError, match="Recursion depth limit exceeded"):
            manager.create_recursion_context(
                job_id="job_too_deep", parent_job_id=parent_id, task="Too deep"
            )

    def test_cleanup(self):
        """Test context cleanup"""
        manager = RecursionManager()

        context = manager.create_recursion_context(job_id="job1", task="Test task")

        assert "job1" in manager.recursion_contexts

        manager.cleanup_job("job1")

        assert "job1" not in manager.recursion_contexts
        assert manager.depth_counts.get(0, 0) == 0


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality"""

    def test_create_metrics(self):
        """Test creating performance metrics"""
        from opsvi_mcp.servers.claude_code.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()
        metrics = monitor.create_metrics("job1")

        assert metrics.job_id == "job1"
        assert metrics.start_time is not None
        assert metrics.error_count == 0

    def test_update_metrics(self):
        """Test updating metrics"""
        from opsvi_mcp.servers.claude_code.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()
        metrics = monitor.create_metrics("job1")

        monitor.update_metrics("job1", "spawned")
        assert metrics.spawn_time is not None
        assert metrics.spawn_delay is not None

        monitor.update_metrics("job1", "first_output")
        assert metrics.first_output_time is not None

        monitor.update_metrics("job1", "completed")
        assert metrics.completion_time is not None
        assert metrics.total_duration is not None


@pytest.mark.asyncio
class TestClaudeCodeServer:
    """Test ClaudeCodeServer MCP functionality"""

    async def test_server_initialization(self):
        """Test server initialization"""
        server = ClaudeCodeServer()
        assert server.server is not None
        assert server.job_manager is not None

    @patch("subprocess.Popen")
    async def test_handle_claude_run(self, mock_popen):
        """Test synchronous Claude run"""
        # Mock subprocess
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('{"result": "success"}', "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        server = ClaudeCodeServer()

        result = await server.handle_claude_run({"task": "Test task"})

        assert result is not None
        # Result should contain content
        assert hasattr(result, "content") or hasattr(result, "error")

    async def test_handle_claude_run_async(self):
        """Test asynchronous Claude run"""
        server = ClaudeCodeServer()

        with patch.object(server.job_manager, "execute_job_async"):
            result = await server.handle_claude_run_async({"task": "Test task"})

            assert result is not None
            # Should return job ID
            if hasattr(result, "content"):
                content = result.content[0].text
                data = json.loads(content)
                assert "jobId" in data
                assert data["status"] == "started"

    async def test_handle_claude_status(self):
        """Test checking job status"""
        server = ClaudeCodeServer()

        # Create a job first
        job = server.job_manager.create_job(task="Test task")

        result = await server.handle_claude_status({"jobId": job.id})

        assert result is not None
        if hasattr(result, "content"):
            content = result.content[0].text
            data = json.loads(content)
            assert data["jobId"] == job.id
            assert data["status"] == "running"

    async def test_handle_claude_list_jobs(self):
        """Test listing jobs"""
        server = ClaudeCodeServer()

        # Create some jobs
        job1 = server.job_manager.create_job(task="Task 1")
        job2 = server.job_manager.create_job(task="Task 2")

        result = await server.handle_claude_list_jobs({})

        assert result is not None
        if hasattr(result, "content"):
            content = result.content[0].text
            jobs = json.loads(content)
            assert isinstance(jobs, list)
            assert len(jobs) >= 2

    async def test_handle_claude_dashboard(self):
        """Test getting dashboard data"""
        server = ClaudeCodeServer()

        result = await server.handle_claude_dashboard({})

        assert result is not None
        if hasattr(result, "content"):
            content = result.content[0].text
            data = json.loads(content)
            assert "activeJobs" in data
            assert "completedJobs" in data
            assert "recursionStats" in data

    async def test_handle_claude_recursion_stats(self):
        """Test getting recursion statistics"""
        server = ClaudeCodeServer()

        result = await server.handle_claude_recursion_stats({})

        assert result is not None
        if hasattr(result, "content"):
            content = result.content[0].text
            stats = json.loads(content)
            assert "max_depth" in stats
            assert "depth_counts" in stats
            assert "active_contexts" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
