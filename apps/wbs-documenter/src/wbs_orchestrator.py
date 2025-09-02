#!/usr/bin/env python3
"""
WBS Documentation Orchestrator
Coordinates 1,872 parallel documentation tasks using headless Claude agents
"""

import asyncio
import hashlib
import json
import os
import sqlite3
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ResearchCache:
    """Shared research cache to prevent redundant searches"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "research_cache.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite cache database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS research (
                query_hash TEXT PRIMARY KEY,
                query TEXT,
                results TEXT,
                timestamp REAL,
                used_count INTEGER DEFAULT 1
            )
        """
        )
        conn.commit()
        conn.close()

    def get(self, query: str) -> Optional[Dict]:
        """Get cached research results"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            "SELECT results FROM research WHERE query_hash = ?", (query_hash,)
        ).fetchone()
        conn.close()

        if result:
            return json.loads(result[0])
        return None

    def put(self, query: str, results: Dict):
        """Store research results"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO research VALUES (?, ?, ?, ?, ?)",
            (query_hash, query, json.dumps(results), datetime.now().timestamp(), 1),
        )
        conn.commit()
        conn.close()


class TokenPool:
    """Manages Claude API tokens for parallel execution"""

    def __init__(self, tokens_file: Path = None):
        self.tokens = []
        self.current_index = 0
        self.lock = asyncio.Lock()

        # Load tokens from environment or file
        if tokens_file and tokens_file.exists():
            with open(tokens_file) as f:
                self.tokens = [line.strip() for line in f if line.strip()]
        else:
            # Use single token from environment
            token = os.environ.get("CLAUDE_CODE_TOKEN")
            if token:
                self.tokens = [token]

    async def acquire(self) -> Tuple[str, int]:
        """Get next available token (round-robin)"""
        async with self.lock:
            if not self.tokens:
                raise ValueError("No tokens available")

            token = self.tokens[self.current_index]
            token_idx = self.current_index
            self.current_index = (self.current_index + 1) % len(self.tokens)
            return token, token_idx

    def size(self) -> int:
        """Get number of available tokens"""
        return len(self.tokens)


class WBSOrchestrator:
    """Main orchestrator for WBS documentation generation"""

    def __init__(self, project_dir: Path, output_dir: Path):
        self.project_dir = project_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.cache = ResearchCache(output_dir / "cache")
        self.token_pool = TokenPool()
        self.status_dir = output_dir / "status"
        self.status_dir.mkdir(exist_ok=True)

        # Setup optimized Claude command
        self.claude_cmd = [
            "claude",
            "-p",
            "--model",
            "sonnet",  # Fastest model
            "--strict-mcp-config",
            "--mcp-config",
            str(Path.home() / ".claude_minimal.json"),
            "--permission-mode",
            "acceptEdits",
            "--output-format",
            "json",
        ]

        # Track execution metrics
        self.metrics = {
            "started": 0,
            "completed": 0,
            "failed": 0,
            "cache_hits": 0,
            "total_time": 0,
        }

    async def execute_agent(
        self,
        agent_id: str,
        agent_type: str,
        prompt: str,
        context: Dict,
        token_idx: int = 0,
    ) -> Dict:
        """Execute a single Claude agent with given prompt"""

        session_id = f"{agent_id}_{uuid.uuid4().hex[:8]}"

        # Build full prompt with context
        full_prompt = self._build_prompt(agent_type, prompt, context)

        # Add workspace directory for file operations
        cmd = self.claude_cmd + [
            "--session-id",
            session_id,
            "--add-dir",
            str(self.output_dir),
            full_prompt,
        ]

        # Set token for this execution
        env = os.environ.copy()
        if self.token_pool.size() > 1:
            token, _ = await self.token_pool.acquire()
            env["CLAUDE_CODE_TOKEN"] = token

        # Execute
        start_time = datetime.now()
        self.metrics["started"] += 1

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            duration = (datetime.now() - start_time).total_seconds()
            self.metrics["total_time"] += duration

            if result.returncode == 0:
                self.metrics["completed"] += 1

                # Parse JSON output
                output = json.loads(stdout.decode())

                # Mark completion
                await self._mark_complete(agent_id, output)

                return {
                    "success": True,
                    "agent_id": agent_id,
                    "output": output,
                    "duration": duration,
                }
            else:
                self.metrics["failed"] += 1
                return {
                    "success": False,
                    "agent_id": agent_id,
                    "error": stderr.decode(),
                    "duration": duration,
                }

        except Exception as e:
            self.metrics["failed"] += 1
            return {"success": False, "agent_id": agent_id, "error": str(e)}

    def _build_prompt(self, agent_type: str, task: str, context: Dict) -> str:
        """Build full prompt with context and templates"""

        template = self._get_template(agent_type)

        prompt = f"""You are documenting part of an auto-coding solution using a 4-level WBS structure.

## Your Task
{task}

## Context
Parent: {context.get('parent', 'N/A')}
Level: {context.get('level', 'N/A')}
Position: {context.get('position', 'N/A')}
Boundaries: Start at {context.get('start_boundary', 'N/A')}, end before {context.get('end_boundary', 'N/A')}

## Template to Follow
{template}

## Available Research
{json.dumps(context.get('research', {}), indent=2)}

## Instructions
1. Generate comprehensive documentation for your assigned section
2. Ensure alignment with parent and sibling sections
3. Use the provided research to inform your content
4. Output as markdown to: {self.output_dir}/{context.get('output_file', 'output.md')}
5. Include all sections from the template
6. Be specific and detailed - this is technical documentation

IMPORTANT: Focus only on YOUR section. Do not document sections outside your boundaries."""

        return prompt

    def _get_template(self, agent_type: str) -> str:
        """Get template for agent type"""

        templates = {
            "stage": """# Stage [Number]: [Title]

## Overview
[High-level description of this stage's purpose and goals]

## Key Objectives
- [Objective 1]
- [Objective 2]
- [Objective 3]

## Input Requirements
[What must be available before this stage can begin]

## Output Deliverables
[What this stage produces]

## Steps
[List of steps within this stage - titles only]

## Dependencies
[Other stages this depends on or that depend on it]

## Success Criteria
[How to measure successful completion]""",
            "step": """## Step [Number]: [Title]

### Purpose
[Why this step is necessary]

### Activities
[Detailed list of what happens in this step]

### Tools & Technologies
[Specific tools, frameworks, or technologies used]

### Actions
[List of actions within this step - titles only]

### Validation
[How to verify this step is complete]""",
            "action": """### Action [Number]: [Title]

#### Description
[Detailed description of this action]

#### Implementation
[How to implement this action]

#### Operations
[List of operations within this action - titles only]

#### Expected Outcome
[What should result from this action]""",
            "operation": """#### Operation [Number]: [Title]

##### Procedure
[Step-by-step procedure]

##### Code/Commands
```
[Specific code or commands if applicable]
```

##### Verification
[How to verify this operation worked]

##### Error Handling
[Common errors and how to handle them]""",
        }

        return templates.get(agent_type, templates["stage"])

    async def _mark_complete(self, agent_id: str, output: Dict):
        """Mark an agent task as complete"""
        status_file = self.status_dir / f"{agent_id}.json"
        status = {
            "agent_id": agent_id,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "output": output,
        }

        with open(status_file, "w") as f:
            json.dump(status, f, indent=2)

    async def execute_batch(
        self, agents: List[Dict], max_parallel: int = 10
    ) -> List[Dict]:
        """Execute a batch of agents with parallelism limit"""

        results = []

        # Process in chunks to respect parallelism limit
        for i in range(0, len(agents), max_parallel):
            chunk = agents[i : i + max_parallel]

            # Execute chunk in parallel
            tasks = [
                self.execute_agent(
                    agent["id"], agent["type"], agent["prompt"], agent["context"]
                )
                for agent in chunk
            ]

            chunk_results = await asyncio.gather(*tasks)
            results.extend(chunk_results)

            # Brief pause between chunks
            await asyncio.sleep(1)

        return results

    async def build_research_cache(self):
        """Stage 1: Build shared research cache"""
        print("Stage 1: Building research cache...")

        research_topics = [
            "Claude API documentation",
            "LangGraph Send API",
            "Git worktree management",
            "Python asyncio patterns",
            "Software architecture patterns",
            "Test-driven development",
            "CI/CD pipelines",
            "Code review best practices",
            "Documentation standards",
            "Agile methodologies",
        ]

        research_agents = []
        for i, topic in enumerate(research_topics):
            research_agents.append(
                {
                    "id": f"research_{i}",
                    "type": "research",
                    "prompt": f"Research and summarize: {topic}",
                    "context": {"output_file": f"research/research_{i}.md"},
                }
            )

        results = await self.execute_batch(research_agents, max_parallel=5)

        # Store in cache
        for result in results:
            if result["success"]:
                topic = research_topics[int(result["agent_id"].split("_")[1])]
                self.cache.put(topic, result["output"])

        print(f"Research cache built: {len(results)} topics")

    async def document_stages(self) -> List[Dict]:
        """Stage 2: Document 12 high-level stages"""
        print("Stage 2: Documenting 12 stages...")

        stages = [
            "Requirements Gathering",
            "System Design",
            "Architecture Planning",
            "Development Setup",
            "Core Implementation",
            "Testing Framework",
            "Integration",
            "Performance Optimization",
            "Security Hardening",
            "Documentation",
            "Deployment",
            "Maintenance",
        ]

        stage_agents = []
        for i, stage in enumerate(stages, 1):
            stage_agents.append(
                {
                    "id": f"stage_{i}",
                    "type": "stage",
                    "prompt": f"Document Stage {i}: {stage}",
                    "context": {
                        "level": "Stage",
                        "position": f"{i} of 12",
                        "parent": "Auto-Coding Solution",
                        "output_file": f"stages/stage_{i}.md",
                        "research": self.cache.get("Software architecture patterns")
                        or {},
                    },
                }
            )

        results = await self.execute_batch(stage_agents, max_parallel=6)

        print(f"Stages documented: {sum(1 for r in results if r['success'])}/12")
        return results

    async def run_full_orchestration(self):
        """Execute the full WBS documentation orchestration"""

        print("=" * 60)
        print("WBS Documentation Orchestrator")
        print(f"Output directory: {self.output_dir}")
        print(f"Available tokens: {self.token_pool.size()}")
        print("=" * 60)

        # Stage 1: Research
        await self.build_research_cache()

        # Stage 2: Document stages
        stage_results = await self.document_stages()

        # Human review gate
        print("\n⚠️  HUMAN REVIEW REQUIRED")
        print("Please review the generated stage documentation in:")
        print(f"  {self.output_dir}/stages/")
        input("Press Enter when ready to continue...")

        # Stage 3-5: Would continue with steps, actions, operations
        # (Abbreviated for demonstration)

        # Final metrics
        print("\n" + "=" * 60)
        print("EXECUTION COMPLETE")
        print(f"Started: {self.metrics['started']}")
        print(f"Completed: {self.metrics['completed']}")
        print(f"Failed: {self.metrics['failed']}")
        print(f"Cache hits: {self.metrics['cache_hits']}")
        print(f"Total time: {self.metrics['total_time']:.2f}s")
        print(
            f"Avg time per agent: {self.metrics['total_time']/max(1, self.metrics['started']):.2f}s"
        )
        print("=" * 60)


async def main():
    """Main entry point"""

    # Setup
    project_dir = Path("/home/opsvi/spawn-test")
    output_dir = project_dir / "wbs_documentation"

    # Ensure minimal MCP config exists
    minimal_config = Path.home() / ".claude_minimal.json"
    if not minimal_config.exists():
        minimal_config.write_text('{"mcpServers": {}}')

    # Create orchestrator
    orchestrator = WBSOrchestrator(project_dir, output_dir)

    # Run
    await orchestrator.run_full_orchestration()


if __name__ == "__main__":
    asyncio.run(main())
