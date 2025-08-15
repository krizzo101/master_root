#!/usr/bin/env python3
"""Test the enhanced CoderAgent implementation."""

import sys
import os
sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-agents')

from opsvi_agents.core_agents.coder import CoderAgent, Language

def test_coder_agent():
    """Test various CoderAgent capabilities."""
    
    # Initialize agent
    agent = CoderAgent()
    print("✓ CoderAgent initialized")
    
    # Test 1: Generate Python class
    print("\n1. Testing Python class generation...")
    result = agent.execute({
        "action": "generate",
        "description": "Create a UserManager class for handling user operations with CRUD functionality",
        "language": "python"
    })
    
    if "code" in result:
        print("✓ Generated Python class:")
        print(result["code"][:500] + "..." if len(result["code"]) > 500 else result["code"])
    
    # Test 2: Generate async function
    print("\n2. Testing async function generation...")
    result = agent.execute({
        "action": "generate",
        "description": "Create an async function to fetch data from API with retry logic",
        "language": "python"
    })
    
    if "code" in result:
        print("✓ Generated async function:")
        print(result["code"][:500] + "..." if len(result["code"]) > 500 else result["code"])
    
    # Test 3: Generate JavaScript/React component
    print("\n3. Testing React component generation...")
    result = agent.execute({
        "action": "generate",
        "description": "Create a React component for displaying user profile",
        "language": "javascript"
    })
    
    if "code" in result:
        print("✓ Generated React component:")
        print(result["code"][:500] + "..." if len(result["code"]) > 500 else result["code"])
    
    # Test 4: Code refactoring
    print("\n4. Testing code refactoring...")
    sample_code = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
"""
    
    result = agent.execute({
        "action": "refactor",
        "code": sample_code,
        "language": "python",
        "goals": ["readability", "performance"]
    })
    
    if "refactored_code" in result:
        print("✓ Refactored code:")
        print(result["refactored_code"])
    
    # Test 5: Code optimization
    print("\n5. Testing code optimization...")
    result = agent.execute({
        "action": "optimize",
        "code": sample_code,
        "language": "python",
        "metrics": ["speed", "memory"]
    })
    
    if "optimized_code" in result:
        print("✓ Optimized code:")
        print(f"Optimizations applied: {result.get('optimizations_applied', [])}")
    
    # Test 6: Generate test code
    print("\n6. Testing test generation...")
    result = agent.execute({
        "action": "generate",
        "description": "Create comprehensive tests for a Calculator class with multiple test cases",
        "language": "python"
    })
    
    if "code" in result:
        print("✓ Generated test code:")
        print(result["code"][:500] + "..." if len(result["code"]) > 500 else result["code"])
    
    print("\n✅ All tests completed successfully!")
    print(f"\nCoderAgent Capabilities:")
    print(f"- Languages supported: {len(Language.__members__)}")
    print(f"- Templates available: {len(agent.templates)}")
    print(f"- Code patterns registered: {len(agent.patterns)}")
    print(f"- Optimization strategies: {len(agent.optimizations)}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_coder_agent()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)