"""
Data models and schemas for Sleuth Intel
"""

# Business models
from .business import (
    BusinessLocation,
    BusinessProfile,
    BusinessStatus,
    EntityType,
    Filing,
    FinancialData,
    IndustryClassification,
    License,
    Principal,
    Registration,
)

# Intelligence models
from .intelligence import (
    BusinessIntelligenceResult,
    ComprehensiveIntelligenceResult,
    ConfidenceLevel,
    ConfidenceScoring,
    DataCorrelation,
    DataSource,
    IntelligenceResult,
    PersonIntelligenceResult,
    QueryMetadata,
    ValidationResult,
)

# Person models
from .person import (
    Address,
    AddressType,
    Associate,
    Demographics,
    Email,
    PersonName,
    PersonProfile,
    Phone,
    PhoneType,
)

# Query models
from .query import (
    AddressLookupQuery,
    BaseQuery,
    BusinessSearchQuery,
    CacheStrategy,
    ComprehensiveSearchQuery,
    DataProvider,
    EmailLookupQuery,
    IdentityVerificationQuery,
    PersonSearchQuery,
    PhoneLookupQuery,
    QueryOptimizer,
    QueryPriority,
    QueryType,
)

__all__ = [
    # Person models
    "PhoneType",
    "AddressType",
    "Phone",
    "Address",
    "Email",
    "PersonName",
    "Demographics",
    "Associate",
    "PersonProfile",
    # Business models
    "BusinessStatus",
    "EntityType",
    "IndustryClassification",
    "Principal",
    "Filing",
    "Registration",
    "License",
    "FinancialData",
    "BusinessLocation",
    "BusinessProfile",
    # Intelligence models
    "ConfidenceLevel",
    "DataSource",
    "ConfidenceScoring",
    "DataCorrelation",
    "ValidationResult",
    "QueryMetadata",
    "IntelligenceResult",
    "PersonIntelligenceResult",
    "BusinessIntelligenceResult",
    "ComprehensiveIntelligenceResult",
    # Query models
    "QueryType",
    "DataProvider",
    "QueryPriority",
    "CacheStrategy",
    "BaseQuery",
    "PersonSearchQuery",
    "BusinessSearchQuery",
    "PhoneLookupQuery",
    "EmailLookupQuery",
    "AddressLookupQuery",
    "IdentityVerificationQuery",
    "ComprehensiveSearchQuery",
    "QueryOptimizer",
]
