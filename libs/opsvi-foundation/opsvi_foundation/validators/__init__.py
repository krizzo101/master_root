"""Validators for opsvi-foundation.

Provides comprehensive validation utilities for schemas, inputs, and data.
"""

from .data import (
    DataValidator,
    ValidationError,
    ValidationResult,
    validate_data,
    validate_email,
    validate_url,
    validate_phone,
    validate_uuid,
    validate_json,
    validate_range,
    validate_length,
    validate_pattern,
)

from .input import (
    InputSanitizer,
    InputValidator,
    sanitize_html,
    sanitize_sql,
    sanitize_filename,
    validate_input,
    check_type,
    coerce_type,
    validate_enum,
    validate_required,
    validate_optional,
)

from .schema import (
    SchemaValidator,
    PydanticValidator,
    JSONSchemaValidator,
    validate_schema,
    validate_pydantic,
    validate_json_schema,
    create_validator,
    compile_schema,
)

__all__ = [
    # Data validation
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
    # Input validation
    "InputSanitizer",
    "InputValidator",
    "sanitize_html",
    "sanitize_sql",
    "sanitize_filename",
    "validate_input",
    "check_type",
    "coerce_type",
    "validate_enum",
    "validate_required",
    "validate_optional",
    # Schema validation
    "SchemaValidator",
    "PydanticValidator",
    "JSONSchemaValidator",
    "validate_schema",
    "validate_pydantic",
    "validate_json_schema",
    "create_validator",
    "compile_schema",
]
