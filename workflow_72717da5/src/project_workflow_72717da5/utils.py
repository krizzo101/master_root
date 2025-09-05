"""Utility helpers for project tests.

Provides deterministic, pure functions for string normalization,
identifier validation, middle truncation, and boolean parsing.
"""
import re
import unicodedata
from typing import Any, Optional

__all__ = [
    "normalize_string",
    "is_valid_identifier",
    "truncate_middle",
    "parse_bool",
]

_WHITESPACE_RE = re.compile(r"\s+")


def _to_ascii(text: str) -> str:
    """Transliterate text to ASCII, dropping characters that can't be transliterated.

    This uses NFKD normalization and encodes to ASCII ignoring errors.
    """
    # Normalize to decompose combined characters (e.g., é -> e +  ́)
    normalized = unicodedata.normalize("NFKD", text)
    # Encode to ASCII bytes ignoring non-ascii, then decode back
    ascii_bytes = normalized.encode("ascii", "ignore")
    return ascii_bytes.decode("ascii")


def normalize_string(s: Optional[str]) -> str:
    """Normalize a string to lowercase ASCII with collapsed whitespace.

    Parameters:"""
