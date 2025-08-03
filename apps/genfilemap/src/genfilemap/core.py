"""
Core functionality for generating file maps.

This module serves as the main entry point for the GenFileMap functionality,
coordinating between specialized modules for processing, cleaning, and reporting.
"""

import time
from typing import Dict, Any
import os

# Re-export from specialized modules for backward compatibility
from genfilemap.core.file_operations import count_lines, get_hash_file_path
from genfilemap.core.processing import process_files_async, update_file_with_map
from genfilemap.core.cleaning import clean_files_async, clean_file_maps
from genfilemap.core.reporting import generate_report, report_data
from genfilemap.core.project_map import generate_project_map
from genfilemap.logging_utils import configure_logging, get_logger, info, debug, error
from genfilemap.config import get_config_value

# Re-export all functions for backward compatibility
__all__ = [
    'update_file_with_map',
    'clean_file_maps',
    'process_files_async',
    'clean_files_async',
    'generate_project_map',
    'generate_report',
    'count_lines',
    'get_hash_file_path',
    'report_data',
    'initialize_logging',
    'run_process'
]

def initialize_logging(config: Dict[str, Any]):
    """
    Initialize logging based on configuration.

    Args:
        config: Configuration dictionary with logging options

    Returns:
        The configured logger
    """
    # Configure logging system
    debug_mode = get_config_value(config, "debug", False)
    log_level = "debug" if debug_mode else get_config_value(config, "log_level", "info")

    logging_config = {
        "log_level": log_level,
        "log_file": get_config_value(config, "log_file"),
        "console_output": True,
        "debug": debug_mode
    }

    configure_logging(logging_config)
    logger = get_logger()

    if debug_mode:
        debug("Debug logging enabled")

    return logger

def run_process(config: Dict[str, Any]) -> bool:
    """
    Run the processing workflow.

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if successful, False otherwise
    """
    # Initialize logging
    initialize_logging(config)

    # Record start time
    start_time = time.time()
    info("Starting GenFileMap process")

    # Print key configuration values for debugging
    info(f"Running process with configuration:")
    info(f"  - Path: {config.get('path', '.')}")
    info(f"  - Force: {config.get('force', False)}")
    info(f"  - Dry run: {config.get('dry_run', False)}")
    info(f"  - Debug: {config.get('debug', False)}")
    info(f"  - Clean: {config.get('clean', False)}")

    try:
        # Disable project map generation by default unless explicitly requested
        project_map_explicitly_set = "project_map" in config and config["project_map"] is True
        if not project_map_explicitly_set:
            config["project_map"] = False
            debug("Project map disabled (not explicitly requested)")
        else:
            debug("Project map enabled via explicit request")

        # Process files
        if get_config_value(config, "clean", False):
            # Clean mode
            info("Running in clean mode - removing file maps")
            success = clean_files_async(config)
        else:
            # Normal mode - process and update file maps
            info("Processing files to generate file maps")
            success = process_files_async(config)

        # Generate project map if requested
        if get_config_value(config, "project_map", False):
            # Make sure we're not processing a single file unless explicitly requested
            path = config.get("path", ".")
            is_single_file = os.path.isfile(path)
            project_map_explicitly_set = "project_map" in config and config["project_map"] is True

            if not is_single_file or project_map_explicitly_set:
                info("Generating project-level file map")
                generate_project_map(config)
            else:
                debug("Skipping project map generation for single file processing without explicit request")

        # Generate report
        report_file = get_config_value(config, "report")
        if report_file:
            # Calculate duration if not already set
            if report_data["duration"] == 0:
                report_data["duration"] = time.time() - start_time

            info(f"Generating report at {report_file}")
            generate_report(report_file, report_data)

        return success

    except Exception as e:
        error(f"Error in run_process: {str(e)}")
        return False