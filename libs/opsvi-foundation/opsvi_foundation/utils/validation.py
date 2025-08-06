"""
Validation utilities for OPSVI Foundation.

Provides comprehensive validation functions and decorators.
"""

import logging
import re
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class CustomValidationError(Exception):
    """Custom validation error."""


class ValidationRule:
    """Base class for validation rules."""

    def __init__(self, name: str, validator_func: Callable, error_message: str) -> None:
        self.name = name
        self.validator_func = validator_func
        self.error_message = error_message

    def validate(self, value: Any) -> bool:
        """Validate a value."""
        try:
            return self.validator_func(value)
        except Exception:
            return False

    def get_error_message(self, value: Any) -> str:
        """Get error message for validation failure."""
        return self.error_message.format(value=value)


class ValidationSchema:
    """Schema for validation rules."""

    def __init__(self) -> None:
        self.rules: list[ValidationRule] = []
        self.custom_validators: dict[str, Callable] = {}

    def add_rule(self, rule: ValidationRule) -> "ValidationSchema":
        """Add a validation rule."""
        self.rules.append(rule)
        return self

    def add_custom_validator(
        self,
        name: str,
        validator_func: Callable,
    ) -> "ValidationSchema":
        """Add a custom validator."""
        self.custom_validators[name] = validator_func
        return self

    def validate(self, data: Any) -> list[str]:
        """Validate data against all rules."""
        errors = []

        for rule in self.rules:
            if not rule.validate(data):
                errors.append(rule.get_error_message(data))

        for name, validator_func in self.custom_validators.items():
            try:
                if not validator_func(data):
                    errors.append(
                        f"Custom validation '{name}' failed for value: {data}",
                    )
            except Exception as e:
                errors.append(f"Custom validation '{name}' error: {e}")

        return errors


# Common validation rules


def is_not_empty(value: Any) -> bool:
    """Check if value is not empty."""
    if value is None:
        return False
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, (list, tuple, set)):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def is_valid_email(value: str) -> bool:
    """Check if value is a valid email address."""
    if not isinstance(value, str):
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, value))


def is_valid_url(value: str) -> bool:
    """Check if value is a valid URL."""
    if not isinstance(value, str):
        return False

    try:
        result = urlparse(value)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_uuid(value: str) -> bool:
    """Check if value is a valid UUID."""
    if not isinstance(value, str):
        return False

    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def is_valid_phone(value: str) -> bool:
    """Check if value is a valid phone number."""
    if not isinstance(value, str):
        return False

    # Remove all non-digit characters
    digits_only = re.sub(r"\D", "", value)
    return len(digits_only) >= 10


def is_valid_date(value: str, format_str: str = "%Y-%m-%d") -> bool:
    """Check if value is a valid date string."""
    if not isinstance(value, str):
        return False

    try:
        datetime.strptime(value, format_str)
        return True
    except ValueError:
        return False


def is_valid_datetime(value: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> bool:
    """Check if value is a valid datetime string."""
    if not isinstance(value, str):
        return False

    try:
        datetime.strptime(value, format_str)
        return True
    except ValueError:
        return False


def is_valid_json(value: str) -> bool:
    """Check if value is valid JSON."""
    if not isinstance(value, str):
        return False

    try:
        import json

        json.loads(value)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def is_valid_ip_address(value: str) -> bool:
    """Check if value is a valid IP address."""
    if not isinstance(value, str):
        return False

    # IPv4 pattern
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ipv4_pattern, value):
        parts = value.split(".")
        return all(0 <= int(part) <= 255 for part in parts)

    # IPv6 pattern (simplified)
    ipv6_pattern = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    return bool(re.match(ipv6_pattern, value))


def is_valid_credit_card(value: str) -> bool:
    """Check if value is a valid credit card number (Luhn algorithm)."""
    if not isinstance(value, str):
        return False

    # Remove spaces and dashes
    digits = re.sub(r"\D", "", value)

    if len(digits) < 13 or len(digits) > 19:
        return False

    # Luhn algorithm
    total = 0
    is_even = False

    for digit in reversed(digits):
        digit = int(digit)
        if is_even:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
        is_even = not is_even

    return total % 10 == 0


def is_valid_password(value: str, min_length: int = 8) -> bool:
    """Check if value is a valid password."""
    if not isinstance(value, str):
        return False

    if len(value) < min_length:
        return False

    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", value):
        return False

    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", value):
        return False

    # Check for at least one digit
    if not re.search(r"\d", value):
        return False

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        return False

    return True


# Validation decorators


def validate_input(schema: ValidationSchema):
    """Decorator to validate function input."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Validate all arguments
            all_args = list(args) + list(kwargs.values())
            for arg in all_args:
                errors = schema.validate(arg)
                if errors:
                    raise CustomValidationError(
                        f"Validation failed: {'; '.join(errors)}"
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_output(schema: ValidationSchema):
    """Decorator to validate function output."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            errors = schema.validate(result)
            if errors:
                raise CustomValidationError(
                    f"Output validation failed: {'; '.join(errors)}"
                )
            return result

        return wrapper

    return decorator


def validate_field(field_name: str, schema: ValidationSchema):
    """Decorator to validate a specific field."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if field_name in kwargs:
                errors = schema.validate(kwargs[field_name])
                if errors:
                    raise CustomValidationError(
                        f"Field '{field_name}' validation failed: {'; '.join(errors)}",
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Pydantic validation models


class EmailValidator(BaseModel):
    """Email validation model."""

    email: str = Field(..., description="Email address")

    @validator("email")
    def validate_email(cls, v):
        if not is_valid_email(v):
            raise ValueError("Invalid email address")
        return v.lower()


class URLValidator(BaseModel):
    """URL validation model."""

    url: str = Field(..., description="URL")

    @validator("url")
    def validate_url(cls, v):
        if not is_valid_url(v):
            raise ValueError("Invalid URL")
        return v


class PhoneValidator(BaseModel):
    """Phone number validation model."""

    phone: str = Field(..., description="Phone number")

    @validator("phone")
    def validate_phone(cls, v):
        if not is_valid_phone(v):
            raise ValueError("Invalid phone number")
        return re.sub(r"\D", "", v)  # Return digits only


class PasswordValidator(BaseModel):
    """Password validation model."""

    password: str = Field(..., min_length=8, description="Password")

    @validator("password")
    def validate_password(cls, v):
        if not is_valid_password(v):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character",
            )
        return v


class CreditCardValidator(BaseModel):
    """Credit card validation model."""

    card_number: str = Field(..., description="Credit card number")

    @validator("card_number")
    def validate_credit_card(cls, v):
        if not is_valid_credit_card(v):
            raise ValueError("Invalid credit card number")
        return re.sub(r"\D", "", v)  # Return digits only


# Validation utilities


class ValidationUtils:
    """Utility class for validation operations."""

    @staticmethod
    def create_email_schema() -> ValidationSchema:
        """Create email validation schema."""
        schema = ValidationSchema()
        schema.add_rule(
            ValidationRule("not_empty", is_not_empty, "Email cannot be empty"),
        )
        schema.add_rule(
            ValidationRule(
                "valid_email",
                is_valid_email,
                "Invalid email format: {value}",
            ),
        )
        return schema

    @staticmethod
    def create_password_schema(min_length: int = 8) -> ValidationSchema:
        """Create password validation schema."""
        schema = ValidationSchema()
        schema.add_rule(
            ValidationRule("not_empty", is_not_empty, "Password cannot be empty"),
        )
        schema.add_rule(
            ValidationRule(
                "min_length",
                lambda v: len(v) >= min_length,
                f"Password must be at least {min_length} characters",
            ),
        )
        schema.add_rule(
            ValidationRule(
                "valid_password",
                lambda v: is_valid_password(v, min_length),
                "Password must contain uppercase, lowercase, digit, and special character",
            ),
        )
        return schema

    @staticmethod
    def create_url_schema() -> ValidationSchema:
        """Create URL validation schema."""
        schema = ValidationSchema()
        schema.add_rule(
            ValidationRule("not_empty", is_not_empty, "URL cannot be empty"),
        )
        schema.add_rule(
            ValidationRule("valid_url", is_valid_url, "Invalid URL format: {value}"),
        )
        return schema

    @staticmethod
    def create_phone_schema() -> ValidationSchema:
        """Create phone validation schema."""
        schema = ValidationSchema()
        schema.add_rule(
            ValidationRule("not_empty", is_not_empty, "Phone number cannot be empty"),
        )
        schema.add_rule(
            ValidationRule(
                "valid_phone",
                is_valid_phone,
                "Invalid phone number: {value}",
            ),
        )
        return schema

    @staticmethod
    def validate_dict(
        data: dict[str, Any],
        validators: dict[str, ValidationSchema],
    ) -> dict[str, list[str]]:
        """Validate a dictionary against multiple schemas."""
        errors = {}

        for field, schema in validators.items():
            if field in data:
                field_errors = schema.validate(data[field])
                if field_errors:
                    errors[field] = field_errors

        return errors

    @staticmethod
    def validate_list(data: list[Any], schema: ValidationSchema) -> list[str]:
        """Validate a list of items against a schema."""
        errors = []

        for i, item in enumerate(data):
            item_errors = schema.validate(item)
            if item_errors:
                errors.extend([f"Item {i}: {error}" for error in item_errors])

        return errors


# Type validation

T = TypeVar("T")


def validate_type(value: Any, expected_type: type[T]) -> T:
    """Validate that a value is of the expected type."""
    if not isinstance(value, expected_type):
        raise CustomValidationError(
            f"Expected {expected_type.__name__}, got {type(value).__name__}",
        )
    return value


def validate_optional_type(value: Any, expected_type: type[T]) -> T | None:
    """Validate that a value is of the expected type or None."""
    if value is None:
        return None
    return validate_type(value, expected_type)


def validate_union_type(value: Any, expected_types: list[type]) -> Any:
    """Validate that a value is one of the expected types."""
    for expected_type in expected_types:
        if isinstance(value, expected_type):
            return value
    raise CustomValidationError(
        f"Expected one of {[t.__name__ for t in expected_types]}, got {type(value).__name__}",
    )


# Range validation


def validate_range(
    value: float,
    min_value: float | None = None,
    max_value: float | None = None,
) -> int | float:
    """Validate that a value is within a range."""
    if min_value is not None and value < min_value:
        raise CustomValidationError(f"Value {value} is less than minimum {min_value}")

    if max_value is not None and value > max_value:
        raise CustomValidationError(
            f"Value {value} is greater than maximum {max_value}"
        )

    return value


def validate_length(
    value: str | list | dict,
    min_length: int | None = None,
    max_length: int | None = None,
) -> str | list | dict:
    """Validate the length of a value."""
    length = len(value)

    if min_length is not None and length < min_length:
        raise CustomValidationError(
            f"Length {length} is less than minimum {min_length}"
        )

    if max_length is not None and length > max_length:
        raise CustomValidationError(
            f"Length {length} is greater than maximum {max_length}"
        )

    return value


# Pattern validation


def validate_pattern(value: str, pattern: str, flags: int = 0) -> str:
    """Validate that a string matches a regex pattern."""
    if not isinstance(value, str):
        raise CustomValidationError(f"Expected string, got {type(value).__name__}")

    if not re.match(pattern, value, flags):
        raise CustomValidationError(
            f"Value '{value}' does not match pattern '{pattern}'"
        )

    return value


def validate_enum(value: Any, enum_class: type) -> Any:
    """Validate that a value is a valid enum value."""
    if not hasattr(enum_class, "__members__"):
        raise CustomValidationError(f"{enum_class.__name__} is not an enum")

    if value not in enum_class.__members__.values():
        valid_values = list(enum_class.__members__.values())
        raise CustomValidationError(
            f"Value {value} is not a valid {enum_class.__name__}. Valid values: {valid_values}",
        )

    return value
