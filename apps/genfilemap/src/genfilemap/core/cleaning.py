"""
Cleaning functionality for GenFileMap.

This module provides functionality for cleaning file maps and hash files from the codebase.
"""

import os
import re
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from genfilemap.logging_utils import debug, info, error
from genfilemap.core.file_operations import get_hash_file_path
from genfilemap.config import get_config_value
from genfilemap.utils import should_ignore_file


async def clean_file_maps(
    file_path: str, dry_run: bool = False, from_deep_clean: bool = False
) -> Tuple[bool, str, Optional[str]]:
    """
    Remove file maps and hash files from a specified file.

    Args:
        file_path: Path to the file
        dry_run: Whether to perform a dry run without making changes
        from_deep_clean: If True, only process file maps that start at line 1 and check recursively for multiple maps

    Returns:
        Tuple of (success, status, error_message)
        Where status is one of: "cleaned", "would_clean", "skipped", "error"
    """

    def remove_python_single_line_file_map(content: str) -> str:
        """Remove single-line Python FILE_MAP format: # FILE_MAP_BEGIN {json} FILE_MAP_END"""
        # Use regex to remove the single-line format
        # Pattern: # FILE_MAP_BEGIN {anything} FILE_MAP_END followed by optional blank line
        pattern = r"# FILE_MAP_BEGIN .*? FILE_MAP_END\s*\n?"
        cleaned = re.sub(pattern, "", content)

        # Also handle the case where there might be a blank line after
        # Remove any leading blank lines that might be left
        cleaned = re.sub(r"^\s*\n", "", cleaned)

        return cleaned

    try:
        debug(f"Attempting to clean file maps from {file_path}")

        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Common patterns for file maps in different formats (excluding Python single-line comment format)
        patterns = [
            # Python format with # markers (old multi-line)
            r'# FILE_MAP_BEGIN.*?\n""".*?\n.*?\n.*?""".*?\n# FILE_MAP_END\s*\n?',
            # Older Python triple-quoted format
            r'"""\s*FILE_MAP_BEGIN\s*"""(?:\s*).*?(?:\s*)"""\s*"""\s*FILE_MAP_END\s*"""\s*\n?',
            # HTML/Markdown format
            r"<!-- FILE_MAP_BEGIN\s*\n<!--\s*\n.*?\n\s*-->\s*\n<!-- FILE_MAP_END -->\s*\n?",
            # Older HTML format
            r"<!-- FILE_MAP_BEGIN -->(?:\s*|\s+)<!--\s*\{.*?\}\s*-->(?:\s*|\s+)<!-- FILE_MAP_END -->\s*\n?",
            # Generic multi-line format
            r"/\*\s*FILE_MAP_BEGIN\s*/\*\s*.*?\s*\*/\s*\*/\s*FILE_MAP_END\s*\*/\s*\n?",
            # JS special format (// for end marker)
            r"/\*\s*FILE_MAP_BEGIN\s*\n.*?\s*\*/\s*//\s*FILE_MAP_END\s*\n?",
            # CSS special format (/* */ for both markers)
            r"/\*\s*FILE_MAP_BEGIN\s*\n.*?\s*\*/\s*/\*\s*FILE_MAP_END\s*\n?",
            # JS with space after //
            r"/\*\s*FILE_MAP_BEGIN\s*\n.*?\*/\s*//\s+FILE_MAP_END\s*\n?",
            # CSS with space after /*
            r"/\*\s*FILE_MAP_BEGIN\s*\n.*?\*/\s*/\*\s+FILE_MAP_END\s*\n?",
        ]

        new_content = remove_python_single_line_file_map(content)
        # Now apply regex-based removal for other formats
        if from_deep_clean:
            debug(f"Deep clean mode: only processing file maps that start at line 1")
            still_cleaning = True
            while still_cleaning:
                still_cleaning = False
                for pattern in patterns:
                    start_pattern = r"^" + pattern
                    start_match = re.match(start_pattern, new_content, flags=re.DOTALL)
                    if start_match:
                        debug(
                            f"Found file map at the start of {file_path}, removing it"
                        )
                        new_content = re.sub(
                            start_pattern, "", new_content, count=1, flags=re.DOTALL
                        )
                        still_cleaning = True
                        break
        else:
            for pattern in patterns:
                new_content = re.sub(pattern, "", new_content, flags=re.DOTALL)

        # Delete corresponding hash file if it exists
        hash_file = get_hash_file_path(file_path)
        hash_file_exists = hash_file.exists()
        hash_file_deleted = False

        if hash_file_exists:
            if dry_run:
                debug(f"Would delete hash file: {hash_file}")
                hash_file_deleted = True
            else:
                try:
                    hash_file.unlink()
                    debug(f"Deleted hash file: {hash_file}")
                    hash_file_deleted = True
                except Exception as e:
                    error(f"Error deleting hash file {hash_file}: {str(e)}")

        # Write updated content if not in dry run mode
        if content != new_content:
            if dry_run:
                info(f"Would remove file map from: {file_path}")
                return True, "would_clean", None
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                info(f"Removed file map from: {file_path}")
                return True, "cleaned", None
        else:
            if hash_file_deleted:
                info(f"No file map found in {file_path}, but removed hash file")
                return True, "cleaned", "Removed hash file only"
            else:
                debug(f"No file map or hash file found for: {file_path}")
                return True, "skipped", "No changes needed"

    except Exception as e:
        error(f"Error cleaning file {file_path}: {str(e)}")
        return False, "error", f"Error cleaning file {file_path}: {str(e)}"


async def clean_files_async(config: Dict[str, Any]) -> bool:
    """
    Clean file maps and hash files from multiple files asynchronously.

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if successful, False if errors occurred
    """
    path = get_config_value(config, "path")
    recursive = get_config_value(config, "file_processing.recursive")
    include = get_config_value(config, "file_processing.include_extensions")
    exclude = get_config_value(config, "file_processing.exclude_extensions")
    concurrency = get_config_value(config, "performance.concurrency", 5)
    dry_run = get_config_value(config, "dry_run", False)
    ignore_pathspec = config.get("ignore_pathspec")

    info(f"Cleaning file maps from {path} (recursive={recursive})")

    # Collect files to process
    files_to_process = []

    # For single file
    if os.path.isfile(path):
        files_to_process.append(path)
    # For directory
    elif os.path.isdir(path):
        # Walk directory recursively if specified
        if recursive:
            for root, dirs, files in os.walk(path):
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore_file(
                        os.path.join(root, d), pathspec_obj=ignore_pathspec
                    )
                ]
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if not os.path.isfile(file_path):
                        continue
                    if should_ignore_file(file_path, pathspec_obj=ignore_pathspec):
                        continue
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if include and file_ext not in include:
                        continue
                    if exclude and file_ext in exclude:
                        continue
                    files_to_process.append(file_path)
        else:
            # Non-recursive directory scan
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if not os.path.isfile(file_path):
                    continue
                if should_ignore_file(file_path, pathspec_obj=ignore_pathspec):
                    continue
                file_ext = os.path.splitext(file_path)[1].lower()
                if include and file_ext not in include:
                    continue
                if exclude and file_ext in exclude:
                    continue
                files_to_process.append(file_path)
    else:
        error(f"Path not found: {path}")
        return False

    if not files_to_process:
        info("No files to process")
        return True

    info(f"Found {len(files_to_process)} files to process")

    # Process files with concurrency
    semaphore = asyncio.Semaphore(concurrency)

    async def process_file(file_path):
        async with semaphore:
            return await clean_file_maps(file_path, dry_run)

    tasks = [process_file(file) for file in files_to_process]
    results = await asyncio.gather(*tasks)

    # Count success, errors, etc.
    processed = len(results)
    cleaned = sum(
        1
        for success, status, _ in results
        if success and (status == "cleaned" or status == "would_clean")
    )
    skipped = sum(
        1 for success, status, _ in results if success and status == "skipped"
    )
    errors = sum(1 for success, _, _ in results if not success)

    # Print summary
    info(f"\nCleaning summary:")
    info(f"  Processed: {processed} files")
    info(f"  Cleaned: {cleaned} files")
    info(f"  Skipped: {skipped} files")
    info(f"  Errors: {errors} files")

    # Report any errors
    error_files = [
        (str(files_to_process[i]), err)
        for i, (success, _, err) in enumerate(results)
        if not success and err
    ]
    if error_files:
        error("\nErrors encountered:")
        for file_path, err_msg in error_files:
            error(f"  {file_path}: {err_msg}")

    return errors == 0  # Return true only if there were no errors


async def deep_clean_files_async(config: Dict[str, Any]) -> bool:
    """
    Deep clean file maps from files, checking all files in the given path regardless of hash files.
    This function checks all files for FILE_MAP_BEGIN marker anywhere in the content.

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if successful, False if errors occurred
    """
    path = get_config_value(config, "path")
    recursive = get_config_value(config, "file_processing.recursive")
    concurrency = get_config_value(config, "performance.concurrency", 5)
    dry_run = get_config_value(config, "dry_run", False)
    ignore_pathspec = config.get("ignore_pathspec")

    info(f"Deep cleaning file maps from {path} (recursive={recursive})")
    info(
        f"This will check all files for FILE_MAP_BEGIN anywhere in the content regardless of hash files."
    )

    # Collect files to process
    files_to_process = []
    files_checked = 0

    # For single file
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "FILE_MAP_BEGIN" in content:
                    files_to_process.append(path)
        except Exception as e:
            debug(f"Error reading {path}: {str(e)}")

        files_checked += 1

    # For directory
    elif os.path.isdir(path):
        # Walk directory recursively if specified
        if recursive:
            for root, dirs, files in os.walk(path):
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore_file(
                        os.path.join(root, d), pathspec_obj=ignore_pathspec
                    )
                ]
                for filename in files:
                    file_path = os.path.join(root, filename)
                    try:
                        if os.path.isfile(file_path):
                            if should_ignore_file(
                                file_path, pathspec_obj=ignore_pathspec
                            ):
                                continue
                            with open(
                                file_path, "r", encoding="utf-8", errors="ignore"
                            ) as f:
                                content = f.read()
                                if "FILE_MAP_BEGIN" in content:
                                    files_to_process.append(file_path)
                            files_checked += 1
                    except Exception as e:
                        debug(f"Error reading {file_path}: {str(e)}")
        else:
            # Non-recursive directory scan
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                try:
                    if os.path.isfile(file_path):
                        if should_ignore_file(file_path, pathspec_obj=ignore_pathspec):
                            continue
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            if "FILE_MAP_BEGIN" in content:
                                files_to_process.append(file_path)
                        files_checked += 1
                except Exception as e:
                    debug(f"Error reading {file_path}: {str(e)}")
    else:
        error(f"Path not found: {path}")
        return False

    info(
        f"Checked {files_checked} files, found {len(files_to_process)} with file maps in content"
    )

    if not files_to_process:
        info("No files to process")
        return True

    # Process files with concurrency
    semaphore = asyncio.Semaphore(concurrency)

    async def process_file(file_path):
        async with semaphore:
            return await clean_file_maps(file_path, dry_run, from_deep_clean=True)

    tasks = [process_file(file) for file in files_to_process]
    results = await asyncio.gather(*tasks)

    # Count success, errors, etc.
    processed = len(results)
    cleaned = sum(
        1
        for success, status, _ in results
        if success and (status == "cleaned" or status == "would_clean")
    )
    skipped = sum(
        1 for success, status, _ in results if success and status == "skipped"
    )
    errors = sum(1 for success, _, _ in results if not success)

    # Print summary
    info(f"\nDeep cleaning summary:")
    info(f"  Processed: {processed} files")
    info(f"  Cleaned: {cleaned} files")
    info(f"  Skipped: {skipped} files")
    info(f"  Errors: {errors} files")

    # Report any errors
    error_files = [
        (str(files_to_process[i]), err)
        for i, (success, _, err) in enumerate(results)
        if not success and err
    ]
    if error_files:
        error("\nErrors encountered:")
        for file_path, err_msg in error_files:
            error(f"  {file_path}: {err_msg}")

    return errors == 0  # Return true only if there were no errors
