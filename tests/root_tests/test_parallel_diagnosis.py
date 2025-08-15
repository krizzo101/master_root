#!/usr/bin/env python3
"""
Diagnostic test to determine where parallel execution is being blocked.
"""

import asyncio
import subprocess
import time
from datetime import datetime
import os

async def test_subprocess_parallel():
    """Test if we can run multiple subprocesses in parallel"""
    print("\n=== TEST 1: Raw Subprocess Parallelism ===")
    print("Running 3 simple echo commands in parallel...")
    
    async def run_echo(n):
        start = time.time()
        proc = await asyncio.create_subprocess_exec(
            'bash', '-c', f'echo "Process {n} started"; sleep 2; echo "Process {n} done"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        elapsed = time.time() - start
        return n, elapsed, stdout.decode()
    
    start_time = time.time()
    results = await asyncio.gather(
        run_echo(1),
        run_echo(2),
        run_echo(3)
    )
    total_time = time.time() - start_time
    
    print(f"Total time: {total_time:.2f}s")
    for n, elapsed, output in results:
        print(f"  Process {n}: {elapsed:.2f}s")
    
    if total_time < 4:  # Should be ~2s if parallel
        print("✅ PARALLEL: Subprocesses ran in parallel")
    else:
        print("❌ SERIAL: Subprocesses ran sequentially")
    
    return total_time < 4


async def test_claude_cli_multiple():
    """Test if multiple Claude CLI instances can run in parallel"""
    print("\n=== TEST 2: Multiple Claude CLI Instances ===")
    print("Attempting to run 3 Claude CLI processes...")
    
    async def run_claude(n):
        start = time.time()
        cmd = ['claude', '--version']  # Quick command that doesn't need auth
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            elapsed = time.time() - start
            success = proc.returncode == 0
            return n, elapsed, success, stdout.decode() if stdout else stderr.decode()
        except Exception as e:
            elapsed = time.time() - start
            return n, elapsed, False, str(e)
    
    start_time = time.time()
    results = await asyncio.gather(
        run_claude(1),
        run_claude(2),
        run_claude(3)
    )
    total_time = time.time() - start_time
    
    print(f"Total time: {total_time:.2f}s")
    for n, elapsed, success, output in results:
        status = "✓" if success else "✗"
        print(f"  Claude {n}: {elapsed:.2f}s [{status}] - {output[:50]}")
    
    # Check if they ran in parallel
    max_individual = max(r[1] for r in results)
    if total_time < (sum(r[1] for r in results) * 0.7):  # Allow some overhead
        print("✅ PARALLEL: Claude CLI instances can run in parallel")
        return True
    else:
        print("❌ SERIAL: Claude CLI instances appear to be serialized")
        return False


async def test_claude_with_tasks():
    """Test if Claude task execution can be parallel"""
    print("\n=== TEST 3: Claude Task Execution ===")
    print("Running 3 simple Claude tasks...")
    
    async def run_task(n):
        start = time.time()
        cmd = [
            'claude',
            '--dangerously-skip-permissions',
            '-p', f'echo "Task {n}"'
        ]
        
        env = os.environ.copy()
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            stdout, stderr = await proc.communicate()
            elapsed = time.time() - start
            success = proc.returncode == 0
            return n, elapsed, success
        except Exception as e:
            elapsed = time.time() - start
            return n, elapsed, False
    
    start_time = time.time()
    results = await asyncio.gather(
        run_task(1),
        run_task(2),
        run_task(3)
    )
    total_time = time.time() - start_time
    
    print(f"Total time: {total_time:.2f}s")
    for n, elapsed, success in results:
        status = "✓" if success else "✗"
        print(f"  Task {n}: {elapsed:.2f}s [{status}]")
    
    # Analyze parallelism
    max_individual = max(r[1] for r in results)
    sum_individual = sum(r[1] for r in results)
    
    print(f"\nAnalysis:")
    print(f"  Sum of individual times: {sum_individual:.2f}s")
    print(f"  Max individual time: {max_individual:.2f}s")
    print(f"  Actual total time: {total_time:.2f}s")
    print(f"  Parallelism ratio: {sum_individual/total_time:.2f}x")
    
    if total_time < (sum_individual * 0.6):
        print("✅ PARALLEL: Tasks executed in parallel")
        return True
    else:
        print("❌ SERIAL: Tasks executed sequentially")
        return False


def check_system_resources():
    """Check system resources that might affect parallelism"""
    print("\n=== System Resource Check ===")
    
    # Check CPU cores
    cpu_count = os.cpu_count()
    print(f"CPU cores available: {cpu_count}")
    
    # Check ulimits
    try:
        result = subprocess.run(['ulimit', '-n'], shell=True, capture_output=True, text=True)
        print(f"File descriptor limit: {result.stdout.strip()}")
    except:
        pass
    
    try:
        result = subprocess.run(['ulimit', '-u'], shell=True, capture_output=True, text=True)
        print(f"Process limit: {result.stdout.strip()}")
    except:
        pass
    
    # Check for Claude process locks
    try:
        result = subprocess.run(['pgrep', '-f', 'claude'], capture_output=True, text=True)
        claude_procs = result.stdout.strip().split('\n') if result.stdout.strip() else []
        print(f"Currently running Claude processes: {len(claude_procs)}")
        if claude_procs:
            for pid in claude_procs[:5]:  # Show first 5
                print(f"  PID: {pid}")
    except:
        pass


async def test_mcp_batch_timing():
    """Analyze the actual MCP batch execution timing"""
    print("\n=== TEST 4: MCP Batch Timing Analysis ===")
    print("Testing via MCP server (if available)...")
    
    # This would need to import and use the actual MCP client
    # For now, we'll just print instructions
    print("To test via MCP:")
    print("1. Submit a batch of 3 identical simple tasks")
    print("2. Record individual start/end times")
    print("3. Compare total time vs max individual time")
    print("4. If total ≈ max individual → parallel")
    print("5. If total ≈ sum of individuals → serial")


async def main():
    print("=" * 60)
    print("PARALLEL EXECUTION DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Check system first
    check_system_resources()
    
    # Run tests
    test1 = await test_subprocess_parallel()
    test2 = await test_claude_cli_multiple()
    test3 = await test_claude_with_tasks()
    await test_mcp_batch_timing()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    if test1 and not test2:
        print("🔍 ISSUE: System can parallelize but Claude CLI cannot")
        print("   → Likely: Claude CLI has internal locking/mutex")
        print("   → Solution: Need process pool or separate conda envs")
    elif test1 and test2 and not test3:
        print("🔍 ISSUE: Claude CLI can parallelize but tasks cannot")
        print("   → Likely: API rate limiting or token constraints")
        print("   → Solution: Check API limits, use different tokens")
    elif not test1:
        print("🔍 ISSUE: System-level parallelization problem")
        print("   → Likely: Resource limits or Python GIL issues")
        print("   → Solution: Check ulimits, use multiprocessing")
    else:
        print("✅ All tests passed - parallelization should work!")
    
    print("\nRecommended next steps:")
    print("1. Check Claude CLI logs for mutex/lock messages")
    print("2. Monitor system resources during batch execution")
    print("3. Test with process pool instead of asyncio")
    print("4. Try different CLAUDE_CODE_TOKEN values per instance")


if __name__ == "__main__":
    asyncio.run(main())