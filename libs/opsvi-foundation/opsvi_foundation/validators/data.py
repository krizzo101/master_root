"""Data validation utilities for opsvi-foundation.

Provides comprehensive data validation for common data types and formats.
"""

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Pattern, Union
from urllib.parse import urlparse

from ..core.base import ComponentError

logger = logging.getLogger(__name__)


class ValidationError(ComponentError):
    """Data validation error."""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    data: Optional[Any] = None

    def raise_if_invalid(self) -> None:
        """Raise ValidationError if not valid."""
        if not self.is_valid:
            raise ValidationError(f"Validation failed: {', '.join(self.errors)}")


class DataValidator:
    """Comprehensive data validation utilities."""

    # Common regex patterns
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

    PHONE_PATTERN = re.compile(
        r"^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$"
    )

    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
    )

    IPV4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    IPV6_PATTERN = re.compile(
        r"^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,7}:|"
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
        r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
        r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
        r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
        r":((:[0-9a-fA-F]{1,4}){1,7}|:))$"
    )

    @staticmethod
    def validate_email(email: str, check_dns: bool = False) -> ValidationResult:
        """Validate email address.

        Args:
            email: Email address to validate
            check_dns: Whether to check DNS records (requires dnspython)

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if not email:
            errors.append("Email address is empty")
            return ValidationResult(False, errors, warnings)

        # Check format
        if not DataValidator.EMAIL_PATTERN.match(email):
            errors.append(f"Invalid email format: {email}")

        # Check length
        if len(email) > 254:
            errors.append("Email address too long (max 254 characters)")

        # Check local part length
        local_part = email.split("@")[0] if "@" in email else email
        if len(local_part) > 64:
            errors.append("Email local part too long (max 64 characters)")

        # DNS check if requested
        if check_dns and "@" in email:
            domain = email.split("@")[1]
            try:
                import dns.resolver

                try:
                    dns.resolver.resolve(domain, "MX")
                except dns.resolver.NXDOMAIN:
                    warnings.append(f"Domain {domain} does not exist")
                except dns.resolver.NoAnswer:
                    warnings.append(f"Domain {domain} has no MX records")
            except ImportError:
                warnings.append("DNS checking requires dnspython package")

        return ValidationResult(
            len(errors) == 0, errors, warnings, email if not errors else None
        )

    @staticmethod
    def validate_url(url: str, require_tld: bool = True) -> ValidationResult:
        """Validate URL.

        Args:
            url: URL to validate
            require_tld: Whether to require top-level domain

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if not url:
            errors.append("URL is empty")
            return ValidationResult(False, errors, warnings)

        # Parse URL
        try:
            parsed = urlparse(url)

            # Check scheme
            if not parsed.scheme:
                errors.append("URL missing scheme (http/https)")
            elif parsed.scheme not in ("http", "https", "ftp", "ftps"):
                warnings.append(f"Unusual URL scheme: {parsed.scheme}")

            # Check netloc
            if not parsed.netloc:
                errors.append("URL missing domain")
            elif require_tld and "." not in parsed.netloc:
                errors.append("URL missing top-level domain")

            # Check for common issues
            if parsed.netloc.startswith(".") or parsed.netloc.endswith("."):
                errors.append("Invalid domain format")

        except Exception as e:
            errors.append(f"Invalid URL: {e}")

        return ValidationResult(
            len(errors) == 0, errors, warnings, url if not errors else None
        )

    @staticmethod
    def validate_phone(
        phone: str, country_code: Optional[str] = None
    ) -> ValidationResult:
        """Validate phone number.

        Args:
            phone: Phone number to validate
            country_code: Optional country code for validation

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if not phone:
            errors.append("Phone number is empty")
            return ValidationResult(False, errors, warnings)

        # Remove common formatting characters
        cleaned = re.sub(r"[\s\-\(\)\.]+", "", phone)

        # Check length
        if len(cleaned) < 7:
            errors.append("Phone number too short")
        elif len(cleaned) > 15:
            errors.append("Phone number too long")

        # Check format
        if not DataValidator.PHONE_PATTERN.match(phone):
            errors.append(f"Invalid phone number format: {phone}")

        # Country-specific validation
        if country_code:
            if (
                country_code == "US"
                and len(cleaned) != 10
                and not cleaned.startswith("1")
            ):
                warnings.append("US phone numbers should be 10 digits")

        return ValidationResult(
            len(errors) == 0, errors, warnings, cleaned if not errors else None
        )

    @staticmethod
    def validate_uuid(uuid_str: str, version: Optional[int] = None) -> ValidationResult:
        """Validate UUID.

        Args:
            uuid_str: UUID string to validate
            version: Optional UUID version to check

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if not uuid_str:
            errors.append("UUID is empty")
            return ValidationResult(False, errors, warnings)

        # Check format
        if not DataValidator.UUID_PATTERN.match(uuid_str):
            errors.append(f"Invalid UUID format: {uuid_str}")
            return ValidationResult(False, errors, warnings)

        # Try to parse UUID
        try:
            uuid_obj = uuid.UUID(uuid_str)

            # Check version if specified
            if version and uuid_obj.version != version:
                errors.append(
                    f"UUID version mismatch: expected {version}, got {uuid_obj.version}"
                )

            return ValidationResult(len(errors) == 0, errors, warnings, str(uuid_obj))
        except ValueError as e:
            errors.append(f"Invalid UUID: {e}")
            return ValidationResult(False, errors, warnings)

    @staticmethod
    def validate_json(json_str: str, schema: Optional[Dict] = None) -> ValidationResult:
        """Validate JSON string.

        Args:
            json_str: JSON string to validate
            schema: Optional JSON schema to validate against

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        data = None

        if not json_str:
            errors.append("JSON string is empty")
            return ValidationResult(False, errors, warnings)

        # Try to parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            return ValidationResult(False, errors, warnings)

        # Validate against schema if provided
        if schema:
            try:
                import jsonschema

                jsonschema.validate(data, schema)
            except ImportError:
                warnings.append("Schema validation requires jsonschema package")
            except jsonschema.ValidationError as e:
                errors.append(f"Schema validation failed: {e.message}")

        return ValidationResult(len(errors) == 0, errors, warnings, data)

    @staticmethod
    def validate_range(
        value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        inclusive: bool = True,
    ) -> ValidationResult:
        """Validate numeric range.

        Args:
            value: Value to validate
            min_value: Minimum value
            max_value: Maximum value
            inclusive: Whether bounds are inclusive

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if min_value is not None:
            if inclusive:
                if value < min_value:
                    errors.append(f"Value {value} is less than minimum {min_value}")
            else:
                if value <= min_value:
                    errors.append(f"Value {value} is not greater than {min_value}")

        if max_value is not None:
            if inclusive:
                if value > max_value:
                    errors.append(f"Value {value} is greater than maximum {max_value}")
            else:
                if value >= max_value:
                    errors.append(f"Value {value} is not less than {max_value}")

        return ValidationResult(
            len(errors) == 0, errors, warnings, value if not errors else None
        )

    @staticmethod
    def validate_length(
        value: Union[str, list, dict],
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> ValidationResult:
        """Validate length.

        Args:
            value: Value to validate
            min_length: Minimum length
            max_length: Maximum length

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        length = len(value)

        if min_length is not None and length < min_length:
            errors.append(f"Length {length} is less than minimum {min_length}")

        if max_length is not None and length > max_length:
            errors.append(f"Length {length} is greater than maximum {max_length}")

        return ValidationResult(
            len(errors) == 0, errors, warnings, value if not errors else None
        )

    @staticmethod
    def validate_pattern(
        value: str, pattern: Union[str, Pattern], flags: int = 0
    ) -> ValidationResult:
        """Validate against regex pattern.

        Args:
            value: Value to validate
            pattern: Regex pattern
            flags: Regex flags

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if isinstance(pattern, str):
            try:
                pattern = re.compile(pattern, flags)
            except re.error as e:
                errors.append(f"Invalid regex pattern: {e}")
                return ValidationResult(False, errors, warnings)

        if not pattern.match(value):
            errors.append(f"Value does not match pattern: {pattern.pattern}")

        return ValidationResult(
            len(errors) == 0, errors, warnings, value if not errors else None
        )

    @staticmethod
    def validate_ip(ip: str, version: Optional[int] = None) -> ValidationResult:
        """Validate IP address.

        Args:
            ip: IP address to validate
            version: Optional IP version (4 or 6)

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if not ip:
            errors.append("IP address is empty")
            return ValidationResult(False, errors, warnings)

        is_ipv4 = DataValidator.IPV4_PATTERN.match(ip)
        is_ipv6 = DataValidator.IPV6_PATTERN.match(ip)

        if version == 4:
            if not is_ipv4:
                errors.append(f"Invalid IPv4 address: {ip}")
        elif version == 6:
            if not is_ipv6:
                errors.append(f"Invalid IPv6 address: {ip}")
        else:
            if not is_ipv4 and not is_ipv6:
                errors.append(f"Invalid IP address: {ip}")

        return ValidationResult(
            len(errors) == 0, errors, warnings, ip if not errors else None
        )


# Convenience functions
def validate_data(
    data: Any, validators: List[Callable[[Any], ValidationResult]]
) -> ValidationResult:
    """Validate data with multiple validators.

    Args:
        data: Data to validate
        validators: List of validator functions

    Returns:
        Combined ValidationResult
    """
    all_errors = []
    all_warnings = []

    for validator in validators:
        result = validator(data)
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)

    return ValidationResult(
        len(all_errors) == 0, all_errors, all_warnings, data if not all_errors else None
    )


def validate_email(email: str, check_dns: bool = False) -> bool:
    """Validate email address."""
    result = DataValidator.validate_email(email, check_dns)
    return result.is_valid


def validate_url(url: str, require_tld: bool = True) -> bool:
    """Validate URL."""
    result = DataValidator.validate_url(url, require_tld)
    return result.is_valid


def validate_phone(phone: str, country_code: Optional[str] = None) -> bool:
    """Validate phone number."""
    result = DataValidator.validate_phone(phone, country_code)
    return result.is_valid


def validate_uuid(uuid_str: str, version: Optional[int] = None) -> bool:
    """Validate UUID."""
    result = DataValidator.validate_uuid(uuid_str, version)
    return result.is_valid


def validate_json(json_str: str, schema: Optional[Dict] = None) -> bool:
    """Validate JSON string."""
    result = DataValidator.validate_json(json_str, schema)
    return result.is_valid


def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    inclusive: bool = True,
) -> bool:
    """Validate numeric range."""
    result = DataValidator.validate_range(value, min_value, max_value, inclusive)
    return result.is_valid


def validate_length(
    value: Union[str, list, dict],
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> bool:
    """Validate length."""
    result = DataValidator.validate_length(value, min_length, max_length)
    return result.is_valid


def validate_pattern(value: str, pattern: Union[str, Pattern], flags: int = 0) -> bool:
    """Validate against regex pattern."""
    result = DataValidator.validate_pattern(value, pattern, flags)
    return result.is_valid


__all__ = [
    "DataValidator",
    "ValidationError",
    "ValidationResult",
    "validate_data",
    "validate_email",
    "validate_url",
    "validate_phone",
    "validate_uuid",
    "validate_json",
    "validate_range",
    "validate_length",
    "validate_pattern",
]
