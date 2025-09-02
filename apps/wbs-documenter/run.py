#!/usr/bin/env python3
"""
WBS Documenter - Adaptive documentation system for auto-coding solutions
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import generic_orchestrator
sys.path.insert(0, str(Path(__file__).parent.parent / "agent-orchestrator" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wbs_implementation import WBSDocumentationOrchestrator


async def main():
    """Main entry point for WBS documentation"""

    print("\nWBS Documentation System")
    print("=" * 50)
    print("This system will:")
    print("1. Discover the structure of an auto-coding solution")
    print("2. Allow agents to determine appropriate breakdown")
    print("3. Generate comprehensive documentation")
    print("\nNOTE: The structure is discovered, not predetermined.")
    print("=" * 50)

    response = input("\nProceed with documentation generation? (y/n): ")

    if response.lower() != "y":
        print("Exiting...")
        return

    # Create orchestrator
    project_dir = Path(".")
    orchestrator = WBSDocumentationOrchestrator(project_dir)

    try:
        # Run adaptive orchestration
        result = await orchestrator.run_adaptive_orchestration()

        print("\n" + "=" * 50)
        print("Documentation Complete!")
        print(f"Output directory: {result['output_dir']}")
        print(f"Structure discovered: See {result['output_dir']}/structure.json")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n\nOrchestration interrupted by user")
    except Exception as e:
        print(f"\nError during orchestration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
