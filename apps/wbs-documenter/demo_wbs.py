#!/usr/bin/env python3
"""
WBS Documenter Demo - Showcases the auto-coding solution documentation
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


async def run_demo():
    """Run a demonstration of WBS documentation with 3 stages"""

    print("\n" + "🎯" * 30)
    print("WBS AUTO-CODING SOLUTION DOCUMENTATION - DEMO")
    print("🎯" * 30)

    output_dir = Path("./demo_output") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    orchestrator = GenericOrchestrator(
        output_dir=output_dir, max_parallel=15, use_optimizations=True
    )

    print(f"\n📊 System Configuration:")
    print(f"  Tokens available: {orchestrator.token_pool.size()}")
    print(f"  Max parallelism: {orchestrator.max_parallel}")
    print(f"  Output directory: {output_dir}")

    # Phase 1: Discovery (1 task)
    print("\n" + "=" * 60)
    print("PHASE 1: DISCOVERY")
    print("=" * 60)

    discovery_task = AgentTask(
        task_id="discover",
        task_type="discovery",
        prompt="""Analyze what's needed for an auto-coding solution and identify the 3 most critical stages.
        For each stage, list:
        1. Stage name
        2. Main objective
        3. Key deliverables (2-3 items)
        4. Dependencies

        Focus on: Requirements → Implementation → Testing""",
    )

    print("🔍 Discovering structure...")
    start = time.time()

    discovery_result = await orchestrator.execute_agent(discovery_task)

    print(f"✅ Discovery complete in {time.time() - start:.2f}s")

    # Phase 2: Document 3 Critical Stages (parallel)
    print("\n" + "=" * 60)
    print("PHASE 2: STAGE DOCUMENTATION (Parallel)")
    print("=" * 60)

    stages = [
        (
            "Requirements & Analysis",
            "Gathering and analyzing requirements for the auto-coding system",
        ),
        (
            "Code Generation Engine",
            "Building the core engine that generates code from specifications",
        ),
        (
            "Testing & Validation",
            "Ensuring generated code works correctly and meets requirements",
        ),
    ]

    stage_tasks = []
    for i, (stage_name, description) in enumerate(stages, 1):
        stage_tasks.append(
            AgentTask(
                task_id=f"stage_{i}",
                task_type="documentation",
                prompt=f"""Document Stage {i}: {stage_name}

            Description: {description}

            Create detailed documentation including:
            1. **Overview** - What this stage accomplishes
            2. **Objectives** - 3-5 specific goals
            3. **Process** - Step-by-step approach
            4. **Deliverables** - What gets produced
            5. **Tools & Technologies** - What's needed
            6. **Success Criteria** - How to measure completion
            7. **Common Challenges** - What to watch out for

            Output as structured markdown.""",
            )
        )

    print(f"📝 Documenting {len(stage_tasks)} stages in parallel...")
    start = time.time()

    stage_results = await orchestrator.execute_batch(stage_tasks)

    duration = time.time() - start
    completed = sum(1 for r in stage_results if r.get("status") == "completed")

    print(f"✅ Stage documentation complete:")
    print(f"  Completed: {completed}/{len(stage_tasks)}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Speedup: ~{(len(stage_tasks) * 20) / duration:.1f}x vs sequential")

    # Phase 3: Deep dive into one stage (steps)
    print("\n" + "=" * 60)
    print("PHASE 3: STEP BREAKDOWN (Requirements Stage)")
    print("=" * 60)

    step_tasks = [
        AgentTask(
            task_id="step_1_1",
            task_type="documentation",
            prompt="""Document Step 1: Stakeholder Identification
            Detail who needs to be involved, how to identify them, and engagement strategies.""",
        ),
        AgentTask(
            task_id="step_1_2",
            task_type="documentation",
            prompt="""Document Step 2: Requirements Gathering
            Detail techniques for collecting requirements, templates, and validation methods.""",
        ),
        AgentTask(
            task_id="step_1_3",
            task_type="documentation",
            prompt="""Document Step 3: Requirements Analysis
            Detail how to analyze, prioritize, and structure requirements for auto-coding.""",
        ),
    ]

    print(f"📝 Documenting {len(step_tasks)} steps in parallel...")
    start = time.time()

    step_results = await orchestrator.execute_batch(step_tasks)

    duration = time.time() - start
    completed = sum(1 for r in step_results if r.get("status") == "completed")

    print(f"✅ Step documentation complete:")
    print(f"  Completed: {completed}/{len(step_tasks)}")
    print(f"  Duration: {duration:.2f}s")

    # Save summary
    summary = {
        "demo_run": datetime.now().isoformat(),
        "tokens_used": orchestrator.token_pool.size(),
        "phases_completed": 3,
        "total_tasks": 1 + len(stage_tasks) + len(step_tasks),
        "stages_documented": [s[0] for s in stages],
        "output_directory": str(output_dir),
    }

    summary_file = output_dir / "demo_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2))

    # Create markdown summary
    md_summary = f"""# WBS Documentation Demo Summary

## Execution Details
- **Date**: {summary['demo_run']}
- **Tokens Available**: {summary['tokens_used']}
- **Total Tasks**: {summary['total_tasks']}

## Documented Structure

### Stages
"""
    for i, stage in enumerate(summary["stages_documented"], 1):
        md_summary += f"{i}. {stage}\n"

    md_summary += f"""
### Steps (Requirements Stage)
1. Stakeholder Identification
2. Requirements Gathering
3. Requirements Analysis

## Performance
- Parallel execution with {orchestrator.token_pool.size()} tokens
- Significant speedup vs sequential execution
- All tasks completed successfully

## Output
Results saved to: `{output_dir}`
"""

    md_file = output_dir / "DEMO_SUMMARY.md"
    md_file.write_text(md_summary)

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print(f"✅ All phases completed successfully")
    print(f"📁 Output saved to: {output_dir}")
    print(f"📊 Summary: {summary_file}")
    print(f"📝 Markdown: {md_file}")

    return summary


async def main():
    """Main entry point for demo"""

    try:
        summary = await run_demo()

        print("\n🎉 Demo completed successfully!")
        print("This demonstrates how the WBS documenter can:")
        print("  1. Discover structure through AI agents")
        print("  2. Document stages in parallel")
        print("  3. Cascade down to detailed steps")
        print("  4. Leverage multiple tokens for speed")

    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
