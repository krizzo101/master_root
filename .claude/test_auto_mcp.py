#!/usr/bin/env python3
"""Test automatic MCP server selection"""

import sys
import os

# Project root
PROJECT_ROOT = "/home/opsvi/master_root"
sys.path.insert(0, os.path.join(PROJECT_ROOT, ".claude"))

from auto_mcp_middleware import analyze_user_prompt, get_metrics
import json

# Test prompts
test_cases = [
    ("Fix the login bug", "V1"),
    ("Analyze all Python files for security issues", "V2"),
    ("Create a production-ready authentication system", "V3"),
    ("What does this function do?", None),
    ("Debug why the API returns 500 errors", "V1"),
    ("Generate tests for every module", "V2"),
    ("Build a robust e-commerce platform", "V3"),
]

print("Testing Automatic MCP Server Selection")
print("=" * 50)

correct = 0
total = len(test_cases)

for prompt, expected in test_cases:
    result = analyze_user_prompt(prompt)
    
    if result['use_mcp']:
        selected = result['server']
    else:
        selected = None
    
    status = "✅" if selected == expected else "❌"
    print(f"{status} Prompt: {prompt[:50]}...")
    print(f"   Expected: {expected}, Got: {selected}")
    
    if selected == expected:
        correct += 1
    
    if result['use_mcp']:
        print(f"   Metadata: {result['metadata']}")
    print()

print(f"Score: {correct}/{total} ({100*correct/total:.1f}%)")
print()
print("Metrics:", json.dumps(get_metrics(), indent=2))
