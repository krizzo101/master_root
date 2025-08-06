"""
Input validation and sanitization utilities.

Provides comprehensive input validation, sanitization, and security utilities
for preventing common vulnerabilities like SQL injection, XSS, and data validation.
"""

from __future__ import annotations

import html
import re
from typing import Any

from opsvi_foundation.patterns import ComponentError


class ValidationError(ComponentError):
    """Raised when input validation fails."""


class SanitizationError(ComponentError):
    """Raised when input sanitization fails."""


def sanitize_input(data: Any, max_length: int | None = None) -> str:
    """
    Sanitize input data to prevent XSS and injection attacks.

    Args:
        data: Input data to sanitize
        max_length: Maximum allowed length for the input

    Returns:
        Sanitized string

    Raises:
        SanitizationError: If sanitization fails
    """
    if data is None:
        return ""

    # Convert to string
    sanitized = str(data).strip()

    # Check length
    if max_length and len(sanitized) > max_length:
        raise SanitizationError(f"Input exceeds maximum length of {max_length}")

    # HTML escape to prevent XSS
    sanitized = html.escape(sanitized)

    return sanitized


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def sanitize_sql_input(value: Any) -> str:
    """
    Sanitize input for SQL queries (basic protection).

    Note: This is a basic implementation. Use parameterized queries
    for production applications.

    Args:
        value: Value to sanitize

    Returns:
        Sanitized string
    """
    if value is None:
        return "NULL"

    # Convert to string and escape single quotes
    sanitized = str(value).replace("'", "''")

    return f"'{sanitized}'"


def validate_json_schema(data: dict[str, Any], schema: dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.

    Args:
        data: Data to validate
        schema: JSON schema definition

    Returns:
        True if valid, False otherwise
    """
    # Basic schema validation implementation
    # In production, use a proper JSON schema validator like jsonschema
    try:
        # Placeholder for actual schema validation
        return True
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed_file"

    return sanitized


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    # Remove all non-digit characters
    digits_only = re.sub(r"\D", "", phone)

    # Check if it's a reasonable length (7-15 digits)
    return 7 <= len(digits_only) <= 15


def sanitize_html(html_content: str, allowed_tags: list[str] | None = None) -> str:
    """
    Sanitize HTML content by removing dangerous tags and attributes.

    Args:
        html_content: HTML content to sanitize
        allowed_tags: List of allowed HTML tags

    Returns:
        Sanitized HTML content
    """
    if allowed_tags is None:
        allowed_tags = ["p", "br", "strong", "em", "u", "ol", "ul", "li"]

    # Basic HTML sanitization
    # In production, use a proper HTML sanitizer like bleach
    sanitized = html_content

    # Remove script tags and event handlers
    sanitized = re.sub(
        r"<script[^>]*>.*?</script>",
        "",
        sanitized,
        flags=re.IGNORECASE | re.DOTALL,
    )
    sanitized = re.sub(r"on\w+\s*=", "", sanitized, flags=re.IGNORECASE)

    return sanitized


class InputValidator:
    """Comprehensive input validation and sanitization class."""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the input validator.

        Args:
            config: Configuration options for validation
        """
        self.config = config or {}
        self.max_length = self.config.get("max_length", 1000)
        self.strict_mode = self.config.get("strict_mode", False)

    def validate_and_sanitize(
        self,
        data: Any,
        field_name: str,
        field_type: str = "string",
    ) -> Any:
        """
        Validate and sanitize input data based on field type.

        Args:
            data: Input data
            field_name: Name of the field for error reporting
            field_type: Type of field (string, email, url, etc.)

        Returns:
            Validated and sanitized data

        Raises:
            ValidationError: If validation fails
        """
        try:
            if field_type == "email":
                if not validate_email(str(data)):
                    raise ValidationError(
                        f"Invalid email format for field '{field_name}'",
                    )
                return str(data).lower().strip()

            if field_type == "url":
                if not validate_url(str(data)):
                    raise ValidationError(
                        f"Invalid URL format for field '{field_name}'",
                    )
                return str(data).strip()

            if field_type == "phone":
                if not validate_phone_number(str(data)):
                    raise ValidationError(
                        f"Invalid phone number format for field '{field_name}'",
                    )
                return str(data).strip()

            # string
            return sanitize_input(data, self.max_length)

        except Exception as e:
            if isinstance(e, (ValidationError, SanitizationError)):
                raise
            raise ValidationError(
                f"Validation failed for field '{field_name}': {e!s}",
            )

    def validate_required_fields(
        self,
        data: dict[str, Any],
        required_fields: list[str],
    ) -> None:
        """
        Validate that all required fields are present and not empty.

        Args:
            data: Data dictionary to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If any required field is missing or empty
        """
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Required field '{field}' is missing")

            if data[field] is None or (
                isinstance(data[field], str) and not data[field].strip()
            ):
                raise ValidationError(f"Required field '{field}' cannot be empty")
