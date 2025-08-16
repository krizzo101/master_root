"""
Validation Data Models

Enums and dataclasses for request validation system.
Extracted from request_validation.py for better modularity.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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
    default: Optional[Any] = None
    validation_pattern: Optional[str] = None


@dataclass
class RequestSchema:
    """Schema definition for a specific request type."""

    request_type: RequestType
    description: str
    fields: List[RequestField]

    def get_required_fields(self) -> List[RequestField]:
        """Get all required fields for this schema."""
        return [field for field in self.fields if field.required]

    def get_optional_fields(self) -> List[RequestField]:
        """Get all optional fields for this schema."""
        return [field for field in self.fields if not field.required]


@dataclass
class ValidationResult:
    """Result of request validation process."""

    request_type: RequestType
    is_valid: bool
    missing_fields: List[str]
    extracted_info: Dict[str, Any]
    confidence: float
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class InformationGap:
    """Represents a gap in request information."""

    field_name: str
    priority: GapPriority
    description: str
    researchable: bool
    suggested_defaults: List[Any] = field(default_factory=list)
    research_keywords: List[str] = field(default_factory=list)


@dataclass
class GapAnalysisResult:
    """Result of gap analysis process."""

    gaps: List[InformationGap]
    confidence: float
    completeness_score: float
    critical_gaps_count: int
    researchable_gaps: List[InformationGap] = field(default_factory=list)
    unresearchable_gaps: List[InformationGap] = field(default_factory=list)


@dataclass
class CompletionResult:
    """Result of information completion process."""

    filled_fields: Dict[str, Any]
    applied_defaults: Dict[str, Any]
    research_results: Dict[str, Any]
    assumptions: List[str]
    escalation_required: bool
    critical_gaps_remaining: List[str]


@dataclass
class ClarificationQuestion:
    """A focused question for user clarification."""

    field_name: str
    question: str
    importance_explanation: str
    options: List[str] = field(default_factory=list)
    default_option: Optional[str] = None
