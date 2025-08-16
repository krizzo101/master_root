#!/usr/bin/env python3
"""
Comprehensive test of the knowledge system to verify all components work.
"""

import json
import subprocess
import time
from neo4j import GraphDatabase

# Neo4j connection
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

def test_mcp_tools_available():
    """Test if MCP tools are properly registered."""
    print("\n1️⃣ Testing MCP Tool Availability...")
    print("-" * 40)
    
    # Test the server can start
    process = subprocess.Popen(
        ["/home/opsvi/miniconda/bin/python", "-m", "apps.knowledge_system"],
        env={"PYTHONPATH": "/home/opsvi/master_root"},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send initialize request
    initialize_request = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }) + "\n"
    
    try:
        stdout, stderr = process.communicate(input=initialize_request, timeout=3)
        if "knowledge-system" in stderr or "knowledge-system" in stdout:
            print("✅ MCP server starts correctly")
            return True
        else:
            print("❌ MCP server failed to start")
            return False
    except:
        process.kill()
        print("❌ MCP server timeout")
        return False
    finally:
        if process.poll() is None:
            process.kill()


def test_knowledge_storage():
    """Test storing knowledge with complex objects."""
    print("\n2️⃣ Testing Knowledge Storage...")
    print("-" * 40)
    
    from apps.knowledge_system.mcp_knowledge_tools import KnowledgeStoreTool
    
    result = KnowledgeStoreTool.execute(
        knowledge_type="TEST_VERIFICATION",
        content="Comprehensive system test entry",
        context={
            "test_time": time.time(),
            "nested": {"data": "structure", "works": True},
            "list": [1, 2, 3]
        },
        tags=["test", "verification"],
        confidence_score=1.0
    )
    
    # Execute in Neo4j
    with driver.session() as session:
        record = session.run(result["query"], **result["params"])
        stored = list(record)
        
        if stored:
            print(f"✅ Stored knowledge with ID: {result['knowledge_id']}")
            return result['knowledge_id']
        else:
            print("❌ Failed to store knowledge")
            return None


def test_knowledge_retrieval(knowledge_id):
    """Test retrieving knowledge."""
    print("\n3️⃣ Testing Knowledge Retrieval...")
    print("-" * 40)
    
    from apps.knowledge_system.mcp_knowledge_tools import KnowledgeQueryTool
    
    result = KnowledgeQueryTool.execute(
        query_type="search",
        query_text="Comprehensive system test",
        limit=5
    )
    
    with driver.session() as session:
        records = session.run(result["query"], **result["params"])
        found = list(records)
        
        if found:
            print(f"✅ Found {len(found)} matching entries")
            for record in found[:2]:
                k = record['k']
                print(f"   - {k.get('knowledge_type')}: {k.get('content')[:50]}...")
            return True
        else:
            print("❌ No entries found")
            return False


def test_embeddings():
    """Test if embeddings are working."""
    print("\n4️⃣ Testing Embeddings...")
    print("-" * 40)
    
    with driver.session() as session:
        result = session.run("""
            MATCH (k:Knowledge)
            WHERE k.embedding IS NOT NULL
            RETURN count(k) as count
        """)
        count = list(result)[0]['count']
        
        if count > 0:
            print(f"✅ Found {count} entries with embeddings")
            
            # Test vector search
            result = session.run("""
                SHOW INDEXES WHERE name = 'knowledge_embeddings'
            """)
            indexes = list(result)
            if indexes:
                print("✅ Vector index is active")
                return True
            else:
                print("⚠️ Vector index not found")
                return False
        else:
            print("⚠️ No embeddings found (run generate_embeddings.py)")
            return False


def test_cross_agent_knowledge():
    """Test if knowledge from other agents is accessible."""
    print("\n5️⃣ Testing Cross-Agent Knowledge Sharing...")
    print("-" * 40)
    
    with driver.session() as session:
        # Check for knowledge from different sessions/agents
        result = session.run("""
            MATCH (k:Knowledge)
            RETURN DISTINCT k.knowledge_type as type, count(k) as count
            ORDER BY count DESC
        """)
        
        types = list(result)
        if len(types) > 1:
            print(f"✅ Found {len(types)} different knowledge types:")
            for t in types:
                print(f"   - {t['type']}: {t['count']} entries")
            return True
        else:
            print("⚠️ Limited knowledge diversity")
            return False


def main():
    print("=" * 50)
    print("KNOWLEDGE SYSTEM COMPREHENSIVE TEST")
    print("=" * 50)
    
    results = []
    
    # Run all tests
    results.append(("MCP Tools", test_mcp_tools_available()))
    
    # Store test knowledge
    test_id = test_knowledge_storage()
    results.append(("Storage", test_id is not None))
    
    # Test retrieval
    if test_id:
        results.append(("Retrieval", test_knowledge_retrieval(test_id)))
    else:
        results.append(("Retrieval", False))
    
    results.append(("Embeddings", test_embeddings()))
    results.append(("Cross-Agent", test_cross_agent_knowledge()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:15} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Knowledge system is fully operational.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    driver.close()


if __name__ == "__main__":
    main()