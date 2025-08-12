"""
Validation Data Models

Enums and dataclasses for request validation system.
Extracted from request_validation.py for better modularity.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RequestType(str, Enum):
    """Types of requests that can be processed."""

    WEB_APPLICATION = "web_application"
    MICROSERVICES = "microservices"
    SIMPLE_SCRIPT = "simple_script"
    DATA_ANALYSIS = "data_analysis"
    AUTOMATION = "automation"
    UNKNOWN = "unknown"


class GapPriority(str, Enum):
    """Priority levels for missing information gaps."""

    CRITICAL = "critical"
    IMPORTANT = "important"
    OPTIONAL = "optional"


@dataclass
class RequestField:
    """Definition of a field in a request schema."""

    name: str
    description: str
    field_type: type
    required: bool = True
    default: Any | None = None
    validation_pattern: str | None = None


@dataclass
class RequestSchema:
    """Schema definition for a specific request type."""

    request_type: RequestType
    description: str
    fields: list[RequestField]

    def get_required_fields(self) -> list[RequestField]:
        """Get all required fields for this schema."""
        return [field for field in self.fields if field.required]

    def get_optional_fields(self) -> list[RequestField]:
        """Get all optional fields for this schema."""
        return [field for field in self.fields if not field.required]


@dataclass
class ValidationResult:
    """Result of request validation process."""

    request_type: RequestType
    is_valid: bool
    missing_fields: list[str]
    extracted_info: dict[str, Any]
    confidence: float
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class InformationGap:
    """Represents a gap in request information."""

    field_name: str
    priority: GapPriority
    description: str
    researchable: bool
    suggested_defaults: list[Any] = field(default_factory=list)
    research_keywords: list[str] = field(default_factory=list)


@dataclass
class GapAnalysisResult:
    """Result of gap analysis process."""

    gaps: list[InformationGap]
    confidence: float
    completeness_score: float
    critical_gaps_count: int
    researchable_gaps: list[InformationGap] = field(default_factory=list)
    unresearchable_gaps: list[InformationGap] = field(default_factory=list)


@dataclass
class CompletionResult:
    """Result of information completion process."""

    filled_fields: dict[str, Any]
    applied_defaults: dict[str, Any]
    research_results: dict[str, Any]
    assumptions: list[str]
    escalation_required: bool
    critical_gaps_remaining: list[str]


@dataclass
class ClarificationQuestion:
    """A focused question for user clarification."""

    field_name: str
    question: str
    importance_explanation: str
    options: list[str] = field(default_factory=list)
    default_option: str | None = None
