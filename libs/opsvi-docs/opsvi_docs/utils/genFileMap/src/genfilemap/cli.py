# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Command Line Interface for Genfilemap","description":"This module provides the CLI entry point and argument processing for generating file maps.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Docstring","description":"Module-level docstring providing an overview of the CLI functionality.","line_start":2,"line_end":4},{"name":"Imports","description":"Import statements for required modules and functions.","line_start":6,"line_end":15},{"name":"Main Function","description":"The main entry point for the CLI, handling argument parsing and execution logic.","line_start":16,"line_end":94},{"name":"Main Check","description":"Check to execute the main function if the script is run directly.","line_start":95,"line_end":96}],"key_elements":[{"name":"main","description":"Main entry point function for the CLI.","line":17},{"name":"DEFAULT_CONFIG_PATH","description":"Default path for the configuration file.","line":13},{"name":"Config","description":"Class for handling configuration settings.","line":13},{"name":"process_files_async","description":"Asynchronous function for processing files.","line":14},{"name":"generate_project_map","description":"Function for generating a project-level file map.","line":14},{"name":"load_schema","description":"Function for loading a schema from a specified path.","line":15},{"name":"FILE_MAP_SCHEMA","description":"Schema definition for file maps.","line":15}]}
"""
# FILE_MAP_END

"""
Command line interface for genfilemap.

This module provides the CLI entry point and argument processing.
"""

import os
import sys
import argparse
import asyncio

from genfilemap.config import Config, DEFAULT_CONFIG_PATH
from genfilemap.core import process_files_async, generate_project_map
from genfilemap.models.schemas import load_schema


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate file maps for better AI agent context"
    )

    # Add argument for config file path
    parser.add_argument(
        "--config", help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})"
    )

    # CLI arguments that override config settings
    parser.add_argument(
        "path", nargs="?", help="Path to the file or directory to update with file maps"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process directories recursively"
    )
    parser.add_argument(
        "-i",
        "--include",
        help="Only process these file types (comma-separated extensions including the dot, e.g., .py,.js)",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help="Exclude these file types (comma-separated extensions including the dot, e.g., .md,.txt)",
    )
    parser.add_argument("-m", "--model", help="Model to use")
    parser.add_argument(
        "-v",
        "--vendor",
        choices=["openai", "anthropic", "cohere"],
        help="API vendor to use",
    )
    parser.add_argument(
        "-k", "--api-key-var", help="Environment variable name for API key"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show changes without writing to files",
    )
    parser.add_argument(
        "-t", "--template", help="Custom template name to use for file maps"
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        help="Maximum number of concurrent file operations",
    )
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        help="Number of processes for CPU-bound operations",
    )
    parser.add_argument(
        "-g",
        "--ignore-file",
        help="Path to a gitignore-style file with patterns to ignore",
    )
    parser.add_argument(
        "-o", "--report", help="Generate a JSON report file at the specified path"
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        help="Minimum number of lines a file must have to generate a file map",
    )
    parser.add_argument(
        "--project-map",
        action="store_true",
        help="Generate a project-level file map with references to all project files and their file maps",
    )
    parser.add_argument(
        "--project-map-out", help="Output file for the project-level file map"
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Generate a default configuration file",
    )

    args = parser.parse_args()

    # If init-config argument is provided, generate default config and exit
    if args.init_config:
        config_path = args.config or DEFAULT_CONFIG_PATH
        Config.generate_default_config(config_path)
        return

    # Initialize configuration with appropriate precedence
    config = Config(args.config, vars(args))

    # If no path is provided, check if one exists in the config
    if not args.path and not config.get("path"):
        parser.error("Path is required unless specified in config file")

    # Convert comma-separated strings to lists if needed
    if args.include:
        config.args["file_processing.include_extensions"] = args.include.split(",")
    if args.exclude:
        config.args["file_processing.exclude_extensions"] = args.exclude.split(",")

    # Make a directory for templates if it doesn't exist
    template_dir = config.get("output.template_dir")
    if (
        template_dir
        and config.get("output.template")
        and not os.path.exists(template_dir)
    ):
        os.makedirs(template_dir)

    # Load schema
    schema_path = config.get("output.schema_path")
    custom_schema = None
    if schema_path:
        custom_schema = load_schema(schema_path)

    # Get the path from config
    path = config.get("path")

    # If project-level file map option is set AND the path is a directory, generate it
    # Skip project map generation for single files
    if config.get("project_map.enabled") and os.path.isdir(path):
        generate_project_map(config)

    # Run async code for per-file file maps
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        success = asyncio.run(process_files_async(config))
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
