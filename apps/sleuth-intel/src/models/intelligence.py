"""
Intelligence data models for Sleuth Intel
Contains wrapper classes for intelligence results, confidence scoring, and data correlation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field, field_validator

from .business import BusinessProfile
from .person import PersonProfile

# Generic type for intelligence results
T = TypeVar("T", PersonProfile, BusinessProfile)


class ConfidenceLevel(str, Enum):
    """Confidence level classifications"""

    VERY_HIGH = "very_high"  # 0.9 - 1.0
    HIGH = "high"  # 0.7 - 0.89
    MEDIUM = "medium"  # 0.5 - 0.69
    LOW = "low"  # 0.3 - 0.49
    VERY_LOW = "very_low"  # 0.0 - 0.29


class DataSource(BaseModel):
    """Data source attribution"""

    provider: str = Field(..., description="Source provider name")
    dataset: Optional[str] = Field(None, description="Specific dataset name")
    query_method: str = Field(..., description="Query method used")
    query_params: Dict[str, Any] = Field(..., description="Query parameters")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    cost: Optional[float] = Field(None, description="Query cost if applicable")

    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Query timestamp"
    )
    rate_limit_remaining: Optional[int] = Field(
        None, description="Rate limit remaining"
    )

    # Quality indicators
    data_freshness: Optional[str] = Field(None, description="How recent the data is")
    completeness: float = Field(
        0.0, ge=0.0, le=1.0, description="Data completeness score"
    )
    reliability: float = Field(
        0.0, ge=0.0, le=1.0, description="Source reliability score"
    )


class ConfidenceScoring(BaseModel):
    """Confidence scoring breakdown"""

    overall_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score"
    )
    level: ConfidenceLevel = Field(
        ConfidenceLevel.LOW, description="Confidence level classification"
    )

    # Component scores
    data_quality: float = Field(
        0.0, ge=0.0, le=1.0, description="Quality of source data"
    )
    data_recency: float = Field(
        0.0, ge=0.0, le=1.0, description="How recent the data is"
    )
    source_reliability: float = Field(
        0.0, ge=0.0, le=1.0, description="Reliability of source"
    )
    cross_validation: float = Field(
        0.0, ge=0.0, le=1.0, description="Cross-validation score"
    )
    completeness: float = Field(0.0, ge=0.0, le=1.0, description="Data completeness")

    # Scoring explanation
    scoring_factors: Dict[str, Any] = Field(
        default_factory=dict, description="Factors affecting score"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Data quality warnings"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Set confidence level based on overall score
        score = self.overall_score
        if score >= 0.9:
            self.level = ConfidenceLevel.VERY_HIGH
        elif score >= 0.7:
            self.level = ConfidenceLevel.HIGH
        elif score >= 0.5:
            self.level = ConfidenceLevel.MEDIUM
        elif score >= 0.3:
            self.level = ConfidenceLevel.LOW
        else:
            self.level = ConfidenceLevel.VERY_LOW


class DataCorrelation(BaseModel):
    """Data correlation and cross-referencing"""

    matched_fields: List[str] = Field(
        default_factory=list, description="Fields that matched across sources"
    )
    conflicting_fields: List[str] = Field(
        default_factory=list, description="Fields with conflicting data"
    )

    # Cross-reference results
    phone_matches: int = Field(0, description="Number of phone cross-matches")
    address_matches: int = Field(0, description="Number of address cross-matches")
    name_matches: int = Field(0, description="Number of name cross-matches")
    email_matches: int = Field(0, description="Number of email cross-matches")

    # Related entities
    related_people: List[str] = Field(
        default_factory=list, description="Related person IDs"
    )
    related_businesses: List[str] = Field(
        default_factory=list, description="Related business IDs"
    )

    correlation_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Overall correlation confidence"
    )


class ValidationResult(BaseModel):
    """Data validation results"""

    is_valid: bool = Field(..., description="Whether data passed validation")
    validation_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Validation confidence score"
    )

    # Validation details
    phone_validation: Optional[bool] = Field(
        None, description="Phone number validation result"
    )
    email_validation: Optional[bool] = Field(
        None, description="Email validation result"
    )
    address_validation: Optional[bool] = Field(
        None, description="Address validation result"
    )

    validation_errors: List[str] = Field(
        default_factory=list, description="Validation errors"
    )
    validation_warnings: List[str] = Field(
        default_factory=list, description="Validation warnings"
    )


class QueryMetadata(BaseModel):
    """Query execution metadata"""

    query_id: str = Field(..., description="Unique query identifier")
    query_type: str = Field(..., description="Type of intelligence query")
    original_query: Dict[str, Any] = Field(..., description="Original query parameters")

    execution_time: float = Field(..., description="Total execution time")
    sources_queried: int = Field(..., description="Number of sources queried")
    sources_successful: int = Field(
        ..., description="Number of successful source queries"
    )

    # Performance metrics
    cache_hit: bool = Field(False, description="Whether result was cached")
    rate_limited: bool = Field(
        False, description="Whether any queries were rate limited"
    )
    errors_encountered: List[str] = Field(
        default_factory=list, description="Errors during query"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Query execution timestamp"
    )


class IntelligenceResult(BaseModel, Generic[T]):
    """Generic intelligence result wrapper"""

    # Core result data
    data: Optional[T] = Field(None, description="Primary intelligence result")
    additional_results: List[T] = Field(
        default_factory=list, description="Additional/related results"
    )

    # Quality and confidence
    confidence: ConfidenceScoring = Field(
        ..., description="Confidence scoring breakdown"
    )
    validation: Optional[ValidationResult] = Field(
        None, description="Data validation results"
    )
    correlation: Optional[DataCorrelation] = Field(
        None, description="Data correlation analysis"
    )

    # Source attribution
    sources: List[DataSource] = Field(..., description="Data sources used")
    primary_source: str = Field(..., description="Primary data source")

    # Query information
    query_metadata: QueryMetadata = Field(..., description="Query execution metadata")

    # Processing information
    processed_by: str = Field("sleuth-intel", description="Processing system")
    processing_version: str = Field("1.0", description="Processing version")

    @property
    def has_data(self) -> bool:
        """Check if result contains any data"""
        return self.data is not None or len(self.additional_results) > 0

    @property
    def is_reliable(self) -> bool:
        """Check if result is considered reliable (high confidence)"""
        return self.confidence.level in [
            ConfidenceLevel.HIGH,
            ConfidenceLevel.VERY_HIGH,
        ]

    @property
    def total_sources(self) -> int:
        """Get total number of sources"""
        return len(self.sources)

    @property
    def successful_sources(self) -> int:
        """Get number of successful sources"""
        return self.query_metadata.sources_successful

    def add_source(self, source: DataSource) -> None:
        """Add a data source"""
        self.sources.append(source)

    def add_warning(self, warning: str) -> None:
        """Add a confidence warning"""
        if warning not in self.confidence.warnings:
            self.confidence.warnings.append(warning)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Return summarized result for display"""
        return {
            "has_data": self.has_data,
            "confidence_level": self.confidence.level.value,
            "confidence_score": self.confidence.overall_score,
            "total_sources": self.total_sources,
            "successful_sources": self.successful_sources,
            "execution_time": self.query_metadata.execution_time,
            "is_reliable": self.is_reliable,
            "data_age": self.sources[0].data_freshness if self.sources else None,
            "warnings": self.confidence.warnings,
            "query_type": self.query_metadata.query_type,
        }


# Specialized result types
class PersonIntelligenceResult(IntelligenceResult[PersonProfile]):
    """Intelligence result specifically for person data"""

    @property
    def person(self) -> Optional[PersonProfile]:
        """Get the person profile"""
        return self.data

    @property
    def related_people(self) -> List[PersonProfile]:
        """Get related person profiles"""
        return self.additional_results


class BusinessIntelligenceResult(IntelligenceResult[BusinessProfile]):
    """Intelligence result specifically for business data"""

    @property
    def business(self) -> Optional[BusinessProfile]:
        """Get the business profile"""
        return self.data

    @property
    def related_businesses(self) -> List[BusinessProfile]:
        """Get related business profiles"""
        return self.additional_results


class ComprehensiveIntelligenceResult(BaseModel):
    """Combined intelligence result containing both person and business data"""

    person_results: List[PersonIntelligenceResult] = Field(
        default_factory=list, description="Person intelligence results"
    )
    business_results: List[BusinessIntelligenceResult] = Field(
        default_factory=list, description="Business intelligence results"
    )

    # Cross-entity relationships
    person_business_connections: List[Dict[str, Any]] = Field(
        default_factory=list, description="Person-business relationships"
    )

    # Overall analysis
    overall_confidence: ConfidenceScoring = Field(
        ..., description="Overall confidence across all results"
    )
    query_metadata: QueryMetadata = Field(..., description="Overall query metadata")

    @property
    def has_person_data(self) -> bool:
        """Check if has person data"""
        return len(self.person_results) > 0 and any(
            r.has_data for r in self.person_results
        )

    @property
    def has_business_data(self) -> bool:
        """Check if has business data"""
        return len(self.business_results) > 0 and any(
            r.has_data for r in self.business_results
        )

    @property
    def primary_person(self) -> Optional[PersonProfile]:
        """Get primary person result"""
        for result in self.person_results:
            if result.has_data and result.is_reliable:
                return result.person
        return None

    @property
    def primary_business(self) -> Optional[BusinessProfile]:
        """Get primary business result"""
        for result in self.business_results:
            if result.has_data and result.is_reliable:
                return result.business
        return None

    def to_summary_dict(self) -> Dict[str, Any]:
        """Return comprehensive summary"""
        return {
            "has_person_data": self.has_person_data,
            "has_business_data": self.has_business_data,
            "person_results": len(self.person_results),
            "business_results": len(self.business_results),
            "connections": len(self.person_business_connections),
            "overall_confidence": self.overall_confidence.overall_score,
            "confidence_level": self.overall_confidence.level.value,
            "execution_time": self.query_metadata.execution_time,
            "total_sources": sum(
                len(r.sources) for r in self.person_results + self.business_results
            ),
            "query_type": self.query_metadata.query_type,
        }
