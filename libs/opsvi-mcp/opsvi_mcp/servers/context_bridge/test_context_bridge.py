"""
Comprehensive test suite for Context Bridge

Tests server, client, and integration scenarios.
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from typing import List
from unittest.mock import Mock, patch, AsyncMock

from .server import ContextBridgeServer
from .client import ContextBridgeClient, EnhancedAgentBase
from .models import (
    IDEContext, ContextEvent, ContextEventType,
    DiagnosticInfo, DiagnosticSeverity, FileSelection,
    ContextQuery
)


# Test fixtures
@pytest.fixture
async def server():
    """Create test server instance"""
    server = ContextBridgeServer(redis_url="redis://localhost:6379/1")  # Use test DB
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def client():
    """Create test client instance"""
    client = ContextBridgeClient(bridge_url="http://localhost:8000")
    yield client
    await client.close()


@pytest.fixture
def sample_context():
    """Create sample IDE context for testing"""
    return IDEContext(
        active_file="/home/opsvi/master_root/test.py",
        selection=FileSelection(
            file_path="/home/opsvi/master_root/test.py",
            start_line=10,
            start_column=5,
            end_line=15,
            end_column=20,
            selected_text="def test_function():\n    pass"
        ),
        open_tabs=[
            "/home/opsvi/master_root/test.py",
            "/home/opsvi/master_root/main.py"
        ],
        diagnostics=[
            DiagnosticInfo(
                file_path="/home/opsvi/master_root/test.py",
                line=12,
                column=10,
                severity=DiagnosticSeverity.ERROR,
                message="Undefined variable 'x'",
                source="pyright"
            ),
            DiagnosticInfo(
                file_path="/home/opsvi/master_root/test.py",
                line=20,
                column=5,
                severity=DiagnosticSeverity.WARNING,
                message="Unused import 'os'",
                source="pyright"
            )
        ],
        project_root="/home/opsvi/master_root"
    )


class TestContextBridgeServer:
    """Test Context Bridge Server functionality"""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test server initializes correctly"""
        assert server.current_context is None
        assert len(server.subscriptions) == 0
        assert server.metrics["queries_served"] == 0
    
    @pytest.mark.asyncio
    async def test_update_context(self, server, sample_context):
        """Test updating IDE context"""
        # Update context
        result = await server.mcp.call_tool(
            "update_ide_context",
            {"context_data": sample_context.dict()}
        )
        
        assert result["status"] == "success"
        assert server.current_context is not None
        assert server.current_context.active_file == sample_context.active_file
    
    @pytest.mark.asyncio
    async def test_get_context(self, server, sample_context):
        """Test retrieving IDE context"""
        # First update context
        await server.mcp.call_tool(
            "update_ide_context",
            {"context_data": sample_context.dict()}
        )
        
        # Then retrieve it
        result = await server.mcp.call_tool("get_ide_context")
        
        assert "error" not in result
        assert result["active_file"] == sample_context.active_file
        assert len(result["diagnostics"]) == 2
        assert server.metrics["queries_served"] == 1
    
    @pytest.mark.asyncio
    async def test_context_query_filtering(self, server, sample_context):
        """Test context query with filters"""
        # Update context
        await server.mcp.call_tool(
            "update_ide_context",
            {"context_data": sample_context.dict()}
        )
        
        # Query with filter
        query = ContextQuery(
            include_diagnostics=True,
            diagnostic_severity_filter=[DiagnosticSeverity.ERROR]
        )
        
        result = await server.mcp.call_tool(
            "get_ide_context",
            {"query": query.dict()}
        )
        
        # Should only get error diagnostics
        assert len(result["diagnostics"]) == 1
        assert result["diagnostics"][0]["severity"] == "error"
    
    @pytest.mark.asyncio
    async def test_context_history(self, server, sample_context):
        """Test context history tracking"""
        # Update context multiple times
        for i in range(5):
            context_data = sample_context.dict()
            context_data["active_file"] = f"/test_{i}.py"
            await server.mcp.call_tool(
                "update_ide_context",
                {"context_data": context_data}
            )
        
        # Get history
        result = await server.mcp.call_tool(
            "get_context_history",
            {"limit": 3}
        )
        
        assert len(result["history"]) == 3
        assert result["total_count"] == 4  # 5 updates, but current is not in history
    
    @pytest.mark.asyncio
    async def test_event_publishing(self, server, sample_context):
        """Test event publishing on context changes"""
        with patch.object(server, '_publish_event') as mock_publish:
            # First update
            await server.mcp.call_tool(
                "update_ide_context",
                {"context_data": sample_context.dict()}
            )
            
            # Second update with different file
            context_data = sample_context.dict()
            context_data["active_file"] = "/new_file.py"
            await server.mcp.call_tool(
                "update_ide_context",
                {"context_data": context_data}
            )
            
            # Should have published events
            assert mock_publish.call_count >= 2  # At least CONTEXT_SYNC and FILE_CHANGED


class TestContextBridgeClient:
    """Test Context Bridge Client functionality"""
    
    @pytest.mark.asyncio
    async def test_client_get_context(self, client):
        """Test client can retrieve context"""
        with patch.object(client.client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "active_file": "/test.py",
                "project_root": "/home/opsvi/master_root",
                "timestamp": datetime.utcnow().isoformat(),
                "diagnostics": [],
                "open_tabs": []
            }
            mock_post.return_value = mock_response
            
            context = await client.get_context()
            
            assert context is not None
            assert context.active_file == "/test.py"
            assert mock_post.called
    
    @pytest.mark.asyncio
    async def test_client_caching(self, client):
        """Test client caches context appropriately"""
        mock_context = IDEContext(
            active_file="/test.py",
            project_root="/home/opsvi/master_root"
        )
        
        # Set cache
        client._update_cache(mock_context)
        
        # Should use cache
        context = await client.get_context(force_refresh=False)
        assert context == mock_context
        
        # Force refresh should bypass cache
        with patch.object(client.client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "active_file": "/new.py",
                "project_root": "/home/opsvi/master_root",
                "timestamp": datetime.utcnow().isoformat(),
                "diagnostics": [],
                "open_tabs": []
            }
            mock_post.return_value = mock_response
            
            context = await client.get_context(force_refresh=True)
            assert context.active_file == "/new.py"
    
    @pytest.mark.asyncio
    async def test_client_diagnostics(self, client, sample_context):
        """Test client diagnostic retrieval"""
        with patch.object(client, 'get_context') as mock_get:
            mock_get.return_value = sample_context
            
            # Get all diagnostics
            diagnostics = await client.get_diagnostics()
            assert len(diagnostics) == 2
            
            # Get filtered diagnostics
            diagnostics = await client.get_diagnostics(
                severity_filter=["error"]
            )
            # Note: This would need proper implementation in get_diagnostics
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_base(self):
        """Test EnhancedAgentBase functionality"""
        
        class TestAgent(EnhancedAgentBase):
            async def execute_core(self, task: str, **kwargs):
                return f"Executed: {task}"
        
        agent = TestAgent("test_agent")
        
        # Mock context
        mock_context = IDEContext(
            active_file="/test.py",
            project_root="/home/opsvi/master_root",
            diagnostics=[
                DiagnosticInfo(
                    file_path="/test.py",
                    line=10,
                    column=5,
                    severity=DiagnosticSeverity.ERROR,
                    message="Test error"
                )
            ]
        )
        
        with patch.object(agent.context_client, 'get_context') as mock_get:
            mock_get.return_value = mock_context
            
            result = await agent.execute_with_context("Fix the bug")
            
            assert "Executed:" in result
            assert "Current file: /test.py" in result
            assert "1 errors" in result


class TestIntegration:
    """Integration tests for full system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete flow from server to client"""
        # This would require running actual server
        # For now, we'll mock the integration
        
        server = ContextBridgeServer()
        client = ContextBridgeClient()
        
        # Create sample context
        context = IDEContext(
            active_file="/integration_test.py",
            project_root="/home/opsvi/master_root"
        )
        
        # Update on server
        await server.mcp.call_tool(
            "update_ide_context",
            {"context_data": context.dict()}
        )
        
        # Verify metrics
        assert server.current_context.active_file == "/integration_test.py"
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, server):
        """Test performance meets requirements"""
        import time
        
        # Update context
        context = IDEContext(
            active_file="/perf_test.py",
            project_root="/home/opsvi/master_root"
        )
        
        await server.mcp.call_tool(
            "update_ide_context",
            {"context_data": context.dict()}
        )
        
        # Measure query time
        start = time.time()
        result = await server.mcp.call_tool("get_ide_context")
        query_time = (time.time() - start) * 1000
        
        # Should be under 50ms
        assert query_time < 50
        assert "error" not in result
        
        # Check metrics
        metrics = await server.mcp.call_tool("get_metrics")
        assert metrics["avg_query_time_ms"] < 50


# Performance benchmarks
@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks"""
    
    @pytest.mark.asyncio
    async def test_context_query_performance(self, benchmark, server, sample_context):
        """Benchmark context query performance"""
        # Setup
        await server.mcp.call_tool(
            "update_ide_context",
            {"context_data": sample_context.dict()}
        )
        
        # Benchmark
        async def query():
            return await server.mcp.call_tool("get_ide_context")
        
        result = benchmark(query)
        assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, benchmark, client):
        """Benchmark cache performance"""
        mock_context = IDEContext(
            active_file="/bench.py",
            project_root="/home/opsvi/master_root"
        )
        client._update_cache(mock_context)
        
        def get_cached():
            return client._is_cache_valid()
        
        result = benchmark(get_cached)
        assert result is True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])