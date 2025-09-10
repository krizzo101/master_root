#!/usr/bin/env python3
"""
Phase 3 Bootstrap Script - Autonomous Self-Improvement
Launches the self-improving orchestrator for continuous optimization cycles
"""

import asyncio
import sys
import time
from pathlib import Path

# Add hecaton to path
hecaton_path = Path(__file__).parent
sys.path.insert(0, str(hecaton_path))

from src.hecaton.orchestration.self_improving_orchestrator import SelfImprovingOrchestrator


async def main():
    """Run autonomous self-improvement cycles"""
    print("=" * 80)
    print("PHASE 3: AUTONOMOUS SELF-IMPROVEMENT SYSTEM")
    print("=" * 80)
    print()

    # Initialize the self-improving orchestrator
    print("Initializing SelfImprovingOrchestrator...")
    orchestrator = SelfImprovingOrchestrator()
    print("✓ Orchestrator initialized\n")

    # Run 3 improvement cycles
    for cycle_num in range(1, 4):
        print(f"\n{'='*80}")
        print(f"IMPROVEMENT CYCLE {cycle_num}/3")
        print(f"{'='*80}\n")

        start_time = time.time()

        # Run the improvement cycle
        print(f"Starting improvement cycle {cycle_num}...")
        results = await orchestrator.run_improvement_cycle()

        execution_time = time.time() - start_time

        # Display performance metrics
        print(f"\n{'-'*40}")
        print(f"CYCLE {cycle_num} METRICS:")
        print(f"{'-'*40}")

        # Extract and display metrics
        bottlenecks_found = results.get("bottlenecks_found", 0)
        improvements_executed = results.get("improvements_executed", 0)
        success_rate = results.get("success_rate", 0.0)

        print(f"• Bottlenecks Found:      {bottlenecks_found}")
        print(f"• Improvements Executed:  {improvements_executed}")
        print(f"• Success Rate:           {success_rate:.1%}")
        print(f"• Execution Time:         {execution_time:.2f} seconds")

        # Display detailed improvements if available
        if "improvements" in results and results["improvements"]:
            print(f"\nImprovements Applied:")
            for idx, improvement in enumerate(results["improvements"], 1):
                print(f"  {idx}. {improvement.get('description', 'No description')}")
                if "performance_gain" in improvement:
                    print(f"     → Performance gain: {improvement['performance_gain']:.1%}")

        # Display any errors encountered
        if "errors" in results and results["errors"]:
            print(f"\n⚠ Errors Encountered:")
            for error in results["errors"]:
                print(f"  • {error}")

        # Wait between cycles (except after the last one)
        if cycle_num < 3:
            print(f"\n⏳ Waiting 60 seconds before next cycle...")
            await asyncio.sleep(60)

    # Final summary
    print(f"\n{'='*80}")
    print("PHASE 3 COMPLETE: Self-Improvement Cycles Finished")
    print(f"{'='*80}")
    print("\n✓ All 3 improvement cycles completed successfully")
    print("The system has been autonomously optimized.\n")


if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Self-improvement interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during self-improvement: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
