"""
Command Line Interface for GenFileMap.

This module provides the command line interface for generating file maps,
allowing users to configure and run the GenFileMap process.
"""

import sys
import os
import time
import argparse
import asyncio
from typing import Dict, Any, Optional
import traceback

from genfilemap.core import run_process
from genfilemap.logging_utils import info, error, debug, error as log_error
from genfilemap.config import (
    get_config_value,
    load_config,
    _deep_update,
    DEFAULT_CONFIG_PATH,
    DEFAULT_PROJECT_CONFIG_PATH,
)


def custom_excepthook(exc_type, exc_value, exc_traceback):
    log_error("\n[DEBUG] Unhandled exception caught by sys.excepthook:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    import pdb

    pdb.post_mortem(exc_traceback)


sys.excepthook = custom_excepthook


def setup_arg_parser() -> argparse.ArgumentParser:
    """Setup argument parser with all supported options."""
    parser = argparse.ArgumentParser(
        description="Generate file maps for code and documentation files"
    )

    # Configuration options
    parser.add_argument(
        "--global-config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to global configuration file",
    )
    parser.add_argument(
        "--project-config",
        default=DEFAULT_PROJECT_CONFIG_PATH,
        help="Path to project-specific configuration file",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Generate default configuration files",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="When used with --init-config, only create project-specific config",
    )

    # Path argument
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to file or directory to process (default: current directory)",
    )

    # General options
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process directories recursively"
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force regeneration of file maps even if no content changes",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove file maps from files instead of generating them",
    )
    parser.add_argument(
        "--deep-clean",
        action="store_true",
        help="Check all files for FILE_MAP_BEGIN tag regardless of hash files and clean all file maps found",
    )

    # File selection options
    file_group = parser.add_argument_group("File Selection")
    file_group.add_argument(
        "-i",
        "--include",
        help="Include only files with these extensions (comma-separated, e.g., '.py,.js,.md')",
    )
    file_group.add_argument(
        "-x",
        "--exclude",
        help="Exclude files with these extensions (comma-separated, e.g., '.min.js,.pyc')",
    )
    file_group.add_argument(
        "--min-lines",
        type=int,
        default=10,
        help="Minimum number of lines for a file to be processed (default: 10)",
    )
    file_group.add_argument(
        "--ignore-file", help="Path to file with ignore patterns (gitignore format)"
    )

    # API options
    api_group = parser.add_argument_group("API Configuration")
    api_group.add_argument(
        "--api-key",
        help="API key for chosen API vendor (defaults to environment variable)",
    )
    api_group.add_argument(
        "--vendor",
        choices=["openai", "anthropic", "local"],
        default="openai",
        help="API vendor to use (default: openai)",
    )
    api_group.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="Model to use for API calls (default: gpt-4.1-mini)",
    )

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--report", help="Path to write JSON report file")
    output_group.add_argument(
        "--project-map",
        action="store_true",
        help="Generate project-level file map document",
    )
    output_group.add_argument(
        "--project-map-output",
        help="Path where the project map file will be written (default: root of target directory)",
    )
    output_group.add_argument(
        "--project-map-filename",
        default="project_map.json",
        help="Filename for the project map (default: project_map.json)",
    )
    output_group.add_argument(
        "--compact-json",
        action="store_true",
        help="Generate compact JSON format optimized for AI agent consumption",
    )
    output_group.add_argument(
        "--compact-level",
        type=int,
        choices=[0, 1, 2, 3],
        help="JSON compactness level: 0=pretty, 1=minimal whitespace, 2=restructured, 3=ultra-compact",
    )

    # Performance options
    performance_group = parser.add_argument_group("Performance")
    performance_group.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Maximum number of concurrent API calls (default: 5)",
    )
    performance_group.add_argument(
        "--processes",
        type=int,
        default=1,
        help="Number of processes to use for file processing (default: 1)",
    )
    performance_group.add_argument(
        "--use-dir-hashing",
        action="store_true",
        help="Use directory-level hashing to optimize processing by only processing changed directories",
    )
    performance_group.add_argument(
        "--force-recompute",
        action="store_true",
        help="Force recomputation of directory hashes, ignoring the cache",
    )

    # Development options
    dev_group = parser.add_argument_group("Development")
    dev_group.add_argument(
        "--debug", action="store_true", help="Enable debug mode with extensive logging"
    )
    dev_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all debug output and processing details",
    )
    dev_group.add_argument("--log-file", help="Path to log file")

    # Add validation options
    validation_group = parser.add_argument_group("Validation Options")
    validation_group.add_argument(
        "--enable-validation",
        action="store_true",
        help="Enable AI-assisted validation of generated file maps",
    )
    validation_group.add_argument(
        "--validation-model",
        help="Model to use for validation (defaults to same as generation model)",
    )
    validation_group.add_argument(
        "--strict-validation",
        action="store_true",
        help="Use stricter validation criteria",
    )
    validation_group.add_argument(
        "--abort-on-validation-failure",
        action="store_true",
        help="Abort processing if validation fails",
    )

    return parser


def setup_config(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Setup configuration from command line arguments.

    Args:
        args: Command line arguments

    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    # Convert args to dictionary with only explicitly provided values
    config = {}
    args_dict = vars(args)

    # Get the parser's default values
    parser = setup_arg_parser()
    defaults = {
        action.dest: action.default
        for action in parser._actions
        if action.default is not argparse.SUPPRESS
    }

    # Only include values that differ from the defaults
    for key, value in args_dict.items():
        if key in defaults and value != defaults[key]:
            config[key] = value
        elif key not in defaults:
            config[key] = value

    # Process include/exclude extensions
    if get_config_value(config, "include"):
        config["file_processing.include_extensions"] = config["include"].split(",")
        del config["include"]
    if get_config_value(config, "exclude"):
        config["file_processing.exclude_extensions"] = config["exclude"].split(",")
        del config["exclude"]

    # Move file processing options to the correct namespace
    file_options = ["min_lines", "ignore_file", "recursive"]
    for option in file_options:
        if option in config:
            config[f"file_processing.{option}"] = config[option]
            del config[option]

    # Configure project map
    if get_config_value(config, "project_map", False):
        if "project_map_output" in config:
            config["project_map.output_path"] = config["project_map_output"]
            del config["project_map_output"]

        if "project_map_filename" in config:
            config["project_map.output_file"] = config["project_map_filename"]
            del config["project_map_filename"]

        if "compact_json" in config and config["compact_json"]:
            config["project_map.compact_json"] = True
            # Default to level 2 if compact_json is set without a specific level
            if "compact_level" not in config:
                config["project_map.compact_level"] = 2
            del config["compact_json"]

        if "compact_level" in config:
            config["project_map.compact_level"] = config["compact_level"]
            del config["compact_level"]

    # Configure performance settings
    if "concurrency" in config:
        config["performance.concurrency"] = config["concurrency"]
        del config["concurrency"]

    if "processes" in config:
        config["performance.processes"] = config["processes"]
        del config["processes"]

    # Handle API configuration
    if "api_key" in config and config["api_key"]:
        config["api.key"] = config["api_key"]
    if "api_key" in config:
        del config["api_key"]

    if "vendor" in config:
        config["api.vendor"] = config["vendor"]
        del config["vendor"]

    if "model" in config:
        config["api.model"] = config["model"]
        del config["model"]

    # Process performance options
    if "use_dir_hashing" in config:
        config["performance.use_dir_hashing"] = config["use_dir_hashing"]
        del config["use_dir_hashing"]

    if "force_recompute" in config:
        config["performance.force_recompute"] = config["force_recompute"]
        del config["force_recompute"]

    # Process validation options
    validation_options = [
        "enable_validation",
        "validation_model",
        "strict_validation",
        "abort_on_validation_failure",
    ]
    for option in validation_options:
        if option in config:
            # Convert CLI option names to config format
            if option == "enable_validation":
                config["validation.enabled"] = config[option]
            elif option == "validation_model":
                config["validation.model"] = config[option]
            elif option == "strict_validation":
                config["validation.strict"] = config[option]
            elif option == "abort_on_validation_failure":
                config["validation.abort_on_failure"] = config[option]
            del config[option]

    return config


def async_main():
    """Entry point for the application."""
    # Setup argument parser
    parser = setup_arg_parser()
    args = parser.parse_args()

    # Handle init-config option
    if args.init_config:
        import subprocess

        init_type = "project" if args.local else "both"
        cmd = [
            sys.executable,
            "-m",
            "scripts.init_config",
            "--global-config",
            args.global_config,
            "--project-config",
            args.project_config,
            "--init-type",
            init_type,
        ]

        try:
            result = subprocess.run(cmd, check=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            error(f"Error initializing configuration: {e}")
            sys.exit(1)

    # First load the configuration
    config = load_config(
        config_path=getattr(args, "global_config", None),
        project_config_path=getattr(args, "project_config", None),
    )

    # Convert args to config format (this creates a new config based only on args)
    cli_config = setup_config(args)

    # Merge the configuration with CLI config taking precedence
    _deep_update(config, cli_config)
    
    # Reload ignore patterns after CLI config merge to ensure CLI overrides work
    from genfilemap.utils.file_utils import load_ignore_patterns
    import pathspec
    
    ignore_file = get_config_value(config, "file_processing.ignore_file", ".fileignore")
    if not os.path.isabs(ignore_file):
        ignore_file = os.path.join(os.getcwd(), ignore_file)
    
    # Load patterns from .fileignore file
    file_patterns = []
    if os.path.exists(ignore_file):
        file_patterns = load_ignore_patterns(ignore_file)
    
    # Get patterns from config JSON
    config_patterns = get_config_value(config, "file_processing.ignore_patterns", [])
    
    # Merge both sources of patterns
    all_patterns = file_patterns + config_patterns
    
    config["ignore_patterns"] = all_patterns
    config["ignore_pathspec"] = pathspec.PathSpec.from_lines(
        "gitwildmatch", all_patterns
    )

    # Run the process with the merged configuration
    success = run_process(config)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


def main():
    """Main entry point for the application."""
    try:
        if sys.platform == "win32":
            # Set event loop policy for Windows
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # Run the main function directly since it handles async execution internally
        async_main()
    except KeyboardInterrupt:
        error("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        error(f"Unexpected error: {str(e)}")
        if os.environ.get("DEBUG") == "1":
            traceback.print_exc()
        error("[DEBUG] About to call sys.exit(1) in main() exception handler")
        sys.exit(1)


def add_arguments(parser):
    """Add command line arguments to the parser."""
    parser.add_argument("path", help="Path to file or directory to process")
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Process directories recursively"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force regeneration of file maps even if up to date",
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=50,
        help="Minimum number of lines for a file to be processed (default: 50)",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=1000,
        help="Maximum number of lines for a file to be processed (default: 1000)",
    )
    parser.add_argument("--report", help="Path to write JSON report")
    parser.add_argument("--ignore-file", help="Path to file containing ignore patterns")
    parser.add_argument(
        "--include-ext", nargs="+", help="File extensions to include (e.g. .py .js)"
    )
    parser.add_argument("--exclude-ext", nargs="+", help="File extensions to exclude")
    parser.add_argument(
        "--api-key", help="OpenAI API key (can also use OPENAI_API_KEY env var)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="Model to use for generation (default: gpt-4.1-mini)",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=1,
        help="Number of processes to use (default: 1)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent API calls per process (default: 5)",
    )

    # Add validation options
    validation_group = parser.add_argument_group("Validation Options")
    validation_group.add_argument(
        "--enable-validation",
        action="store_true",
        help="Enable AI-assisted validation of generated file maps",
    )
    validation_group.add_argument(
        "--validation-model",
        help="Model to use for validation (defaults to same as generation model)",
    )
    validation_group.add_argument(
        "--strict-validation",
        action="store_true",
        help="Use stricter validation criteria",
    )
    validation_group.add_argument(
        "--abort-on-validation-failure",
        action="store_true",
        help="Abort processing if validation fails",
    )


def create_config_from_args(args) -> Dict[str, Any]:
    """Create configuration dictionary from command line arguments."""
    config = {
        "path": args.path,
        "file_processing": {
            "recursive": args.recursive,
            "min_lines": args.min_lines,
            "max_lines": args.max_lines,
            "ignore_file": args.ignore_file,
        },
        "api": {"vendor": "openai", "model": args.model, "api_key": args.api_key},
        "performance": {"processes": args.processes, "concurrency": args.concurrency},
        "dry_run": args.dry_run,
        "force": args.force,
        "report_path": args.report,
    }

    # Add validation configuration
    config["validation"] = {
        "enabled": args.enable_validation,
        "model": args.validation_model,
        "strict": args.strict_validation,
        "abort_on_failure": args.abort_on_validation_failure,
    }

    # Handle file extensions
    if args.include_ext:
        config["file_processing"]["include_extensions"] = [
            ext if ext.startswith(".") else f".{ext}" for ext in args.include_ext
        ]
    if args.exclude_ext:
        config["file_processing"]["exclude_extensions"] = [
            ext if ext.startswith(".") else f".{ext}" for ext in args.exclude_ext
        ]

    return config


def handle_exception(exc_type, exc_value, exc_traceback):
    """Custom exception handler for better error reporting"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log_error("\n[DEBUG] Unhandled exception caught by sys.excepthook:")


if __name__ == "__main__":
    main()
