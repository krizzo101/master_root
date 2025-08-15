#!/usr/bin/env python3
"""
Test multiple Claude tokens to see if they work independently and in parallel
"""
import asyncio
import os
import time
from datetime import datetime
import subprocess
# Load tokens from environment or .env file
def load_tokens():
    """Load tokens from environment or .env file"""
    import os
    
    # First check environment
    token1 = os.getenv('CLAUDE_CODE_TOKEN')
    token2 = os.getenv('CLAUDE_CODE_TOKEN1')
    
    # If not in environment, try to load from .env file
    if not token1 or not token2:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key == 'CLAUDE_CODE_TOKEN' and not token1:
                            token1 = value.strip('"').strip("'")
                        elif key == 'CLAUDE_CODE_TOKEN1' and not token2:
                            token2 = value.strip('"').strip("'")
        except FileNotFoundError:
            pass
    
    return token1, token2

# Load tokens at module level
TOKEN1, TOKEN2 = load_tokens()

async def test_token(token_name: str, token_value: str, task_num: int):
    """Test a single token with a simple task"""
    start = time.time()
    
    # Create environment with specific token
    env = os.environ.copy()
    env['CLAUDE_CODE_TOKEN'] = token_value
    
    cmd = [
        'claude',
        '--dangerously-skip-permissions',
        '-p', f'Just say "Token {task_num} works!" and nothing else'
    ]
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = await proc.communicate()
        elapsed = time.time() - start
        
        if proc.returncode == 0:
            # Check if response contains expected message
            output = stdout.decode()
            if "works" in output.lower():
                return {
                    "token_name": token_name,
                    "task_num": task_num,
                    "status": "SUCCESS",
                    "elapsed": elapsed,
                    "timestamp": datetime.now().isoformat(),
                    "output_preview": output[:100].replace('\n', ' ')
                }
            else:
                return {
                    "token_name": token_name,
                    "task_num": task_num,
                    "status": "UNEXPECTED_OUTPUT",
                    "elapsed": elapsed,
                    "timestamp": datetime.now().isoformat(),
                    "output_preview": output[:100].replace('\n', ' ')
                }
        else:
            error = stderr.decode()
            return {
                "token_name": token_name,
                "task_num": task_num,
                "status": "FAILED",
                "elapsed": elapsed,
                "timestamp": datetime.now().isoformat(),
                "error": error[:200]
            }
    except Exception as e:
        return {
            "token_name": token_name,
            "task_num": task_num,
            "status": "ERROR",
            "elapsed": time.time() - start,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


async def test_sequential():
    """Test tokens one at a time"""
    print("\n" + "="*60)
    print("TEST 1: SEQUENTIAL TOKEN TESTING")
    print("="*60)
    
    # Get tokens
    token1 = TOKEN1
    token2 = TOKEN2
    
    if not token1:
        print("❌ CLAUDE_CODE_TOKEN not found in environment")
        return False
        
    if not token2:
        print("❌ CLAUDE_CODE_TOKEN1 not found in environment")
        return False
    
    print(f"Token 1 (original): {token1[:20]}...")
    print(f"Token 2 (new):      {token2[:20]}...")
    
    # Test original token
    print("\nTesting original token (CLAUDE_CODE_TOKEN)...")
    result1 = await test_token("CLAUDE_CODE_TOKEN", token1, 1)
    print(f"  Status: {result1['status']}")
    print(f"  Time: {result1['elapsed']:.2f}s")
    if result1['status'] == 'SUCCESS':
        print(f"  Output: {result1['output_preview']}")
    else:
        print(f"  Error: {result1.get('error', 'Unknown error')}")
    
    # Test new token
    print("\nTesting new token (CLAUDE_CODE_TOKEN1)...")
    result2 = await test_token("CLAUDE_CODE_TOKEN1", token2, 2)
    print(f"  Status: {result2['status']}")
    print(f"  Time: {result2['elapsed']:.2f}s")
    if result2['status'] == 'SUCCESS':
        print(f"  Output: {result2['output_preview']}")
    else:
        print(f"  Error: {result2.get('error', 'Unknown error')}")
    
    # Analysis
    print("\n" + "-"*40)
    if result1['status'] == 'SUCCESS' and result2['status'] == 'SUCCESS':
        print("✅ BOTH TOKENS WORK INDEPENDENTLY")
        return True
    elif result1['status'] == 'SUCCESS' and result2['status'] != 'SUCCESS':
        print("⚠️ Original token works but new token failed")
        print("   → New token might be invalid or not activated")
        return False
    elif result1['status'] != 'SUCCESS' and result2['status'] == 'SUCCESS':
        print("⚠️ New token works but original token failed")
        print("   → Creating new token might have invalidated the old one")
        return False
    else:
        print("❌ BOTH TOKENS FAILED")
        return False


async def test_parallel():
    """Test tokens running simultaneously"""
    print("\n" + "="*60)
    print("TEST 2: PARALLEL TOKEN EXECUTION")
    print("="*60)
    
    # Get tokens
    token1 = TOKEN1
    token2 = TOKEN2
    
    if not token1 or not token2:
        print("❌ Missing required tokens")
        return False
    
    print("Launching 4 tasks (2 per token) simultaneously...")
    print(f"  Tasks 1&3: Using original token")
    print(f"  Tasks 2&4: Using new token")
    
    start_time = time.time()
    
    # Launch 4 tasks in parallel - 2 per token
    results = await asyncio.gather(
        test_token("TOKEN_1", token1, 1),
        test_token("TOKEN_2", token2, 2),
        test_token("TOKEN_1", token1, 3),
        test_token("TOKEN_2", token2, 4),
        return_exceptions=True
    )
    
    total_time = time.time() - start_time
    
    # Display results
    print(f"\nTotal execution time: {total_time:.2f}s")
    print("\nIndividual results:")
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  Task {i}: EXCEPTION - {str(result)}")
        else:
            print(f"  Task {i}: {result['status']} - {result['elapsed']:.2f}s - Token: {result['token_name']}")
    
    # Analysis
    successful = [r for r in results if not isinstance(r, Exception) and r['status'] == 'SUCCESS']
    print("\n" + "-"*40)
    print(f"Success rate: {len(successful)}/{len(results)}")
    
    if len(successful) == 4:
        # Check if truly parallel
        max_time = max(r['elapsed'] for r in successful)
        sum_time = sum(r['elapsed'] for r in successful)
        parallelism_ratio = sum_time / total_time
        
        print(f"Parallelism ratio: {parallelism_ratio:.2f}x")
        print(f"  (Sum of individual times: {sum_time:.2f}s / Total time: {total_time:.2f}s)")
        
        if parallelism_ratio > 1.5:
            print("✅ TRUE PARALLEL EXECUTION ACHIEVED!")
            print("   → Multiple tokens enable real parallelism")
            return True
        else:
            print("⚠️ Still mostly sequential despite multiple tokens")
            print("   → Might be system-level or API-level limiting")
            return False
    else:
        print("❌ Some tasks failed - cannot confirm parallelism")
        return False


async def test_stress():
    """Stress test with many parallel requests"""
    print("\n" + "="*60)
    print("TEST 3: STRESS TEST (10 tasks, alternating tokens)")
    print("="*60)
    
    token1 = os.getenv('CLAUDE_CODE_TOKEN')
    token2 = os.getenv('CLAUDE_CODE_TOKEN1')
    
    if not token1 or not token2:
        print("❌ Missing required tokens")
        return
    
    print("Launching 10 tasks with alternating tokens...")
    
    start_time = time.time()
    
    # Create 10 tasks alternating between tokens
    tasks = []
    for i in range(10):
        token = token1 if i % 2 == 0 else token2
        token_name = "TOKEN_1" if i % 2 == 0 else "TOKEN_2"
        tasks.append(test_token(token_name, token, i+1))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if not isinstance(r, Exception) and r['status'] == 'SUCCESS']
    token1_success = len([r for r in successful if r['token_name'] == 'TOKEN_1'])
    token2_success = len([r for r in successful if r['token_name'] == 'TOKEN_2'])
    
    print(f"\nCompleted in {total_time:.2f}s")
    print(f"Success rate: {len(successful)}/10")
    print(f"  Token 1: {token1_success}/5 successful")
    print(f"  Token 2: {token2_success}/5 successful")
    
    if len(successful) > 0:
        avg_time = sum(r['elapsed'] for r in successful) / len(successful)
        print(f"Average task time: {avg_time:.2f}s")
        print(f"Theoretical sequential time: {avg_time * 10:.2f}s")
        print(f"Actual time: {total_time:.2f}s")
        print(f"Speedup: {(avg_time * 10) / total_time:.2f}x")


async def main():
    print("="*60)
    print("MULTIPLE TOKEN PARALLELISM TEST")
    print("="*60)
    
    # Test 1: Sequential verification
    seq_result = await test_sequential()
    
    if seq_result:
        # Test 2: Parallel execution
        await test_parallel()
        
        # Test 3: Stress test
        await test_stress()
    else:
        print("\n⚠️ Skipping parallel tests due to token issues")
    
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    print("""
    Next steps based on results:
    1. If both tokens work in parallel → Implement multi-token manager
    2. If new token invalidated old → Need separate accounts/projects
    3. If still sequential → API has account-level rate limiting
    """)


if __name__ == "__main__":
    asyncio.run(main())