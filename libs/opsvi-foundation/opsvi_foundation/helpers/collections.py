"""Collection manipulation helper utilities for opsvi-foundation.

Provides dict/list utilities, deep merge, and safe access.
"""

import copy
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


def deep_merge(
    dict1: Dict[str, Any], dict2: Dict[str, Any], in_place: bool = False
) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge in
        in_place: Modify dict1 in place

    Returns:
        Merged dictionary
    """
    if in_place:
        result = dict1
    else:
        result = copy.deepcopy(dict1)

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value, in_place=False)
        else:
            result[key] = copy.deepcopy(value) if not in_place else value

    return result


def deep_get(
    dictionary: Dict[str, Any], path: str, default: Any = None, separator: str = "."
) -> Any:
    """Get value from nested dictionary using dot notation.

    Args:
        dictionary: Dictionary to search
        path: Path to value (e.g., "a.b.c")
        default: Default value if not found
        separator: Path separator

    Returns:
        Value at path or default
    """
    keys = path.split(separator)
    value = dictionary

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


def deep_set(
    dictionary: Dict[str, Any], path: str, value: Any, separator: str = "."
) -> Dict[str, Any]:
    """Set value in nested dictionary using dot notation.

    Args:
        dictionary: Dictionary to modify
        path: Path to value (e.g., "a.b.c")
        value: Value to set
        separator: Path separator

    Returns:
        Modified dictionary
    """
    keys = path.split(separator)
    current = dictionary

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value
    return dictionary


def flatten_dict(
    dictionary: Dict[str, Any], parent_key: str = "", separator: str = "."
) -> Dict[str, Any]:
    """Flatten nested dictionary to single level.

    Args:
        dictionary: Dictionary to flatten
        parent_key: Parent key prefix
        separator: Key separator

    Returns:
        Flattened dictionary
    """
    items = []

    for key, value in dictionary.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))

    return dict(items)


def unflatten_dict(dictionary: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Unflatten dictionary from single level to nested.

    Args:
        dictionary: Flattened dictionary
        separator: Key separator

    Returns:
        Nested dictionary
    """
    result = {}

    for key, value in dictionary.items():
        deep_set(result, key, value, separator)

    return result


def safe_get(
    obj: Union[Dict, List, Any],
    path: Union[str, List[Union[str, int]]],
    default: Any = None,
) -> Any:
    """Safely get value from nested structure.

    Args:
        obj: Object to search (dict, list, or any)
        path: Path to value (string or list of keys/indices)
        default: Default value if not found

    Returns:
        Value at path or default
    """
    if isinstance(path, str):
        path = path.split(".")

    current = obj

    for key in path:
        try:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, (list, tuple)):
                current = current[int(key)]
            else:
                return default
        except (KeyError, IndexError, ValueError, TypeError):
            return default

    return current


def safe_set(
    obj: Union[Dict, List], path: Union[str, List[Union[str, int]]], value: Any
) -> bool:
    """Safely set value in nested structure.

    Args:
        obj: Object to modify (dict or list)
        path: Path to value (string or list of keys/indices)
        value: Value to set

    Returns:
        True if successful
    """
    if isinstance(path, str):
        path = path.split(".")

    if not path:
        return False

    current = obj

    for key in path[:-1]:
        try:
            if isinstance(current, dict):
                if key not in current:
                    # Determine if next key is numeric (list) or string (dict)
                    next_key = path[path.index(key) + 1]
                    try:
                        int(next_key)
                        current[key] = []
                    except ValueError:
                        current[key] = {}
                current = current[key]
            elif isinstance(current, list):
                idx = int(key)
                while len(current) <= idx:
                    current.append(None)
                if current[idx] is None:
                    current[idx] = {}
                current = current[idx]
            else:
                return False
        except (ValueError, TypeError):
            return False

    # Set final value
    final_key = path[-1]
    try:
        if isinstance(current, dict):
            current[final_key] = value
        elif isinstance(current, list):
            idx = int(final_key)
            while len(current) <= idx:
                current.append(None)
            current[idx] = value
        else:
            return False
    except (ValueError, TypeError):
        return False

    return True


def dict_diff(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Get differences between two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        Dictionary with added, removed, and changed keys
    """
    result = {"added": {}, "removed": {}, "changed": {}}

    # Find added and changed
    for key, value in dict2.items():
        if key not in dict1:
            result["added"][key] = value
        elif dict1[key] != value:
            result["changed"][key] = {"old": dict1[key], "new": value}

    # Find removed
    for key, value in dict1.items():
        if key not in dict2:
            result["removed"][key] = value

    return result


def remove_none(obj: Union[Dict, List]) -> Union[Dict, List]:
    """Remove None values from dictionary or list recursively.

    Args:
        obj: Dictionary or list to clean

    Returns:
        Cleaned object
    """
    if isinstance(obj, dict):
        return {k: remove_none(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [remove_none(item) for item in obj if item is not None]
    else:
        return obj


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deduplicate(lst: List[T], key_func: Optional[Callable[[T], Any]] = None) -> List[T]:
    """Remove duplicates from list while preserving order.

    Args:
        lst: List to deduplicate
        key_func: Optional function to extract comparison key

    Returns:
        Deduplicated list
    """
    seen = set()
    result = []

    for item in lst:
        key = key_func(item) if key_func else item

        # Handle unhashable types
        try:
            if key not in seen:
                seen.add(key)
                result.append(item)
        except TypeError:
            # Unhashable type, use slower method
            if item not in result:
                result.append(item)

    return result


def group_by(lst: List[T], key_func: Callable[[T], Any]) -> Dict[Any, List[T]]:
    """Group list items by key function.

    Args:
        lst: List to group
        key_func: Function to extract group key

    Returns:
        Dictionary of grouped items
    """
    grouped = defaultdict(list)

    for item in lst:
        key = key_func(item)
        grouped[key].append(item)

    return dict(grouped)


def partition(lst: List[T], predicate: Callable[[T], bool]) -> tuple[List[T], List[T]]:
    """Partition list into two based on predicate.

    Args:
        lst: List to partition
        predicate: Function to test each item

    Returns:
        Tuple of (matching, non_matching)
    """
    matching = []
    non_matching = []

    for item in lst:
        if predicate(item):
            matching.append(item)
        else:
            non_matching.append(item)

    return matching, non_matching


def find_first(
    lst: List[T], predicate: Callable[[T], bool], default: Any = None
) -> Any:
    """Find first item in list matching predicate.

    Args:
        lst: List to search
        predicate: Function to test each item
        default: Default value if not found

    Returns:
        First matching item or default
    """
    for item in lst:
        if predicate(item):
            return item
    return default


def find_all(lst: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """Find all items in list matching predicate.

    Args:
        lst: List to search
        predicate: Function to test each item

    Returns:
        List of matching items
    """
    return [item for item in lst if predicate(item)]


__all__ = [
    "deep_merge",
    "deep_get",
    "deep_set",
    "flatten_dict",
    "unflatten_dict",
    "safe_get",
    "safe_set",
    "dict_diff",
    "remove_none",
    "chunk_list",
    "deduplicate",
    "group_by",
    "partition",
    "find_first",
    "find_all",
]
