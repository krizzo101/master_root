#!/usr/bin/env python3
"""
POC Launcher: 2-Agent Requirements Gathering Test
Tests if agents can collaborate on designing their own communication system
"""

import argparse
import asyncio
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration import ExecutionMode, SafeOrchestrator, SafetyLevel


class RequirementsPOC:
    """Proof of Concept for 2-agent collaboration"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.workspace = Path(
            "/home/opsvi/master_root/apps/multi-agent-monitor/missions/poc_workspace"
        )
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "messages_exchanged": 0,
            "files_created": 0,
            "tokens_used": {"agent1": 0, "agent2": 0},
            "errors": [],
        }

    def setup_workspace(self) -> bool:
        """Create workspace structure for agent collaboration"""
        print("\n📁 Setting up workspace...")

        # Create directories
        dirs = ["inputs", "outputs", "messages", "logs", "metrics"]
        for dir_name in dirs:
            dir_path = self.workspace / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ Created {dir_path}")

        # Create message bus file
        message_bus = self.workspace / "message_bus.json"
        if not message_bus.exists():
            message_bus.write_text(json.dumps({"messages": []}, indent=2))

        # Create status file
        status_file = self.workspace / "status.json"
        status = {
            "poc_id": f"poc_{self.timestamp}",
            "phase": "setup",
            "agents": {
                "requirements-analyst": {"status": "pending"},
                "business-analyst": {"status": "pending"},
            },
        }
        status_file.write_text(json.dumps(status, indent=2))

        return True

    def create_agent_tasks(self) -> Dict[str, str]:
        """Create task descriptions for each agent"""
        print("\n📝 Creating agent tasks...")

        # Task for Requirements Analyst
        task1 = """# Task: Design Requirements for Inter-Agent Communication System

You are Agent 1 (Requirements Analyst) working with Agent 2 (Business Analyst) to define requirements for an inter-agent communication system.

## Context
- We have 15 AI agents that need to coordinate
- Agents run in separate Claude sessions
- Real-time coordination is needed
- Human monitoring is required

## Your Responsibilities
1. Define functional requirements
2. Define technical requirements
3. Define performance requirements
4. Define security requirements

## Collaboration Instructions
- Check for messages from Agent 2 in: messages/
- Leave messages for Agent 2 about:
  - Areas where you need business context
  - Technical decisions that affect workflows
  - Questions about priorities

## Output Requirements
Create a structured requirements document in: outputs/requirements_functional.md

Include:
- System capabilities
- Message formats
- API specifications
- Storage requirements
- Performance targets
- Security constraints

## Message Protocol
When leaving messages, use this format:
```json
{
  "from": "requirements-analyst",
  "to": "business-analyst",
  "timestamp": "ISO-8601",
  "subject": "Brief subject",
  "body": "Message content",
  "requires_response": true/false
}
```

Remember: You're designing a system that YOU will use to communicate!
"""

        # Task for Business Analyst
        task2 = """# Task: Add Business Context to Communication System Requirements

You are Agent 2 (Business Analyst) working with Agent 1 (Requirements Analyst) to define requirements for an inter-agent communication system.

## Context
Agent 1 has started defining functional requirements. Your role is to add business context and use cases.

## Your Responsibilities
1. Review Agent 1's functional requirements
2. Define user workflows
3. Create use case scenarios
4. Define success metrics
5. Prioritize features

## Collaboration Instructions
- Check Agent 1's work in: outputs/requirements_functional.md
- Check for messages in: messages/
- Respond to Agent 1's questions
- Ask clarifying questions if needed

## Output Requirements
Create a business requirements document in: outputs/requirements_business.md

Include:
- User stories ("As an agent, I want to...")
- Workflow diagrams (text-based)
- Success criteria
- Failure scenarios
- Priority matrix (must-have, nice-to-have)

## Message Protocol
Same format as Agent 1 - maintain consistency!

## Key Questions to Address
- How will agents discover each other?
- What happens if an agent goes offline?
- How do we handle message priorities?
- What metrics determine success?

Remember: Think about how YOU as an agent would want to communicate!
"""

        # Save tasks
        task1_path = self.workspace / "inputs" / "task_requirements_analyst.md"
        task2_path = self.workspace / "inputs" / "task_business_analyst.md"

        task1_path.write_text(task1)
        task2_path.write_text(task2)

        print(f"   ✓ Created task for requirements-analyst")
        print(f"   ✓ Created task for business-analyst")

        return {
            "requirements-analyst": str(task1_path),
            "business-analyst": str(task2_path),
        }

    async def launch_agent(self, agent_type: str, task_file: str) -> Dict[str, Any]:
        """Launch a single agent with task"""

        if self.dry_run:
            print(f"\n🤖 [DRY RUN] Would launch: {agent_type}")
            print(f"   Task: {task_file}")
            await asyncio.sleep(2)  # Simulate work
            return {
                "success": True,
                "agent": agent_type,
                "output": "Dry run - no actual execution",
            }

        print(f"\n🚀 Launching {agent_type}...")

        # Update status
        status_file = self.workspace / "status.json"
        status = json.loads(status_file.read_text())
        status["agents"][agent_type]["status"] = "running"
        status["agents"][agent_type]["start_time"] = datetime.now().isoformat()
        status_file.write_text(json.dumps(status, indent=2))

        # TODO: Actually launch agent here
        # For now, simulate with placeholder

        print(f"   ⏳ Agent working...")
        await asyncio.sleep(5)  # Simulate agent work

        # Create mock output
        if agent_type == "requirements-analyst":
            output = self.workspace / "outputs" / "requirements_functional.md"
            output.write_text(
                """# Functional Requirements for Inter-Agent Communication

## Core Capabilities
1. Async message passing between agents
2. Broadcast capabilities for announcements
3. Direct agent-to-agent messaging
4. Message persistence and replay

## Message Format
```json
{
  "id": "uuid",
  "from": "agent-id",
  "to": "agent-id|broadcast",
  "timestamp": "ISO-8601",
  "type": "request|response|notification",
  "body": "content"
}
```

## Questions for Business Analyst
- What are the priority workflows?
- How should we handle agent failures?
- What monitoring is needed?
"""
            )

            # Leave a message
            message = {
                "from": "requirements-analyst",
                "to": "business-analyst",
                "timestamp": datetime.now().isoformat(),
                "subject": "Priority clarification needed",
                "body": "Which workflows are most critical? Real-time or async?",
                "requires_response": True,
            }
            message_file = (
                self.workspace / "messages" / f"{self.timestamp}_req_to_biz.json"
            )
            message_file.write_text(json.dumps(message, indent=2))
            self.metrics["messages_exchanged"] += 1

        elif agent_type == "business-analyst":
            output = self.workspace / "outputs" / "requirements_business.md"
            output.write_text(
                """# Business Requirements for Inter-Agent Communication

## User Stories
1. As an agent, I want to broadcast discoveries to all other agents
2. As an agent, I want to request specific expertise from specialists
3. As a human operator, I want to monitor all agent communications

## Priority Workflows
1. **Critical**: Error reporting and recovery coordination
2. **High**: Task handoffs between specialized agents
3. **Medium**: Progress updates and status reports
4. **Low**: General knowledge sharing

## Success Metrics
- Message delivery < 1 second
- Zero message loss
- 100% message traceability
"""
            )

        self.metrics["files_created"] += 1

        # Update status
        status["agents"][agent_type]["status"] = "completed"
        status["agents"][agent_type]["end_time"] = datetime.now().isoformat()
        status_file.write_text(json.dumps(status, indent=2))

        print(f"   ✅ {agent_type} completed!")

        return {
            "success": True,
            "agent": agent_type,
            "output": str(output) if "output" in locals() else "No output",
        }

    async def run_poc(self) -> Dict[str, Any]:
        """Execute the full POC"""

        print(
            """
╔══════════════════════════════════════════════════════════════╗
║          2-AGENT REQUIREMENTS GATHERING POC                  ║
╚══════════════════════════════════════════════════════════════╝
        """
        )

        self.metrics["start_time"] = datetime.now().isoformat()

        # Setup
        if not self.setup_workspace():
            return {"success": False, "error": "Workspace setup failed"}

        # Create tasks
        tasks = self.create_agent_tasks()

        # Launch agents sequentially with gap for collaboration
        results = []

        # Agent 1
        result1 = await self.launch_agent(
            "requirements-analyst", tasks["requirements-analyst"]
        )
        results.append(result1)

        print("\n⏸️  Waiting 10 seconds for message checking opportunity...")
        await asyncio.sleep(10)

        # Agent 2
        result2 = await self.launch_agent("business-analyst", tasks["business-analyst"])
        results.append(result2)

        self.metrics["end_time"] = datetime.now().isoformat()

        # Analyze results
        return self.analyze_results(results)

    def analyze_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze POC results and determine success"""

        print("\n📊 Analyzing Results...")

        # Check outputs
        outputs = list(self.workspace.glob("outputs/*.md"))
        messages = list(self.workspace.glob("messages/*.json"))

        analysis = {
            "success": True,
            "metrics": self.metrics,
            "outputs": [str(o) for o in outputs],
            "messages": [str(m) for m in messages],
            "collaboration_score": 0,
        }

        # Calculate collaboration score
        if len(outputs) >= 2:
            analysis["collaboration_score"] += 40
            print("   ✓ Both agents produced outputs (+40)")

        if len(messages) >= 1:
            analysis["collaboration_score"] += 30
            print(f"   ✓ {len(messages)} messages exchanged (+30)")

        # Check if outputs reference each other
        if len(outputs) == 2:
            content1 = outputs[0].read_text()
            content2 = outputs[1].read_text()

            if "business" in content1.lower() or "requirements" in content2.lower():
                analysis["collaboration_score"] += 30
                print("   ✓ Agents referenced each other's work (+30)")

        # Summary
        print(f"\n🎯 Collaboration Score: {analysis['collaboration_score']}/100")

        if analysis["collaboration_score"] >= 70:
            print("   ⭐ Excellent collaboration!")
            analysis["recommendation"] = "Ready to scale to 3-5 agents"
        elif analysis["collaboration_score"] >= 40:
            print("   ✅ Good collaboration")
            analysis["recommendation"] = "Minor improvements needed before scaling"
        else:
            print("   ⚠️ Limited collaboration")
            analysis["recommendation"] = "Address issues before scaling"

        # Save analysis
        analysis_file = self.workspace / "metrics" / f"analysis_{self.timestamp}.json"
        analysis_file.write_text(json.dumps(analysis, indent=2))

        print(f"\n📁 Full analysis saved to: {analysis_file}")

        return analysis


async def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description="Launch 2-Agent Requirements POC")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without launching agents"
    )
    parser.add_argument("--agents", nargs="+", help="Specific agents to launch")
    parser.add_argument(
        "--test", action="store_true", help="Test mode with single agent"
    )

    args = parser.parse_args()

    # Initialize POC
    poc = RequirementsPOC(dry_run=args.dry_run)

    # Run POC
    result = await poc.run_poc()

    # Final status
    if result["success"]:
        print("\n✅ POC completed successfully!")
    else:
        print(f"\n❌ POC failed: {result.get('error', 'Unknown error')}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
