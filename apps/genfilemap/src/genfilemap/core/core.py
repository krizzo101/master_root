
"""
Core process runner for GenFileMap.

This module provides the main entry point for the GenFileMap process,
coordinating between specialized modules for processing, cleaning, and reporting.
"""

import time
import asyncio
import os
from typing import Dict, Any

from genfilemap.core.processing import process_files_async
from genfilemap.core.cleaning import clean_files_async, deep_clean_files_async
from genfilemap.core.reporting import generate_report, report_data
from genfilemap.core.project_map import generate_project_map
from genfilemap.core.directory_hash_processing import process_files_with_directory_hashing
from genfilemap.logging_utils import info, debug, error, initialize_logging
from genfilemap.config import get_config_value

def run_process(config: Dict[str, Any]) -> bool:
    """
    Run the processing workflow.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Record start time
    start_time = time.time()
    
    # Disable project map generation by default unless explicitly requested
    project_map_explicitly_set = "project_map" in config and config["project_map"] is True
    if not project_map_explicitly_set:
        config["project_map"] = False
    
    # Initialize logging
    if "initialize_logging" in globals():
        initialize_logging(config)
    
    info("Starting GenFileMap process")
    
    # Log details about project map setting for debugging
    if project_map_explicitly_set:
        debug("Project map enabled via explicit request")
    else:
        debug("Project map disabled (not explicitly requested)")
            
    try:
        # Check if a deep clean operation was requested
        if get_config_value(config, "clean", False):
            # Clean mode
            info("Running in clean mode - removing file maps")
            # Run the async function in an event loop
            success = asyncio.run(clean_files_async(config))
            
            if not success:
                error("Errors occurred during cleaning process")
                return False
                
            # End early since we're only cleaning
            info("Cleaning completed successfully")
            return True
        
        elif get_config_value(config, "deep_clean", False):
            # Deep clean mode
            info("Running in deep clean mode - checking all files for FILE_MAP_BEGIN and removing file maps")
            # Run the async function in an event loop
            success = asyncio.run(deep_clean_files_async(config))
            
            if not success:
                error("Errors occurred during deep cleaning process")
                return False
                
            # End early since we're only cleaning
            info("Deep cleaning completed successfully")
            return True
        
        # Check if directory hashing should be used
        use_dir_hashing = get_config_value(config, "use_dir_hashing", False)
        recursive = get_config_value(config, "recursive", False)
        
        if use_dir_hashing and recursive:
            # Use directory hashing optimization
            info("Using directory-level hashing optimization")
            success = process_files_with_directory_hashing(config)
        else:
            # Normal mode - process and update file maps
            info("Processing files to generate file maps")
            # Run the async function in an event loop
            success = asyncio.run(process_files_async(config))
        
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