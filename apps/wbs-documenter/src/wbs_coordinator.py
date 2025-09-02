#!/usr/bin/env python3
"""
WBS Coordinator - Inter-agent communication and dependency management
Uses file-based IPC with message queue patterns
"""

import asyncio
import json
import queue
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class AgentMessage:
    """Message between agents"""

    id: str
    sender: str
    receiver: str
    msg_type: str  # 'context', 'boundary', 'validation', 'complete'
    payload: Dict
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()


class FileBasedMessageQueue:
    """File-based message queue for inter-agent communication"""

    def __init__(self, queue_dir: Path):
        self.queue_dir = queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_dir = queue_dir / "inbox"
        self.outbox_dir = queue_dir / "outbox"
        self.processed_dir = queue_dir / "processed"

        for d in [self.inbox_dir, self.outbox_dir, self.processed_dir]:
            d.mkdir(exist_ok=True)

    async def send(self, message: AgentMessage):
        """Send message to agent's inbox"""
        receiver_inbox = self.inbox_dir / message.receiver
        receiver_inbox.mkdir(exist_ok=True)

        msg_file = receiver_inbox / f"{message.timestamp}_{message.id}.json"
        msg_file.write_text(json.dumps(asdict(message), indent=2))

    async def receive(
        self, agent_id: str, timeout: float = None
    ) -> Optional[AgentMessage]:
        """Receive next message for agent"""
        agent_inbox = self.inbox_dir / agent_id

        if not agent_inbox.exists():
            return None

        # Get oldest unprocessed message
        messages = sorted(agent_inbox.glob("*.json"))

        if messages:
            msg_file = messages[0]
            data = json.loads(msg_file.read_text())

            # Move to processed
            processed_file = self.processed_dir / msg_file.name
            msg_file.rename(processed_file)

            return AgentMessage(**data)

        return None

    async def broadcast(
        self, sender: str, msg_type: str, payload: Dict, receivers: List[str]
    ):
        """Broadcast message to multiple agents"""
        for receiver in receivers:
            msg = AgentMessage(
                id=f"{sender}_{datetime.now().timestamp()}",
                sender=sender,
                receiver=receiver,
                msg_type=msg_type,
                payload=payload,
            )
            await self.send(msg)


class DependencyGraph:
    """Manages dependencies between documentation sections"""

    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = {}
        self.completed: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.lock = asyncio.Lock()

    def add_dependency(self, task: str, depends_on: List[str]):
        """Add dependency relationship"""
        if task not in self.dependencies:
            self.dependencies[task] = set()
        self.dependencies[task].update(depends_on)

    async def can_start(self, task: str) -> bool:
        """Check if task can start based on dependencies"""
        async with self.lock:
            deps = self.dependencies.get(task, set())
            return all(dep in self.completed for dep in deps)

    async def mark_started(self, task: str):
        """Mark task as started"""
        async with self.lock:
            self.in_progress.add(task)

    async def mark_completed(self, task: str):
        """Mark task as completed"""
        async with self.lock:
            self.in_progress.discard(task)
            self.completed.add(task)

    async def get_ready_tasks(self, all_tasks: List[str]) -> List[str]:
        """Get all tasks ready to execute"""
        ready = []
        for task in all_tasks:
            if task not in self.completed and task not in self.in_progress:
                if await self.can_start(task):
                    ready.append(task)
        return ready


class HierarchyManager:
    """Manages the WBS hierarchy and context propagation"""

    def __init__(self, structure_file: Path = None):
        self.hierarchy = {}
        self.load_structure(structure_file)

    def load_structure(self, structure_file: Path = None):
        """Load WBS structure from file or create default"""

        # Default 12-stage structure
        self.hierarchy = {
            "stages": {
                1: {
                    "title": "Requirements Gathering",
                    "steps": {
                        1: {"title": "Stakeholder Analysis", "actions": 4},
                        2: {"title": "Requirements Elicitation", "actions": 5},
                        3: {"title": "Requirements Documentation", "actions": 3},
                        4: {"title": "Requirements Validation", "actions": 4},
                    },
                },
                2: {
                    "title": "System Design",
                    "steps": {
                        1: {"title": "Architecture Design", "actions": 5},
                        2: {"title": "Interface Design", "actions": 4},
                        3: {"title": "Database Design", "actions": 4},
                        4: {"title": "Security Design", "actions": 3},
                    },
                },
                # ... continue for all 12 stages
            }
        }

    def get_context(self, level: str, position: tuple) -> Dict:
        """Get context for a specific position in hierarchy"""

        context = {"level": level, "position": position}

        if level == "stage":
            stage_num = position[0]
            stage = self.hierarchy["stages"].get(stage_num, {})
            context["title"] = stage.get("title", f"Stage {stage_num}")
            context["parent"] = "Auto-Coding Solution"

            # Get siblings
            context["prev_sibling"] = (
                self.hierarchy["stages"].get(stage_num - 1, {}).get("title")
            )
            context["next_sibling"] = (
                self.hierarchy["stages"].get(stage_num + 1, {}).get("title")
            )

        elif level == "step":
            stage_num, step_num = position
            stage = self.hierarchy["stages"].get(stage_num, {})
            step = stage.get("steps", {}).get(step_num, {})

            context["title"] = step.get("title", f"Step {step_num}")
            context["parent"] = stage.get("title", f"Stage {stage_num}")

        # Add boundary information
        context["boundaries"] = self.get_boundaries(level, position)

        return context

    def get_boundaries(self, level: str, position: tuple) -> Dict:
        """Get boundary definitions for a section"""

        boundaries = {"start": "Beginning of section", "end": "End of section"}

        if level == "stage" and position[0] > 1:
            prev_stage = self.hierarchy["stages"].get(position[0] - 1, {})
            boundaries[
                "start"
            ] = f"After completion of {prev_stage.get('title', 'previous stage')}"

        if level == "stage" and position[0] < 12:
            next_stage = self.hierarchy["stages"].get(position[0] + 1, {})
            boundaries[
                "end"
            ] = f"Before start of {next_stage.get('title', 'next stage')}"

        return boundaries

    def get_children(self, level: str, position: tuple) -> List[Dict]:
        """Get child sections for a position"""

        children = []

        if level == "stage":
            stage_num = position[0]
            stage = self.hierarchy["stages"].get(stage_num, {})

            for step_num, step in stage.get("steps", {}).items():
                children.append(
                    {
                        "level": "step",
                        "position": (stage_num, step_num),
                        "title": step["title"],
                    }
                )

        return children


class ValidationEngine:
    """Validates generated documentation for consistency"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.validation_results = {}

    async def validate_section(self, section_file: Path) -> Dict:
        """Validate a documentation section"""

        if not section_file.exists():
            return {"valid": False, "errors": ["File not found"]}

        content = section_file.read_text()
        errors = []
        warnings = []

        # Check minimum length
        if len(content) < 500:
            warnings.append("Content seems too short")

        # Check for required sections based on level
        if "stage" in section_file.name:
            required = ["## Overview", "## Key Objectives", "## Steps"]
        elif "step" in section_file.name:
            required = ["### Purpose", "### Activities", "### Actions"]
        else:
            required = []

        for section in required:
            if section not in content:
                errors.append(f"Missing required section: {section}")

        # Check for placeholder text
        if "[Title]" in content or "[Number]" in content:
            errors.append("Contains placeholder text")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "file": str(section_file),
        }

    async def validate_hierarchy(self, level: str) -> Dict:
        """Validate all sections at a level"""

        level_dir = self.output_dir / f"{level}s"
        results = {"level": level, "total": 0, "valid": 0, "invalid": 0, "sections": []}

        if level_dir.exists():
            for section_file in sorted(level_dir.glob(f"{level}_*.md")):
                validation = await self.validate_section(section_file)
                results["sections"].append(validation)
                results["total"] += 1

                if validation["valid"]:
                    results["valid"] += 1
                else:
                    results["invalid"] += 1

        self.validation_results[level] = results
        return results

    async def cross_validate(self, parent_file: Path, child_files: List[Path]) -> Dict:
        """Cross-validate parent and child sections"""

        if not parent_file.exists():
            return {"valid": False, "error": "Parent file not found"}

        parent_content = parent_file.read_text()
        issues = []

        for child_file in child_files:
            if child_file.exists():
                child_content = child_file.read_text()

                # Check if child is referenced in parent
                child_name = child_file.stem
                if child_name not in parent_content:
                    issues.append(f"Child {child_name} not referenced in parent")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "parent": str(parent_file),
            "children": [str(f) for f in child_files],
        }


class WBSCoordinator:
    """Main coordinator bringing everything together"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.coord_dir = project_dir / "coordination"
        self.coord_dir.mkdir(exist_ok=True)

        # Initialize components
        self.message_queue = FileBasedMessageQueue(self.coord_dir / "messages")
        self.dependency_graph = DependencyGraph()
        self.hierarchy = HierarchyManager()
        self.validator = ValidationEngine(project_dir / "wbs_documentation")

    async def setup_dependencies(self):
        """Setup dependency graph for WBS structure"""

        # Stages have no dependencies (can run in parallel)
        for i in range(1, 13):
            self.dependency_graph.add_dependency(f"stage_{i}", [])

        # Steps depend on their parent stage
        for stage_num in range(1, 13):
            for step_num in range(1, 5):  # Assuming 4 steps per stage
                step_id = f"step_{stage_num}_{step_num}"
                self.dependency_graph.add_dependency(step_id, [f"stage_{stage_num}"])

        # Actions depend on their parent step
        # Operations depend on their parent action
        # (Continue pattern...)

    async def coordinate_execution(self, all_tasks: List[str]) -> Dict:
        """Coordinate task execution based on dependencies"""

        results = {"executed": [], "pending": [], "failed": []}

        while len(results["executed"]) < len(all_tasks):
            # Get ready tasks
            ready = await self.dependency_graph.get_ready_tasks(all_tasks)

            if not ready:
                # Check for deadlock
                if len(results["executed"]) + len(results["failed"]) < len(all_tasks):
                    print("WARNING: Potential deadlock detected")
                    results["pending"] = [
                        t
                        for t in all_tasks
                        if t not in results["executed"] and t not in results["failed"]
                    ]
                break

            # Mark tasks as started
            for task in ready:
                await self.dependency_graph.mark_started(task)

            # Execute ready tasks (would call orchestrator here)
            # For now, simulate completion
            await asyncio.sleep(0.1)

            # Mark as completed
            for task in ready:
                await self.dependency_graph.mark_completed(task)
                results["executed"].append(task)

                # Send completion message to dependents
                await self.message_queue.broadcast(
                    sender=task,
                    msg_type="complete",
                    payload={"status": "success"},
                    receivers=self._get_dependents(task, all_tasks),
                )

        return results

    def _get_dependents(self, task: str, all_tasks: List[str]) -> List[str]:
        """Get tasks that depend on the given task"""
        dependents = []
        for other_task in all_tasks:
            deps = self.dependency_graph.dependencies.get(other_task, set())
            if task in deps:
                dependents.append(other_task)
        return dependents

    async def run_validation_cycle(self):
        """Run full validation cycle"""

        print("Running validation cycle...")

        # Validate each level
        for level in ["stage", "step", "action", "operation"]:
            result = await self.validator.validate_hierarchy(level)
            print(f"{level.capitalize()}s: {result['valid']}/{result['total']} valid")

            # Report issues
            for section in result["sections"]:
                if not section["valid"]:
                    print(f"  ❌ {section['file']}: {section['errors']}")

        return self.validator.validation_results


# Example usage
async def test_coordinator():
    """Test the coordination system"""

    project_dir = Path("/home/opsvi/spawn-test")
    coordinator = WBSCoordinator(project_dir)

    # Setup dependencies
    await coordinator.setup_dependencies()

    # Create task list
    tasks = [f"stage_{i}" for i in range(1, 13)]

    # Coordinate execution
    results = await coordinator.coordinate_execution(tasks)

    print(f"Executed: {len(results['executed'])} tasks")
    print(f"Pending: {len(results['pending'])} tasks")
    print(f"Failed: {len(results['failed'])} tasks")


if __name__ == "__main__":
    asyncio.run(test_coordinator())
