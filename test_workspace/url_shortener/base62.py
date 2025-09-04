"""Base62 encoding and decoding module for URL shortening."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(BASE62_ALPHABET)


class Base62Error(Exception):
    """Custom exception for Base62 encoding/decoding errors."""

    pass


def encode(number: int) -> str:
    """
    Encode an integer to a base62 string.

    Args:
        number: A non-negative integer to encode.

    Returns:
        A base62 encoded string.

    Raises:
        Base62Error: If number is negative.
    """
    if number < 0:
        raise Base62Error(f"Cannot encode negative number: {number}")

    if number == 0:
        return BASE62_ALPHABET[0]

    result = []
    while number > 0:
        number, remainder = divmod(number, BASE)
        result.append(BASE62_ALPHABET[remainder])

    encoded = "".join(reversed(result))
    logger.debug(f"Encoded {number} to {encoded}")
    return encoded


def decode(encoded: str) -> int:
    """
    Decode a base62 string to an integer.

    Args:
        encoded: A base62 encoded string.

    Returns:
        The decoded integer.

    Raises:
        Base62Error: If the string contains invalid characters.
    """
    if not encoded:
        raise Base62Error("Cannot decode empty string")

    result = 0
    for char in encoded:
        if char not in BASE62_ALPHABET:
            raise Base62Error(f"Invalid character in base62 string: {char}")
        result = result * BASE + BASE62_ALPHABET.index(char)

    logger.debug(f"Decoded {encoded} to {result}")
    return result


def generate_short_code(url_id: int, min_length: int = 6) -> str:
    """
    Generate a short code from a URL ID with minimum length padding.

    Args:
        url_id: The database ID of the URL.
        min_length: Minimum length of the generated code.

    Returns:
        A base62 encoded string with minimum length.
    """
    encoded = encode(url_id)

    # Pad with leading zeros if needed
    if len(encoded) < min_length:
        padding = BASE62_ALPHABET[0] * (min_length - len(encoded))
        encoded = padding + encoded

    return encoded


def extract_id_from_code(code: str) -> Optional[int]:
    """
    Extract the URL ID from a short code.

    Args:
        code: The short code to decode.

    Returns:
        The extracted URL ID or None if decoding fails.
    """
    try:
        # Remove leading zeros
        code = code.lstrip(BASE62_ALPHABET[0])
        if not code:
            return 0
        return decode(code)
    except Base62Error as e:
        logger.error(f"Failed to extract ID from code {code}: {e}")
        return None
