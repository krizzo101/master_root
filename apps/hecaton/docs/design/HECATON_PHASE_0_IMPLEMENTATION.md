# HECATON - Phase 0 Implementation Design
## "A Hundred Hands Building as One"

### Last Updated: 2025-08-26
### Status: Ready for Implementation

---

## 🎯 Phase 0 Goal: Minimum Viable Parallelism

Build the absolute minimum required for 2-agent parallel execution using existing, proven code from `multi-agent-reference/`. No reinventing the wheel - we copy, simplify, and adapt.

## 📂 Directory Structure

```
/home/opsvi/master_root/
├── apps/
│   └── hecaton/                    # Our new multi-agent orchestrator
│       ├── core.py                 # Adapted from oamat-sd/execution_engine.py
│       ├── tokens.py               # Adapted from multi-agent-monitor/token_pool.py
│       ├── worktrees.py            # Adapted from multi-agent-monitor/worktree_manager.py
│       ├── runner.py               # New minimal CLI
│       └── README.md               # Quick start guide
│
└── multi-agent-reference/          # Source of truth for code patterns
    ├── CRITICAL_PATTERNS_ANALYSIS.md # ← MUST READ: Identifies critical patterns
    ├── oamat-sd/
    │   └── execution_engine.py     # ← SOURCE for Send API pattern
    ├── multi-agent-monitor/
    │   └── orchestration/
    │       ├── token_pool.py       # ← SOURCE for token management
    │       └── worktree_manager.py # ← SOURCE for git isolation
    └── new-design/
        └── *.md                    # Our design docs
```

## ⚠️ CRITICAL PATTERNS TO FOLLOW

Based on `CRITICAL_PATTERNS_ANALYSIS.md`, these patterns are NON-NEGOTIABLE:

1. **Send API Pattern** - MUST use `add_conditional_edges` (3-5x performance gain)
2. **Thread-Safe Token Pool** - MUST use lock for concurrent access
3. **Git Branch Creation** - MUST use `git branch` NOT `git checkout -b`
4. **NO asyncio.gather()** - Forbidden by Rule 997
5. **State Access** - MUST use `.get()` not attribute access

## 🔧 Component Implementation Details

### 1. core.py - The Orchestrator Heart
**Source:** `multi-agent-reference/oamat-sd/execution_engine.py`
**Lines to extract:** The Send API pattern (lines 1-100 approximately)

```python
#!/usr/bin/env python3
"""
HECATON Core Orchestrator - Phase 0
Minimal implementation for 2-agent parallel execution using Send API
Borrowed from: multi-agent-reference/oamat-sd/execution_engine.py
"""

from langgraph.graph import StateGraph
from langgraph.constants import Send
from typing import Dict, List, Any
import subprocess
import json

class HecatonOrchestrator:
    """
    Minimal orchestrator for 2-agent parallel execution.
    This is our seed that will grow into the full system.
    """

    def __init__(self):
        # Create workflow with simple dict state
        self.workflow = StateGraph(dict)
        self._setup_workflow()

    def _setup_workflow(self):
        """Setup the minimal workflow"""
        # Add nodes
        self.workflow.add_node("initialize", self._initialize)
        self.workflow.add_node("distribute", self._distribute)
        self.workflow.add_node("execute", self._execute_agent)
        self.workflow.add_node("collect", self._collect_results)

        # CRITICAL: Use add_conditional_edges for Send API (from oamat-sd)
        self.workflow.add_conditional_edges(
            "distribute",
            self._create_send_objects,  # Returns Send objects for parallelism
            ["execute"]
        )

        # Regular edges
        self.workflow.add_edge("initialize", "distribute")
        self.workflow.add_edge("execute", "collect")

        # Set entry
        self.workflow.set_entry_point("initialize")

    def _initialize(self, state: Dict) -> Dict:
        """Initialize the workflow state"""
        print(f"[HECATON] Initializing parallel execution for {len(state.get('tasks', []))} agents")
        return {"status": "initialized", **state}

    def _distribute(self, state: Dict) -> Dict:
        """Prepare for distribution (state update only)"""
        return {"status": "distributing", **state}

    def _create_send_objects(self, state: Dict) -> List[Send]:
        """
        CRITICAL: This is what enables parallel execution!
        Copied from oamat-sd/execution_engine.py pattern
        """
        from tokens import get_next_token
        from worktrees import create_agent_worktree

        sends = []
        for i, task in enumerate(state.get("tasks", [])):
            agent_id = task.get("id", f"agent_{i}")

            # Get token and worktree for this agent
            token = get_next_token()
            worktree = create_agent_worktree(agent_id)

            # Create Send object - this runs in parallel!
            sends.append(Send(
                "execute",  # Target node
                {
                    "agent_id": agent_id,
                    "task": task,
                    "token": token,
                    "worktree": str(worktree),
                }
            ))

        print(f"[HECATON] Launching {len(sends)} parallel agents")
        return sends

    def _execute_agent(self, state: Dict) -> Dict:
        """Execute a single agent with Claude Code"""
        agent_id = state["agent_id"]
        task = state["task"]
        token = state["token"]
        worktree = state["worktree"]

        print(f"[HECATON] Agent {agent_id} starting in {worktree}")

        # Build Claude command
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--output-format", "json",
            "-p", task["prompt"]
        ]

        # Execute with token and worktree
        env = {"CLAUDE_CODE_TOKEN": token}

        try:
            result = subprocess.run(
                cmd,
                env=env,
                cwd=worktree,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            output = result.stdout
            if result.returncode == 0:
                print(f"[HECATON] Agent {agent_id} completed successfully")
                return {"agent_id": agent_id, "result": output, "status": "success"}
            else:
                print(f"[HECATON] Agent {agent_id} failed: {result.stderr}")
                return {"agent_id": agent_id, "error": result.stderr, "status": "failed"}

        except subprocess.TimeoutExpired:
            print(f"[HECATON] Agent {agent_id} timed out")
            return {"agent_id": agent_id, "error": "timeout", "status": "timeout"}
        except Exception as e:
            print(f"[HECATON] Agent {agent_id} error: {e}")
            return {"agent_id": agent_id, "error": str(e), "status": "error"}

    def _collect_results(self, state: Dict) -> Dict:
        """Collect results from all agents"""
        # In the full system, this would aggregate results
        # For Phase 0, we just pass through
        return state

    async def run(self, tasks: List[Dict]) -> Dict:
        """Main entry point for running parallel tasks"""
        initial_state = {"tasks": tasks}
        result = await self.workflow.arun(initial_state)
        return result
```

### 2. tokens.py - Token Pool Management
**Source:** `multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py`
**Simplified for 2 tokens only**

```python
#!/usr/bin/env python3
"""
HECATON Token Pool - Phase 0
Minimal 2-token rotation for parallel execution
Borrowed from: multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py
"""

import os
import threading

class HecatonTokenPool:
    """
    Simplified token pool for 2 Claude Code tokens.
    Thread-safe round-robin rotation.
    """

    def __init__(self):
        # Load 2 tokens from environment
        self.tokens = [
            os.environ.get("CLAUDE_CODE_TOKEN"),
            os.environ.get("CLAUDE_CODE_TOKEN_1")
        ]

        # Validate tokens
        if not all(self.tokens):
            missing = []
            if not self.tokens[0]:
                missing.append("CLAUDE_CODE_TOKEN")
            if not self.tokens[1]:
                missing.append("CLAUDE_CODE_TOKEN_1")
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

        self.index = 0
        self.lock = threading.Lock()  # Thread safety from original

        print(f"[HECATON] Token pool initialized with {len(self.tokens)} tokens")

    def get_next_token(self) -> str:
        """Get next token in rotation (thread-safe)"""
        with self.lock:
            token = self.tokens[self.index]
            self.index = (self.index + 1) % len(self.tokens)
            # Don't log actual token for security
            print(f"[HECATON] Token {self.index} allocated")
            return token

# Module-level instance for easy import
_pool = HecatonTokenPool()
get_next_token = _pool.get_next_token
```

### 3. worktrees.py - Git Worktree Isolation
**Source:** `multi-agent-reference/multi-agent-monitor/orchestration/worktree_manager.py`
**Simplified for basic isolation**

```python
#!/usr/bin/env python3
"""
HECATON Worktree Manager - Phase 0
Minimal git worktree isolation for parallel agents
Borrowed from: multi-agent-reference/multi-agent-monitor/orchestration/worktree_manager.py
"""

import subprocess
from pathlib import Path
from datetime import datetime
import shutil

# Configuration
BASE_REPO = Path("/home/opsvi/master_root")
WORKTREES_DIR = Path("/home/opsvi/hecaton_worktrees")

def create_agent_worktree(agent_id: str) -> Path:
    """
    Create isolated worktree for an agent.
    Simplified from multi-agent-monitor/orchestration/worktree_manager.py
    """
    # Ensure worktrees directory exists
    WORKTREES_DIR.mkdir(exist_ok=True)

    # Create unique branch and worktree path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    branch_name = f"hecaton/{timestamp}/{agent_id}"
    worktree_path = WORKTREES_DIR / f"{agent_id}_{timestamp}"

    try:
        # Create branch WITHOUT checking it out (critical for avoiding conflicts)
        # This pattern from multi-agent-monitor POC
        result = subprocess.run(
            ["git", "branch", branch_name],
            cwd=BASE_REPO,
            capture_output=True,
            text=True
        )

        # Ignore "already exists" error for retries
        if result.returncode != 0 and "already exists" not in result.stderr:
            raise RuntimeError(f"Failed to create branch: {result.stderr}")

        # Add worktree
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            cwd=BASE_REPO,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")

        print(f"[HECATON] Created worktree for {agent_id} at {worktree_path}")

        # Create reference to our consolidated code
        reference_link = worktree_path / "HECATON_REFERENCE"
        reference_link.write_text(f"""
# HECATON Agent Reference

You are a HECATON agent. When implementing features, reference existing code at:
/home/opsvi/master_root/multi-agent-reference/

CRITICAL: Read CRITICAL_PATTERNS_ANALYSIS.md first! It identifies must-implement patterns.

Key directories:
- CRITICAL_PATTERNS_ANALYSIS.md - MUST-FOLLOW patterns (Send API, token pool, worktrees)
- oamat-sd/ - Send API patterns (3-5x performance gain)
- multi-agent-monitor/ - Token pool, worktree management
- claude-integration/ - SDLC patterns
- new-design/ - Architecture documentation

Rules to follow:
1. Use add_conditional_edges for Send API (NOT add_edge)
2. Use thread locks for token pool
3. Use 'git branch' NOT 'git checkout -b'
4. NEVER use asyncio.gather() (Rule 997)
5. Access state with .get() not attributes

Always check these directories for existing patterns before implementing from scratch.
        """)

        return worktree_path

    except Exception as e:
        print(f"[HECATON] Error creating worktree for {agent_id}: {e}")
        # Cleanup on failure
        cleanup_worktree(worktree_path, branch_name)
        raise

def cleanup_worktree(worktree_path: Path, branch_name: str = None):
    """Clean up worktree and branch"""
    try:
        # Remove worktree
        if worktree_path.exists():
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=BASE_REPO,
                capture_output=True
            )

        # Delete branch if provided
        if branch_name:
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                cwd=BASE_REPO,
                capture_output=True
            )

        print(f"[HECATON] Cleaned up worktree at {worktree_path}")

    except Exception as e:
        print(f"[HECATON] Cleanup error: {e}")

def cleanup_all_worktrees():
    """Clean up all Hecaton worktrees"""
    if WORKTREES_DIR.exists():
        for worktree in WORKTREES_DIR.iterdir():
            if worktree.is_dir():
                cleanup_worktree(worktree)
        print("[HECATON] All worktrees cleaned")
```

### 4. runner.py - CLI Interface
**New file, but references patterns from our analysis**

```python
#!/usr/bin/env python3
"""
HECATON Runner - Phase 0
CLI for testing 2-agent parallel execution
This will be expanded by the agents themselves in Phase 1!
"""

import asyncio
import sys
import json
from pathlib import Path
from core import HecatonOrchestrator
from worktrees import cleanup_all_worktrees

async def run_parallel_agents(task1: str, task2: str):
    """Run two agents in parallel with given tasks"""

    print("\n" + "="*60)
    print("HECATON - A Hundred Hands Building as One")
    print("Phase 0: 2-Agent Parallel Execution Test")
    print("="*60 + "\n")

    # Create orchestrator
    orchestrator = HecatonOrchestrator()

    # Define tasks with reference to existing code
    tasks = [
        {
            "id": "agent_1",
            "prompt": f"""
{task1}

IMPORTANT: You have access to reference implementations at:
/home/opsvi/master_root/multi-agent-reference/

CRITICAL: First read CRITICAL_PATTERNS_ANALYSIS.md for must-follow patterns!

Check these directories for patterns:
- CRITICAL_PATTERNS_ANALYSIS.md - MANDATORY patterns to follow
- oamat-sd/ for Send API patterns (use add_conditional_edges!)
- multi-agent-monitor/ for orchestration patterns (thread-safe!)
- claude-integration/ for SDLC patterns

Critical rules:
1. MUST use add_conditional_edges for Send API
2. MUST use thread locks for token pool
3. MUST use 'git branch' not 'git checkout -b'
4. NEVER use asyncio.gather()
5. Access state with .get() not attributes

Don't reinvent the wheel - adapt existing code when possible.
"""
        },
        {
            "id": "agent_2",
            "prompt": f"""
{task2}

IMPORTANT: You have access to reference implementations at:
/home/opsvi/master_root/multi-agent-reference/

CRITICAL: First read CRITICAL_PATTERNS_ANALYSIS.md for must-follow patterns!

Check these directories for patterns:
- CRITICAL_PATTERNS_ANALYSIS.md - MANDATORY patterns to follow
- oamat-sd/ for Send API patterns (use add_conditional_edges!)
- multi-agent-monitor/ for orchestration patterns (thread-safe!)
- claude-integration/ for SDLC patterns

Critical rules:
1. MUST use add_conditional_edges for Send API
2. MUST use thread locks for token pool
3. MUST use 'git branch' not 'git checkout -b'
4. NEVER use asyncio.gather()
5. Access state with .get() not attributes

Don't reinvent the wheel - adapt existing code when possible.
"""
        }
    ]

    # Run in parallel!
    print("[HECATON] Starting parallel execution...")
    result = await orchestrator.run(tasks)

    print("\n[HECATON] Execution complete!")
    return result

def main():
    """Main entry point"""

    # Default test tasks
    if len(sys.argv) < 3:
        print("Usage: python runner.py '<task1>' '<task2>'")
        print("\nRunning default test...")
        task1 = "Create a Python function to calculate fibonacci numbers efficiently"
        task2 = "Create a Python function to check if a number is prime"
    else:
        task1 = sys.argv[1]
        task2 = sys.argv[2]

    try:
        # Run the parallel tasks
        result = asyncio.run(run_parallel_agents(task1, task2))

        # Save results
        output_file = Path("hecaton_phase0_results.json")
        output_file.write_text(json.dumps(result, indent=2))
        print(f"\n[HECATON] Results saved to {output_file}")

    except KeyboardInterrupt:
        print("\n[HECATON] Interrupted by user")
    except Exception as e:
        print(f"\n[HECATON] Error: {e}")
    finally:
        # Cleanup
        print("\n[HECATON] Cleaning up worktrees...")
        cleanup_all_worktrees()

if __name__ == "__main__":
    main()
```

## 🚀 Implementation Commands

```bash
# Step 1: Create Hecaton directory
cd /home/opsvi/master_root
mkdir -p apps/hecaton
cd apps/hecaton

# Step 2: Copy and adapt core.py from oamat-sd
cat > core.py << 'EOF'
[Insert core.py content from above]
EOF

# Step 3: Copy and adapt tokens.py from multi-agent-monitor
cat > tokens.py << 'EOF'
[Insert tokens.py content from above]
EOF

# Step 4: Copy and adapt worktrees.py from multi-agent-monitor
cat > worktrees.py << 'EOF'
[Insert worktrees.py content from above]
EOF

# Step 5: Create runner.py
cat > runner.py << 'EOF'
[Insert runner.py content from above]
EOF

# Step 6: Set up environment
export CLAUDE_CODE_TOKEN="your_token_1"
export CLAUDE_CODE_TOKEN_1="your_token_2"

# Step 7: Test 2-agent parallel execution
python runner.py

# Step 8: Verify parallelism
# Check that two worktrees were created simultaneously
ls -la /home/opsvi/hecaton_worktrees/
```

## 🧪 Test Script

```python
#!/usr/bin/env python3
"""
test_hecaton_phase0.py - Verify parallel execution works
"""

import time
import asyncio
from runner import run_parallel_agents

async def test_parallelism():
    """Test that agents actually run in parallel"""

    start_time = time.time()

    # Two tasks that would take long sequentially
    task1 = "Create a comprehensive README.md for Hecaton project"
    task2 = "Create a setup.py file for Hecaton with all dependencies"

    result = await run_parallel_agents(task1, task2)

    duration = time.time() - start_time

    print(f"\n[TEST] Execution took {duration:.2f} seconds")
    print(f"[TEST] Parallel execution: {'SUCCESS' if duration < 60 else 'FAILED'}")

    return result

if __name__ == "__main__":
    asyncio.run(test_parallelism())
```

## 📊 Success Criteria

Phase 0 is successful when:

1. ✅ Two agents execute simultaneously (not sequentially)
2. ✅ Each agent gets its own worktree (no conflicts)
3. ✅ Token rotation works (both tokens used)
4. ✅ Results are collected from both agents
5. ✅ Total execution time < 30 seconds for simple tasks

## 🔄 Phase 1 Preview

Once Phase 0 works, we'll use these 2 agents to:
1. Expand token pool to 5 tokens
2. Add error handling and retry logic
3. Enhance the orchestrator with better state management
4. Create agent profiles

The key: Phase 0 builds Phase 1, Phase 1 builds Phase 2, etc.

## 📚 Reference Mapping

| Component | Source File | Key Lines | Adaptation |
|-----------|------------|-----------|------------|
| Send API | `oamat-sd/execution_engine.py` | 1-100 | Simplified StateGraph |
| Token Pool | `multi-agent-monitor/orchestration/token_pool.py` | Full file | Reduced to 2 tokens |
| Worktrees | `multi-agent-monitor/orchestration/worktree_manager.py` | Full file | Simplified paths |
| SDLC Patterns | `claude-integration/sdlc*.py` | Various | Referenced in prompts |

## 🎯 Next Immediate Step

```bash
cd /home/opsvi/master_root
mkdir -p apps/hecaton
cd apps/hecaton
# Start creating core.py with the Send API pattern!
```

---

**HECATON Phase 0 Design:** COMPLETE
**Ready to Build:** YES
**Estimated Time:** 2 hours to working prototype
