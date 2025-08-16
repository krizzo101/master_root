#!/usr/bin/env python3
"""
Integration test for Context Bridge system

Tests the complete flow from IDE context to agent execution with knowledge.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from opsvi_mcp.servers.context_bridge import (
    ContextBridgeServer,
    ContextBridgeClient,
    EnhancedAgentBase,
    KnowledgeAggregator,
    IDEContext,
    DiagnosticInfo,
    DiagnosticSeverity,
    FileSelection,
)


class TestAgent(EnhancedAgentBase):
    """Test agent for integration testing"""
    
    def __init__(self):
        super().__init__("test_agent")
        self.executed_tasks = []
    
    async def execute_core(self, task: str, **kwargs):
        """Execute test task"""
        self.executed_tasks.append(task)
        
        result = {
            "task": task,
            "context_available": self.current_context is not None,
            "active_file": None,
            "diagnostics_count": 0,
        }
        
        if self.current_context:
            result["active_file"] = self.current_context.active_file
            result["diagnostics_count"] = len(self.current_context.diagnostics)
        
        return result


async def test_full_integration():
    """Test the complete Context Bridge integration"""
    
    print("🧪 Context Bridge Integration Test\n")
    print("=" * 50)
    
    # 1. Initialize components
    print("\n1. Initializing components...")
    
    server = ContextBridgeServer(redis_url="redis://localhost:6379/15")  # Use test DB
    await server.start()
    print("   ✓ Server started")
    
    client = ContextBridgeClient()
    print("   ✓ Client created")
    
    agent = TestAgent()
    print("   ✓ Test agent created")
    
    aggregator = KnowledgeAggregator()
    print("   ✓ Knowledge aggregator created")
    
    # 2. Create test context
    print("\n2. Creating test IDE context...")
    
    test_context = IDEContext(
        active_file="/home/opsvi/master_root/test_file.py",
        selection=FileSelection(
            file_path="/home/opsvi/master_root/test_file.py",
            start_line=10,
            start_column=0,
            end_line=15,
            end_column=0,
            selected_text="def process():\n    pass"
        ),
        diagnostics=[
            DiagnosticInfo(
                file_path="/home/opsvi/master_root/test_file.py",
                line=12,
                column=5,
                severity=DiagnosticSeverity.ERROR,
                message="undefined variable 'result'"
            ),
            DiagnosticInfo(
                file_path="/home/opsvi/master_root/test_file.py",
                line=20,
                column=0,
                severity=DiagnosticSeverity.WARNING,
                message="unused import 'sys'"
            )
        ],
        project_root="/home/opsvi/master_root",
        open_tabs=[
            "/home/opsvi/master_root/test_file.py",
            "/home/opsvi/master_root/main.py"
        ]
    )
    
    # 3. Update server context
    print("\n3. Updating server context...")
    
    update_result = await server.mcp.call_tool(
        "update_ide_context",
        {"context_data": test_context.dict()}
    )
    
    assert update_result["status"] == "success", "Failed to update context"
    print(f"   ✓ Context updated: {update_result['message']}")
    
    # 4. Retrieve context via client
    print("\n4. Testing context retrieval...")
    
    retrieved_context = await client.get_context()
    assert retrieved_context is not None, "Failed to retrieve context"
    assert retrieved_context.active_file == test_context.active_file
    print(f"   ✓ Retrieved active file: {retrieved_context.active_file}")
    print(f"   ✓ Diagnostics count: {len(retrieved_context.diagnostics)}")
    
    # 5. Test agent with context
    print("\n5. Testing enhanced agent...")
    
    agent.current_context = retrieved_context
    result = await agent.execute_core("Fix the undefined variable error")
    
    assert result["context_available"] == True
    assert result["active_file"] == test_context.active_file
    assert result["diagnostics_count"] == 2
    print(f"   ✓ Agent executed with context")
    print(f"   ✓ Active file: {result['active_file']}")
    print(f"   ✓ Diagnostics: {result['diagnostics_count']}")
    
    # 6. Test knowledge aggregator
    print("\n6. Testing knowledge aggregator...")
    
    knowledge_result = await aggregator.mcp.call_tool(
        "query_knowledge",
        {
            "request": {
                "query": "undefined variable error Python",
                "limit": 5
            }
        }
    )
    
    assert "sources" in knowledge_result
    print(f"   ✓ Knowledge query executed")
    print(f"   ✓ Sources found: {len(knowledge_result['sources'])}")
    
    # 7. Test metrics
    print("\n7. Testing metrics...")
    
    metrics = await server.mcp.call_tool("get_metrics")
    
    assert metrics["queries_served"] > 0
    print(f"   ✓ Queries served: {metrics['queries_served']}")
    print(f"   ✓ Avg query time: {metrics['avg_query_time_ms']:.2f}ms")
    
    # 8. Test context history
    print("\n8. Testing context history...")
    
    # Update context again to create history
    test_context.active_file = "/home/opsvi/master_root/updated_file.py"
    await server.mcp.call_tool(
        "update_ide_context",
        {"context_data": test_context.dict()}
    )
    
    history = await server.mcp.call_tool("get_context_history", {"limit": 5})
    
    assert len(history["history"]) > 0
    print(f"   ✓ History entries: {len(history['history'])}")
    
    # 9. Performance check
    print("\n9. Performance verification...")
    
    import time
    
    # Test context query performance
    start = time.time()
    for _ in range(10):
        await server.mcp.call_tool("get_ide_context")
    avg_time = (time.time() - start) / 10 * 1000
    
    assert avg_time < 50, f"Context query too slow: {avg_time:.2f}ms"
    print(f"   ✓ Avg context query time: {avg_time:.2f}ms (< 50ms target)")
    
    # Cleanup
    await server.stop()
    await client.close()
    
    print("\n" + "=" * 50)
    print("✅ All integration tests passed!")
    print("\nContext Bridge system is fully operational:")
    print("  • Server: ✓")
    print("  • Client: ✓")
    print("  • Agent enhancement: ✓")
    print("  • Knowledge aggregation: ✓")
    print("  • Performance targets met: ✓")
    
    return True


async def main():
    """Run integration test"""
    try:
        success = await test_full_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())