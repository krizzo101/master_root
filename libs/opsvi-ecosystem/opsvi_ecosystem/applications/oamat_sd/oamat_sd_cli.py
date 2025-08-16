#!/usr/bin/env python3
"""
OAMAT Smart Decomposition CLI

Command line interface for the Smart Decomposition meta-intelligence system.
Runs within the oamat_sd application scope.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

# Import the Smart Decomposition Agent
from src.applications.oamat_sd.smart_decomposition_agent import SmartDecompositionAgent


async def run_project_generation(request: str, verbose: bool = False) -> dict[str, Any]:
    """Run the Smart Decomposition Agent to generate a project"""

    if verbose:
        print("🧠 Initializing Smart Decomposition Meta-Intelligence Agent...")

    # Initialize the agent
    agent = SmartDecompositionAgent()

    if verbose:
        print(f"📝 Processing request: {request}")
        print("=" * 60)

    # Process the request
    result = await agent.process_request(request)

    return result


def print_results(result: dict[str, Any], verbose: bool = False):
    """Print the results in a user-friendly format"""

    print("\n" + "🎯 SMART DECOMPOSITION RESULTS")
    print("=" * 60)

    # Check for success
    success = result.get("success", False)
    print(f"✅ Success: {success}")

    # Show final deliverables
    deliverables = result.get("deliverables", {})
    if deliverables:
        files_created = deliverables.get("files_created", [])
        project_dir = deliverables.get("project_directory")

        print(f"📁 Files created: {len(files_created)}")
        if project_dir:
            print(f"📂 Project directory: {project_dir}")

        if verbose and files_created:
            print("\n📄 Created Files:")
            for file_info in files_created[:10]:  # Show first 10
                path = file_info.get("path", "Unknown")
                size = file_info.get("size", 0)
                print(f"   - {path} ({size} bytes)")

    # Show workflow summary
    workflow_summary = result.get("workflow_summary", {})
    if workflow_summary:
        agents_used = workflow_summary.get("agents_used", [])
        tools_used = workflow_summary.get("tools_used", [])

        print(f"🤖 Agents deployed: {len(agents_used)}")
        print(f"🛠️ Tools used: {len(tools_used)}")

        if verbose:
            print(f"\n🤖 Agent Types: {', '.join(agents_used)}")

    # Show any errors
    errors = result.get("errors", [])
    if errors:
        print(f"⚠️ Errors: {len(errors)}")
        if verbose:
            for error in errors[:3]:  # Show first 3 errors
                print(f"   - {error}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="OAMAT Smart Decomposition CLI - Generate complete projects using meta-intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python oamat_sd_cli.py "Create a Python calculator with GUI using tkinter"
  python oamat_sd_cli.py "Build a REST API for task management" --verbose
  python oamat_sd_cli.py "Design a web scraper for e-commerce data" --output results.json
        """,
    )

    # Required arguments
    parser.add_argument("request", help="The project request to process")

    # Optional arguments
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output during execution"
    )

    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print("   Please set your OpenAI API key to run the Smart Decomposition Agent")
        sys.exit(1)

    # Execute the agent
    try:
        if args.verbose:
            print("🚀 OAMAT Smart Decomposition - Starting project generation")
            print("=" * 60)

        result = asyncio.run(
            run_project_generation(request=args.request, verbose=args.verbose)
        )

        # Print results
        print_results(result, args.verbose)

        # Save to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"💾 Results saved to {args.output}")

        # Exit with appropriate code
        success = result.get("success", False)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Project generation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Smart Decomposition failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
