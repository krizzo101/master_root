
"""
Directory Hash-based File Processing Module for GenFileMap.

This module provides optimized file processing functionality by using directory-level
hashing to only process directories that have changed since the last run.

FILE_MAP_BEGIN
version: 1.0
author: GenFileMap
created_at: 2023-10-07
description: Directory hash-based file processing module
metadata:
  type: core_module
  complexity: high
  last_modified: 2023-10-07
sections:
  imports: 1-16
  processing_function: 18-129
key_elements:
  - process_files_with_directory_hashing: 19
FILE_MAP_END
"""

import os
import time
import shutil
from typing import Dict, Any, List, Optional, Set, Union, Tuple, Callable

from genfilemap.logging_utils import debug, info, error
from genfilemap.config import get_config_value
from genfilemap.utils import load_ignore_patterns, should_ignore_file
from genfilemap.core.processing import process_files_async
from genfilemap.core.directory_hash import (
    load_hash_cache, save_hash_cache, find_changed_directories, compute_directory_hashes
)


def process_files_with_directory_hashing(config: Dict[str, Any]) -> bool:
    """
    Process files using directory-level change detection for optimization.

    This function:
    1. Computes directory-level hashes for the specified path
    2. Compares with cached hashes from previous runs to identify changed directories
    3. Only processes files in directories that have changed
    4. Updates the cache for future runs

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if processing was successful, False otherwise
    """
    start_time = time.time()
    debug("Starting file processing with directory hashing optimization")

    # Extract configuration values
    path = config.get("path", ".")
    recursive = get_config_value(config, "file_processing.recursive", False)
    ignore_file = get_config_value(config, "file_processing.ignore_file", None)
    ignore_pathspec = config.get('ignore_pathspec')

    # Always use project-local cache in the project root directory
    # Convert relative path to absolute path if it's not already
    if not os.path.isabs(path):
        abs_path = os.path.abspath(path)
        info(f"Converting relative path '{path}' to absolute path '{abs_path}'")
        path = abs_path
    else:
        info(f"Using provided absolute path: '{path}'")

    # Normalize the path (resolves any ../ and ./ segments)
    project_root = os.path.normpath(path)
    info(f"Normalized project root: '{project_root}'")

    # Define project-local .genfilemap directory with absolute path
    genfilemap_dir = os.path.join(project_root, '.genfilemap')
    cache_dir = os.path.join(genfilemap_dir, 'cache')

    info(f"Using GenFileMap directory: '{genfilemap_dir}'")
    info(f"Using cache directory: '{cache_dir}'")

    # Force creation of the .genfilemap directory and cache subdirectory
    try:
        # Create main .genfilemap directory with parents=True to ensure full path is created
        os.makedirs(genfilemap_dir, exist_ok=True)
        debug(f"Checking if .genfilemap directory exists: {os.path.exists(genfilemap_dir)}")
        info(f"Created/verified .genfilemap directory at: '{genfilemap_dir}'")

        # Create cache subdirectory
        os.makedirs(cache_dir, exist_ok=True)
        debug(f"Checking if cache directory exists: {os.path.exists(cache_dir)}")
        info(f"Created/verified cache directory at: '{cache_dir}'")

        # Output a listing of the directories to confirm their existence
        if os.path.exists(genfilemap_dir):
            try:
                genfilemap_contents = os.listdir(genfilemap_dir)
                info(f"Contents of .genfilemap directory: {genfilemap_contents}")
            except Exception as e:
                error(f"Error listing .genfilemap directory: {str(e)}")

        # If there's a global .fileignore template, copy it to the project
        global_template = os.path.expanduser("~/.genfilemap/.fileignore.template")
        if os.path.exists(global_template) and not os.path.exists(os.path.join(genfilemap_dir, '.fileignore')):
            try:
                local_ignore = os.path.join(genfilemap_dir, '.fileignore')
                shutil.copy2(global_template, local_ignore)
                info(f"Copied global .fileignore template to '{local_ignore}'")
            except Exception as e:
                debug(f"Failed to copy global .fileignore template: {str(e)}")
    except Exception as e:
        # If we can't create the directory, log the error but continue with temporary directory
        error(f"Failed to create cache directory: {str(e)}")
        import tempfile
        temp_dir = tempfile.gettempdir()
        cache_dir = os.path.join(temp_dir, 'genfilemap_cache')
        os.makedirs(cache_dir, exist_ok=True)
        info(f"Using fallback temporary cache directory: '{cache_dir}'")

    # Define cache file path
    cache_file = os.path.join(cache_dir, "directory_hash_cache.json")
    info(f"Using cache file: '{cache_file}'")

    # Load ignore patterns
    ignore_patterns = []
    if ignore_file:
        expanded_ignore_file = os.path.expanduser(ignore_file)
        if os.path.exists(expanded_ignore_file):
            ignore_patterns = load_ignore_patterns(expanded_ignore_file)
            debug(f"Loaded {len(ignore_patterns)} ignore patterns from {ignore_file}")

    # Get force_recompute flag
    force_recompute = get_config_value(config, "performance.force_recompute", False)

    # Load existing cache unless forced to recompute
    cache = {}
    if not force_recompute:
        cache = load_hash_cache(cache_file)
        debug(f"Loaded hash cache with {len(cache)} entries from {cache_file}")

    # Check for directory-level changes
    if not recursive:
        # If not recursive, just process the directory directly
        debug("Non-recursive mode: processing single directory")
        return process_files_async(config)

    # Find directories with changes
    debug(f"Finding changed directories in {path}")
    changed_dirs = find_changed_directories(path, cache, ignore_patterns)

    if not changed_dirs:
        info("No directory changes detected - skipping file processing")
        # Report that no API calls were made since no changes were detected
        if hasattr(config, "reporting") and config["reporting"].get("print_api_stats", True):
            info("API calls: 0 (no changes detected)")
        return True

    info(f"Processing {len(changed_dirs)} changed directories")

    # Handle multiprocessing with directory hashing correctly
    # If we're in multiprocessing mode, we need to pass only the changed directories
    # This prevents multiple processes from being created for unchanged directories
    process_count = get_config_value(config, "performance.processes", 1)
    if process_count > 1:
        debug(f"Using multiprocessing with {process_count} processes for changed directories")

        # Create a modified config that only processes changed directories
        modified_config = config.copy()
        # We'll handle the changed directories here rather than letting process_files_async recurse
        modified_config["file_processing.recursive"] = False

        # Create a list to store all files that need processing
        all_files_to_process = []

        # Gather all files from changed directories
        for dir_path in changed_dirs:
            files_in_dir = []
            if os.path.isdir(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    dirs[:] = [d for d in dirs if not should_ignore_file(os.path.join(root, d), pathspec_obj=ignore_pathspec)]
                    for file in files:
                        file_path = os.path.join(root, file)
                        if should_ignore_file(file_path, pathspec_obj=ignore_pathspec):
                            continue

                        # Check file extension
                        _, ext = os.path.splitext(file_path)
                        include_extensions = get_config_value(config, "file_processing.include_extensions", [])
                        exclude_extensions = get_config_value(config, "file_processing.exclude_extensions", [])

                        if include_extensions and ext.lower() not in include_extensions:
                            continue
                        if exclude_extensions and ext.lower() in exclude_extensions:
                            continue

                        # Only include this file if it meets the minimum line count
                        min_lines = get_config_value(config, "file_processing.min_lines", 50)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()

                            if content.count('\n') + 1 < min_lines:
                                debug(f"Skipping {file_path}: fewer than {min_lines} lines")
                                continue

                            files_in_dir.append(file_path)
                        except Exception as e:
                            error(f"Error reading {file_path}: {str(e)}")

            # Add files from this directory to the overall list
            all_files_to_process.extend(files_in_dir)
            debug(f"Found {len(files_in_dir)} eligible files in changed directory: {dir_path}")

        # Set the path to the list of individual files
        if all_files_to_process:
            debug(f"Total files to process from changed directories: {len(all_files_to_process)}")
            # Call multiprocessing directly with the list of files
            modified_config["files_to_process"] = all_files_to_process
            modified_config["path"] = project_root  # Keep the original path for context
            success = process_files_with_multiprocessing(modified_config, process_count)
        else:
            info("No eligible files found in changed directories")
            success = True
    else:
        # Process each changed directory sequentially
        success = True
        for dir_path in changed_dirs:
            # Create a copy of the config with the directory path
            dir_config = config.copy()
            dir_config["path"] = dir_path

            # By default, don't recurse further since we're already handling recursion
            # But if the changed directory is the root, we need to recurse to find files
            if dir_path == os.path.abspath(os.path.normpath(path)):
                dir_config["file_processing.recursive"] = True
            else:
                dir_config["file_processing.recursive"] = False

            debug(f"Processing changed directory: {dir_path}")
            dir_success = process_files_async(dir_config)
            success = success and dir_success

    # Update cache with new hashes
    if success:
        debug(f"Updating directory hash cache for {path}")
        new_hashes = compute_directory_hashes(path, ignore_patterns)
        abs_path = os.path.abspath(os.path.normpath(path))
        cache[abs_path] = new_hashes
        save_hash_cache(cache, cache_file)
        debug(f"Saved updated hash cache to {cache_file}")

    # Calculate statistics
    elapsed_time = time.time() - start_time
    info(f"Directory hash-based processing completed in {elapsed_time:.2f} seconds")

    return success