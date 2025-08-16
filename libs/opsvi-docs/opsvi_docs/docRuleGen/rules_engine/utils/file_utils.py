# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"File Utilities","description":"This module contains utilities for file operations related to rules management.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules for file operations.","line_start":5,"line_end":10},{"name":"Ensure Rules Directory","description":"Function to ensure that the rules directory exists.","line_start":11,"line_end":25},{"name":"Check Rule File Existence","description":"Function to check if a specific rule file exists.","line_start":26,"line_end":42},{"name":"Get Rule File Path","description":"Function to construct the file path for a rule.","line_start":43,"line_end":57},{"name":"Read Rule File","description":"Function to read the contents of a rule file.","line_start":58,"line_end":79},{"name":"Write Rule File","description":"Function to write content to a rule file.","line_start":80,"line_end":101}],"key_elements":[{"name":"ensure_rules_dir","description":"Function to ensure the rules directory exists.","line":12},{"name":"rule_file_exists","description":"Function to check if a rule file already exists.","line":27},{"name":"get_rule_file_path","description":"Function to get the file path for a rule.","line":43},{"name":"read_rule_file","description":"Function to read a rule file.","line":58},{"name":"write_rule_file","description":"Function to write content to a rule file.","line":80},{"name":"os","description":"Module for operating system dependent functionality.","line":7},{"name":"Path","description":"Class from pathlib for handling filesystem paths.","line":8},{"name":"Optional","description":"Type hint for optional values.","line":9}]}
"""
# FILE_MAP_END

"""
File Utilities

This module contains utilities for file operations.
"""

from pathlib import Path
from typing import Optional


def ensure_rules_dir(base_dir: str = ".cursor/rules/") -> Path:
    """
    Ensure the rules directory exists.

    Args:
        base_dir: The base directory for rules.

    Returns:
        The Path object for the directory.
    """
    rules_dir = Path(base_dir)
    rules_dir.mkdir(exist_ok=True, parents=True)
    return rules_dir


def rule_file_exists(
    rule_id: str, rule_slug: str, base_dir: str = ".cursor/rules/"
) -> bool:
    """
    Check if a rule file already exists.

    Args:
        rule_id: The rule ID.
        rule_slug: The rule slug.
        base_dir: The base directory for rules.

    Returns:
        True if the file exists, False otherwise.
    """
    file_path = Path(base_dir) / f"{rule_id}-{rule_slug}.mdc"
    return file_path.exists()


def get_rule_file_path(
    rule_id: str, rule_slug: str, base_dir: str = ".cursor/rules/"
) -> Path:
    """
    Get the file path for a rule.

    Args:
        rule_id: The rule ID.
        rule_slug: The rule slug.
        base_dir: The base directory for rules.

    Returns:
        The Path object for the rule file.
    """
    return Path(base_dir) / f"{rule_id}-{rule_slug}.mdc"


def read_rule_file(file_path: str) -> Optional[str]:
    """
    Read a rule file.

    Args:
        file_path: The path to the rule file.

    Returns:
        The contents of the file, or None if the file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def write_rule_file(file_path: str, content: str) -> bool:
    """
    Write content to a rule file.

    Args:
        file_path: The path to the rule file.
        content: The content to write.

    Returns:
        True if writing was successful, False otherwise.
    """
    path = Path(file_path)

    # Ensure the directory exists
    path.parent.mkdir(exist_ok=True, parents=True)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False
