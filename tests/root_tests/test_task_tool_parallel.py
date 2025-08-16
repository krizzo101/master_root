#!/usr/bin/env python3
"""
Test if we can leverage Claude's built-in Task tool for true parallelism
"""
import time
import subprocess
import json

def test_task_tool_parallel():
    """Test parallel execution using Claude's built-in Task tool"""
    print("=== Testing Parallel Execution via Task Tool ===")
    
    # Create a prompt that uses the Task tool to spawn multiple agents
    prompt = """
    Use the Task tool to spawn 3 parallel agents with these tasks:
    1. Agent 1: Write "TASK1_COMPLETE" 
    2. Agent 2: Write "TASK2_COMPLETE"
    3. Agent 3: Write "TASK3_COMPLETE"
    
    Execute them simultaneously and report back when all complete.
    """
    
    start_time = time.time()
    
    # Execute via Claude CLI with the Task tool request
    cmd = [
        'claude',
        '--dangerously-skip-permissions',
        '-p', prompt
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    elapsed = time.time() - start_time
    
    print(f"Total execution time: {elapsed:.2f}s")
    print(f"Output preview: {result.stdout[:500]}...")
    
    if elapsed < 20:  # Should be much faster if truly parallel
        print("✅ LIKELY PARALLEL: Task tool completed quickly")
    else:
        print("❌ LIKELY SERIAL: Task tool took too long")
    
    return elapsed

if __name__ == "__main__":
    test_task_tool_parallel()