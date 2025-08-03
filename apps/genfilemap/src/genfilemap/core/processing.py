"""
Processing functionality for GenFileMap.

This module provides functionality for processing files and updating them with file maps.
"""

import os
import time
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import multiprocessing
from functools import partial

from genfilemap.logging_utils import debug, info, error
from genfilemap.config import get_config_value
from genfilemap.api import create_api_client
from genfilemap.processors import get_processor_for_file
from genfilemap.utils import (
    get_comment_style,
    extract_existing_file_map,
    should_ignore_file,
    load_ignore_patterns,
    expand_ignore_patterns,
    create_default_fileignore,
    get_api_key,
)
from genfilemap.core.file_operations import count_lines
from genfilemap.core.reporting import report_data
from genfilemap.core.validation import (
    validate_file_map,
    log_validation_issues,
    should_abort_on_validation_failure,
)


async def update_file_with_map(
    file_path: str,
    api_client,
    model: str,
    template: Optional[str] = None,
    dry_run: bool = False,
    min_lines: int = 0,
    force: bool = False,
    config: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Update the file with a generated file map.

    Args:
        file_path: Path to the file to update
        api_client: API client instance to use for generating the file map
        model: Model name to use for API calls
        template: Optional template to use for the file map
        dry_run: If True, show what would be done without making changes
        min_lines: Minimum number of lines for a file to be processed
        force: If True, force regeneration even if file hasn't changed
        config: Configuration dictionary

    Returns:
        bool: True if the file was updated, False otherwise
    """
    try:
        # Read the file
        debug(f"Reading file {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Get the appropriate comment style
        comment_style = get_comment_style(file_path)
        debug(f"Using comment style: {comment_style}")

        # Get the appropriate processor for this file type
        processor = get_processor_for_file(file_path, api_client, model, config)
        debug(f"Using processor: {processor.__class__.__name__}")

        # Generate a new file map
        debug(f"Generating file map...")
        try:
            new_map = await processor.generate_file_map(content, comment_style, force)
        except Exception as e:
            # Capture validation failures or other processing errors and mark as actual failures
            error(f"Error generating file map for {file_path}: {str(e)}")
            report_data["errors"] += 1
            report_data["detailed_logs"].append(
                {"file": file_path, "action": "error", "error": str(e)}
            )
            return False

        # If the file map generator decided no changes are needed, exit
        if new_map is None:
            debug(f"No new map generated (None returned)")
            info(f"File map for {file_path} is already up to date. No changes made.")
            report_data["skipped_files"] += 1
            report_data["detailed_logs"].append(
                {"file": file_path, "action": "skipped", "reason": "up-to-date"}
            )
            return False

        # AI validation if enabled
        if get_config_value(config, "validation.enabled", False):
            debug(f"AI validation enabled, validating generated file map...")
            try:
                validation_model = get_config_value(config, "validation.model", model)
                strict_validation = get_config_value(config, "validation.strict", False)

                # Extract the JSON content from the file map for validation
                import re

                # Try to extract JSON from single-line format first (current format)
                json_match = re.search(r"# FILE_MAP_BEGIN (.*?) FILE_MAP_END", new_map)
                if not json_match:
                    # Try old multi-line format as fallback
                    json_match = re.search(
                        r"# FILE_MAP_BEGIN\s*\n# (.*?)\n# FILE_MAP_END",
                        new_map,
                        re.DOTALL,
                    )
                if not json_match:
                    # Try triple-quoted format as fallback
                    json_match = re.search(
                        r'"""[\s]*\n(.*?)\n[\s]*"""', new_map, re.DOTALL
                    )
                if not json_match:
                    # Try HTML/Markdown format (new multi-line)
                    json_match = re.search(
                        r"<!-- FILE_MAP_BEGIN\s*\n<!--\s*\n(.*?)\n\s*-->\s*\n<!-- FILE_MAP_END -->",
                        new_map,
                        re.DOTALL,
                    )
                if not json_match:
                    # Try HTML/Markdown format (old single-line)
                    json_match = re.search(
                        r"<!-- FILE_MAP_BEGIN -->(?:\s*|\s+)<!--\s*(\{.*?\})\s*-->(?:\s*|\s+)<!-- FILE_MAP_END -->",
                        new_map,
                        re.DOTALL,
                    )
                if not json_match:
                    # Try JavaScript/CSS format
                    json_match = re.search(
                        r"/\* FILE_MAP_BEGIN\s*\n(.*?)\s*\*/\s*//\s*FILE_MAP_END",
                        new_map,
                        re.DOTALL,
                    )
                if not json_match:
                    # Try CSS format
                    json_match = re.search(
                        r"/\* FILE_MAP_BEGIN\s*\n(.*?)\s*\*/\s*/\*\s*FILE_MAP_END",
                        new_map,
                        re.DOTALL,
                    )

                if json_match:
                    file_map_json = json_match.group(1)

                    validation_result = await validate_file_map(
                        file_path=file_path,
                        content=content,
                        file_map_json=file_map_json,
                        api_client=api_client,
                        model=validation_model,
                        config=config,
                    )

                    if not validation_result["is_valid"]:
                        # In relaxed mode, log validation issues but continue processing
                        # unless there are truly critical structural issues
                        log_validation_issues(validation_result, file_path)

                        # Check if we should abort based on the severity of issues
                        should_abort = should_abort_on_validation_failure(
                            validation_result, config
                        )

                        if should_abort:
                            error(
                                f"Critical validation failure for {file_path}, aborting"
                            )
                            report_data["errors"] += 1
                            report_data["detailed_logs"].append(
                                {
                                    "file": file_path,
                                    "action": "critical_validation_failure",
                                    "error": validation_result.get(
                                        "summary",
                                        "Critical file map validation failure",
                                    ),
                                    "issues": validation_result.get("issues", []),
                                }
                            )
                            return False
                        else:
                            # Continue processing despite validation issues
                            info(
                                f"Validation issues found for {file_path}, but continuing with file map generation"
                            )
                            report_data["detailed_logs"].append(
                                {
                                    "file": file_path,
                                    "action": "validation_issues_ignored",
                                    "warning": validation_result.get(
                                        "summary",
                                        "Minor validation issues found but ignored",
                                    ),
                                    "issues": validation_result.get("issues", []),
                                }
                            )
                            # Continue to write the file map despite minor validation issues
                    else:
                        debug(f"AI validation passed for {file_path}")
                        if validation_result.get("suggestions"):
                            info(
                                f"Validation suggestions for {file_path}: {validation_result['suggestions']}"
                            )
                else:
                    error(
                        f"Could not extract JSON from generated file map for validation: {file_path}"
                    )

            except Exception as e:
                error(f"Error during AI validation for {file_path}: {str(e)}")
                # Don't fail the entire process due to validation errors unless configured to do so
                if get_config_value(config, "validation.abort_on_failure", False):
                    report_data["errors"] += 1
                    report_data["detailed_logs"].append(
                        {
                            "file": file_path,
                            "action": "validation_error",
                            "error": str(e),
                        }
                    )
                    return False

        # Extract existing file map if it exists
        existing_map, remaining_content = extract_existing_file_map(
            content, comment_style
        )
        debug(f"Existing map found: {existing_map is not None}")

        # If dry run, just print the changes
        if dry_run:
            info(f"\n--- Would update file map for {file_path} ---")
            debug(f"New file map:\n{new_map}")
            report_data["detailed_logs"].append(
                {"file": file_path, "action": "dry-run", "new_map": new_map}
            )
            return True

        # Write the updated content
        debug(f"Writing updated content to file...")
        debug(f"Content starts with: {(new_map + remaining_content)[:50]}...")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_map + remaining_content)

        # Verify the file was written correctly
        debug(f"Verifying file was written correctly...")
        with open(file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()
            if updated_content.startswith(new_map):
                debug(f"File verification successful")
            else:
                error(f"File verification failed! Content doesn't start with file map")
                debug(f"First 50 chars: {updated_content[:50]}")

        info(f"Updated file map for {file_path}")
        report_data["updated_files"] += 1
        report_data["detailed_logs"].append({"file": file_path, "action": "updated"})
        return True

    except Exception as e:
        error(f"Error updating file {file_path}: {str(e)}")
        report_data["errors"] += 1
        report_data["detailed_logs"].append(
            {"file": file_path, "action": "error", "error": str(e)}
        )
        return False


async def process_files_async(config: Dict[str, Any]) -> bool:
    """
    Process files asynchronously with concurrency control.

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if all files were processed successfully, False otherwise
    """
    start_time = time.time()
    path = config.get("path", ".")
    recursive = get_config_value(config, "file_processing.recursive", False)
    ignore_file = get_config_value(config, "file_processing.ignore_file", None)
    dry_run = get_config_value(config, "dry_run", False)
    force = get_config_value(config, "force", False) or get_config_value(
        config, "performance.force_recompute", False
    )
    min_lines = get_config_value(config, "file_processing.min_lines", 50)
    concurrency = get_config_value(config, "performance.concurrency", 5)
    process_count = get_config_value(config, "performance.processes", 1)
    ignore_pathspec = config.get("ignore_pathspec")

    # Check for multi-process mode (only use if process_count > 1)
    if process_count > 1 and not dry_run:
        debug(f"Using multiprocessing with {process_count} processes")
        return process_files_with_multiprocessing(config, process_count)

    debug(
        f"Processing path: {path} (recursive: {recursive}, concurrency: {concurrency})"
    )

    # Load ignore patterns if specified
    ignore_patterns = []
    if ignore_file:
        # Expand user home directory for consistent path resolution
        expanded_ignore_file = os.path.expanduser(ignore_file)
        ignore_patterns = load_ignore_patterns(expanded_ignore_file)
        debug(
            f"Loaded {len(ignore_patterns)} ignore patterns from {expanded_ignore_file}"
        )

    # Get include and exclude extensions
    include_extensions = get_config_value(
        config, "file_processing.include_extensions", []
    )
    exclude_extensions = get_config_value(
        config, "file_processing.exclude_extensions", []
    )

    if include_extensions:
        debug(f"Including extensions: {', '.join(include_extensions)}")
    if exclude_extensions:
        debug(f"Excluding extensions: {', '.join(exclude_extensions)}")

    # Get API configuration
    vendor = get_config_value(config, "api.vendor", "openai")
    model = get_config_value(config, "api.model", "gpt-4.1-mini")
    api_key = get_api_key(vendor, config)

    # Create API client
    api_client = create_api_client(vendor, api_key, config)

    # Gather files to process
    files_to_process = []

    # If we don't have a pre-populated list, gather files to process
    if not files_to_process:
        if os.path.isfile(path):
            if not should_ignore_file(path, pathspec_obj=ignore_pathspec):
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if content.count("\n") + 1 < min_lines:
                    info(f"Skipping {path}: fewer than {min_lines} lines")
                else:
                    files_to_process.append(path)
            else:
                info(f"Skipping {path}: matched ignore pattern")
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore_file(
                        os.path.join(root, d), pathspec_obj=ignore_pathspec
                    )
                ]
                for file in files:
                    file_path = os.path.join(root, file)
                    if should_ignore_file(file_path, pathspec_obj=ignore_pathspec):
                        continue
                    _, ext = os.path.splitext(file_path)
                    if include_extensions and ext.lower() not in include_extensions:
                        continue
                    if exclude_extensions and ext.lower() in exclude_extensions:
                        continue
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            content = f.read()
                        if content.count("\n") + 1 < min_lines:
                            debug(f"Skipping {file_path}: fewer than {min_lines} lines")
                            continue
                        files_to_process.append(file_path)
                    except Exception as e:
                        error(f"Error reading {file_path}: {str(e)}")
                if not recursive:
                    break
        else:
            error(f"Path not found: {path}")
            return False
    else:
        # If we already have a pre-populated list, log it
        debug(f"Using pre-populated list of {len(files_to_process)} files")

    info(f"Found {len(files_to_process)} files to process")

    if not files_to_process:
        info("No files to process")
        return True

    # Create semaphore for limiting concurrent operations
    semaphore = asyncio.Semaphore(concurrency)

    # Process files with concurrency limit
    debug(f"Using concurrency limit of {concurrency}")

    async def process_with_semaphore(file_path):
        async with semaphore:
            # Add a small delay to avoid overwhelming the API
            await asyncio.sleep(0.1)
            try:
                result = await update_file_with_map(
                    file_path=file_path,
                    api_client=api_client,
                    model=model,
                    dry_run=dry_run,
                    force=force,
                    min_lines=min_lines,
                    config=config,
                )
                # Special handling for skipped files
                # If a file was skipped (returns False from update_file_with_map),
                # we should treat it as a success for counting purposes
                if result is False:
                    # Check if this was reported as skipped in the logs
                    for log in report_data.get("detailed_logs", []):
                        if (
                            log.get("file") == file_path
                            and log.get("action") == "skipped"
                        ):
                            debug(
                                f"Treating skipped file as success for counting: {file_path}"
                            )
                            return True  # Count skipped files as success
                return result
            except Exception as e:
                error(f"Error processing {file_path}: {str(e)}")
                return False

    # Create tasks for each file
    tasks = [process_with_semaphore(file_path) for file_path in files_to_process]

    # Run tasks concurrently with semaphore limit
    results = await asyncio.gather(*tasks)

    # Count successes and failures
    successes = sum(1 for r in results if r is True)

    # Check detailed logs to identify which False results were skips
    skipped_files = set()
    for log in report_data.get("detailed_logs", []):
        if log.get("action") == "skipped" and "file" in log:
            skipped_files.add(log.get("file"))

    # Count actual failures (excluding skipped files which returned False)
    failures = len(files_to_process) - successes - len(skipped_files)

    # Calculate statistics
    elapsed_time = time.time() - start_time
    files_per_second = len(files_to_process) / elapsed_time if elapsed_time > 0 else 0

    # Ensure failures is never negative
    failures = max(0, failures)

    # For the status breakdown, we only want to count files that were actually updated,
    # not those that were already up-to-date
    actual_updates = report_data["updated_files"]

    # Use the error count from report_data for accurate failure reporting
    failures = report_data["errors"]

    info(
        f"Processed {len(files_to_process)} files in {elapsed_time:.2f} seconds ({files_per_second:.2f} files/sec)"
    )
    info(f"Success: {len(files_to_process) - failures}, Failures: {failures}")
    info(
        f"Status breakdown: {actual_updates} updated, {len(skipped_files)} already up-to-date, {failures} failed"
    )

    # Log API statistics if available
    if hasattr(api_client, "stats") and isinstance(api_client.stats, dict):
        info(f"API calls: {api_client.stats.get('api_calls', 0)}")
        info(f"Tokens used: {api_client.stats.get('tokens_used', 0)}")

    return failures == 0


def process_file_batch(batch_index, file_batch, config, expanded_ignore_patterns=None):
    """
    Process a batch of files in a separate process.

    Args:
        batch_index: Index of the batch (for reporting)
        file_batch: List of files to process
        config: Configuration dictionary
        expanded_ignore_patterns: Pre-expanded ignore patterns to use

    Returns:
        dict: Results of batch processing
    """
    batch_config = config.copy()  # Create a copy of the config for this process

    # Save expanded ignore patterns in the config for use in nested functions
    if expanded_ignore_patterns is not None:
        batch_config["_expanded_ignore_patterns"] = expanded_ignore_patterns

    # Set up process-specific logging
    batch_name = f"Process-{batch_index+1}"
    debug(f"[{batch_name}] Starting batch processing of {len(file_batch)} files")
    debug(f"[{batch_name}] Process ID: {os.getpid()}")

    # Create a new event loop for this process
    asyncio.set_event_loop(asyncio.new_event_loop())

    # Define the async processing function for this batch
    async def process_batch_async():
        # Get API configuration
        vendor = get_config_value(batch_config, "api.vendor", "openai")
        model = get_config_value(batch_config, "api.model", "gpt-4.1-mini")
        api_key_var = get_config_value(batch_config, "api.key_var", "OPENAI_API_KEY")
        api_key = os.environ.get(api_key_var, "")
        dry_run = get_config_value(batch_config, "dry_run", False)
        force = get_config_value(batch_config, "force", False) or get_config_value(
            batch_config, "performance.force_recompute", False
        )
        concurrency = get_config_value(batch_config, "performance.concurrency", 5)
        min_lines = get_config_value(batch_config, "file_processing.min_lines", 50)

        # Create API client for this process
        api_client = create_api_client(vendor, api_key, batch_config)

        # Create semaphore for limiting concurrent operations in this process
        semaphore = asyncio.Semaphore(concurrency)

        # Process files with concurrency limit
        debug(f"[{batch_name}] Using concurrency limit of {concurrency}")

        # Skip empty batches - this fixes the "Process 3 API calls" issue
        if not file_batch:
            debug(f"[{batch_name}] Empty batch, no files to process")
            return {
                "batch_index": batch_index,
                "processed": 0,
                "successes": 0,
                "failures": 0,
                "api_calls": 0,
                "tokens_used": 0,
            }

        async def process_with_semaphore(file_path):
            async with semaphore:
                # Add a small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)
                try:
                    # Double-check that the file should still be processed, applying expanded
                    # ignore patterns if available
                    ignore_patterns = batch_config.get("_expanded_ignore_patterns", [])
                    if ignore_patterns and should_ignore_file(
                        file_path, ignore_patterns
                    ):
                        debug(
                            f"[{batch_name}] Skipping {file_path}: matched ignore pattern (child process check)"
                        )
                        return True  # Return True to not count as failure

                    result = await update_file_with_map(
                        file_path=file_path,
                        api_client=api_client,
                        model=model,
                        dry_run=dry_run,
                        force=force,
                        min_lines=min_lines,
                        config=batch_config,
                    )

                    # Special handling for skipped files (up-to-date maps)
                    if result is False:
                        # We don't have direct access to report_data here, so we'll infer from logs
                        # If update_file_with_map returned False but didn't raise an exception,
                        # it's likely because the file was skipped as already up-to-date
                        debug(
                            f"[{batch_name}] File likely skipped as up-to-date: {file_path}"
                        )
                        return True  # Count skipped files as success

                    return result
                except Exception as e:
                    error(f"[{batch_name}] Error processing {file_path}: {str(e)}")
                    return False

        # Create tasks for each file in this batch
        tasks = [process_with_semaphore(file_path) for file_path in file_batch]

        # Run tasks concurrently with semaphore limit
        results = await asyncio.gather(*tasks)

        # Count successes and failures
        # Modified logic: All True results are successes
        direct_successes = sum(1 for r in results if r is True)

        # We don't have direct access to report_data here
        # But we know that files that returned False were likely skipped as up-to-date
        # So we'll count them as successes too
        skipped_successes = sum(1 for r in results if r is False)

        # Total successes include both direct and skipped
        successes = direct_successes + skipped_successes

        # True failures are files that threw exceptions
        # Ensure failures is never negative
        failures = max(0, len(file_batch) - successes)

        # Log API statistics if available
        if hasattr(api_client, "stats") and isinstance(api_client.stats, dict):
            info(f"[{batch_name}] API calls: {api_client.stats.get('api_calls', 0)}")
            info(
                f"[{batch_name}] Tokens used: {api_client.stats.get('tokens_used', 0)}"
            )

        debug(
            f"[{batch_name}] Completed batch: {successes} successes ({direct_successes} updated, {skipped_successes} already up-to-date), {failures} failures"
        )

        # Return batch results
        return {
            "batch_index": batch_index,
            "processed": len(file_batch),
            "successes": successes,
            "failures": failures,
            "api_calls": (
                api_client.stats.get("api_calls", 0)
                if hasattr(api_client, "stats")
                else 0
            ),
            "tokens_used": (
                api_client.stats.get("tokens_used", 0)
                if hasattr(api_client, "stats")
                else 0
            ),
        }

    # Run the async processing and return results
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(process_batch_async())


def process_files_with_multiprocessing(
    config: Dict[str, Any], process_count: int
) -> bool:
    """
    Process files using multiple processes for parallel execution.

    This function divides files into batches and processes each batch in a separate process.
    Each process still uses asyncio for concurrent API calls within the process.

    Args:
        config: Configuration dictionary
        process_count: Number of processes to use

    Returns:
        bool: True if processing was successful, False otherwise
    """
    start_time = time.time()
    path = config.get("path", ".")
    recursive = get_config_value(config, "file_processing.recursive", False)
    ignore_file = get_config_value(config, "file_processing.ignore_file", None)
    min_lines = get_config_value(config, "file_processing.min_lines", 50)
    ignore_pathspec = config.get("ignore_pathspec")

    # Load ignore patterns if specified and expand paths for consistent processing across processes
    ignore_patterns = []
    expanded_ignore_patterns = []

    if ignore_file:
        # Expand user home directory for consistent path resolution
        expanded_ignore_file = os.path.expanduser(ignore_file)
        ignore_patterns = load_ignore_patterns(expanded_ignore_file)
        expanded_ignore_patterns = expand_ignore_patterns(ignore_patterns)

        debug(
            f"Loaded {len(ignore_patterns)} ignore patterns from {expanded_ignore_file}"
        )
        debug(
            f"Expanded {sum(1 for i, p in enumerate(expanded_ignore_patterns) if p != ignore_patterns[i])} patterns with home directory references"
        )

    # Get include and exclude extensions
    include_extensions = get_config_value(
        config, "file_processing.include_extensions", []
    )
    exclude_extensions = get_config_value(
        config, "file_processing.exclude_extensions", []
    )

    # Check if we already have a pre-populated list of files from directory hashing or other sources
    files_to_process = config.get("files_to_process", [])

    # If we don't have a pre-populated list, gather files to process
    if not files_to_process:
        if os.path.isfile(path):
            debug("Single file mode detected, falling back to single-process mode")
            return process_files_single_process(config)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore_file(
                        os.path.join(root, d), pathspec_obj=ignore_pathspec
                    )
                ]
                for file in files:
                    file_path = os.path.join(root, file)
                    if should_ignore_file(file_path, pathspec_obj=ignore_pathspec):
                        continue
                    _, ext = os.path.splitext(file_path)
                    if include_extensions and ext.lower() not in include_extensions:
                        continue
                    if exclude_extensions and ext.lower() in exclude_extensions:
                        continue
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            content = f.read()
                        if content.count("\n") + 1 < min_lines:
                            debug(f"Skipping {file_path}: fewer than {min_lines} lines")
                            continue
                        files_to_process.append(file_path)
                    except Exception as e:
                        error(f"Error reading {file_path}: {str(e)}")
                if not recursive:
                    break
        else:
            error(f"Path not found: {path}")
            return False
    else:
        # If we already have a pre-populated list, log it
        debug(f"Using pre-populated list of {len(files_to_process)} files")

    info(
        f"Found {len(files_to_process)} files to process with {process_count} processes"
    )

    if not files_to_process:
        info("No files to process")
        return True

    # Divide files into batches for each process
    batch_size = max(1, len(files_to_process) // process_count)
    file_batches = [
        files_to_process[i : i + batch_size]
        for i in range(0, len(files_to_process), batch_size)
    ]

    # Ensure we don't create more processes than needed
    actual_process_count = min(process_count, len(file_batches))
    debug(
        f"Using {actual_process_count} processes with approximately {batch_size} files per process"
    )

    # Debug main process ID for comparison
    debug(f"Main process ID: {os.getpid()}")

    # If a batch is empty, don't create a process for it (fixes the Process 3 API calls issue when no files change)
    file_batches = [batch for batch in file_batches if batch]

    # Recreate actual_process_count based on non-empty batches
    actual_process_count = min(process_count, len(file_batches))
    if actual_process_count != process_count:
        info(
            f"Adjusted to {actual_process_count} processes after removing empty batches"
        )

    if actual_process_count == 0:
        # If no files need processing after filtering, return success
        info("No files need processing after filtering")
        return True

    # Create a process pool and execute batch processing
    with multiprocessing.Pool(processes=actual_process_count) as pool:
        batch_results = pool.starmap(
            process_file_batch,
            [
                (i, batch, config, expanded_ignore_patterns)
                for i, batch in enumerate(file_batches[:actual_process_count])
            ],
        )

    # Aggregate results
    total_processed = sum(result["processed"] for result in batch_results)
    total_successes = sum(result["successes"] for result in batch_results)
    total_failures = sum(result["failures"] for result in batch_results)
    # Ensure failures is never negative
    total_failures = max(0, total_failures)
    total_api_calls = sum(result["api_calls"] for result in batch_results)
    total_tokens_used = sum(result["tokens_used"] for result in batch_results)

    # Calculate statistics
    elapsed_time = time.time() - start_time
    files_per_second = total_processed / elapsed_time if elapsed_time > 0 else 0

    info(
        f"Processed {total_processed} files in {elapsed_time:.2f} seconds ({files_per_second:.2f} files/sec)"
    )
    info(f"Success: {total_successes}, Failures: {total_failures}")
    info(f"Total API calls: {total_api_calls}")
    info(f"Total tokens used: {total_tokens_used}")

    return total_failures == 0


def process_files_single_process(config: Dict[str, Any]) -> bool:
    """
    Wrapper function to process files in a single process, using the standard async processing.
    This function runs the async function in the current process.

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if processing was successful, False otherwise
    """
    # Set the multiprocessing flag to 1 to ensure we don't recurse
    config_copy = config.copy()
    config_copy["performance.processes"] = 1

    # Get the current event loop or create a new one if needed
    try:
        loop = asyncio.get_running_loop()
        # If we get here, there's already a running loop
        return loop.create_task(process_files_async(config_copy))
    except RuntimeError:
        # No running event loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(process_files_async(config_copy))
