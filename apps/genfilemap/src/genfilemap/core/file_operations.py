"""
File operations for GenFileMap.

This module provides low-level file operations for reading, writing, and managing file hashes.
"""

import os
from pathlib import Path
from typing import Union, Optional

from genfilemap.logging_utils import debug, error

def count_lines(file_path: str) -> int:
    """
    Count the number of lines in a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Number of lines in the file or 0 if an error occurs
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for _ in f)
        debug(f"File {file_path} has {line_count} lines")
        return line_count
    except Exception as e:
        error(f"Error counting lines in {file_path}: {str(e)}")
        return 0

def get_hash_file_path(file_path: Union[str, Path]) -> Path:
    """
    Get the path to the hash file for a given file.
    
    Args:
        file_path: Path to the original file
        
    Returns:
        Path to the hash file
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Add .hash extension to the original file path
    hash_file = Path(f"{file_path}.hash")
    return hash_file 