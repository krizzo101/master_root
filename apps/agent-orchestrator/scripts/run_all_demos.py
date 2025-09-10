#!/usr/bin/env python3
"""
Run All Demos Script

Convenience script to run all Agent Orchestrator demonstrations in sequence
with proper spacing and result collection.
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Import the demo system
try:
    from comprehensive_demo import main as run_demo_main
except ImportError:
    print(
        "❌ Could not import demo system. Make sure you're in the agent-orchestrator directory."
    )
    sys.exit(1)


async def run_all_demos():
    """Run all demo types in sequence"""

    print("🎭 AGENT ORCHESTRATOR - COMPLETE DEMONSTRATION SUITE")
    print("=" * 70)
    print("This script will run all demo types to showcase the full capabilities")
    print("of the Agent Orchestrator system.\n")

    # Define demo sequence
    demos = [
        ("basic", "Multi-agent workflow with specialized roles", "3-5 minutes"),
        ("monitoring", "Real-time progress tracking showcase", "2-3 minutes"),
        ("parallel", "Parallel agent execution demonstration", "2-4 minutes"),
        ("dependencies", "Complex dependency chain management", "4-7 minutes"),
    ]

    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = Path(f"./demo_suite_results_{timestamp}")

    print(f"📁 All demo results will be saved to: {output_base}")
    print(f"🕐 Estimated total time: 11-19 minutes")
    print(f"⚡ Running {len(demos)} demonstration types\n")

    # Confirm before starting
    try:
        response = input(
            "Press Enter to start the demonstration suite (or Ctrl+C to cancel): "
        )
    except KeyboardInterrupt:
        print("\n🛑 Demo suite cancelled by user")
        return

    start_time = time.time()
    results = []

    for i, (demo_type, description, duration) in enumerate(demos, 1):
        print(f"\n{'='*70}")
        print(f"🎬 DEMO {i}/{len(demos)}: {demo_type.upper()}")
        print(f"📝 {description}")
        print(f"⏱️  Expected duration: {duration}")
        print(f"{'='*70}")

        demo_start = time.time()

        try:
            # Set up arguments for the demo
            import sys

            original_argv = sys.argv.copy()
            sys.argv = [
                "comprehensive_demo.py",
                demo_type,
                "--output-dir",
                str(output_base / f"demo_{i}_{demo_type}"),
            ]

            # Run the demo
            result = await run_demo_main()

            # Restore original argv
            sys.argv = original_argv

            demo_duration = time.time() - demo_start

            if result:
                print(
                    f"\n✅ Demo {i} ({demo_type}) completed successfully in {demo_duration:.1f} seconds"
                )
                results.append(
                    {
                        "demo_type": demo_type,
                        "description": description,
                        "success": True,
                        "duration": demo_duration,
                        "error": None,
                    }
                )
            else:
                print(
                    f"\n❌ Demo {i} ({demo_type}) failed after {demo_duration:.1f} seconds"
                )
                results.append(
                    {
                        "demo_type": demo_type,
                        "description": description,
                        "success": False,
                        "duration": demo_duration,
                        "error": "Demo returned failure status",
                    }
                )

        except Exception as e:
            demo_duration = time.time() - demo_start
            print(f"\n💥 Demo {i} ({demo_type}) failed with exception: {e}")
            results.append(
                {
                    "demo_type": demo_type,
                    "description": description,
                    "success": False,
                    "duration": demo_duration,
                    "error": str(e),
                }
            )

        # Brief pause between demos
        if i < len(demos):
            print(f"\n⏸️  Pausing 5 seconds before next demo...")
            time.sleep(5)

    # Final summary
    total_duration = time.time() - start_time
    successful_demos = sum(1 for r in results if r["success"])

    print(f"\n{'='*70}")
    print(f"🏁 DEMONSTRATION SUITE COMPLETE")
    print(f"{'='*70}")
    print(f"📊 Summary:")
    print(f"   • Total time: {total_duration/60:.1f} minutes")
    print(f"   • Demos run: {len(results)}")
    print(f"   • Successful: {successful_demos}")
    print(f"   • Failed: {len(results) - successful_demos}")
    print(f"   • Success rate: {successful_demos/len(results)*100:.1f}%")

    print(f"\n📋 Individual Results:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(
            f"   {status} {result['demo_type']:>12}: {result['duration']:>5.1f}s - {result['description']}"
        )
        if not result["success"]:
            print(f"      Error: {result['error']}")

    print(f"\n📁 All results saved to: {output_base}")

    # Save summary report
    summary_file = output_base / "demo_suite_summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)

    import json

    summary_data = {
        "suite_run_timestamp": datetime.now().isoformat(),
        "total_duration_seconds": total_duration,
        "total_duration_minutes": total_duration / 60,
        "demos_run": len(results),
        "successful_demos": successful_demos,
        "failed_demos": len(results) - successful_demos,
        "success_rate_percent": successful_demos / len(results) * 100,
        "individual_results": results,
        "output_directory": str(output_base),
    }

    summary_file.write_text(json.dumps(summary_data, indent=2))
    print(f"📊 Suite summary saved to: {summary_file}")

    if successful_demos == len(results):
        print(f"\n🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print(f"The Agent Orchestrator system has been proven to work effectively")
        print(f"across all demonstration scenarios.")
    else:
        print(f"\n⚠️  Some demonstrations failed. Check the results above for details.")

    print(f"\n{'='*70}")


def main():
    """Main entry point"""
    try:
        asyncio.run(run_all_demos())
    except KeyboardInterrupt:
        print(f"\n🛑 Demo suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
