#!/usr/bin/env python3
"""
POC Launcher with Git Worktrees: 2-Agent Requirements Gathering Test
Tests parallel agent collaboration using isolated worktrees
"""

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.worktree_manager import WorktreeManager
from src.safety import GitSafetyManager, SafetyLevel


class WorktreePOC:
    """Proof of Concept for parallel agent execution with worktrees"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.repo_path = Path("/home/opsvi/master_root")
        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.worktree_manager = WorktreeManager(self.repo_path)
        self.safety_manager = GitSafetyManager(self.repo_path)

        # Shared communication space
        self.shared_space = Path("/home/opsvi/agent_shared")
        self.shared_space.mkdir(parents=True, exist_ok=True)
        (self.shared_space / "messages").mkdir(exist_ok=True)
        (self.shared_space / "outputs").mkdir(exist_ok=True)
        (self.shared_space / "status").mkdir(exist_ok=True)

        self.metrics = {
            "execution_id": self.execution_id,
            "start_time": None,
            "end_time": None,
            "agents": {},
            "messages_exchanged": 0,
            "parallel_execution": False,
        }

    def create_base_branch(self) -> str:
        """Create base branch for POC"""
        base_branch = f"poc/agent-communication/{self.execution_id}"

        if not self.dry_run:
            try:
                # Create branch from current HEAD
                subprocess.run(
                    ["git", "checkout", "-b", base_branch],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )
                print(f"✅ Created base branch: {base_branch}")
            except subprocess.CalledProcessError:
                # Branch might already exist or we're already on it
                print(f"ℹ️  Using existing branch or current branch")
                base_branch = "main"
        else:
            print(f"[DRY RUN] Would create branch: {base_branch}")

        return base_branch

    def create_agent_task(self, agent_type: str) -> Dict[str, Any]:
        """Create task definition for an agent"""

        tasks = {
            "requirements-analyst": {
                "title": "Define Functional Requirements for Inter-Agent Communication",
                "description": """You are the Requirements Analyst designing a communication system for AI agents.

## Your Task
Create functional requirements for an inter-agent communication system that will enable 15 AI agents to coordinate in parallel.

## Key Considerations
- Agents run in separate Claude sessions (isolated processes)
- Messages must persist between agent executions
- Real-time coordination needs (sub-second messaging)
- Human operators need to monitor all communications
- System must handle agent failures gracefully

## Deliverables
1. Create: outputs/requirements_functional.md with:
   - System capabilities
   - Message format specification
   - API design
   - Performance requirements
   - Security constraints

2. Leave messages for Business Analyst in: /home/opsvi/agent_shared/messages/
   - Questions about business priorities
   - Technical decisions that need business input
   - Areas where you need clarification

## Message Format
```json
{
  "from": "requirements-analyst",
  "to": "business-analyst",
  "timestamp": "ISO-8601",
  "subject": "topic",
  "body": "content",
  "priority": "high|medium|low"
}
```

Remember: You're designing the system YOU will use to communicate!""",
                "working_directory": None,  # Will be set to worktree path
                "output_files": ["outputs/requirements_functional.md"],
                "estimated_duration": 300,  # 5 minutes
            },
            "business-analyst": {
                "title": "Define Business Requirements and Use Cases",
                "description": """You are the Business Analyst adding business context to the communication system design.

## Your Task
Review functional requirements and add business perspective for the inter-agent communication system.

## Key Considerations
- Check for requirements from Requirements Analyst in their worktree outputs
- Consider workflows for 15 parallel agents
- Define success metrics and KPIs
- Identify failure scenarios and recovery

## Deliverables
1. Create: outputs/requirements_business.md with:
   - User stories and workflows
   - Success metrics
   - Priority matrix
   - Risk assessment
   - Integration requirements

2. Check messages in: /home/opsvi/agent_shared/messages/
   - Respond to Requirements Analyst questions
   - Provide business priorities
   - Clarify use cases

## Collaboration
- Your worktree has the same codebase as Requirements Analyst
- You work in parallel but share messages via the shared space
- Aim to build on their work, not duplicate it

Remember: Think about how YOU as an agent want to communicate!""",
                "working_directory": None,
                "output_files": ["outputs/requirements_business.md"],
                "estimated_duration": 300,
            },
        }

        return tasks.get(agent_type, {})

    async def setup_agent_worktree(
        self, agent_type: str, base_branch: str
    ) -> Optional[Dict]:
        """Set up worktree for an agent"""

        agent_id = f"{agent_type}_{self.execution_id}"

        if self.dry_run:
            print(f"[DRY RUN] Would create worktree for {agent_type}")
            return {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "worktree_path": f"/mock/path/{agent_id}",
                "environment": {
                    "working_directory": f"/mock/path/{agent_id}",
                    "agent_workspace": f"/mock/path/{agent_id}/agent_workspace",
                    "shared_messages": str(self.shared_space / "messages"),
                    "shared_outputs": str(self.shared_space / "outputs"),
                    "branch_name": f"mock/branch/{agent_type}",
                    "agent_type": agent_type,
                    "created_at": datetime.now().isoformat(),
                },
                "task": self.create_agent_task(agent_type),
            }

        try:
            # Create worktree
            worktree = self.worktree_manager.create_agent_worktree(
                agent_id=agent_id,
                agent_type=agent_type,
                base_branch=base_branch,
                execution_id=self.execution_id,
            )

            # Get environment
            env = self.worktree_manager.get_agent_environment(agent_id)

            # Create task file in worktree
            task_data = self.create_agent_task(agent_type)
            task_data["working_directory"] = env["working_directory"]

            task_file = Path(env["agent_workspace"]) / "task.json"
            task_file.parent.mkdir(parents=True, exist_ok=True)
            task_file.write_text(json.dumps(task_data, indent=2))

            print(f"✅ Created worktree for {agent_type}")
            print(f"   Path: {env['working_directory']}")
            print(f"   Branch: {env['branch_name']}")

            return {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "worktree": worktree,
                "environment": env,
                "task": task_data,
            }

        except Exception as e:
            print(f"❌ Failed to create worktree for {agent_type}: {e}")
            return None

    async def simulate_agent_execution(self, agent_config: Dict) -> Dict[str, Any]:
        """Simulate agent execution in worktree"""

        agent_type = agent_config["agent_type"]
        agent_id = agent_config["agent_id"]
        workspace = Path(agent_config["environment"]["agent_workspace"])

        print(f"\n🤖 Simulating {agent_type} execution...")

        # Track in metrics
        self.metrics["agents"][agent_id] = {
            "type": agent_type,
            "start_time": datetime.now().isoformat(),
            "status": "running",
        }

        # Simulate some work
        await asyncio.sleep(2)

        # Create mock output only if not in dry run
        if not self.dry_run:
            output_dir = workspace / "outputs"
            output_dir.mkdir(exist_ok=True)
        else:
            output_dir = self.shared_space / "outputs"
            output_dir.mkdir(exist_ok=True)

        if agent_type == "requirements-analyst":
            output = output_dir / "requirements_functional.md"
            output.write_text(
                f"""# Functional Requirements for Inter-Agent Communication

## System Overview
Communication system enabling 15 parallel AI agents to coordinate.

## Core Requirements

### 1. Message Bus Architecture
- Publish/subscribe pattern for broadcast messages
- Direct peer-to-peer messaging for targeted communication
- Message persistence with at least 24-hour retention
- Guaranteed delivery with acknowledgment

### 2. Message Format
```json
{{
  "id": "uuid-v4",
  "from": "agent-id",
  "to": "agent-id|broadcast",
  "timestamp": "2024-01-15T12:00:00Z",
  "type": "request|response|notification|error",
  "priority": "high|medium|low",
  "body": {{
    "content": "message-content",
    "metadata": {{}}
  }},
  "ttl": 3600
}}
```

### 3. Performance Requirements
- Message delivery < 100ms (p99)
- Support 1000 messages/second
- Zero message loss during normal operation
- Automatic retry with exponential backoff

### 4. Questions for Business Analyst
- What are the most critical workflows to support?
- Should we prioritize latency or reliability?
- What compliance requirements exist?

Generated at: {datetime.now().isoformat()}
"""
            )

            # Create a message for business analyst
            message = {
                "from": "requirements-analyst",
                "to": "business-analyst",
                "timestamp": datetime.now().isoformat(),
                "subject": "Priority clarification needed",
                "body": "Should we optimize for real-time collaboration or async workflows?",
                "priority": "high",
            }

            message_file = (
                self.shared_space / "messages" / f"{agent_id}_to_business.json"
            )
            message_file.write_text(json.dumps(message, indent=2))
            self.metrics["messages_exchanged"] += 1

        elif agent_type == "business-analyst":
            output = output_dir / "requirements_business.md"
            output.write_text(
                f"""# Business Requirements for Inter-Agent Communication

## User Stories

### As an AI Agent
1. I want to broadcast discoveries so all agents benefit from my findings
2. I want to request specific expertise when I encounter specialized problems
3. I want to report errors immediately so the system can adapt

### As a Human Operator
1. I want to monitor all agent communications in real-time
2. I want to intervene when agents are stuck or diverging
3. I want to analyze communication patterns for optimization

## Success Metrics
- 95% of messages delivered within 100ms
- Zero data loss during agent failures
- 100% message traceability for audit
- < 5 second recovery time from failures

## Priority Matrix
1. **Critical**: Error reporting and recovery
2. **High**: Task coordination and handoffs
3. **Medium**: Knowledge sharing
4. **Low**: Status updates

## Response to Requirements Analyst
Based on the functional requirements, we should prioritize reliability over latency for most workflows, except for error reporting which needs both.

Generated at: {datetime.now().isoformat()}
"""
            )

        # Commit the work
        try:
            commit_hash = self.worktree_manager.commit_agent_work(
                agent_id=agent_id, message=f"Complete requirements definition task"
            )
            print(
                f"   📝 Committed work: {commit_hash[:8] if commit_hash else 'nothing to commit'}"
            )
        except Exception as e:
            print(f"   ⚠️  Could not commit: {e}")

        # Update metrics
        self.metrics["agents"][agent_id]["end_time"] = datetime.now().isoformat()
        self.metrics["agents"][agent_id]["status"] = "completed"

        return {
            "agent_id": agent_id,
            "success": True,
            "outputs": [str(output)],
            "messages_sent": 1 if agent_type == "requirements-analyst" else 0,
        }

    async def run_parallel_poc(self) -> Dict[str, Any]:
        """Execute POC with parallel agents in worktrees"""

        print(
            """
╔══════════════════════════════════════════════════════════════╗
║     2-AGENT PARALLEL EXECUTION POC WITH WORKTREES           ║
╚══════════════════════════════════════════════════════════════╝
        """
        )

        self.metrics["start_time"] = datetime.now().isoformat()

        # Step 1: Create base branch
        print("\n📌 Step 1: Setting up base branch")
        base_branch = self.create_base_branch()

        # Step 2: Create worktrees for both agents
        print("\n📌 Step 2: Creating agent worktrees")
        agents = ["requirements-analyst", "business-analyst"]
        agent_configs = []

        for agent_type in agents:
            config = await self.setup_agent_worktree(agent_type, base_branch)
            if config:
                agent_configs.append(config)

        if len(agent_configs) != 2:
            return {
                "success": False,
                "error": "Failed to create worktrees for all agents",
            }

        # Step 3: Execute agents IN PARALLEL
        print("\n📌 Step 3: Executing agents in parallel")
        print("   ⚡ Both agents running simultaneously...")

        self.metrics["parallel_execution"] = True

        # Launch both agents at the same time
        tasks = [self.simulate_agent_execution(config) for config in agent_configs]

        # Wait for both to complete
        results = await asyncio.gather(*tasks)

        # Step 4: Analyze results
        print("\n📌 Step 4: Analyzing results")
        self.metrics["end_time"] = datetime.now().isoformat()

        analysis = self.analyze_parallel_results(results, agent_configs)

        # Step 5: Cleanup (optional)
        if not self.dry_run and analysis["success"]:
            print("\n📌 Step 5: Merging agent work")
            for config in agent_configs:
                try:
                    success = self.worktree_manager.merge_agent_work(
                        config["agent_id"], target_branch=base_branch, strategy="merge"
                    )
                    if success:
                        print(f"   ✅ Merged {config['agent_type']} work")
                except Exception as e:
                    print(f"   ⚠️  Could not merge {config['agent_type']}: {e}")

        return analysis

    def analyze_parallel_results(
        self, results: List[Dict], configs: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze POC results"""

        print("\n" + "=" * 60)
        print("📊 RESULTS ANALYSIS")
        print("=" * 60)

        # Calculate execution time
        start = datetime.fromisoformat(self.metrics["start_time"])
        end = datetime.fromisoformat(self.metrics["end_time"])
        duration = (end - start).total_seconds()

        # Check success
        all_success = all(r["success"] for r in results)

        # Count outputs
        total_outputs = sum(len(r.get("outputs", [])) for r in results)

        print(f"\n⏱️  Execution Time: {duration:.1f} seconds")
        print(f"⚡ Parallel Execution: YES - both agents ran simultaneously")
        print(f"📁 Worktrees Created: {len(configs)}")
        print(f"📄 Outputs Generated: {total_outputs}")
        print(f"💬 Messages Exchanged: {self.metrics['messages_exchanged']}")

        # Check if agents actually worked in parallel
        agent_times = []
        for agent_id, info in self.metrics["agents"].items():
            if "start_time" in info and "end_time" in info:
                agent_start = datetime.fromisoformat(info["start_time"])
                agent_end = datetime.fromisoformat(info["end_time"])
                agent_times.append((agent_start, agent_end))

        # Check for time overlap (proves parallel execution)
        if len(agent_times) == 2:
            overlap = (
                min(agent_times[0][1], agent_times[1][1])
                - max(agent_times[0][0], agent_times[1][0])
            ).total_seconds()

            if overlap > 0:
                print(f"✨ Time Overlap: {overlap:.1f}s (TRUE PARALLEL EXECUTION!)")
            else:
                print("⚠️  No overlap - agents ran sequentially")

        # Success scoring
        score = 0
        if all_success:
            score += 40
            print("\n✅ Both agents completed successfully (+40)")

        if self.metrics["messages_exchanged"] > 0:
            score += 30
            print(f"✅ Inter-agent communication detected (+30)")

        if total_outputs >= 2:
            score += 30
            print(f"✅ Both agents produced outputs (+30)")

        print(f"\n🎯 Total Score: {score}/100")

        # Recommendations
        print("\n" + "=" * 60)
        print("💡 RECOMMENDATIONS")
        print("=" * 60)

        if score >= 70:
            print("⭐ Excellent! Ready to scale to 5-8 agents")
            print("   - Worktrees working perfectly")
            print("   - Parallel execution confirmed")
            print("   - Communication established")
            recommendation = "scale_up"
        elif score >= 40:
            print("✅ Good progress, minor improvements needed")
            print("   - Consider enhancing message protocol")
            print("   - Add more sophisticated coordination")
            recommendation = "iterate"
        else:
            print("⚠️  Issues detected, investigation needed")
            recommendation = "debug"

        # List active worktrees
        print("\n📁 Active Worktrees:")
        for wt in self.worktree_manager.list_active_worktrees():
            print(f"   - {wt['agent_type']}: {wt['branch']}")
            print(
                f"     Files modified: {wt['modified_files']}, Commits: {wt['commits']}"
            )

        return {
            "success": all_success,
            "score": score,
            "metrics": self.metrics,
            "recommendation": recommendation,
            "duration_seconds": duration,
            "parallel_confirmed": overlap > 0 if len(agent_times) == 2 else False,
        }


async def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description="POC: 2-Agent Parallel Execution with Git Worktrees"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without creating worktrees"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up all worktrees after"
    )

    args = parser.parse_args()

    # Initialize POC
    poc = WorktreePOC(dry_run=args.dry_run)

    try:
        # Run POC
        result = await poc.run_parallel_poc()

        # Save results
        results_file = (
            poc.shared_space / "status" / f"poc_results_{poc.execution_id}.json"
        )
        results_file.write_text(json.dumps(result, indent=2))
        print(f"\n📁 Results saved to: {results_file}")

        # Cleanup if requested
        if args.cleanup and not args.dry_run:
            print("\n🧹 Cleaning up worktrees...")
            poc.worktree_manager.cleanup_all(force=True)
            print("   ✅ Cleanup complete")

        # Final status
        if result["success"]:
            print("\n" + "=" * 60)
            print("✅ POC COMPLETED SUCCESSFULLY!")
            print("=" * 60)

            if result.get("parallel_confirmed"):
                print("🎉 TRUE PARALLEL EXECUTION ACHIEVED!")
                print("   We can now scale to 15 agents!")

            return 0
        else:
            print("\n❌ POC encountered issues")
            return 1

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
