"""Schema validation utilities for opsvi-foundation.

Provides JSON schema and Pydantic model validation capabilities.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError as JSONSchemaError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    JSONSchemaError = Exception

try:
    from pydantic import BaseModel, ValidationError as PydanticError

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object
    PydanticError = Exception

from ..core.base import ComponentError

logger = logging.getLogger(__name__)


class SchemaValidationError(ComponentError):
    """Schema validation error."""

    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.errors = errors or []


class SchemaValidator(ABC):
    """Abstract base class for schema validators."""

    @abstractmethod
    def validate(self, data: Any) -> tuple[bool, Optional[List[str]]]:
        """Validate data against schema.

        Args:
            data: Data to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass

    @abstractmethod
    def is_valid(self, data: Any) -> bool:
        """Check if data is valid.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        pass


class JSONSchemaValidator(SchemaValidator):
    """JSON Schema validator."""

    def __init__(self, schema: Dict[str, Any], draft: str = "draft7"):
        """Initialize JSON schema validator.

        Args:
            schema: JSON schema dictionary
            draft: JSON schema draft version

        Raises:
            SchemaValidationError: If jsonschema is not installed
        """
        if not HAS_JSONSCHEMA:
            raise SchemaValidationError(
                "jsonschema package is required for JSON schema validation. "
                "Install with: pip install jsonschema"
            )

        self.schema = schema

        # Select validator class based on draft
        if draft == "draft7":
            self.validator_class = Draft7Validator
        else:
            # Default to Draft7
            self.validator_class = Draft7Validator

        # Create validator instance
        try:
            self.validator = self.validator_class(schema)
            self.validator.check_schema(schema)  # Validate the schema itself
        except Exception as e:
            raise SchemaValidationError(f"Invalid JSON schema: {e}")

    def validate(self, data: Any) -> tuple[bool, Optional[List[str]]]:
        """Validate data against JSON schema.

        Args:
            data: Data to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            self.validator.validate(data)
            return True, None
        except JSONSchemaError as e:
            # Collect all validation errors
            for error in self.validator.iter_errors(data):
                error_path = (
                    ".".join(str(p) for p in error.path) if error.path else "root"
                )
                errors.append(f"{error_path}: {error.message}")
            return False, errors
        except Exception as e:
            errors.append(str(e))
            return False, errors

    def is_valid(self, data: Any) -> bool:
        """Check if data is valid against schema.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            self.validator.validate(data)
            return True
        except:
            return False


class PydanticValidator(SchemaValidator):
    """Pydantic model validator."""

    def __init__(self, model_class: Type[BaseModel]):
        """Initialize Pydantic validator.

        Args:
            model_class: Pydantic model class

        Raises:
            SchemaValidationError: If pydantic is not installed
        """
        if not HAS_PYDANTIC:
            raise SchemaValidationError(
                "pydantic package is required for Pydantic validation. "
                "Install with: pip install pydantic"
            )

        if not issubclass(model_class, BaseModel):
            raise SchemaValidationError(
                f"{model_class} must be a Pydantic BaseModel subclass"
            )

        self.model_class = model_class

    def validate(self, data: Any) -> tuple[bool, Optional[List[str]]]:
        """Validate data against Pydantic model.

        Args:
            data: Data to validate (dict or model instance)

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            # If data is already a model instance, validate it
            if isinstance(data, self.model_class):
                # Trigger validation by accessing dict
                data.dict()
            else:
                # Create model instance from data
                self.model_class(**data if isinstance(data, dict) else {"value": data})
            return True, None
        except PydanticError as e:
            # Extract error messages from Pydantic validation error
            for error in e.errors():
                loc = ".".join(str(l) for l in error["loc"]) if error["loc"] else "root"
                errors.append(f"{loc}: {error['msg']}")
            return False, errors
        except Exception as e:
            errors.append(str(e))
            return False, errors

    def is_valid(self, data: Any) -> bool:
        """Check if data is valid against model.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            if isinstance(data, self.model_class):
                data.dict()
            else:
                self.model_class(**data if isinstance(data, dict) else {"value": data})
            return True
        except:
            return False

    def parse(self, data: Any) -> BaseModel:
        """Parse and validate data into model instance.

        Args:
            data: Data to parse

        Returns:
            Validated model instance

        Raises:
            SchemaValidationError: If validation fails
        """
        try:
            if isinstance(data, self.model_class):
                return data
            return self.model_class(
                **data if isinstance(data, dict) else {"value": data}
            )
        except PydanticError as e:
            errors = []
            for error in e.errors():
                loc = ".".join(str(l) for l in error["loc"]) if error["loc"] else "root"
                errors.append(f"{loc}: {error['msg']}")
            raise SchemaValidationError(
                f"Validation failed: {', '.join(errors)}",
                errors=[{"loc": e["loc"], "msg": e["msg"]} for e in e.errors()],
            )


class CompositeValidator(SchemaValidator):
    """Composite validator that combines multiple validators."""

    def __init__(self, validators: List[SchemaValidator], require_all: bool = True):
        """Initialize composite validator.

        Args:
            validators: List of validators to combine
            require_all: If True, all validators must pass
        """
        self.validators = validators
        self.require_all = require_all

    def validate(self, data: Any) -> tuple[bool, Optional[List[str]]]:
        """Validate data against all validators.

        Args:
            data: Data to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        all_errors = []
        passed_count = 0

        for validator in self.validators:
            is_valid, errors = validator.validate(data)

            if is_valid:
                passed_count += 1
                if not self.require_all:
                    # One validator passed, that's enough
                    return True, None
            else:
                if errors:
                    all_errors.extend(errors)

        if self.require_all:
            # All must pass
            if passed_count == len(self.validators):
                return True, None
            else:
                return False, all_errors
        else:
            # At least one must pass (none did)
            return False, all_errors

    def is_valid(self, data: Any) -> bool:
        """Check if data is valid.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        is_valid, _ = self.validate(data)
        return is_valid


def validate_schema(data: Any, schema: Union[Dict[str, Any], Type[BaseModel]]) -> bool:
    """Validate data against a schema.

    Args:
        data: Data to validate
        schema: JSON schema dict or Pydantic model class

    Returns:
        True if valid, False otherwise
    """
    if isinstance(schema, type) and HAS_PYDANTIC and issubclass(schema, BaseModel):
        validator = PydanticValidator(schema)
    elif isinstance(schema, dict):
        validator = JSONSchemaValidator(schema)
    else:
        raise SchemaValidationError(f"Unsupported schema type: {type(schema)}")

    return validator.is_valid(data)


def validate_pydantic(data: Any, model_class: Type[BaseModel]) -> BaseModel:
    """Validate and parse data with Pydantic model.

    Args:
        data: Data to validate
        model_class: Pydantic model class

    Returns:
        Validated model instance

    Raises:
        SchemaValidationError: If validation fails
    """
    validator = PydanticValidator(model_class)
    return validator.parse(data)


def validate_json_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """Validate data against JSON schema.

    Args:
        data: Data to validate
        schema: JSON schema dictionary

    Returns:
        True if valid

    Raises:
        SchemaValidationError: If validation fails
    """
    validator = JSONSchemaValidator(schema)
    is_valid, errors = validator.validate(data)

    if not is_valid:
        raise SchemaValidationError(
            f"JSON schema validation failed: {', '.join(errors or [])}",
            errors=[{"message": e} for e in (errors or [])],
        )

    return True


def create_validator(
    schema: Optional[Dict[str, Any]] = None,
    model: Optional[Type[BaseModel]] = None,
    validators: Optional[List[SchemaValidator]] = None,
    require_all: bool = True,
) -> SchemaValidator:
    """Create a validator from various sources.

    Args:
        schema: JSON schema dictionary
        model: Pydantic model class
        validators: List of validators to combine
        require_all: For composite validator, require all to pass

    Returns:
        Schema validator instance

    Raises:
        SchemaValidationError: If no valid validator source provided
    """
    created_validators = []

    if schema:
        created_validators.append(JSONSchemaValidator(schema))

    if model:
        created_validators.append(PydanticValidator(model))

    if validators:
        created_validators.extend(validators)

    if not created_validators:
        raise SchemaValidationError("No validator source provided")

    if len(created_validators) == 1:
        return created_validators[0]
    else:
        return CompositeValidator(created_validators, require_all=require_all)


def compile_schema(schema: Dict[str, Any]) -> JSONSchemaValidator:
    """Compile a JSON schema for repeated use.

    Args:
        schema: JSON schema dictionary

    Returns:
        Compiled schema validator
    """
    return JSONSchemaValidator(schema)


# Example schemas for common use cases
COMMON_SCHEMAS = {
    "email": {
        "type": "string",
        "format": "email",
        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    },
    "url": {
        "type": "string",
        "format": "uri",
        "pattern": r"^https?://[^\s/$.?#].[^\s]*$",
    },
    "uuid": {
        "type": "string",
        "format": "uuid",
        "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    },
    "date": {"type": "string", "format": "date", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
    "datetime": {"type": "string", "format": "date-time"},
    "ipv4": {"type": "string", "format": "ipv4"},
    "ipv6": {"type": "string", "format": "ipv6"},
}


__all__ = [
    "SchemaValidator",
    "SchemaValidationError",
    "JSONSchemaValidator",
    "PydanticValidator",
    "CompositeValidator",
    "validate_schema",
    "validate_pydantic",
    "validate_json_schema",
    "create_validator",
    "compile_schema",
    "COMMON_SCHEMAS",
]
