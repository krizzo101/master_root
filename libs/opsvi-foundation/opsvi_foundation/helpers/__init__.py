"""Helper utilities for opsvi-foundation.

Provides utility functions for common operations.
"""

from .collections import (
    deep_merge,
    deep_get,
    deep_set,
    flatten_dict,
    unflatten_dict,
    safe_get,
    safe_set,
    dict_diff,
    remove_none,
    chunk_list,
    deduplicate,
    group_by,
)

from .datetime import (
    DateTimeHelper,
    parse_datetime,
    format_datetime,
    get_timezone,
    convert_timezone,
    calculate_duration,
    add_duration,
    subtract_duration,
    is_past,
    is_future,
    time_until,
    time_since,
    get_timestamp,
    from_timestamp,
)

from .string import (
    StringHelper,
    slugify,
    truncate,
    strip_html,
    extract_urls,
    extract_emails,
    camel_to_snake,
    snake_to_camel,
    encode_base64,
    decode_base64,
    generate_random_string,
    hash_string,
    mask_sensitive,
    render_template,
)

__all__ = [
    # Collections
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
    # DateTime
    "DateTimeHelper",
    "parse_datetime",
    "format_datetime",
    "get_timezone",
    "convert_timezone",
    "calculate_duration",
    "add_duration",
    "subtract_duration",
    "is_past",
    "is_future",
    "time_until",
    "time_since",
    "get_timestamp",
    "from_timestamp",
    # String
    "StringHelper",
    "slugify",
    "truncate",
    "strip_html",
    "extract_urls",
    "extract_emails",
    "camel_to_snake",
    "snake_to_camel",
    "encode_base64",
    "decode_base64",
    "generate_random_string",
    "hash_string",
    "mask_sensitive",
    "render_template",
]
