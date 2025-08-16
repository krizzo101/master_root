# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Core Functionality for Generating File Maps","description":"This module contains the main logic for generating and updating file maps, including functions for processing files asynchronously and generating reports.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Contains all the necessary imports for the module.","line_start":3,"line_end":16},{"name":"Global Variables","description":"Defines the report_data dictionary to track processing statistics.","line_start":18,"line_end":20},{"name":"Function: get_api_key","description":"Retrieves the API key based on the provided configuration.","line_start":22,"line_end":36},{"name":"Function: update_file_with_map","description":"Updates a specified file with a generated file map asynchronously.","line_start":38,"line_end":272},{"name":"Function: process_files_async","description":"Processes files using asynchronous operations, managing concurrency and file handling.","line_start":274,"line_end":330},{"name":"Function: generate_project_map","description":"Generates a project-level file map that consolidates references to all project files and their file maps.","line_start":332,"line_end":356},{"name":"Function: generate_report","description":"Generates a summary report of file map operations.","line_start":358,"line_end":357}],"key_elements":[{"name":"report_data","description":"Dictionary to track the statistics of processed files.","line":18},{"name":"get_api_key","description":"Function to retrieve the API key from the configuration.","line":22},{"name":"update_file_with_map","description":"Function to update a file with a generated file map.","line":38},{"name":"process_files_async","description":"Function to process files asynchronously.","line":274},{"name":"generate_project_map","description":"Function to generate a project-level file map.","line":332},{"name":"generate_report","description":"Function to generate a report of file map operations.","line":358}]}
"""
# FILE_MAP_END

"""
Core functionality for generating file maps.

This module contains the main logic for generating and updating file maps.
"""

import os
import time
import asyncio
import json
from pathlib import Path
from typing import Optional

from genfilemap.config import Config
from genfilemap.api import create_api_client
from genfilemap.processors import get_processor_for_file
from genfilemap.utils.file_utils import (
    get_comment_style,
    extract_existing_file_map,
    should_ignore_file,
    load_ignore_patterns,
)

# Report data
report_data = {
    "processed_files": 0,
    "updated_files": 0,
    "skipped_files": 0,
    "errors": 0,
    "api_calls": 0,
    "api_tokens_used": 0,
    "duration": 0,
    "detailed_logs": [],
}


def get_api_key(config: Config) -> str:
    """Get API key based on configuration"""
    # First check if direct API key is configured
    api_key = config.get("api.api_key")
    if api_key:
        return api_key

    # Next, check if we have an environment variable name to use
    api_key_var = config.get("api.api_key_var")
    if api_key_var:
        api_key = os.environ.get(api_key_var)
        if not api_key:
            raise ValueError(f"{api_key_var} environment variable not set")
        return api_key

    # Fallback to vendor-specific environment variables
    vendor = config.get("api.vendor")
    if vendor == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return api_key
    elif vendor == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return api_key
    elif vendor == "cohere":
        api_key = os.environ.get("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable not set")
        return api_key
    else:
        raise ValueError(f"Unsupported vendor: {vendor}")


async def update_file_with_map(
    file_path: str,
    api_client,
    model: str,
    template: Optional[str] = None,
    dry_run: bool = False,
    min_lines: int = 0,
) -> bool:
    """Update the file with a generated file map"""
    try:
        # Read the file
        print(f"DEBUG: Reading file {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if file is too short for a file map
        if min_lines > 0:
            line_count = content.count("\n") + 1
            if line_count < min_lines:
                print(
                    f"Skipping file map for {file_path}: only {line_count} lines (minimum: {min_lines})"
                )
                report_data["skipped_files"] += 1
                report_data["detailed_logs"].append(
                    {"file": file_path, "action": "skipped", "reason": "too-short"}
                )
                return False

        # Get the appropriate comment style
        comment_style = get_comment_style(file_path)
        print(f"DEBUG: Using comment style: {comment_style}")

        # Get the appropriate processor for this file type
        processor = get_processor_for_file(file_path, api_client, model)
        print(f"DEBUG: Using processor: {processor.__class__.__name__}")

        # Generate a new file map
        print("DEBUG: Generating file map...")
        new_map = await processor.generate_file_map(content, comment_style)

        # If the file map generator decided no changes are needed, exit
        if new_map is None:
            print("DEBUG: No new map generated (None returned)")
            print(f"File map for {file_path} is already up to date. No changes made.")
            report_data["skipped_files"] += 1
            report_data["detailed_logs"].append(
                {"file": file_path, "action": "skipped", "reason": "up-to-date"}
            )
            return False

        # Extract existing file map if it exists
        existing_map, remaining_content = extract_existing_file_map(
            content, comment_style
        )
        print(f"DEBUG: Existing map found: {existing_map is not None}")

        # If dry run, just print the changes
        if dry_run:
            print(f"\n--- Would update file map for {file_path} ---")
            print(f"New file map:\n{new_map}")
            report_data["detailed_logs"].append(
                {"file": file_path, "action": "dry-run", "new_map": new_map}
            )
            return True

        # Write the updated content
        print("DEBUG: Writing updated content to file...")
        print(f"DEBUG: Content starts with: {(new_map + remaining_content)[:50]}...")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_map + remaining_content)

        # Verify the file was written correctly
        print("DEBUG: Verifying file was written correctly...")
        with open(file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()
            if updated_content.startswith(new_map):
                print("DEBUG: File verification successful")
            else:
                print(
                    "DEBUG: ERROR - File verification failed! Content doesn't start with file map"
                )
                print(f"DEBUG: First 50 chars: {updated_content[:50]}")

        print(f"Updated file map for {file_path}")
        report_data["updated_files"] += 1
        report_data["detailed_logs"].append({"file": file_path, "action": "updated"})
        return True

    except Exception as e:
        print(f"Error updating file {file_path}: {str(e)}")
        report_data["errors"] += 1
        report_data["detailed_logs"].append(
            {"file": file_path, "action": "error", "error": str(e)}
        )
        return False


async def process_files_async(config):
    """Process files using async operations"""
    start_time = time.time()

    # Get settings from config
    path = config.get("path")
    recursive = config.get("file_processing.recursive")
    include = config.get("file_processing.include_extensions")
    exclude = config.get("file_processing.exclude_extensions")
    min_lines = config.get("file_processing.min_lines")
    ignore_file = config.get("file_processing.ignore_file")
    model = config.get("api.model")
    vendor = config.get("api.vendor")
    template = config.get("output.template")
    concurrency = config.get("performance.concurrency")
    dry_run = config.get("dry_run", False)

    # Get API client
    api_key = get_api_key(config)
    api_client = create_api_client(vendor, api_key)

    # Load ignore patterns
    ignore_patterns = []
    if ignore_file and os.path.exists(ignore_file):
        ignore_patterns = load_ignore_patterns(ignore_file)

    # Collect files to process
    files_to_process = []

    if os.path.isfile(path):
        if not should_ignore_file(path, ignore_patterns):
            files_to_process.append(path)
    elif os.path.isdir(path):
        # Collect all files, recursively if specified
        if recursive:
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if should_ignore_file(file_path, ignore_patterns):
                        continue

                    file_ext = Path(file_path).suffix.lower()

                    # Apply include/exclude filters
                    if include and file_ext not in include:
                        continue
                    if exclude and file_ext in exclude:
                        continue

                    files_to_process.append(file_path)
        else:
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if not os.path.isfile(file_path) or should_ignore_file(
                    file_path, ignore_patterns
                ):
                    continue

                file_ext = Path(file_path).suffix.lower()

                # Apply include/exclude filters
                if include and file_ext not in include:
                    continue
                if exclude and file_ext in exclude:
                    continue

                files_to_process.append(file_path)
    else:
        print(f"Error: Path {path} does not exist")
        return False

    # Update report data
    report_data["processed_files"] = len(files_to_process)

    # Process files in parallel with a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(concurrency)

    async def process_with_semaphore(file_path):
        async with semaphore:
            return await update_file_with_map(
                file_path, api_client, model, template, dry_run, min_lines
            )

    # Create tasks for all files
    tasks = [process_with_semaphore(file) for file in files_to_process]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    success = True
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error processing {files_to_process[i]}: {str(result)}")
            report_data["errors"] += 1
            success = False
        elif not result:
            # File was skipped or had an error
            pass

    # Calculate duration
    report_data["duration"] = time.time() - start_time

    # Generate report if requested
    report_path = config.get("output.report_path")
    if report_path:
        generate_report(report_path)

    return success


def generate_project_map(config):
    """
    Generate a project-level file map that consolidates references to all project files and their file maps.
    """
    path = config.get("path")
    recursive = config.get("file_processing.recursive")
    include = config.get("file_processing.include_extensions")
    exclude = config.get("file_processing.exclude_extensions")
    ignore_file = config.get("file_processing.ignore_file")
    output_path = config.get("project_map.output_path")

    # Load ignore patterns
    ignore_patterns = []
    if ignore_file and os.path.exists(ignore_file):
        ignore_patterns = load_ignore_patterns(ignore_file)

    lines = []
    lines.append("# Project File Map\n")
    lines.append(
        "This document provides an overview of all project files and their file maps.\n"
    )

    if recursive:
        walker = os.walk(path)
    else:
        # If not recursive, list files in the top-level directory only
        walker = [(path, [], os.listdir(path))]

    for root, _, files in walker:
        for file in files:
            file_path = os.path.join(root, file)
            if should_ignore_file(file_path, ignore_patterns):
                continue
            file_ext = Path(file_path).suffix.lower()
            if include and file_ext not in include:
                continue
            if exclude and file_ext in exclude:
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                comment_style = get_comment_style(file_path)
                file_map, _ = extract_existing_file_map(content, comment_style)
                lines.append(f"## {file_path}")
                if file_map:
                    lines.append("```")
                    lines.append(file_map)
                    lines.append("```")
                else:
                    lines.append("_No file map available_")
                lines.append("\n")
            except Exception as e:
                lines.append(f"## {file_path}")
                lines.append(f"_Error reading file: {str(e)}_")
                lines.append("\n")
    output = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\nProject-level file map generated at {output_path}")


def generate_report(report_path: str):
    """Generate a summary report of file map operations"""
    report = {
        "summary": {
            "total_processed": report_data["processed_files"],
            "updated": report_data["updated_files"],
            "skipped": report_data["skipped_files"],
            "errors": report_data["errors"],
            "api_calls": report_data["api_calls"],
            "api_tokens_estimated": report_data["api_tokens_used"],
            "duration_seconds": report_data["duration"],
        },
        "detailed_logs": report_data["detailed_logs"],
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport generated at {report_path}")

    # Also print summary to console
    print("\nSummary:")
    print(f"  Files processed: {report_data['processed_files']}")
    print(f"  Files updated: {report_data['updated_files']}")
    print(f"  Files skipped: {report_data['skipped_files']}")
    print(f"  Errors: {report_data['errors']}")
    print(f"  API calls: {report_data['api_calls']}")
    print(f"  Duration: {report_data['duration']:.2f} seconds")
