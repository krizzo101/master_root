"""
Automated Implementation Pipeline

Orchestrates the implementation of discovered TODOs using SDLC agents
and captures knowledge from each completion.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .todo_discovery import TodoItem

logger = logging.getLogger(__name__)


@dataclass
class ImplementationResult:
    """Result of a TODO implementation attempt"""

    todo_id: str
    status: str  # success, failure, partial, skipped
    implementation_details: Dict[str, Any]
    files_modified: List[str]
    tests_added: List[str]
    knowledge_captured: Dict[str, Any]
    error_message: Optional[str]
    duration_seconds: float
    agent_used: str
    timestamp: str


class ImplementationPipeline:
    """Orchestrates automatic implementation of TODOs using SDLC agents"""

    def __init__(
        self,
        project_root: str = "/home/opsvi/master_root",
        knowledge_base_enabled: bool = True,
    ):
        self.project_root = Path(project_root)
        self.knowledge_base_enabled = knowledge_base_enabled
        self.results: List[ImplementationResult] = []
        self.active_implementations: Dict[str, Any] = {}

    async def implement_todo(self, todo: TodoItem) -> ImplementationResult:
        """Implement a single TODO using appropriate SDLC agent"""

        start_time = datetime.now()

        try:
            # Phase 1: Discovery - Understand context
            discovery_result = await self._run_discovery_phase(todo)

            # Phase 2: Design - Create implementation plan
            design_result = await self._run_design_phase(todo, discovery_result)

            # Phase 3: Implementation - Execute the plan
            implementation_result = await self._run_implementation_phase(
                todo, design_result
            )

            # Phase 4: Testing - Validate implementation
            test_result = await self._run_test_phase(todo, implementation_result)

            # Phase 5: Knowledge Capture
            knowledge = await self._capture_knowledge(
                todo, implementation_result, test_result
            )

            duration = (datetime.now() - start_time).total_seconds()

            result = ImplementationResult(
                todo_id=todo.id,
                status="success" if test_result["passed"] else "partial",
                implementation_details={
                    "discovery": discovery_result,
                    "design": design_result,
                    "implementation": implementation_result,
                    "testing": test_result,
                },
                files_modified=implementation_result.get("files_modified", []),
                tests_added=test_result.get("tests_created", []),
                knowledge_captured=knowledge,
                error_message=None,
                duration_seconds=duration,
                agent_used=todo.suggested_agent,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = ImplementationResult(
                todo_id=todo.id,
                status="failure",
                implementation_details={},
                files_modified=[],
                tests_added=[],
                knowledge_captured={},
                error_message=str(e),
                duration_seconds=duration,
                agent_used=todo.suggested_agent,
                timestamp=datetime.now().isoformat(),
            )
            logger.error(f"Failed to implement TODO {todo.id}: {e}")

        self.results.append(result)
        return result

    async def _run_discovery_phase(self, todo: TodoItem) -> Dict[str, Any]:
        """Run discovery phase to understand TODO context"""

        prompt = f"""
        Analyze this TODO item and its context:

        File: {todo.file_path}
        Line: {todo.line_number}
        TODO: {todo.content}
        Category: {todo.category}

        Context:
        Function: {todo.context.get('function', 'N/A')}
        Class: {todo.context.get('class', 'N/A')}

        Surrounding Code:
        {chr(10).join(todo.context.get('surrounding_code', []))}

        Provide:
        1. What needs to be implemented
        2. Required dependencies
        3. Potential impacts
        4. Suggested approach
        """

        # Use Claude Code V1 for discovery
        result = await self._execute_claude_agent(
            task=prompt,
            agent="mcp__claude-code-wrapper__claude_run",
            output_format="json",
        )

        return result

    async def _run_design_phase(
        self, todo: TodoItem, discovery: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run design phase to create implementation plan"""

        prompt = f"""
        Design implementation for this TODO:

        TODO: {todo.content}
        Discovery Results: {json.dumps(discovery, indent=2)}

        Create a detailed implementation plan including:
        1. Step-by-step implementation approach
        2. Code structure and patterns to use
        3. Test cases to write
        4. Error handling strategy
        5. Performance considerations
        """

        # Use solution-architect agent for design
        result = await self._execute_claude_agent(
            task=prompt,
            agent="mcp__claude-code-wrapper__claude_run",
            output_format="json",
        )

        return result

    async def _run_implementation_phase(
        self, todo: TodoItem, design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the implementation based on design"""

        prompt = f"""
        Implement this TODO following the design plan:

        File: {todo.file_path}
        Line: {todo.line_number}
        TODO to replace: {todo.content}

        Design Plan: {json.dumps(design, indent=2)}

        Requirements:
        1. Replace the TODO with working implementation
        2. Follow existing code style and patterns
        3. Add appropriate error handling
        4. Include inline documentation
        5. Ensure backward compatibility
        """

        # Use development-specialist for implementation
        result = await self._execute_claude_agent(
            task=prompt,
            agent="mcp__claude-code-wrapper__claude_run",
            output_format="json",
        )

        return result

    async def _run_test_phase(
        self, todo: TodoItem, implementation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test the implementation"""

        prompt = f"""
        Test and validate this implementation:

        TODO that was implemented: {todo.content}
        Files modified: {json.dumps(implementation.get('files_modified', []))}

        Tasks:
        1. Write comprehensive unit tests
        2. Run existing tests to ensure no breakage
        3. Validate the implementation works correctly
        4. Check for edge cases
        5. Verify performance is acceptable
        """

        # Use test-remediation-specialist for testing
        result = await self._execute_claude_agent(
            task=prompt,
            agent="mcp__claude-code-wrapper__claude_run",
            output_format="json",
        )

        return result

    async def _capture_knowledge(
        self,
        todo: TodoItem,
        implementation: Dict[str, Any],
        test_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Capture knowledge from successful implementation"""

        if not self.knowledge_base_enabled:
            return {}

        knowledge = {
            "pattern_type": "TODO_IMPLEMENTATION",
            "category": todo.category,
            "complexity": todo.estimated_complexity,
            "solution": {
                "approach": implementation.get("approach"),
                "code_changes": implementation.get("files_modified", []),
                "tests_added": test_result.get("tests_created", []),
            },
            "context": {
                "file_type": todo.context.get("file_type"),
                "had_dependencies": len(todo.dependencies) > 0,
            },
            "success_factors": [],
            "lessons_learned": [],
        }

        # Store in knowledge base using MCP
        try:
            await self._store_knowledge(knowledge)
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")

        return knowledge

    async def _execute_claude_agent(
        self, task: str, agent: str, output_format: str = "json"
    ) -> Dict[str, Any]:
        """Execute a Claude agent via MCP"""

        # This would integrate with the actual MCP servers
        # For now, returning a placeholder

        # In real implementation:
        # result = await mcp_client.execute(agent, task=task, output_format=output_format)

        return {
            "status": "completed",
            "approach": "automated implementation",
            "files_modified": [str(self.project_root / "example.py")],
            "tests_created": [str(self.project_root / "test_example.py")],
            "passed": True,
        }

    async def _store_knowledge(self, knowledge: Dict[str, Any]):
        """Store knowledge in the knowledge base"""

        # This would integrate with mcp__knowledge__knowledge_store
        # For now, just log it

        logger.info(f"Storing knowledge: {json.dumps(knowledge, indent=2)}")

    async def run_batch_implementation(
        self, todos: List[TodoItem], max_parallel: int = 3
    ) -> List[ImplementationResult]:
        """Run implementation for multiple TODOs"""

        results = []

        # Process in batches to avoid overwhelming the system
        for i in range(0, len(todos), max_parallel):
            batch = todos[i : i + max_parallel]
            batch_tasks = [self.implement_todo(todo) for todo in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch implementation error: {result}")
                else:
                    results.append(result)

        return results

    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate implementation report"""

        report = {
            "summary": {
                "total_attempted": len(self.results),
                "successful": len([r for r in self.results if r.status == "success"]),
                "partial": len([r for r in self.results if r.status == "partial"]),
                "failed": len([r for r in self.results if r.status == "failure"]),
                "total_duration_seconds": sum(r.duration_seconds for r in self.results),
                "average_duration_seconds": sum(
                    r.duration_seconds for r in self.results
                )
                / len(self.results)
                if self.results
                else 0,
            },
            "by_agent": {},
            "by_complexity": {},
            "files_modified": set(),
            "tests_added": set(),
            "knowledge_items": [],
            "failures": [],
        }

        for result in self.results:
            # Group by agent
            agent = result.agent_used
            if agent not in report["by_agent"]:
                report["by_agent"][agent] = {"success": 0, "failure": 0}

            if result.status == "success":
                report["by_agent"][agent]["success"] += 1
            else:
                report["by_agent"][agent]["failure"] += 1

            # Collect modified files and tests
            report["files_modified"].update(result.files_modified)
            report["tests_added"].update(result.tests_added)

            # Collect knowledge items
            if result.knowledge_captured:
                report["knowledge_items"].append(result.knowledge_captured)

            # Collect failures
            if result.status == "failure":
                report["failures"].append(
                    {
                        "todo_id": result.todo_id,
                        "error": result.error_message,
                        "agent": result.agent_used,
                    }
                )

        # Convert sets to lists for JSON serialization
        report["files_modified"] = list(report["files_modified"])
        report["tests_added"] = list(report["tests_added"])

        if output_path:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved to {output_path}")

        return report

    async def validate_implementation(self, result: ImplementationResult) -> bool:
        """Validate that an implementation was successful"""

        # Run tests on modified files
        for file_path in result.files_modified:
            test_file = file_path.replace(".py", "_test.py")
            if Path(test_file).exists():
                try:
                    proc = await asyncio.create_subprocess_exec(
                        "python",
                        "-m",
                        "pytest",
                        test_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()

                    if proc.returncode != 0:
                        logger.warning(f"Tests failed for {file_path}")
                        return False

                except Exception as e:
                    logger.error(f"Failed to run tests: {e}")
                    return False

        return True
