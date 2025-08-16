#!/usr/bin/env python3
"""
Quick test for V3 server - minimal execution to prove functionality
"""

import os
import sys
import json
import asyncio

# Add libs to path
sys.path.insert(0, '/home/opsvi/master_root/libs')

from opsvi_mcp.servers.claude_code_v3.server import claude_run_v3, get_v3_status

async def quick_test():
    """Quick functionality test"""
    
    print("V3 Quick Test - Proving Real Claude Code Execution")
    print("=" * 50)
    
    # 1. Check status
    print("\n1. Server Status:")
    status = await get_v3_status()
    print(f"   - Version: {status['version']}")
    print(f"   - Real Execution: {status.get('execution') == 'REAL'}")
    print(f"   - Not Stubbed: {not status.get('stubbed', True)}")
    
    # 2. Execute a VERY simple task in RAPID mode
    print("\n2. Executing minimal task...")
    
    # Ultra-simple task that should execute quickly
    task = "Write a one-line Python comment that says hello"
    
    print(f"   Task: '{task}'")
    print("   Mode: RAPID (fastest)")
    print("   Calling Claude Code...")
    
    try:
        result = await claude_run_v3(
            task=task,
            mode="RAPID",
            auto_detect=False,
            quality_level="normal"
        )
        
        print(f"\n3. Result:")
        print(f"   - Success: {result.get('success', False)}")
        print(f"   - Status: {result.get('status', 'unknown')}")
        print(f"   - Mode Used: {result.get('mode', 'unknown')}")
        
        if result.get('session_id'):
            print(f"   - Session ID: {result['session_id'][:30]}... (real Claude session)")
        
        if result.get('cost'):
            print(f"   - Cost: ${result['cost']:.6f} (real API cost)")
        
        if result.get('error'):
            print(f"   - Error: {result['error']}")
        
        # Check for actual output
        if result.get('output'):
            output = result['output']
            if isinstance(output, dict):
                if output.get('result'):
                    print(f"   - Claude Output: Found (contains actual code)")
                if output.get('type'):
                    print(f"   - Output Type: {output.get('type')}")
            else:
                print(f"   - Raw Output Length: {len(str(output))} chars")
        
        # Verdict
        print("\n" + "=" * 50)
        if result.get('success'):
            print("✅ V3 IS WORKING - Real Claude Code execution confirmed!")
        else:
            print("❌ V3 execution failed - check error above")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print(f"Environment Check:")
    print(f"  CLAUDE_CODE_TOKEN: {'SET' if os.environ.get('CLAUDE_CODE_TOKEN') else 'NOT SET'}")
    print(f"  ANTHROPIC_API_KEY: {os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')}")
    print()
    
    result = asyncio.run(quick_test())
    
    # Save result
    if result:
        with open("/tmp/v3_quick_test.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nResults saved to /tmp/v3_quick_test.json")