"""Input validation and sanitization utilities for opsvi-foundation.

Provides comprehensive input validation, type checking, and sanitization.
"""

import html
import logging
import re
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union

from ..core.base import ComponentError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class InputValidationError(ComponentError):
    """Input validation error."""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value


class InputSanitizer:
    """Input sanitization utilities."""

    # Patterns for sanitization
    SQL_KEYWORDS = {
        "select",
        "insert",
        "update",
        "delete",
        "drop",
        "create",
        "alter",
        "union",
        "exec",
        "execute",
        "script",
        "javascript",
    }

    FILENAME_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    WHITESPACE_PATTERN = re.compile(r"\s+")

    @staticmethod
    def sanitize_html(text: str, allowed_tags: Optional[Set[str]] = None) -> str:
        """Sanitize HTML input by escaping or removing tags.

        Args:
            text: Input text to sanitize
            allowed_tags: Optional set of allowed HTML tags

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # First, escape all HTML
        sanitized = html.escape(text)

        # If there are allowed tags, unescape them
        if allowed_tags:
            for tag in allowed_tags:
                # Unescape opening tags
                sanitized = sanitized.replace(f"&lt;{tag}&gt;", f"<{tag}>")
                sanitized = sanitized.replace(f"&lt;{tag} ", f"<{tag} ")
                # Unescape closing tags
                sanitized = sanitized.replace(f"&lt;/{tag}&gt;", f"</{tag}>")

        return sanitized

    @staticmethod
    def sanitize_sql(text: str, escape_quotes: bool = True) -> str:
        """Sanitize SQL input to prevent injection.

        Args:
            text: Input text to sanitize
            escape_quotes: Whether to escape quotes

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        sanitized = text

        # Remove SQL comments
        sanitized = re.sub(r"--.*$", "", sanitized, flags=re.MULTILINE)
        sanitized = re.sub(r"/\*.*?\*/", "", sanitized, flags=re.DOTALL)

        # Escape quotes if requested
        if escape_quotes:
            sanitized = sanitized.replace("'", "''")
            sanitized = sanitized.replace('"', '""')

        # Check for SQL keywords (case-insensitive)
        words = sanitized.lower().split()
        for keyword in InputSanitizer.SQL_KEYWORDS:
            if keyword in words:
                logger.warning(f"Potential SQL injection attempt detected: {keyword}")
                # Remove the keyword
                pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
                sanitized = pattern.sub("", sanitized)

        return sanitized.strip()

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """Sanitize filename to be filesystem-safe.

        Args:
            filename: Input filename to sanitize
            max_length: Maximum filename length

        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed"

        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]

        # Replace invalid characters
        sanitized = InputSanitizer.FILENAME_INVALID_CHARS.sub("_", filename)

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # Limit length
        if len(sanitized) > max_length:
            # Keep extension if present
            parts = sanitized.rsplit(".", 1)
            if len(parts) == 2:
                name, ext = parts
                max_name_length = max_length - len(ext) - 1
                sanitized = f"{name[:max_name_length]}.{ext}"
            else:
                sanitized = sanitized[:max_length]

        # Default if empty after sanitization
        if not sanitized:
            sanitized = "unnamed"

        return sanitized

    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URL input.

        Args:
            url: Input URL to sanitize

        Returns:
            Sanitized URL
        """
        if not url:
            return ""

        # Parse and reconstruct URL
        try:
            parsed = urllib.parse.urlparse(url)

            # Only allow http(s) and ftp schemes
            if parsed.scheme not in ("http", "https", "ftp", ""):
                logger.warning(f"Invalid URL scheme: {parsed.scheme}")
                return ""

            # Reconstruct URL with sanitized components
            sanitized = urllib.parse.urlunparse(parsed)
            return sanitized
        except Exception as e:
            logger.error(f"Error sanitizing URL: {e}")
            return ""

    @staticmethod
    def sanitize_whitespace(text: str, collapse: bool = True) -> str:
        """Sanitize whitespace in text.

        Args:
            text: Input text
            collapse: Whether to collapse multiple spaces

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Strip leading/trailing whitespace
        sanitized = text.strip()

        # Collapse multiple spaces if requested
        if collapse:
            sanitized = InputSanitizer.WHITESPACE_PATTERN.sub(" ", sanitized)

        return sanitized


class InputValidator:
    """Input validation utilities."""

    @staticmethod
    def check_type(value: Any, expected_type: Type, strict: bool = False) -> bool:
        """Check if value matches expected type.

        Args:
            value: Value to check
            expected_type: Expected type
            strict: If True, no type coercion

        Returns:
            True if type matches
        """
        if strict:
            return type(value) == expected_type
        else:
            return isinstance(value, expected_type)

    @staticmethod
    def coerce_type(value: Any, target_type: Type[T]) -> Optional[T]:
        """Attempt to coerce value to target type.

        Args:
            value: Value to coerce
            target_type: Target type

        Returns:
            Coerced value or None if coercion fails
        """
        if isinstance(value, target_type):
            return value

        try:
            # Special handling for bool
            if target_type == bool:
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)

            # Special handling for None
            if value is None:
                return None

            # Try direct conversion
            return target_type(value)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to coerce {value} to {target_type}: {e}")
            return None

    @staticmethod
    def validate_enum(value: Any, allowed_values: Union[List, Set, tuple]) -> bool:
        """Validate that value is in allowed values.

        Args:
            value: Value to validate
            allowed_values: Allowed values

        Returns:
            True if value is allowed
        """
        return value in allowed_values

    @staticmethod
    def validate_required(
        data: Dict[str, Any], required_fields: List[str]
    ) -> tuple[bool, List[str]]:
        """Validate that required fields are present.

        Args:
            data: Data dictionary
            required_fields: List of required field names

        Returns:
            Tuple of (is_valid, missing_fields)
        """
        missing = []

        for field in required_fields:
            if field not in data or data[field] is None:
                missing.append(field)

        return len(missing) == 0, missing

    @staticmethod
    def validate_optional(
        data: Dict[str, Any], optional_fields: List[str]
    ) -> Dict[str, Any]:
        """Extract only optional fields that are present.

        Args:
            data: Data dictionary
            optional_fields: List of optional field names

        Returns:
            Dictionary with only optional fields
        """
        return {field: data[field] for field in optional_fields if field in data}

    @staticmethod
    def validate_length(
        value: Union[str, list, dict],
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> bool:
        """Validate length of value.

        Args:
            value: Value to check
            min_length: Minimum length
            max_length: Maximum length

        Returns:
            True if length is valid
        """
        length = len(value)

        if min_length is not None and length < min_length:
            return False

        if max_length is not None and length > max_length:
            return False

        return True

    @staticmethod
    def validate_range(
        value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        inclusive: bool = True,
    ) -> bool:
        """Validate that value is in range.

        Args:
            value: Value to check
            min_value: Minimum value
            max_value: Maximum value
            inclusive: Whether bounds are inclusive

        Returns:
            True if in range
        """
        if min_value is not None:
            if inclusive:
                if value < min_value:
                    return False
            else:
                if value <= min_value:
                    return False

        if max_value is not None:
            if inclusive:
                if value > max_value:
                    return False
            else:
                if value >= max_value:
                    return False

        return True

    @staticmethod
    def validate_pattern(value: str, pattern: str, flags: int = 0) -> bool:
        """Validate that value matches regex pattern.

        Args:
            value: Value to check
            pattern: Regex pattern
            flags: Regex flags

        Returns:
            True if matches
        """
        try:
            regex = re.compile(pattern, flags)
            return regex.match(value) is not None
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return False


# Convenience functions
def sanitize_html(text: str, allowed_tags: Optional[Set[str]] = None) -> str:
    """Sanitize HTML input."""
    return InputSanitizer.sanitize_html(text, allowed_tags)


def sanitize_sql(text: str, escape_quotes: bool = True) -> str:
    """Sanitize SQL input."""
    return InputSanitizer.sanitize_sql(text, escape_quotes)


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename."""
    return InputSanitizer.sanitize_filename(filename, max_length)


def validate_input(
    data: Dict[str, Any],
    required: Optional[List[str]] = None,
    optional: Optional[List[str]] = None,
    types: Optional[Dict[str, Type]] = None,
    validators: Optional[Dict[str, Callable[[Any], bool]]] = None,
) -> tuple[bool, Dict[str, Any], List[str]]:
    """Comprehensive input validation.

    Args:
        data: Input data dictionary
        required: Required field names
        optional: Optional field names
        types: Expected types for fields
        validators: Custom validators for fields

    Returns:
        Tuple of (is_valid, validated_data, errors)
    """
    errors = []
    validated = {}

    # Check required fields
    if required:
        is_valid, missing = InputValidator.validate_required(data, required)
        if not is_valid:
            for field in missing:
                errors.append(f"Required field missing: {field}")

    # Process all fields
    all_fields = set()
    if required:
        all_fields.update(required)
    if optional:
        all_fields.update(optional)

    for field in all_fields:
        if field not in data:
            if required and field in required:
                continue  # Already reported as missing
            else:
                continue  # Optional and not present

        value = data[field]

        # Type checking
        if types and field in types:
            expected_type = types[field]
            if not InputValidator.check_type(value, expected_type):
                # Try coercion
                coerced = InputValidator.coerce_type(value, expected_type)
                if coerced is not None:
                    value = coerced
                else:
                    errors.append(
                        f"Field '{field}' has wrong type: expected {expected_type.__name__}"
                    )
                    continue

        # Custom validation
        if validators and field in validators:
            validator = validators[field]
            try:
                if not validator(value):
                    errors.append(f"Field '{field}' failed validation")
                    continue
            except Exception as e:
                errors.append(f"Field '{field}' validation error: {e}")
                continue

        validated[field] = value

    return len(errors) == 0, validated, errors


def check_type(value: Any, expected_type: Type, strict: bool = False) -> bool:
    """Check if value matches expected type."""
    return InputValidator.check_type(value, expected_type, strict)


def coerce_type(value: Any, target_type: Type[T]) -> Optional[T]:
    """Attempt to coerce value to target type."""
    return InputValidator.coerce_type(value, target_type)


def validate_enum(value: Any, allowed_values: Union[List, Set, tuple]) -> bool:
    """Validate that value is in allowed values."""
    return InputValidator.validate_enum(value, allowed_values)


def validate_required(
    data: Dict[str, Any], required_fields: List[str]
) -> tuple[bool, List[str]]:
    """Validate that required fields are present."""
    return InputValidator.validate_required(data, required_fields)


def validate_optional(
    data: Dict[str, Any], optional_fields: List[str]
) -> Dict[str, Any]:
    """Extract only optional fields that are present."""
    return InputValidator.validate_optional(data, optional_fields)


__all__ = [
    "InputSanitizer",
    "InputValidator",
    "InputValidationError",
    "sanitize_html",
    "sanitize_sql",
    "sanitize_filename",
    "validate_input",
    "check_type",
    "coerce_type",
    "validate_enum",
    "validate_required",
    "validate_optional",
]
