"""
Query parameter models for Sleuth Intel
Contains query classes for different intelligence types with validation and optimization
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, field_validator


class QueryType(str, Enum):
    """Types of intelligence queries"""

    PERSON_SEARCH = "person_search"
    BUSINESS_SEARCH = "business_search"
    PHONE_LOOKUP = "phone_lookup"
    EMAIL_LOOKUP = "email_lookup"
    ADDRESS_LOOKUP = "address_lookup"
    IDENTITY_VERIFICATION = "identity_verification"
    COMPREHENSIVE_SEARCH = "comprehensive_search"


class DataProvider(str, Enum):
    """Available data providers"""

    ENFORMION = "enformion"
    LEXISNEXIS = "lexisnexis"
    WHITEPAGES = "whitepages"
    PIPL = "pipl"
    CLEARBIT = "clearbit"
    ALL = "all"  # Query all available providers


class QueryPriority(str, Enum):
    """Query execution priority"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CacheStrategy(str, Enum):
    """Cache usage strategy"""

    USE_CACHE = "use_cache"  # Use cache if available
    REFRESH_CACHE = "refresh_cache"  # Force refresh cache
    NO_CACHE = "no_cache"  # Don't use cache at all


class BaseQuery(BaseModel):
    """Base query parameters"""

    query_id: Optional[str] = Field(None, description="Unique query identifier")
    priority: QueryPriority = Field(
        QueryPriority.NORMAL, description="Query execution priority"
    )

    # Provider selection
    providers: List[DataProvider] = Field(
        [DataProvider.ALL], description="Data providers to query"
    )
    max_providers: int = Field(
        3, ge=1, le=10, description="Maximum providers to query simultaneously"
    )

    # Cache and performance
    cache_strategy: CacheStrategy = Field(
        CacheStrategy.USE_CACHE, description="Cache usage strategy"
    )
    timeout: int = Field(30, ge=5, le=300, description="Query timeout in seconds")

    # Quality controls
    min_confidence: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
    require_validation: bool = Field(False, description="Require data validation")

    # Cost controls
    max_cost: Optional[float] = Field(None, description="Maximum query cost")
    cost_estimate: bool = Field(False, description="Return cost estimate only")

    # Result controls
    max_results: int = Field(10, ge=1, le=100, description="Maximum results to return")
    include_raw_data: bool = Field(False, description="Include raw API responses")

    # Metadata
    requested_by: Optional[str] = Field(
        None, description="User/system requesting query"
    )
    tags: List[str] = Field(
        default_factory=list, description="Query tags for organization"
    )


class PersonSearchQuery(BaseQuery):
    """Person search query parameters"""

    # Name parameters
    first_name: Optional[str] = Field(None, min_length=1, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name or initial")
    full_name: Optional[str] = Field(None, description="Full name as single string")
    aliases: List[str] = Field(default_factory=list, description="Known aliases")

    # Contact parameters
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")

    # Address parameters
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State abbreviation")
    zip_code: Optional[str] = Field(None, description="ZIP code")

    # Demographic filters
    age_min: Optional[int] = Field(None, ge=18, le=120, description="Minimum age")
    age_max: Optional[int] = Field(None, ge=18, le=120, description="Maximum age")

    # Search options
    fuzzy_matching: bool = Field(True, description="Enable fuzzy name matching")
    include_relatives: bool = Field(False, description="Include relatives in results")
    include_associates: bool = Field(False, description="Include associates in results")
    historical_addresses: bool = Field(
        False, description="Include historical addresses"
    )

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Ensure state is uppercase 2-letter code"""
        if v:
            v = v.upper().strip()
            if len(v) != 2:
                raise ValueError("State must be 2-letter abbreviation")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """Clean phone number"""
        if v:
            # Remove all non-digits
            cleaned = "".join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError("Phone number must have at least 10 digits")
            return cleaned
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        """Validate ZIP code"""
        if v:
            v = v.strip()
            if not v.replace("-", "").isdigit():
                raise ValueError("ZIP code must contain only digits and hyphens")
        return v

    def has_sufficient_params(self) -> bool:
        """Check if query has sufficient parameters for execution"""
        name_params = sum(
            [bool(self.first_name), bool(self.last_name), bool(self.full_name)]
        )

        contact_params = sum([bool(self.phone), bool(self.email)])

        address_params = sum(
            [
                bool(self.street and self.city),
                bool(self.city and self.state),
                bool(self.zip_code),
            ]
        )

        # Need at least one name param + one other identifying param
        return name_params >= 1 and (contact_params >= 1 or address_params >= 1)


class BusinessSearchQuery(BaseQuery):
    """Business search query parameters"""

    # Business name parameters
    business_name: Optional[str] = Field(
        None, min_length=2, description="Business name"
    )
    dba_name: Optional[str] = Field(None, description="Doing business as name")
    trade_name: Optional[str] = Field(None, description="Trade name")

    # Contact parameters
    phone: Optional[str] = Field(None, description="Business phone number")
    website: Optional[str] = Field(None, description="Business website")
    email: Optional[EmailStr] = Field(None, description="Business email")

    # Address parameters
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State abbreviation")
    zip_code: Optional[str] = Field(None, description="ZIP code")

    # Business identifiers
    ein: Optional[str] = Field(None, description="Federal EIN")
    entity_id: Optional[str] = Field(None, description="State entity ID")
    registration_number: Optional[str] = Field(None, description="Registration number")

    # Industry and classification
    industry: Optional[str] = Field(None, description="Industry type")
    naics_code: Optional[str] = Field(None, description="NAICS code")
    sic_code: Optional[str] = Field(None, description="SIC code")

    # Business filters
    entity_type: Optional[str] = Field(
        None, description="Entity type (LLC, Corp, etc.)"
    )
    status: Optional[str] = Field(None, description="Business status filter")
    min_employees: Optional[int] = Field(
        None, ge=1, description="Minimum employee count"
    )
    max_employees: Optional[int] = Field(
        None, ge=1, description="Maximum employee count"
    )

    # Search options
    fuzzy_matching: bool = Field(True, description="Enable fuzzy name matching")
    include_principals: bool = Field(False, description="Include business principals")
    include_subsidiaries: bool = Field(
        False, description="Include subsidiary information"
    )
    include_filings: bool = Field(False, description="Include legal filings")

    @field_validator("ein")
    @classmethod
    def validate_ein(cls, v):
        """Validate EIN format"""
        if v:
            # Remove any formatting
            ein = "".join(filter(str.isdigit, v))
            if len(ein) != 9:
                raise ValueError("EIN must be 9 digits")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """Clean phone number"""
        if v:
            cleaned = "".join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError("Phone number must have at least 10 digits")
            return cleaned
        return v

    def has_sufficient_params(self) -> bool:
        """Check if query has sufficient parameters"""
        business_params = sum(
            [bool(self.business_name), bool(self.dba_name), bool(self.trade_name)]
        )

        identifier_params = sum(
            [bool(self.ein), bool(self.entity_id), bool(self.registration_number)]
        )

        contact_params = sum([bool(self.phone), bool(self.email), bool(self.website)])

        address_params = sum([bool(self.city and self.state), bool(self.zip_code)])

        # Need business name OR identifier + location info
        return (business_params >= 1 or identifier_params >= 1) and (
            address_params >= 1 or contact_params >= 1
        )


class PhoneLookupQuery(BaseQuery):
    """Phone number lookup query"""

    phone_number: str = Field(..., min_length=10, description="Phone number to lookup")

    # Lookup options
    include_caller_id: bool = Field(True, description="Include caller ID information")
    include_owner_details: bool = Field(True, description="Include phone owner details")
    include_line_type: bool = Field(True, description="Include line type information")
    include_carrier: bool = Field(True, description="Include carrier information")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        """Clean and validate phone number"""
        cleaned = "".join(filter(str.isdigit, v))
        if len(cleaned) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return cleaned


class EmailLookupQuery(BaseQuery):
    """Email address lookup query"""

    email_address: EmailStr = Field(..., description="Email address to lookup")

    # Lookup options
    include_social_profiles: bool = Field(
        False, description="Include social media profiles"
    )
    include_breach_data: bool = Field(
        False, description="Include data breach information"
    )
    include_reputation: bool = Field(False, description="Include email reputation")


class AddressLookupQuery(BaseQuery):
    """Address lookup query"""

    # Address components
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    full_address: Optional[str] = Field(None, description="Full address as string")

    # Lookup options
    include_residents: bool = Field(True, description="Include resident information")
    include_property_data: bool = Field(
        False, description="Include property information"
    )
    include_demographics: bool = Field(False, description="Include area demographics")

    def has_sufficient_params(self) -> bool:
        """Check if has sufficient address parameters"""
        if self.full_address:
            return True

        return bool(
            (self.street and self.city)
            or (self.city and self.state)
            or bool(self.zip_code)
        )


class IdentityVerificationQuery(BaseQuery):
    """Identity verification query"""

    # Required identity information
    first_name: str = Field(..., min_length=1, description="First name")
    last_name: str = Field(..., min_length=1, description="Last name")

    # Verification data points
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Address")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    ssn_last4: Optional[str] = Field(None, description="Last 4 digits of SSN")

    # Verification options
    strict_matching: bool = Field(False, description="Require exact matches")
    allow_partial_matches: bool = Field(True, description="Allow partial matches")

    @field_validator("ssn_last4")
    @classmethod
    def validate_ssn_last4(cls, v):
        """Validate SSN last 4 digits"""
        if v:
            if not v.isdigit() or len(v) != 4:
                raise ValueError("SSN last 4 must be exactly 4 digits")
        return v


class ComprehensiveSearchQuery(BaseQuery):
    """Comprehensive multi-type search query"""

    # All possible search parameters
    person_query: Optional[PersonSearchQuery] = Field(
        None, description="Person search parameters"
    )
    business_query: Optional[BusinessSearchQuery] = Field(
        None, description="Business search parameters"
    )
    phone_query: Optional[PhoneLookupQuery] = Field(
        None, description="Phone lookup parameters"
    )
    email_query: Optional[EmailLookupQuery] = Field(
        None, description="Email lookup parameters"
    )
    address_query: Optional[AddressLookupQuery] = Field(
        None, description="Address lookup parameters"
    )

    # Cross-reference options
    find_connections: bool = Field(True, description="Find connections between results")
    correlation_threshold: float = Field(
        0.5, ge=0.0, le=1.0, description="Correlation threshold"
    )

    def has_any_query(self) -> bool:
        """Check if has any query parameters"""
        return any(
            [
                self.person_query,
                self.business_query,
                self.phone_query,
                self.email_query,
                self.address_query,
            ]
        )


# Query optimization helpers
class QueryOptimizer:
    """Helper class for query optimization"""

    @staticmethod
    def optimize_person_query(query: PersonSearchQuery) -> PersonSearchQuery:
        """Optimize person search query for better results"""
        optimized = query.copy()

        # If we have full name but not first/last, try to split
        if optimized.full_name and not (optimized.first_name or optimized.last_name):
            parts = optimized.full_name.strip().split()
            if len(parts) >= 2:
                optimized.first_name = parts[0]
                optimized.last_name = parts[-1]
                if len(parts) > 2:
                    optimized.middle_name = " ".join(parts[1:-1])

        # Adjust provider selection based on available data
        if optimized.phone and not optimized.email:
            # Phone-based searches work better with certain providers
            if DataProvider.ALL in optimized.providers:
                optimized.providers = [DataProvider.ENFORMION, DataProvider.WHITEPAGES]

        return optimized

    @staticmethod
    def estimate_query_cost(query: BaseQuery) -> Dict[str, Any]:
        """Estimate query cost and execution time"""
        base_cost = 0.10  # Base cost per provider
        provider_count = (
            len(query.providers) if DataProvider.ALL not in query.providers else 3
        )

        estimated_cost = base_cost * provider_count
        estimated_time = 2.0 * provider_count  # 2 seconds per provider

        return {
            "estimated_cost": estimated_cost,
            "estimated_time": estimated_time,
            "provider_count": provider_count,
            "confidence_adjustment": query.min_confidence,
        }


# General Intelligence Query Class for Workflow Templates
class IntelligenceQuery(BaseModel):
    """General intelligence query for workflow orchestration"""

    query_type: QueryType = Field(description="Type of intelligence query")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Query parameters"
    )
    priority: QueryPriority = Field(QueryPriority.NORMAL, description="Query priority")
    providers: List[DataProvider] = Field(
        [DataProvider.ALL], description="Data providers"
    )
    cache_strategy: CacheStrategy = Field(
        CacheStrategy.USE_CACHE, description="Cache strategy"
    )
    timeout: int = Field(30, ge=5, le=300, description="Query timeout in seconds")
    max_cost: Optional[float] = Field(None, description="Maximum cost")

    def to_specific_query(self) -> BaseQuery:
        """Convert to specific query type based on query_type"""

        query_classes = {
            QueryType.PERSON_SEARCH: PersonSearchQuery,
            QueryType.BUSINESS_SEARCH: BusinessSearchQuery,
            QueryType.PHONE_LOOKUP: PhoneLookupQuery,
            QueryType.EMAIL_LOOKUP: EmailLookupQuery,
            QueryType.ADDRESS_LOOKUP: AddressLookupQuery,
            QueryType.IDENTITY_VERIFICATION: IdentityVerificationQuery,
            QueryType.COMPREHENSIVE_SEARCH: ComprehensiveSearchQuery,
        }

        query_class = query_classes.get(self.query_type)
        if not query_class:
            raise ValueError(f"Unknown query type: {self.query_type}")

        # Build query parameters
        query_params = {
            "priority": self.priority,
            "providers": self.providers,
            "cache_strategy": self.cache_strategy,
            "timeout": self.timeout,
            "max_cost": self.max_cost,
        }

        # Add specific parameters
        query_params.update(self.parameters)

        return query_class(**query_params)
