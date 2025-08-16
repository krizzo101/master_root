#!/usr/bin/env python3
"""
OAMAT Smart Decomposition - Main Entry Point

The primary entry point for the Smart Decomposition meta-intelligence system.
Handles CLI parsing, dependency injection, and orchestration.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# Add project root to path for absolute imports
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

# Import dependencies
from src.applications.oamat_sd.smart_decomposition_agent import SmartDecompositionAgent
from src.applications.oamat_sd.src.operations.file_manager import FileOperationsManager
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config
from src.applications.oamat_sd.src.tools.mcp_tool_registry import (
    create_mcp_tool_registry,
)
from src.shared.openai_interfaces.chat_completions_interface import (
    OpenAIChatCompletionsInterface,
)


async def run_smart_decomposition(
    request: str, debug: bool = False, no_review: bool = False
) -> dict[str, Any]:
    """Run the Smart Decomposition Agent with request preprocessing and dynamic configuration generation"""

    # Initialize beautiful console interface
    from src.applications.oamat_sd.src.sd_logging.console_interface import (
        ConsoleInterface,
    )

    console = ConsoleInterface()

    # Show beautiful header
    console.show_header()

    # Step 0: Request Preprocessing - Standardize user input
    from src.applications.oamat_sd.src.preprocessing.request_standardizer import (
        RequestStandardizer,
    )

    logger_factory = LoggerFactory(default_config, setup_file_handlers=False)
    request_standardizer = RequestStandardizer(logger_factory)

    # Standardize the raw user request
    preprocessing_result = await request_standardizer.standardize_request(
        request, debug=debug
    )

    if not preprocessing_result.success:
        console.show_error(preprocessing_result.error_message, "Request Preprocessing")
        return {
            "success": False,
            "error": f"Preprocessing failed: {preprocessing_result.error_message}",
            "preprocessing_time_ms": preprocessing_result.processing_time_ms,
        }

    standardized_request = preprocessing_result.standardized_request

    # Show beautiful request analysis results
    analysis_data = {
        "request_type": standardized_request.classification.request_type.value,
        "complexity_level": standardized_request.classification.complexity_level.value,
        "technologies": (
            standardized_request.key_technologies
            if standardized_request.key_technologies
            else []
        ),
        "confidence": standardized_request.confidence_scores.overall_confidence,
        "processing_time_ms": preprocessing_result.processing_time_ms,
    }
    console.show_request_analysis(request, analysis_data)

    # Master agent will use console interface for beautiful output

    # Step 1: Generate Dynamic Configuration via Master Agent
    from src.applications.oamat_sd.src.config.dynamic_config_generator import (
        generate_dynamic_config,
    )

    # Use the standardized request for better configuration generation
    dynamic_config = await generate_dynamic_config(
        standardized_request.original_request,
        debug,
        standardized_request=standardized_request,
    )

    # Dynamic configuration generated (logged in debug files)

    # Step 2: Apply dynamic config to ConfigManager
    from src.applications.oamat_sd.src.config.config_manager import ConfigManager

    config_manager = ConfigManager()
    # Properly parse the dynamic config into typed objects
    config_manager._config = config_manager._parse_config(dynamic_config)

    # Configuration details logged in debug files

    # Step 3: Create project path and update config FIRST
    # Simple project path creation
    from datetime import datetime
    from pathlib import Path

    clean_request = "".join(c for c in request.lower() if c.isalnum() or c in " _-")[
        :50
    ]
    clean_request = "_".join(clean_request.split())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"{clean_request}_{timestamp}"

    projects_dir = Path(__file__).parent / "projects"
    projects_dir.mkdir(exist_ok=True)
    project_path = projects_dir / project_name
    project_path.mkdir(exist_ok=True)

    # Update centralized config BEFORE creating any loggers
    project_logs_dir = project_path / "logs"
    project_logs_dir.mkdir(exist_ok=True)
    default_config.log_dir = project_logs_dir
    print(f"📂 Project: {project_path}")
    print(f"📋 Config updated: all logs → {project_logs_dir}")

    # Step 4: Now initialize components with updated config
    logger_factory = LoggerFactory(default_config, setup_file_handlers=False)
    logger_factory._setup_file_handlers()  # Set up with project-specific config
    file_manager = FileOperationsManager(logger_factory)

    mcp_tools_registry = create_mcp_tool_registry(use_real_clients=True)
    openai_client = OpenAIChatCompletionsInterface()

    # Step 5: Create and run agent with project-specific logging and beautiful console interface
    agent = SmartDecompositionAgent(
        logger_factory, mcp_tools_registry, openai_client, console
    )
    result = await agent.process_request(
        user_request=request,
        project_name=project_name,
        project_path=project_path,
        standardized_request=standardized_request,
    )

    return result


def print_results(result: dict[str, Any]) -> None:
    """Print results in a user-friendly format"""
    print("\n" + "=" * 80)
    print("🧠 SMART DECOMPOSITION AGENT - RESULTS")
    print("=" * 80)

    if result.get("success", False):
        print("✅ SUCCESS")

        # Show project information
        if result.get("project_path"):
            print(f"\n📁 Project Files Saved To: {result['project_path']}")
            print(f"📝 Project Name: {result.get('project_name') or 'Unknown'}")
            print(f"📋 Logs for this run: {result['project_path']}/logs/")

            # List files in project directory if it exists
            project_dir = Path(result["project_path"])
            if project_dir.exists():
                print("\n📂 Generated Files:")
                files_found = False
                for file_path in project_dir.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(project_dir)
                        print(f"  📄 {relative_path}")
                        files_found = True
                if not files_found:
                    print(
                        "  📁 Project structure created (files may be generated later)"
                    )

        # Show agent outputs if available
        if result.get("agent_outputs"):
            print("\n🤖 Agent Outputs:")
            for role, output in result["agent_outputs"].items():
                # Fix: Agent outputs are strings containing deliverables, not dicts with success flags
                # Check for actual content and deliverable patterns instead of dict structure
                if (
                    (
                        isinstance(output, str)
                        and len(output.strip()) > 0
                        and not output.startswith("ERROR:")
                        and (
                            "deliverables" in output
                            or "```" in output
                            or len(output) > 100
                        )
                    )
                    or isinstance(output, dict)
                    and output.get("success")
                ):
                    print(f"  ✅ {role}: Completed successfully")
                else:
                    print(f"  ❌ {role}: Failed or incomplete")

        # Show synthesis results if available
        if result.get("final_solution"):
            solution = result["final_solution"]
            print("\n📋 Final Solution:")
            if isinstance(solution, dict):
                if solution.get("content"):
                    print(f"📄 Content: {solution['content'][:200]}...")
                if solution.get("artifact_type"):
                    print(f"📋 Type: {solution['artifact_type']}")
            else:
                print(f"📄 {str(solution)[:200]}...")

        # Show execution summary
        print("\n📊 Execution Summary:")
        print(f"  ⏱️  Total Time: ~{result.get('execution_time', 'Unknown')}s")
        print(
            f"  🔄 Workflow Status: {'Complete' if result.get('success') else 'Failed'}"
        )

    else:
        print("❌ FAILED")
        print(f"Error: {result.get('error') or 'Unknown error'}")
        if result.get("errors"):
            print("Additional errors:")
            for error in result["errors"]:
                print(f"  - {error}")

        # Show debug info for failed runs
        if result.get("debug_info"):
            print("\n🔍 Debug Information:")
            debug = result["debug_info"]
            for key, value in debug.items():
                print(f"  {key}: {value}")


async def main():
    """Main CLI interface for OAMAT Smart Decomposition"""
    parser = argparse.ArgumentParser(
        description="OAMAT Smart Decomposition Meta-Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.applications.oamat_sd "Create a Python calculator with GUI"
  python -m src.applications.oamat_sd "Build a REST API for task management" --debug
        """,
    )

    parser.add_argument("request", help="User request to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-review", action="store_true", help="Skip review steps")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.debug:
        print("🔧 Debug mode enabled")
        print(f"📝 Processing request: {args.request}")
        print("=" * 60)

    try:
        # Run the Smart Decomposition Agent
        result = await run_smart_decomposition(
            request=args.request, debug=args.debug, no_review=args.no_review
        )

        # Print results
        print_results(result)

        # Exit with appropriate code
        sys.exit(0 if result.get("success", False) else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Smart Decomposition interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Smart Decomposition failed: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
