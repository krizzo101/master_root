#!/usr/bin/env python3
"""
Working recursive Claude Code task demonstration.
This creates a task that spawns another Claude Code instance.
"""

print("=" * 70)
print("RECURSIVE CLAUDE CODE TASK - PARENT INSTANCE")
print("=" * 70)

# Report we're the parent
print("\n[PARENT] This is the parent Claude Code instance")
print("[PARENT] Now spawning a child Claude Code instance...")

# Import required for calling MCP tools
import subprocess
import json

# Call the MCP wrapper synchronously
cmd = [
    "/home/opsvi/miniconda/bin/python",
    "-c",
    """
import sys
sys.path.insert(0, '/home/opsvi/master_root/libs')
from opsvi_mcp.servers.claude_code.server import main
import asyncio

# Create a simple task
task = 'echo "[CHILD] This is the child Claude Code instance" && python -c "import sys; print(f\\"[CHILD] Python version: {sys.version.split()[0]}\\")" && echo "[CHILD] Task completed"'

# Run it
from opsvi_mcp.servers.claude_code.server import ClaudeCodeServer
server = ClaudeCodeServer()
asyncio.run(server.initialize())

result = asyncio.run(server.claude_run(
    task=task,
    cwd='/home/opsvi/master_root',
    output_format='text',
    permission_mode='bypassPermissions',
    verbose=False
))
print(result)
""",
]

print("\n[PARENT] Executing child task...")
print("-" * 70)

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"[PARENT] Child error: {result.stderr}")
except subprocess.TimeoutExpired:
    print("[PARENT] Child task timed out")
except Exception as e:
    print(f"[PARENT] Error: {e}")

print("-" * 70)
print("\n[PARENT] Recursive demonstration complete!")
print("=" * 70)
