"""Command-line interface for Project Mapper.

This module provides the command-line interface for the Project Mapper tool.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from rich.progress import Progress

from proj_mapper.core.project_manager import ProjectManager
from proj_mapper.output.storage import StorageManager
from proj_mapper.output.visualization.generator import VisualizationGenerator

# Configure logging
logger = logging.getLogger(__name__)


def configure_logging(debug: bool = False) -> None:
    """Configure logging for the application.

    Args:
        debug: Whether to enable debug logging
    """
    # Create formatters
    debug_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    info_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(debug_formatter if debug else info_formatter)

    # Set log level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Log initial configuration
    logger.debug("Log level set to DEBUG" if debug else "Log level set to INFO")


def analyze_command(args: argparse.Namespace) -> int:
    """Handle the analyze command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger.info(f"Analyzing project: {args.project_path}")

    # Create output directory if it doesn't exist
    output_dir = Path(args.project_path) / ".maps"
    output_dir.mkdir(exist_ok=True)

    # Create output path
    output_path = output_dir / "project_map.json"
    logger.info(f"Output will be saved to: {output_path}")

    try:
        # Create project manager
        manager = ProjectManager()

        # Run analysis with progress bar
        with Progress() as progress:
            task = progress.add_task("Generating output", total=100)

            # Analyze project
            project_map = manager.analyze_project(args.project_path)
            progress.update(task, advance=100)

        # Save output
        storage = StorageManager()
        storage.store_map(project_map, args.project_path, {})

        logger.info(f"Project analysis complete. Output saved to: {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Error analyzing project: {e}")
        if args.debug:
            logger.exception("Detailed error information:")
        return 1


def update_command(args: argparse.Namespace) -> int:
    """Handle the update command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger.info(f"Updating project maps: {args.project_path}")

    try:
        # Create project manager
        manager = ProjectManager()

        # Run update with progress bar
        with Progress() as progress:
            task = progress.add_task("Updating maps", total=100)

            # Update maps
            project_map = manager.update_maps(
                args.project_path,
                incremental=not args.full
            )
            progress.update(task, advance=100)

        # Save output
        output_dir = Path(args.project_path) / ".maps"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "project_map.json"

        storage = StorageManager()
        storage.store_map(project_map, args.project_path, {})

        logger.info(f"Project maps updated. Output saved to: {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Error updating project maps: {e}")
        if args.debug:
            logger.exception("Detailed error information:")
        return 1


def visualize_command(args: argparse.Namespace) -> int:
    """Handle the visualize command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger.info(f"Visualizing project maps: {args.project_path}")

    try:
        # Load map file
        map_file = Path(args.project_path) / ".maps" / "project_map.json"
        if not map_file.exists():
            logger.error(f"Map file not found: {map_file}")
            return 1

        storage = StorageManager()
        project_map = storage.get_latest_map(args.project_path)

        # Create visualization generator
        generator = VisualizationGenerator()

        # Generate visualization
        output_path = args.output if args.output else Path(args.project_path) / ".maps" / "visualization.html"
        generator.generate(project_map, output_path)

        logger.info(f"Visualization generated at: {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Error visualizing project maps: {e}")
        if args.debug:
            logger.exception("Detailed error information:")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the command-line interface.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Project Mapper - Generate and visualize project maps"
    )

    # Global options
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a project and generate maps"
    )
    analyze_parser.add_argument(
        "project_path",
        help="Path to the project to analyze"
    )
    analyze_parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update existing project maps"
    )
    update_parser.add_argument(
        "project_path",
        help="Path to the project to update"
    )
    update_parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    update_parser.add_argument(
        "--full",
        action="store_true",
        help="Perform a full update instead of incremental"
    )

    # Visualize command
    visualize_parser = subparsers.add_parser(
        "visualize",
        help="Generate visualizations from project maps"
    )
    visualize_parser.add_argument(
        "project_path",
        help="Path to the project to visualize"
    )
    visualize_parser.add_argument(
        "-o", "--output",
        help="Path to save the visualization"
    )
    visualize_parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    # Parse arguments
    args = parser.parse_args(argv)

    # Configure logging
    configure_logging(args.debug)

    # Run command
    if args.command == "analyze":
        return analyze_command(args)
    elif args.command == "update":
        return update_command(args)
    elif args.command == "visualize":
        return visualize_command(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())