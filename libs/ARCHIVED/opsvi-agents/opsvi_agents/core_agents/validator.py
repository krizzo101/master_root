"""ValidatorAgent - Data validation and rules."""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


class ValidationType(Enum):
    """Types of validation."""

    SCHEMA = "schema"
    TYPE = "type"
    FORMAT = "format"
    RANGE = "range"
    PATTERN = "pattern"
    BUSINESS = "business"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    UNIQUENESS = "uniqueness"
    REFERENTIAL = "referential"


class Severity(Enum):
    """Validation issue severity."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationRule:
    """Validation rule definition."""

    id: str
    name: str
    type: ValidationType
    condition: Union[str, Dict[str, Any], Callable]
    severity: Severity = Severity.ERROR
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def apply(self, data: Any) -> Optional["ValidationIssue"]:
        """Apply validation rule."""
        if self.type == ValidationType.TYPE:
            return self._validate_type(data)
        elif self.type == ValidationType.PATTERN:
            return self._validate_pattern(data)
        elif self.type == ValidationType.RANGE:
            return self._validate_range(data)
        else:
            return self._generic_validate(data)

    def _validate_type(self, data: Any) -> Optional["ValidationIssue"]:
        """Validate data type."""
        expected_type = self.condition
        if isinstance(expected_type, str):
            expected_type = eval(expected_type)

        if not isinstance(data, expected_type):
            return ValidationIssue(
                rule_id=self.id,
                field="",
                value=data,
                severity=self.severity,
                message=self.message
                or f"Expected type {expected_type.__name__}, got {type(data).__name__}",
            )
        return None

    def _validate_pattern(self, data: Any) -> Optional["ValidationIssue"]:
        """Validate against pattern."""
        if not isinstance(data, str):
            return None

        pattern = (
            self.condition if isinstance(self.condition, str) else str(self.condition)
        )
        if not re.match(pattern, data):
            return ValidationIssue(
                rule_id=self.id,
                field="",
                value=data,
                severity=self.severity,
                message=self.message or f"Does not match pattern: {pattern}",
            )
        return None

    def _validate_range(self, data: Any) -> Optional["ValidationIssue"]:
        """Validate range."""
        if not isinstance(data, (int, float)):
            return None

        if isinstance(self.condition, dict):
            min_val = self.condition.get("min", float("-inf"))
            max_val = self.condition.get("max", float("inf"))

            if data < min_val or data > max_val:
                return ValidationIssue(
                    rule_id=self.id,
                    field="",
                    value=data,
                    severity=self.severity,
                    message=self.message
                    or f"Value {data} outside range [{min_val}, {max_val}]",
                )
        return None

    def _generic_validate(self, data: Any) -> Optional["ValidationIssue"]:
        """Generic validation."""
        if callable(self.condition):
            if not self.condition(data):
                return ValidationIssue(
                    rule_id=self.id,
                    field="",
                    value=data,
                    severity=self.severity,
                    message=self.message or "Validation failed",
                )
        return None


@dataclass
class ValidationIssue:
    """Validation issue/error."""

    rule_id: str
    field: str
    value: Any
    severity: Severity
    message: str
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "field": self.field,
            "value": str(self.value),
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationSchema:
    """Validation schema definition."""

    id: str
    name: str
    rules: List[ValidationRule]
    version: str = "1.0"
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self, data: Any) -> "ValidationResult":
        """Validate data against schema."""
        issues = []

        for rule in self.rules:
            issue = rule.apply(data)
            if issue:
                issues.append(issue)

        return ValidationResult(
            schema_id=self.id,
            valid=len([i for i in issues if i.severity == Severity.ERROR]) == 0,
            issues=issues,
        )


@dataclass
class ValidationResult:
    """Validation result."""

    schema_id: str
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_errors(self) -> List[ValidationIssue]:
        """Get error-level issues."""
        return [i for i in self.issues if i.severity == Severity.ERROR]

    def get_warnings(self) -> List[ValidationIssue]:
        """Get warning-level issues."""
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schema_id": self.schema_id,
            "valid": self.valid,
            "issues": [i.to_dict() for i in self.issues],
            "error_count": len(self.get_errors()),
            "warning_count": len(self.get_warnings()),
            "metadata": self.metadata,
        }


class ValidatorAgent(BaseAgent):
    """Validates data against rules and schemas."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize validator agent."""
        super().__init__(
            config
            or AgentConfig(
                name="ValidatorAgent",
                description="Data validation and rules",
                capabilities=["validate", "verify", "check", "enforce", "audit"],
                max_retries=1,
                timeout=30,
            )
        )
        self.schemas: Dict[str, ValidationSchema] = {}
        self.rules: Dict[str, ValidationRule] = {}
        self.validation_history: List[ValidationResult] = []
        self._rule_counter = 0
        self._schema_counter = 0
        self._register_builtin_rules()

    def initialize(self) -> bool:
        """Initialize the validator agent."""
        self._register_builtin_schemas()
        logger.info("validator_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation task."""
        action = task.get("action", "validate")

        if action == "validate":
            return self._validate_data(task)
        elif action == "validate_schema":
            return self._validate_against_schema(task)
        elif action == "create_rule":
            return self._create_rule(task)
        elif action == "create_schema":
            return self._create_schema(task)
        elif action == "batch_validate":
            return self._batch_validate(task)
        elif action == "check_consistency":
            return self._check_consistency(task)
        elif action == "check_completeness":
            return self._check_completeness(task)
        elif action == "audit":
            return self._audit_data(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def validate(
        self,
        data: Any,
        schema_id: Optional[str] = None,
        rules: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Validate data."""
        result = self.execute(
            {"action": "validate", "data": data, "schema_id": schema_id, "rules": rules}
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["validation_result"]

    def _register_builtin_rules(self):
        """Register built-in validation rules."""
        # Type rules
        self._add_rule(
            "required",
            ValidationType.TYPE,
            lambda x: x is not None,
            Severity.ERROR,
            "Field is required",
        )
        self._add_rule(
            "string", ValidationType.TYPE, str, Severity.ERROR, "Must be a string"
        )
        self._add_rule(
            "integer", ValidationType.TYPE, int, Severity.ERROR, "Must be an integer"
        )
        self._add_rule(
            "float", ValidationType.TYPE, float, Severity.ERROR, "Must be a float"
        )
        self._add_rule(
            "boolean", ValidationType.TYPE, bool, Severity.ERROR, "Must be a boolean"
        )
        self._add_rule(
            "list", ValidationType.TYPE, list, Severity.ERROR, "Must be a list"
        )
        self._add_rule(
            "dict", ValidationType.TYPE, dict, Severity.ERROR, "Must be a dictionary"
        )

        # Format rules
        self._add_rule(
            "email",
            ValidationType.PATTERN,
            r"^[\w\.-]+@[\w\.-]+\.\w+$",
            Severity.ERROR,
            "Must be a valid email",
        )
        self._add_rule(
            "url",
            ValidationType.PATTERN,
            r"^https?://[\w\.-]+[\w\.-]+[\w\.-]*$",
            Severity.ERROR,
            "Must be a valid URL",
        )
        self._add_rule(
            "phone",
            ValidationType.PATTERN,
            r"^\+?[\d\s\-\(\)]+$",
            Severity.ERROR,
            "Must be a valid phone number",
        )
        self._add_rule(
            "date",
            ValidationType.PATTERN,
            r"^\d{4}-\d{2}-\d{2}$",
            Severity.ERROR,
            "Must be YYYY-MM-DD format",
        )

        # Range rules
        self._add_rule(
            "positive",
            ValidationType.RANGE,
            {"min": 0},
            Severity.ERROR,
            "Must be positive",
        )
        self._add_rule(
            "percentage",
            ValidationType.RANGE,
            {"min": 0, "max": 100},
            Severity.ERROR,
            "Must be between 0 and 100",
        )

    def _register_builtin_schemas(self):
        """Register built-in validation schemas."""
        # User schema
        user_rules = [self.rules.get("required"), self.rules.get("email")]
        user_rules = [r for r in user_rules if r]

        if user_rules:
            self._create_schema_internal("user", "User validation", user_rules)

        # API request schema
        api_rules = [self.rules.get("required"), self.rules.get("string")]
        api_rules = [r for r in api_rules if r]

        if api_rules:
            self._create_schema_internal(
                "api_request", "API request validation", api_rules
            )

    def _add_rule(
        self,
        name: str,
        type: ValidationType,
        condition: Any,
        severity: Severity,
        message: str,
    ) -> ValidationRule:
        """Add a validation rule."""
        self._rule_counter += 1
        rule = ValidationRule(
            id=f"rule_{self._rule_counter}",
            name=name,
            type=type,
            condition=condition,
            severity=severity,
            message=message,
        )
        self.rules[name] = rule
        return rule

    def _create_schema_internal(
        self, name: str, description: str, rules: List[ValidationRule]
    ) -> ValidationSchema:
        """Create a validation schema internally."""
        self._schema_counter += 1
        schema = ValidationSchema(
            id=f"schema_{self._schema_counter}",
            name=name,
            description=description,
            rules=rules,
        )
        self.schemas[name] = schema
        return schema

    def _validate_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data with rules or schema."""
        data = task.get("data")
        schema_id = task.get("schema_id")
        rule_names = task.get("rules", [])

        if data is None:
            return {"error": "Data is required"}

        # Use schema if provided
        if schema_id and schema_id in self.schemas:
            schema = self.schemas[schema_id]
            result = schema.validate(data)
        else:
            # Use individual rules
            issues = []
            for rule_name in rule_names:
                if rule_name in self.rules:
                    rule = self.rules[rule_name]
                    issue = rule.apply(data)
                    if issue:
                        issues.append(issue)

            result = ValidationResult(
                schema_id="custom",
                valid=len([i for i in issues if i.severity == Severity.ERROR]) == 0,
                issues=issues,
            )

        # Store in history
        self.validation_history.append(result)

        logger.info(
            "validation_completed",
            valid=result.valid,
            issues_count=len(result.issues),
            errors=len(result.get_errors()),
        )

        return {
            "validation_result": result,
            "valid": result.valid,
            "issues": [i.to_dict() for i in result.issues],
        }

    def _validate_against_schema(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against specific schema."""
        data = task.get("data")
        schema_id = task.get("schema_id")

        if data is None:
            return {"error": "Data is required"}

        if not schema_id or schema_id not in self.schemas:
            return {"error": f"Schema {schema_id} not found"}

        schema = self.schemas[schema_id]
        result = schema.validate(data)

        return {"result": result.to_dict(), "valid": result.valid}

    def _create_rule(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new validation rule."""
        name = task.get("name", "")
        type_str = task.get("type", "type")
        condition = task.get("condition")
        severity_str = task.get("severity", "error")
        message = task.get("message", "")

        if not name or condition is None:
            return {"error": "Name and condition are required"}

        type_enum = ValidationType[type_str.upper()]
        severity_enum = Severity[severity_str.upper()]

        rule = self._add_rule(name, type_enum, condition, severity_enum, message)

        return {"rule_id": rule.id, "name": name, "created": True}

    def _create_schema(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new validation schema."""
        name = task.get("name", "")
        description = task.get("description", "")
        rule_names = task.get("rules", [])

        if not name:
            return {"error": "Schema name is required"}

        # Collect rules
        rules = []
        for rule_name in rule_names:
            if rule_name in self.rules:
                rules.append(self.rules[rule_name])
            else:
                logger.warning(f"Rule {rule_name} not found")

        if not rules:
            return {"error": "At least one valid rule is required"}

        schema = self._create_schema_internal(name, description, rules)

        return {"schema_id": schema.id, "name": name, "rules_count": len(rules)}

    def _batch_validate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate multiple data items."""
        data_items = task.get("data_items", [])
        schema_id = task.get("schema_id")

        if not data_items:
            return {"error": "Data items are required"}

        results = []
        valid_count = 0
        total_issues = []

        for i, data in enumerate(data_items):
            result = self._validate_data({"data": data, "schema_id": schema_id})

            if "validation_result" in result:
                validation = result["validation_result"]
                results.append(
                    {
                        "index": i,
                        "valid": validation.valid,
                        "issues_count": len(validation.issues),
                    }
                )

                if validation.valid:
                    valid_count += 1

                total_issues.extend(validation.issues)

        return {
            "results": results,
            "total_items": len(data_items),
            "valid_count": valid_count,
            "invalid_count": len(data_items) - valid_count,
            "total_issues": len(total_issues),
        }

    def _check_consistency(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check data consistency."""
        data = task.get("data")
        rules = task.get("consistency_rules", {})

        if data is None:
            return {"error": "Data is required"}

        issues = []

        # Check for internal consistency
        if isinstance(data, dict):
            # Check for conflicting values
            if "start_date" in data and "end_date" in data:
                if data["start_date"] > data["end_date"]:
                    issues.append(
                        ValidationIssue(
                            rule_id="consistency_dates",
                            field="dates",
                            value=f"{data['start_date']} > {data['end_date']}",
                            severity=Severity.ERROR,
                            message="Start date cannot be after end date",
                        )
                    )

            # Check for dependent fields
            for field, dependency in rules.get("dependencies", {}).items():
                if field in data and dependency not in data:
                    issues.append(
                        ValidationIssue(
                            rule_id="consistency_dependency",
                            field=field,
                            value=data[field],
                            severity=Severity.WARNING,
                            message=f"Field {field} requires {dependency}",
                        )
                    )

        elif isinstance(data, list):
            # Check for duplicate entries
            seen = set()
            for i, item in enumerate(data):
                item_str = str(item)
                if item_str in seen:
                    issues.append(
                        ValidationIssue(
                            rule_id="consistency_duplicate",
                            field=f"item_{i}",
                            value=item,
                            severity=Severity.WARNING,
                            message="Duplicate entry found",
                        )
                    )
                seen.add(item_str)

        return {"consistent": len(issues) == 0, "issues": [i.to_dict() for i in issues]}

    def _check_completeness(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check data completeness."""
        data = task.get("data")
        required_fields = task.get("required_fields", [])

        if data is None:
            return {"error": "Data is required"}

        missing_fields = []
        empty_fields = []

        if isinstance(data, dict):
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                elif data[field] in [None, "", [], {}]:
                    empty_fields.append(field)

        completeness_score = 1.0
        if required_fields:
            present_count = (
                len(required_fields) - len(missing_fields) - len(empty_fields)
            )
            completeness_score = present_count / len(required_fields)

        return {
            "complete": len(missing_fields) == 0 and len(empty_fields) == 0,
            "completeness_score": completeness_score,
            "missing_fields": missing_fields,
            "empty_fields": empty_fields,
        }

    def _audit_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive data audit."""
        data = task.get("data")
        audit_types = task.get(
            "audit_types", ["type", "format", "consistency", "completeness"]
        )

        if data is None:
            return {"error": "Data is required"}

        audit_results = {
            "timestamp": time.time(),
            "data_type": type(data).__name__,
            "checks_performed": [],
        }

        # Type validation
        if "type" in audit_types:
            type_result = self._validate_data({"data": data, "rules": ["required"]})
            audit_results["checks_performed"].append(
                {"check": "type", "passed": type_result.get("valid", False)}
            )

        # Format validation
        if "format" in audit_types and isinstance(data, str):
            # Check various formats
            format_checks = ["email", "url", "date"]
            for format_check in format_checks:
                if format_check in self.rules:
                    rule = self.rules[format_check]
                    issue = rule.apply(data)
                    if not issue:
                        audit_results["detected_format"] = format_check
                        break

        # Consistency check
        if "consistency" in audit_types:
            consistency_result = self._check_consistency({"data": data})
            audit_results["checks_performed"].append(
                {
                    "check": "consistency",
                    "passed": consistency_result.get("consistent", False),
                    "issues": consistency_result.get("issues", []),
                }
            )

        # Completeness check
        if "completeness" in audit_types and isinstance(data, dict):
            completeness_result = self._check_completeness(
                {"data": data, "required_fields": list(data.keys())}  # Check all fields
            )
            audit_results["checks_performed"].append(
                {
                    "check": "completeness",
                    "passed": completeness_result.get("complete", False),
                    "score": completeness_result.get("completeness_score", 0),
                }
            )

        # Calculate overall audit score
        passed_checks = sum(
            1
            for check in audit_results["checks_performed"]
            if check.get("passed", False)
        )
        total_checks = len(audit_results["checks_performed"])
        audit_results["audit_score"] = (
            passed_checks / total_checks if total_checks > 0 else 0
        )

        return {"audit_results": audit_results}

    def shutdown(self) -> bool:
        """Shutdown the validator agent."""
        logger.info(
            "validator_agent_shutdown",
            schemas_count=len(self.schemas),
            rules_count=len(self.rules),
            validations_performed=len(self.validation_history),
        )
        self.schemas.clear()
        self.rules.clear()
        self.validation_history.clear()
        return True
