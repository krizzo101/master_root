#!/usr/bin/env python3
"""
Complex test for V3 server - Designed to trigger task decomposition and multi-execution
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Add libs to path
sys.path.insert(0, '/home/opsvi/master_root/libs')

from opsvi_mcp.servers.claude_code_v3.server import claude_run_v3, get_v3_status
from opsvi_mcp.servers.claude_code_v3.task_decomposer import TaskDecomposer
from opsvi_mcp.servers.claude_code_v3.config import config

async def test_v3_complex():
    """Test V3 with a complex task that should trigger decomposition"""
    
    print("=" * 70)
    print("V3 COMPLEX TEST - Testing Task Decomposition & Multi-Execution")
    print("=" * 70)
    
    # First, let's test the decomposer directly to understand what it does
    print("\n[Phase 1] Testing Task Decomposer Directly")
    print("-" * 50)
    
    decomposer = TaskDecomposer(config)
    
    # Complex task that should trigger decomposition
    complex_task = """Create a complete Python REST API server with the following:
    1. User authentication system with login and registration
    2. Database models for users and posts
    3. CRUD endpoints for managing posts
    4. Input validation and error handling
    5. Comprehensive unit tests for all endpoints
    6. API documentation with examples"""
    
    print(f"Complex Task: {complex_task[:100]}...")
    
    # Check complexity
    complexity = decomposer.estimate_complexity(complex_task)
    print(f"\nComplexity Analysis:")
    print(f"  - Estimated Complexity: {complexity}")
    
    # Map to numeric for comparison
    complexity_map = {'simple': 1, 'moderate': 2, 'complex': 3, 'very_complex': 4}
    complexity_num = complexity_map.get(complexity, 2)
    print(f"  - Numeric Value: {complexity_num}")
    print(f"  - Decomposition Threshold: > 2")
    print(f"  - Will Decompose: {complexity_num > 2}")
    
    # Test decomposition
    if complexity_num > 2:
        subtasks = decomposer.decompose(complex_task)
        print(f"\nDecomposition Results:")
        print(f"  - Number of Subtasks: {len(subtasks)}")
        for i, subtask in enumerate(subtasks, 1):
            task_desc = subtask.description if hasattr(subtask, 'description') else str(subtask)
            is_critical = subtask.critical if hasattr(subtask, 'critical') else False
            print(f"  {i}. {task_desc[:60]}... [Critical: {is_critical}]")
    else:
        print("\n⚠️ Task not complex enough for decomposition!")
    
    # Now test actual V3 execution
    print("\n[Phase 2] Testing V3 Execution with Complex Task")
    print("-" * 50)
    
    # Use FULL_CYCLE mode to trigger all agents
    print("Execution Parameters:")
    print("  - Mode: FULL_CYCLE (triggers all agents)")
    print("  - Quality: high")
    print("  - Expected: Multiple subtask executions")
    
    start_time = datetime.now()
    
    try:
        print("\nStarting V3 execution...")
        print("(This will spawn multiple Claude instances if decomposition triggers)")
        
        result = await claude_run_v3(
            task=complex_task,
            mode="FULL_CYCLE",  # Most comprehensive mode
            auto_detect=False,   # Force our mode choice
            quality_level="high" # Highest quality
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n[Phase 3] Execution Results")
        print("-" * 50)
        print(f"✓ Execution Time: {execution_time:.2f} seconds")
        print(f"✓ Status: {result.get('status', 'unknown')}")
        print(f"✓ Success: {result.get('success', False)}")
        print(f"✓ Mode Used: {result.get('mode', 'unknown')}")
        print(f"✓ Complexity: {result.get('complexity', 'unknown')}")
        
        # Check for subtask execution
        if 'subtasks_executed' in result:
            print(f"\n🔄 SUBTASK EXECUTION DETECTED!")
            print(f"  - Subtasks Executed: {result['subtasks_executed']}")
            print(f"  - Total Subtasks: {result['subtasks_total']}")
            print(f"  - Total Cost: ${result.get('total_cost', 0):.2f}")
            
            # Show individual subtask results
            if 'results' in result and result['results']:
                print(f"\n  Individual Subtask Results:")
                for i, sub_result in enumerate(result['results'], 1):
                    print(f"    {i}. Success: {sub_result.get('success', False)}, "
                          f"Cost: ${sub_result.get('cost', 0):.4f}")
        else:
            print(f"\n⚠️ No subtask execution detected")
            print(f"  - Single execution mode used")
            if result.get('cost'):
                print(f"  - Cost: ${result['cost']:.4f}")
        
        # Check configuration used
        if 'config' in result:
            config_used = result['config']
            print(f"\nConfiguration Used:")
            print(f"  - Quality Threshold: {config_used.get('quality_threshold', 'N/A')}")
            print(f"  - Review Iterations: {config_used.get('review_iterations', 0)}")
            print(f"  - Critic Enabled: {config_used.get('enable_critic', False)}")
            print(f"  - Tester Enabled: {config_used.get('enable_tester', False)}")
            print(f"  - Documenter Enabled: {config_used.get('enable_documenter', False)}")
        
        # Analysis
        print(f"\n[Phase 4] Analysis")
        print("-" * 50)
        
        if 'subtasks_executed' in result and result['subtasks_executed'] > 0:
            print("✅ SUCCESS: V3 performed task decomposition and multi-execution!")
            print(f"   - {result['subtasks_executed']} separate Claude instances were spawned")
            print(f"   - Each handled a portion of the complex task")
            print(f"   - Results were aggregated into final output")
        else:
            print("⚠️ PARTIAL: V3 executed but didn't decompose the task")
            print("   Possible reasons:")
            print("   - Task complexity not high enough")
            print("   - Decomposition disabled in config")
            print("   - Single execution was sufficient")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        print(f"\nTotal Test Time: {(datetime.now() - start_time).total_seconds():.2f} seconds")

async def test_decomposition_only():
    """Test just the decomposition logic without execution"""
    
    print("\n" + "=" * 70)
    print("DECOMPOSITION-ONLY TEST (No Execution)")
    print("=" * 70)
    
    decomposer = TaskDecomposer(config)
    
    # Test various task complexities
    test_tasks = [
        ("Write hello world", "simple"),
        ("Create a function to calculate fibonacci", "moderate"),
        ("Build a REST API with authentication", "complex"),
        ("Create a complete web application with frontend, backend, database, tests, and deployment", "very_complex")
    ]
    
    for task, expected in test_tasks:
        complexity = decomposer.estimate_complexity(task)
        print(f"\nTask: {task[:50]}...")
        print(f"  Expected: {expected}")
        print(f"  Detected: {complexity}")
        
        complexity_num = {'simple': 1, 'moderate': 2, 'complex': 3, 'very_complex': 4}.get(complexity, 0)
        
        if complexity_num > 2:
            subtasks = decomposer.decompose(task)
            print(f"  Decomposed into {len(subtasks)} subtasks:")
            for st in subtasks[:3]:  # Show first 3
                desc = st.description if hasattr(st, 'description') else str(st)
                print(f"    - {desc[:60]}...")

async def main():
    """Main test runner"""
    
    print("V3 COMPLEX TESTING SUITE")
    print("Testing task decomposition and multi-agent execution")
    print()
    
    # Check environment
    print("Environment Check:")
    print(f"  CLAUDE_CODE_TOKEN: {'SET' if os.environ.get('CLAUDE_CODE_TOKEN') else 'NOT SET'}")
    print(f"  Decomposition Enabled: {config.decomposition.enable_decomposition}")
    print()
    
    # First test decomposition logic
    await test_decomposition_only()
    
    # Then test actual execution with complex task
    print("\n" + "=" * 70)
    print("NOW TESTING ACTUAL EXECUTION WITH COMPLEX TASK")
    print("WARNING: This will make real API calls and incur costs!")
    print("=" * 70)
    
    # Add a small delay to let user see the warning
    await asyncio.sleep(2)
    
    result = await test_v3_complex()
    
    # Save results
    if result:
        with open("/tmp/v3_complex_test.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n📄 Full results saved to: /tmp/v3_complex_test.json")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())