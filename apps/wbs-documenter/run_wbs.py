#!/usr/bin/env python3
"""
WBS Documenter - Production Run Script
Uses the working agent-orchestrator with 15 parallel tokens
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add agent-orchestrator to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent-orchestrator" / "src"))

from generic_orchestrator import AgentTask, GenericOrchestrator


class WBSDocumenter:
    """WBS documentation system using parallel agents"""

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            output_dir = Path("./wbs_output") / datetime.now().strftime("%Y%m%d_%H%M%S")

        self.output_dir = output_dir
        self.docs_dir = output_dir / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize orchestrator with full parallelism
        self.orchestrator = GenericOrchestrator(
            output_dir=output_dir,
            max_parallel=15,  # Use all available tokens
            use_optimizations=True,
        )

        # Structure tracking
        self.discovered_structure = {
            "stages": [],
            "total_elements": 0,
            "timestamp": datetime.now().isoformat(),
        }

        print(f"✅ WBS Documenter initialized")
        print(f"📊 Token pool size: {self.orchestrator.token_pool.size()}")
        print(f"⚡ Max parallelism: {self.orchestrator.max_parallel}")
        print(f"📁 Output directory: {self.output_dir}")

    async def phase1_discovery(self) -> Dict:
        """Phase 1: Research and structure discovery"""

        print("\n" + "=" * 60)
        print("PHASE 1: DISCOVERY & RESEARCH")
        print("=" * 60)

        discovery_tasks = [
            AgentTask(
                task_id="research_autocoding",
                task_type="research",
                prompt="""Research and identify all major components needed for a comprehensive auto-coding solution.
                Consider the full software development lifecycle from requirements to deployment.
                List 10-15 major stages that would be needed.""",
            ),
            AgentTask(
                task_id="research_best_practices",
                task_type="research",
                prompt="""Research industry best practices for automated code generation systems.
                Focus on architecture patterns, testing strategies, and deployment approaches.""",
            ),
            AgentTask(
                task_id="research_tools",
                task_type="research",
                prompt="""Research current tools and technologies used in auto-coding solutions.
                Include AI models, development frameworks, testing tools, and deployment platforms.""",
            ),
            AgentTask(
                task_id="define_structure",
                task_type="architect",
                prompt="""Based on research about auto-coding solutions, define a comprehensive WBS structure.
                Create a hierarchical breakdown with stages, steps, actions, and operations.
                Output a clear structure that others can follow.""",
                dependencies=[
                    "research_autocoding",
                    "research_best_practices",
                    "research_tools",
                ],
            ),
        ]

        print(f"📋 Executing {len(discovery_tasks)} discovery tasks...")
        start_time = time.time()

        results = await self.orchestrator.execute_batch(discovery_tasks)

        duration = time.time() - start_time
        completed = sum(1 for r in results if r.get("status") == "completed")

        print(f"✅ Discovery complete: {completed}/{len(discovery_tasks)} tasks")
        print(f"⏱️  Duration: {duration:.2f}s")

        # Extract structure from results
        for result in results:
            if (
                result.get("task_id") == "define_structure"
                and result.get("status") == "completed"
            ):
                # Save structure definition
                structure_file = self.docs_dir / "discovered_structure.json"
                structure_file.write_text(json.dumps(result, indent=2))
                print(f"📝 Structure saved to: {structure_file}")

        return results

    async def phase2_stage_documentation(self) -> Dict:
        """Phase 2: Document high-level stages"""

        print("\n" + "=" * 60)
        print("PHASE 2: STAGE DOCUMENTATION")
        print("=" * 60)

        # Define stages based on common auto-coding solution needs
        stages = [
            "Requirements Analysis & Planning",
            "System Architecture Design",
            "Development Environment Setup",
            "Core Code Generation Engine",
            "Testing Framework Implementation",
            "Quality Assurance & Validation",
            "Documentation Generation",
            "Deployment & Integration",
            "Monitoring & Maintenance",
            "Performance Optimization",
            "Security & Compliance",
            "User Interface & Experience",
        ]

        # Create documentation tasks for each stage
        stage_tasks = []
        for i, stage in enumerate(stages, 1):
            stage_tasks.append(
                AgentTask(
                    task_id=f"stage_{i}",
                    task_type="documentation",
                    prompt=f"""Document Stage {i}: {stage}

                Create comprehensive documentation including:
                1. Overview and objectives
                2. Key components and deliverables
                3. Required inputs and outputs
                4. Success criteria
                5. Dependencies on other stages
                6. Typical timeline and effort
                7. Tools and technologies used
                8. Best practices and pitfalls

                Output detailed documentation to: {self.docs_dir}/stages/stage_{i}_{stage.replace(' ', '_').lower()}.md

                IMPORTANT: Identify 3-7 major steps within this stage that should be documented separately.""",
                )
            )

        print(f"📋 Documenting {len(stage_tasks)} stages in parallel...")
        start_time = time.time()

        # Execute all stage documentation in parallel
        results = await self.orchestrator.execute_batch(stage_tasks)

        duration = time.time() - start_time
        completed = sum(1 for r in results if r.get("status") == "completed")

        print(f"✅ Stage documentation complete: {completed}/{len(stage_tasks)} stages")
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📊 Average per stage: {duration/len(stage_tasks):.2f}s")

        # Track discovered structure
        self.discovered_structure["stages"] = stages
        self.discovered_structure["total_elements"] = len(stages)

        return results

    async def phase3_cascade_documentation(self, stage_results: Dict) -> Dict:
        """Phase 3: Cascade through steps, actions, and operations"""

        print("\n" + "=" * 60)
        print("PHASE 3: CASCADING DOCUMENTATION")
        print("=" * 60)

        # For demo, document steps for first 3 stages
        step_tasks = []

        for stage_num in range(1, 4):  # First 3 stages
            for step_num in range(1, 4):  # 3 steps per stage
                step_tasks.append(
                    AgentTask(
                        task_id=f"step_{stage_num}_{step_num}",
                        task_type="documentation",
                        prompt=f"""Document Step {step_num} of Stage {stage_num}.

                    Create detailed step documentation including:
                    1. Purpose and objectives
                    2. Detailed activities
                    3. Tools and techniques
                    4. Inputs and outputs
                    5. Validation criteria

                    Output to: {self.docs_dir}/steps/stage_{stage_num}_step_{step_num}.md""",
                    )
                )

        print(f"📋 Documenting {len(step_tasks)} steps in parallel...")
        start_time = time.time()

        results = await self.orchestrator.execute_batch(step_tasks)

        duration = time.time() - start_time
        completed = sum(1 for r in results if r.get("status") == "completed")

        print(f"✅ Step documentation complete: {completed}/{len(step_tasks)} steps")
        print(f"⏱️  Duration: {duration:.2f}s")

        self.discovered_structure["total_elements"] += len(step_tasks)

        return results

    async def save_final_structure(self):
        """Save the complete discovered structure"""

        structure_file = self.output_dir / "final_structure.json"
        structure_file.write_text(json.dumps(self.discovered_structure, indent=2))

        # Create summary
        summary = f"""# WBS Documentation Summary

## Execution Summary
- **Date**: {self.discovered_structure['timestamp']}
- **Stages Documented**: {len(self.discovered_structure['stages'])}
- **Total Elements**: {self.discovered_structure['total_elements']}
- **Output Directory**: {self.output_dir}

## Discovered Stages
"""
        for i, stage in enumerate(self.discovered_structure["stages"], 1):
            summary += f"{i}. {stage}\n"

        summary_file = self.output_dir / "SUMMARY.md"
        summary_file.write_text(summary)

        print(f"\n📊 Final structure saved to: {structure_file}")
        print(f"📝 Summary saved to: {summary_file}")

    async def run_full_documentation(self):
        """Run the complete WBS documentation process"""

        print("\n" + "🚀" * 30)
        print("WBS AUTO-CODING SOLUTION DOCUMENTATION")
        print("🚀" * 30)

        overall_start = time.time()

        # Phase 1: Discovery
        discovery_results = await self.phase1_discovery()

        # Human review checkpoint
        print("\n" + "⚠️" * 20)
        print("HUMAN REVIEW CHECKPOINT")
        print("Please review the discovered structure in:")
        print(f"  {self.docs_dir}/discovered_structure.json")
        print("⚠️" * 20)

        response = input("\nProceed with stage documentation? (y/n): ")
        if response.lower() != "y":
            print("Documentation halted for review.")
            return

        # Phase 2: Stage documentation
        stage_results = await self.phase2_stage_documentation()

        # Phase 3: Cascade documentation
        cascade_results = await self.phase3_cascade_documentation(stage_results)

        # Save final structure
        await self.save_final_structure()

        overall_duration = time.time() - overall_start

        print("\n" + "=" * 60)
        print("WBS DOCUMENTATION COMPLETE")
        print("=" * 60)
        print(
            f"✅ Total elements documented: {self.discovered_structure['total_elements']}"
        )
        print(f"⏱️  Total duration: {overall_duration:.2f}s")
        print(f"📁 Output directory: {self.output_dir}")
        print(
            f"⚡ Parallelism utilized: {min(self.orchestrator.token_pool.size(), 15)} agents"
        )


async def main():
    """Main entry point"""

    print("\n" + "=" * 60)
    print("WBS DOCUMENTER - PRODUCTION VERSION")
    print("Powered by Agent Orchestrator with 15 parallel tokens")
    print("=" * 60)

    # Check token availability
    documenter = WBSDocumenter()

    if documenter.orchestrator.token_pool.size() < 2:
        print("\n⚠️  WARNING: Limited parallelism available")
        print(f"Only {documenter.orchestrator.token_pool.size()} token(s) found")
        print("For best performance, ensure encrypted tokens are available")

    # Run documentation
    try:
        await documenter.run_full_documentation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Documentation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during documentation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
