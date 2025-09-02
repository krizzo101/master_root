#!/usr/bin/env python3
"""
WBS Documentation Implementation
Uses the generic orchestrator for the specific WBS documentation use case
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from generic_orchestrator import AgentTask, GenericOrchestrator

logger = logging.getLogger(__name__)


class WBSDocumentationOrchestrator:
    """
    Specific implementation for WBS documentation generation.
    The agents will determine the actual structure, not enforce a preset number.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.output_dir = project_dir / "wbs_output"

        # Initialize generic orchestrator
        self.orchestrator = GenericOrchestrator(
            output_dir=self.output_dir, max_parallel=10, use_optimizations=True
        )

        # Set up hooks
        self.orchestrator.task_builder_hook = self.build_agent_prompt
        self.orchestrator.post_execute_hook = self.handle_agent_completion

        # Track discovered structure
        self.discovered_structure = {"stages": {}, "total_elements": 0}

    async def build_agent_prompt(self, task: AgentTask) -> str:
        """Build contextualized prompt for each agent"""

        base_prompt = f"""You are documenting part of an auto-coding solution.

IMPORTANT: You determine the appropriate breakdown and structure based on the content,
not a predetermined number. Create as many or as few subsections as make logical sense.

Task Type: {task.task_type}
Task: {task.prompt}

Context:
{json.dumps(task.context, indent=2)}

Instructions:
1. Analyze what needs to be documented
2. Determine the logical breakdown (don't force a specific number)
3. Create comprehensive documentation
4. List any subsections that should be documented separately
5. Save your output to: {self.output_dir}/docs/{task.task_id}.md

Output Format:
- Use clear markdown structure
- Include a "Subsections" list at the end if this section should be broken down further
- Be thorough but concise
- Focus on practical, implementable details"""

        return base_prompt

    async def handle_agent_completion(self, task: AgentTask):
        """Process completed agent task and potentially spawn new tasks"""

        if task.status != "completed":
            return

        # Check if the agent identified subsections to document
        output_file = self.output_dir / "docs" / f"{task.task_id}.md"

        if output_file.exists():
            content = output_file.read_text()

            # Look for subsections list (agents will generate this)
            if "## Subsections" in content or "### Subsections" in content:
                # Extract and queue new tasks for subsections
                # This would be parsed from the agent's output
                logger.info(
                    f"Agent {task.task_id} identified subsections for further documentation"
                )

    def generate_initial_tasks(self) -> List[AgentTask]:
        """Generate the initial high-level tasks to start the cascade"""

        # Start with discovery phase - let agents determine the structure
        initial_tasks = []

        # Phase 1: Research and discovery
        initial_tasks.append(
            AgentTask(
                task_id="discovery_research",
                task_type="research",
                prompt="Research and identify all major stages needed for a comprehensive auto-coding solution. Consider the full software development lifecycle.",
                context={
                    "purpose": "Identify high-level stages",
                    "note": "Determine the actual number and nature of stages based on research",
                },
            )
        )

        # Phase 2: Structure definition (depends on research)
        initial_tasks.append(
            AgentTask(
                task_id="structure_definition",
                task_type="architect",
                prompt="Based on the research, define the complete WBS structure for the auto-coding solution. Create the hierarchy of stages, steps, actions, and operations.",
                dependencies=["discovery_research"],
                context={
                    "purpose": "Define the full WBS structure",
                    "note": "The structure should emerge from analysis, not be predetermined",
                },
            )
        )

        # Phase 3: Stage documentation (depends on structure)
        initial_tasks.append(
            AgentTask(
                task_id="stage_documentation_coordinator",
                task_type="coordinator",
                prompt="Coordinate the documentation of all identified stages. Create individual documentation tasks for each stage discovered.",
                dependencies=["structure_definition"],
                context={
                    "purpose": "Orchestrate stage documentation",
                    "note": "Create as many stage documentation tasks as identified",
                },
            )
        )

        return initial_tasks

    def generate_cascade_tasks(self, structure: Dict) -> List[AgentTask]:
        """
        Generate documentation tasks based on discovered structure.
        This would be called after the initial discovery phase.
        """

        tasks = []

        # This is where we'd generate tasks based on what the agents discovered
        # Rather than assuming 12 stages or any specific number

        for stage_id, stage_info in structure.get("stages", {}).items():
            # Create stage documentation task
            tasks.append(
                AgentTask(
                    task_id=f"stage_{stage_id}",
                    task_type="documentation",
                    prompt=f"Document {stage_info['title']}",
                    context={
                        "level": "stage",
                        "info": stage_info,
                        "parent": "Auto-Coding Solution",
                    },
                )
            )

            # Let each stage agent determine its own steps
            # They will output what subsections are needed

        return tasks

    async def run_adaptive_orchestration(self):
        """
        Run orchestration that adapts to discovered structure.
        Doesn't assume 1,872 or any specific number of elements.
        """

        logger.info("=" * 60)
        logger.info("WBS Documentation - Adaptive Orchestration")
        logger.info("Agents will determine the actual structure")
        logger.info("=" * 60)

        # Phase 1: Discovery
        initial_tasks = self.generate_initial_tasks()
        results = await self.orchestrator.execute_batch(initial_tasks)

        # Analyze discovery results
        structure_file = self.output_dir / "docs" / "structure_definition.md"
        if structure_file.exists():
            # Parse the discovered structure
            # This would extract the actual WBS from the agent's output
            logger.info(
                "Structure discovered by agents - proceeding with documentation"
            )

        # Phase 2: Human review point
        print("\n⚠️  HUMAN REVIEW CHECKPOINT")
        print("The agents have identified the structure.")
        print(f"Review the discovered structure at: {structure_file}")
        input("Press Enter to proceed with full documentation...")

        # Phase 3: Cascade documentation based on discovered structure
        # This would continue iteratively, with each level of agents
        # determining what needs to be documented at the next level

        logger.info("Documentation cascade beginning...")
        # The cascade would continue until no more subsections are identified

        return {
            "discovered_structure": self.discovered_structure,
            "output_dir": str(self.output_dir),
        }


async def main():
    """Main entry point"""

    project_dir = Path("/home/opsvi/spawn-test")

    # Create WBS orchestrator
    wbs = WBSDocumentationOrchestrator(project_dir)

    # Run adaptive orchestration
    result = await wbs.run_adaptive_orchestration()

    print(f"\nDocumentation generated at: {result['output_dir']}")
    print(
        f"Total elements documented: {result['discovered_structure'].get('total_elements', 'TBD')}"
    )


if __name__ == "__main__":
    asyncio.run(main())
