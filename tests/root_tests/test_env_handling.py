#!/usr/bin/env python3
"""Test script to verify ANTHROPIC_API_KEY is properly overridden"""

import os
import subprocess
import sys

def test_env_override():
    """Test that spawned processes properly override ANTHROPIC_API_KEY"""
    
    # First, set ANTHROPIC_API_KEY in the environment (simulating default)
    os.environ["ANTHROPIC_API_KEY"] = "test_api_key_should_be_removed"
    os.environ["CLAUDE_CODE_TOKEN"] = "test_token_should_be_kept"
    
    print("Initial environment:")
    print(f"  ANTHROPIC_API_KEY: {os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')}")
    print(f"  CLAUDE_CODE_TOKEN: {os.environ.get('CLAUDE_CODE_TOKEN', 'NOT SET')}")
    
    # Create a test script that prints environment
    test_script = """
import os
print("Child process environment:")
print(f"  ANTHROPIC_API_KEY: {os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')!r}")
print(f"  CLAUDE_CODE_TOKEN: {os.environ.get('CLAUDE_CODE_TOKEN', 'NOT SET')!r}")
"""
    
    # Test 1: Without env modification (should inherit parent's env)
    print("\nTest 1: Without modification (BAD - inherits API key):")
    result = subprocess.run([sys.executable, "-c", test_script], capture_output=True, text=True)
    print(result.stdout)
    
    # Test 2: With proper env modification (like our fixed servers)
    print("Test 2: With proper modification (GOOD - removes API key):")
    env = os.environ.copy()
    
    # This is what our fixed servers do:
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]
    env["ANTHROPIC_API_KEY"] = ""  # Explicitly set to empty
    
    result = subprocess.run([sys.executable, "-c", test_script], env=env, capture_output=True, text=True)
    print(result.stdout)
    
    # Verify the fix works
    if "''" in result.stdout or "NOT SET" in result.stdout:
        print("✅ SUCCESS: ANTHROPIC_API_KEY properly overridden!")
    else:
        print("❌ FAILURE: ANTHROPIC_API_KEY still present!")
    
    # Verify CLAUDE_CODE_TOKEN is preserved
    if "test_token_should_be_kept" in result.stdout:
        print("✅ SUCCESS: CLAUDE_CODE_TOKEN preserved!")
    else:
        print("❌ FAILURE: CLAUDE_CODE_TOKEN not preserved!")

if __name__ == "__main__":
    test_env_override()