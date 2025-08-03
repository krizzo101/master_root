
"""
Directory Hashing Module for GenFileMap.

This module provides functionality for computing and comparing directory-level hashes
to optimize file processing by only processing directories that have changed.

FILE_MAP_BEGIN
version: 1.0
author: GenFileMap
created_at: 2023-10-07
description: Directory hashing module for optimized file processing
metadata:
  type: core_module
  complexity: high
  last_modified: 2023-10-07
sections:
  imports: 1-19
  directory_hash_info: 21-51
  hash_computation: 53-161
  cache_management: 163-231
  directory_traversal: 233-301
key_elements:
  - DirectoryHashInfo: 22
  - compute_file_hash: 54
  - compute_directory_hashes: 70
  - should_ignore_file: 127
  - load_hash_cache: 164
  - save_hash_cache: 197
  - find_changed_directories: 234
FILE_MAP_END
"""

import os
import time
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Union

from genfilemap.logging_utils import debug
from genfilemap.config import get_config_value
from genfilemap.utils import should_ignore_file, load_ignore_patterns


class DirectoryHashInfo:
    """Stores hash information for a directory."""

    def __init__(self, path: str, local_hash: Optional[str] = None, recursive_hash: Optional[str] = None):
        """
        Initialize a directory hash info object.

        Args:
            path: Path to the directory
            local_hash: Hash of files in this directory only (non-recursive)
            recursive_hash: Hash of this directory and all subdirectories
        """
        self.path = path                          # Path to the directory
        self.local_hash = local_hash              # Hash of files in this directory only
        self.recursive_hash = recursive_hash      # Hash of this directory and all subdirectories
        self.last_updated = datetime.now().isoformat()  # When this hash was last computed
        self.file_hashes = {}                     # Map of filename -> hash for files in this directory
        self.subdir_hashes = {}                   # Map of dirname -> DirectoryHashInfo for subdirectories

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a serializable dictionary."""
        return {
            'path': self.path,
            'local_hash': self.local_hash,
            'recursive_hash': self.recursive_hash,
            'last_updated': self.last_updated,
            'file_hashes': self.file_hashes,
            'subdir_hashes': {k: v.path for k, v in self.subdir_hashes.items()}
        }


def compute_file_hash(file_path: str) -> Optional[str]:
    """
    Compute a hash for a single file.

    Args:
        file_path: Path to the file

    Returns:
        File hash as a hexadecimal string, or None if an error occurred
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()
    except Exception as e:
        debug(f"Error hashing file {file_path}: {str(e)}")
        return None


def compute_directory_hashes(
    directory_path: str,
    ignore_patterns: Optional[List[str]] = None,
    cache: Optional[Dict[str, DirectoryHashInfo]] = None,
    config: Optional[Dict[str, Any]] = None
) -> DirectoryHashInfo:
    """
    Compute both local and recursive hashes for a directory.

    Args:
        directory_path: Path to the directory
        ignore_patterns: Patterns of files to ignore
        cache: Existing cache to update
        config: Configuration dictionary

    Returns:
        DirectoryHashInfo for the directory
    """
    if cache is None:
        cache = {}

    # Normalize path for consistent keys
    norm_path = os.path.normpath(directory_path)
    abs_path = os.path.abspath(norm_path)

    # Initialize hash info for this directory
    dir_info = DirectoryHashInfo(abs_path)

    # Get all files and subdirectories in this directory
    try:
        entries = os.listdir(abs_path)
    except Exception as e:
        debug(f"Error listing directory {abs_path}: {str(e)}")
        return dir_info

    # Process files and compute local hash
    local_hashes = []
    ignore_pathspec = None
    if config is not None:
        ignore_pathspec = config.get('ignore_pathspec')
    for entry in sorted(entries):  # Sort for deterministic ordering
        entry_path = os.path.join(abs_path, entry)

        # Skip entries that match ignore patterns
        if (ignore_pathspec and should_ignore_file(entry_path, pathspec_obj=ignore_pathspec)) or (ignore_patterns and should_ignore_file(entry_path, ignore_patterns)):
            continue

        if os.path.isfile(entry_path):
            # Compute file hash
            file_hash = compute_file_hash(entry_path)
            if file_hash:
                dir_info.file_hashes[entry] = file_hash
                local_hashes.append(f"{entry}:{file_hash}")

    # Compute local hash (only files in this directory)
    if local_hashes:
        combined_local = '|'.join(local_hashes)
        dir_info.local_hash = hashlib.md5(combined_local.encode()).hexdigest()

    # Process subdirectories and compute recursive hash
    recursive_hashes = [dir_info.local_hash] if dir_info.local_hash else []

    for entry in sorted(entries):  # Sort for deterministic ordering
        entry_path = os.path.join(abs_path, entry)

        # Skip entries that match ignore patterns
        if (ignore_pathspec and should_ignore_file(entry_path, pathspec_obj=ignore_pathspec)) or (ignore_patterns and should_ignore_file(entry_path, ignore_patterns)):
            continue

        if os.path.isdir(entry_path):
            # Recursively compute hashes for subdirectory
            subdir_info = compute_directory_hashes(entry_path, ignore_patterns, cache, config)
            if subdir_info.recursive_hash:
                dir_info.subdir_hashes[entry] = subdir_info
                recursive_hashes.append(f"{entry}:{subdir_info.recursive_hash}")

    # Compute recursive hash (this directory + all subdirectories)
    if recursive_hashes:
        combined_recursive = '|'.join(recursive_hashes)
        dir_info.recursive_hash = hashlib.md5(combined_recursive.encode()).hexdigest()

    # Add to cache
    cache[abs_path] = dir_info

    return dir_info


def load_hash_cache(cache_file: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the hash cache from a file.

    Args:
        cache_file: Path to the cache file

    Returns:
        dict: Cache data, indexed by directory path
    """
    if not os.path.exists(cache_file):
        debug(f"Hash cache file does not exist: {cache_file}")
        return {}

    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
            debug(f"Loaded hash cache with {len(cache)} entries")
            return cache
    except Exception as e:
        error(f"Error loading hash cache from {cache_file}: {str(e)}")
        return {}


def save_hash_cache(cache: Dict[str, Dict[str, Any]], cache_file: str) -> None:
    """
    Save the hash cache to a file.

    Args:
        cache: Cache data to save
        cache_file: Path to the cache file
    """
    # Create the directory if it doesn't exist
    cache_dir = os.path.dirname(cache_file)

    # Ensure the cache directory exists
    try:
        if not os.path.exists(cache_dir):
            debug(f"Creating cache directory: {cache_dir}")
            os.makedirs(cache_dir, exist_ok=True)
    except Exception as e:
        error(f"Error creating cache directory {cache_dir}: {str(e)}")
        return

    try:
        debug(f"Saving hash cache with {len(cache)} entries to {cache_file}")
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        error(f"Error saving hash cache to {cache_file}: {str(e)}")


def find_changed_directories(
    base_path: str,
    cache: Dict[str, DirectoryHashInfo],
    ignore_patterns: Optional[List[str]] = None
) -> List[str]:
    """
    Find directories that have changes compared to the cache.

    Args:
        base_path: Base directory path
        cache: Existing directory hash cache
        ignore_patterns: Patterns of files to ignore

    Returns:
        List of directories that need processing
    """
    # Compute current hashes
    current_hashes = compute_directory_hashes(base_path, ignore_patterns)

    changed_dirs = []

    # Helper function to compare recursively
    def compare_recursive(current: DirectoryHashInfo, cached_path: str) -> List[str]:
        if cached_path not in cache:
            # Directory doesn't exist in cache, process entire directory
            return [current.path]

        cached = cache[cached_path]
        if current.recursive_hash != cached.recursive_hash:
            # Recursive hash differs, check if local changes or subdirectory changes
            dirs_to_process = []

            # Check local changes
            if current.local_hash != cached.local_hash:
                dirs_to_process.append(current.path)

            # Check subdirectories
            for subdir_name, subdir_info in current.subdir_hashes.items():
                if subdir_name not in cached.subdir_hashes:
                    # New subdirectory
                    dirs_to_process.append(subdir_info.path)
                elif subdir_info.recursive_hash != cached.subdir_hashes[subdir_name].recursive_hash:
                    # Subdirectory has changes, recurse
                    dirs_to_process.extend(
                        compare_recursive(subdir_info, cached.subdir_hashes[subdir_name].path)
                    )

            return dirs_to_process

        # No changes detected
        return []

    # Compare current state with cache
    changed_dirs = compare_recursive(current_hashes, base_path)
    debug(f"Found {len(changed_dirs)} directories with changes")

    return changed_dirs