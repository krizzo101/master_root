"""
OAMAT Manager Utilities Module

Contains utility functions for data processing and serialization.
Extracted from manager.py for better modularity and maintainability.
"""

import json
import logging
import re
from typing import Any

from src.applications.oamat.agents.models import EnhancedRequestAnalysis

logger = logging.getLogger("OAMAT.ManagerUtilities")


def extract_structured_info(text: str, pattern: str) -> str | None:
    """
    Extract structured information from text using regex pattern.

    Args:
        text: Text to search in
        pattern: Regex pattern to match

    Returns:
        Extracted match or None if not found
    """
    # FAIL-FAST: No try/except. Let regex errors propagate.
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def clean_json_response(response_text: str) -> str:
    """
    Clean JSON response text by removing common formatting issues.

    Args:
        response_text: Raw response text

    Returns:
        Cleaned JSON string
    """
    # FAIL-FAST: No try/except. Let regex errors propagate.
    # Remove markdown code blocks
    response_text = re.sub(r"```json\s*", "", response_text)
    response_text = re.sub(r"```\s*$", "", response_text)

    # Remove extra whitespace and newlines
    response_text = response_text.strip()

    # Ensure proper JSON formatting
    if not response_text.startswith("{"):
        # Try to find JSON object in text
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group()

    return response_text


def extract_json_from_response(response_text: str) -> dict[str, Any]:
    """
    Extract and parse JSON from response text.

    Args:
        response_text: Response text that may contain JSON

    Returns:
        Parsed JSON dictionary. Raises JSONDecodeError on failure.
    """
    # FAIL-FAST: No try/except. Let JSONDecodeError propagate.
    cleaned_text = clean_json_response(response_text)
    return json.loads(cleaned_text)


def serialize_analysis(analysis: EnhancedRequestAnalysis) -> str:
    """
    Serialize an EnhancedRequestAnalysis object to a formatted string.

    Args:
        analysis: The analysis object to serialize

    Returns:
        Formatted string representation of the analysis
    """
    # FAIL-FAST: No try/except. Let serialization errors propagate.
    if hasattr(analysis, "model_dump"):
        # Pydantic v2
        analysis_dict = analysis.model_dump()
    elif hasattr(analysis, "dict"):
        # Pydantic v1
        analysis_dict = analysis.dict()
    else:
        # Fallback for other types
        analysis_dict = vars(analysis)

    return json.dumps(analysis_dict, indent=2)


def format_list_for_display(items: list[str], title: str = None) -> str:
    """
    Format a list of items for display in console output.

    Args:
        items: List of items to format
        title: Optional title for the list

    Returns:
        Formatted string representation of the list
    """
    if not items:
        return ""

    formatted = ""
    if title:
        formatted += f"\n{title}:\n"
        formatted += "-" * len(title) + "\n"

    for i, item in enumerate(items, 1):
        formatted += f"{i}. {item}\n"

    return formatted


def format_dict_for_display(data: dict[str, Any], title: str = None) -> str:
    """
    Format a dictionary for display in console output.

    Args:
        data: Dictionary to format
        title: Optional title for the dictionary

    Returns:
        Formatted string representation of the dictionary
    """
    if not data:
        return ""

    formatted = ""
    if title:
        formatted += f"\n{title}:\n"
        formatted += "-" * len(title) + "\n"

    for key, value in data.items():
        formatted_key = key.replace("_", " ").title()
        formatted += f"• {formatted_key}: {value}\n"

    return formatted


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def validate_json_structure(data: dict[str, Any], required_keys: list[str]) -> bool:
    """
    Validate that a JSON structure contains required keys.

    Args:
        data: Dictionary to validate
        required_keys: List of required keys

    Returns:
        True if all required keys are present. Raises TypeError on failure.
    """
    # FAIL-FAST: No try/except. Let TypeError propagate if data is not a dict.
    return all(key in data for key in required_keys)


def safe_get_nested_value(
    data: dict[str, Any], keys: list[str], default: Any = None
) -> Any:
    """
    Safely get a nested value from a dictionary.

    Args:
        data: Dictionary to search in
        keys: List of keys representing the path
        default: Default value if path doesn't exist

    Returns:
        The value at the specified path or default
    """
    # This function's purpose is safety, so the try/except is intentional.
    # It will remain as is, as its contract is to not raise errors.
    try:
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    except Exception as e:
        logger.error(f"Error getting nested value: {e}")
        return default


def merge_dictionaries(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """
    Merge two dictionaries, with dict2 values taking precedence.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    # FAIL-FAST: No try/except. Let errors propagate.
    result = dict1.copy()
    result.update(dict2)
    return result
