#!/usr/bin/env python3
"""
Test recursive Claude spawning with token rotation
Tier 1: 3 Claude instances (one per token)
Tier 2: Each spawns 3 more (9 total, 3 per token)
"""
import json
import time

# Create the task that tells each Claude to spawn 3 more
recursive_task = """
You have access to an MCP server that can spawn Claude instances. 
Use the mcp__claude-code-wrapper__claude_run_batch tool to spawn 3 parallel tasks:

Task 1: Create file /tmp/tier2_{parent_id}_1.txt with content 'TIER2_{parent_id}_1_COMPLETE'
Task 2: Create file /tmp/tier2_{parent_id}_2.txt with content 'TIER2_{parent_id}_2_COMPLETE'  
Task 3: Create file /tmp/tier2_{parent_id}_3.txt with content 'TIER2_{parent_id}_3_COMPLETE'

Use model 'sonnet' to save tokens. Report when all 3 complete.
"""

# Create tier 1 tasks that will each spawn tier 2
tier1_tasks = [
    {
        "task": recursive_task.replace("{parent_id}", "A"),
        "model": "opus"  # Use Opus for tier 1 since it needs to use MCP tools
    },
    {
        "task": recursive_task.replace("{parent_id}", "B"),
        "model": "opus"
    },
    {
        "task": recursive_task.replace("{parent_id}", "C"),
        "model": "opus"
    }
]

print("RECURSIVE SPAWNING TEST")
print("="*60)
print("Tier 1: Spawning 3 Claude instances (one per token)")
print("Each will spawn 3 more instances (9 total in Tier 2)")
print("="*60)

# Save the task configuration
with open('/tmp/recursive_spawn_config.json', 'w') as f:
    json.dump(tier1_tasks, f, indent=2)

print("\nConfiguration saved to /tmp/recursive_spawn_config.json")
print("\nTo execute, run:")
print("mcp__claude-code-wrapper__claude_run_batch with tasks from config file")
print("\nExpected outcome:")
print("- 3 Tier 1 instances run in parallel (~15-20s)")
print("- Each spawns 3 Tier 2 instances (9 total)")
print("- If successful: 9 files created in /tmp/tier2_*.txt")
print("- If rate limited: Some spawns will fail")

# Also create a verification script
verify_script = """#!/usr/bin/env python3
import os
import glob

files = glob.glob('/tmp/tier2_*.txt')
print(f"Found {len(files)} tier 2 output files:")
for f in sorted(files):
    with open(f) as fh:
        content = fh.read().strip()
    print(f"  {os.path.basename(f)}: {content}")

if len(files) == 9:
    print("\\n✅ SUCCESS: All 9 tier 2 instances completed!")
else:
    print(f"\\n⚠️ PARTIAL: Only {len(files)}/9 completed (likely rate limited)")
"""

with open('/tmp/verify_recursive.py', 'w') as f:
    f.write(verify_script)

print("\nVerification script saved to /tmp/verify_recursive.py")