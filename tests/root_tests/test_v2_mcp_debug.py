#!/usr/bin/env python3
"""
Comprehensive test script for V2 MCP server with debug logging
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime

# Ensure environment is correct
print("=" * 60)
print("V2 MCP Server Test with Debug Logging")
print("=" * 60)

# Check environment variables
print("\n1. Environment Check:")
print("-" * 40)
claude_token = os.environ.get('CLAUDE_CODE_TOKEN', '')
anthropic_key = os.environ.get('ANTHROPIC_API_KEY', 'NOT_SET')

print(f"CLAUDE_CODE_TOKEN: {'SET' if claude_token else 'NOT SET'} (length: {len(claude_token)})")
print(f"ANTHROPIC_API_KEY: {repr(anthropic_key)}")

if not claude_token:
    print("ERROR: CLAUDE_CODE_TOKEN not set!")
    sys.exit(1)

if anthropic_key and anthropic_key != '' and anthropic_key != 'NOT_SET':
    print("WARNING: ANTHROPIC_API_KEY should be empty or unset!")

# Add the library path
sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-mcp')

print("\n2. Importing V2 Server Components:")
print("-" * 40)

try:
    from opsvi_mcp.servers.claude_code_v2.server import ClaudeCodeV2Server
    from opsvi_mcp.servers.claude_code_v2.config import ServerConfig
    from opsvi_mcp.servers.claude_code_v2.job_manager import JobManager
    print("✓ Successfully imported V2 server components")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Initializing V2 Server:")
print("-" * 40)

try:
    config = ServerConfig()
    print(f"✓ Config created with token: {'SET' if config.claude_token else 'NOT SET'}")
    print(f"  Results dir: {config.default_results_dir}")
    print(f"  Max concurrent: {config.max_concurrent_first_level}")
    
    server = ClaudeCodeV2Server(config)
    print("✓ Server initialized")
except Exception as e:
    print(f"✗ Failed to initialize server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing spawn_parallel_agents:")
print("-" * 40)

async def test_spawn():
    """Test spawning parallel agents"""
    
    # Simple test tasks
    test_tasks = [
        "Create a simple function that returns 'Hello from Agent 1'",
        "Create a simple function that returns 'Hello from Agent 2'",
        "Create a simple function that returns 'Hello from Agent 3'"
    ]
    
    output_dir = "/tmp/v2_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"Output directory: {output_dir}")
    print(f"Spawning {len(test_tasks)} agents...")
    
    try:
        # Create the request object
        from types import SimpleNamespace
        request = SimpleNamespace(
            tasks=test_tasks,
            agent_profile=None,
            output_dir=output_dir,
            timeout=120,
            metadata={"test": True}
        )
        
        # Call spawn_parallel_agents
        result = await server._spawn_parallel_agents_impl(request)
        
        print(f"\nSpawn Result:")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print(f"\n✓ Successfully spawned {result.get('total_spawned', 0)} agents")
            
            # Wait a bit for agents to start
            print("\nWaiting 10 seconds for agents to process...")
            await asyncio.sleep(10)
            
            # Check for results
            print("\n5. Checking Results:")
            print("-" * 40)
            
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                print(f"Files in output directory: {files}")
                
                for file in files:
                    if file.endswith('.json'):
                        filepath = os.path.join(output_dir, file)
                        try:
                            with open(filepath, 'r') as f:
                                content = json.load(f)
                                print(f"\n{file}:")
                                print(json.dumps(content, indent=2)[:500])  # First 500 chars
                        except Exception as e:
                            print(f"Error reading {file}: {e}")
            else:
                print(f"Output directory {output_dir} does not exist")
                
            # Try to collect results
            print("\n6. Testing collect_results:")
            print("-" * 40)
            
            collect_request = SimpleNamespace(
                job_ids=[job['job_id'] for job in result.get('jobs', [])],
                output_dir=output_dir,
                include_partial=True,
                cleanup=False
            )
            
            collect_result = await server._collect_results_impl(collect_request)
            print(f"Collect Result:")
            print(json.dumps(collect_result, indent=2))
            
        else:
            print(f"\n✗ Spawn failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

print("\nRunning async test...")
success = asyncio.run(test_spawn())

print("\n7. Checking Debug Logs:")
print("-" * 40)

# Check if debug log was created
if os.path.exists('/tmp/v2_debug.log'):
    print("Debug log found at /tmp/v2_debug.log")
    print("\nLast 50 lines of debug log:")
    print("-" * 40)
    with open('/tmp/v2_debug.log', 'r') as f:
        lines = f.readlines()
        for line in lines[-50:]:
            print(line.rstrip())
else:
    print("No debug log found at /tmp/v2_debug.log")

print("\n8. Checking for Agent Scripts:")
print("-" * 40)

# Check for any agent scripts that were created
agent_scripts = [f for f in os.listdir('/tmp') if f.startswith('agent_') and f.endswith('.py')]
if agent_scripts:
    print(f"Found {len(agent_scripts)} agent scripts:")
    for script in agent_scripts[:5]:  # Show first 5
        print(f"  - {script}")
        # Check if script exists and show first few lines
        script_path = os.path.join('/tmp', script)
        if os.path.exists(script_path):
            with open(script_path, 'r') as f:
                lines = f.readlines()[:10]
                print(f"    First 10 lines:")
                for line in lines:
                    print(f"      {line.rstrip()}")
else:
    print("No agent scripts found in /tmp")

print("\n" + "=" * 60)
print("Test Summary:")
print("=" * 60)

if success:
    print("✓ V2 MCP Server test completed successfully")
else:
    print("✗ V2 MCP Server test failed - check logs above")

print("\nFor detailed debugging, check:")
print("  - /tmp/v2_debug.log (debug log)")
print("  - /tmp/v2_test_*/  (output directories)")
print("  - /tmp/agent_*.py (agent scripts)")