"""
Business data models for Sleuth Intel
Contains models for business profiles, filings, registrations, and corporate data
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from .person import Address, Email, PersonName, Phone


class BusinessStatus(str, Enum):
    """Business registration status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DISSOLVED = "dissolved"
    MERGED = "merged"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """Business entity types"""

    CORPORATION = "corporation"
    LLC = "llc"
    PARTNERSHIP = "partnership"
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"
    UNKNOWN = "unknown"


class IndustryClassification(BaseModel):
    """Industry classification codes"""

    naics_code: Optional[str] = Field(None, description="NAICS industry code")
    naics_description: Optional[str] = Field(
        None, description="NAICS industry description"
    )
    sic_code: Optional[str] = Field(None, description="SIC industry code")
    sic_description: Optional[str] = Field(None, description="SIC industry description")
    primary_industry: Optional[str] = Field(
        None, description="Primary industry category"
    )


class Principal(BaseModel):
    """Business principal/officer/owner"""

    name: PersonName = Field(..., description="Principal's name")
    title: Optional[str] = Field(None, description="Title/position")
    role: Optional[str] = Field(None, description="Role in business")
    ownership_percentage: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Ownership percentage"
    )
    start_date: Optional[datetime] = Field(None, description="Date when role started")
    end_date: Optional[datetime] = Field(None, description="Date when role ended")
    is_current: bool = Field(True, description="Whether this is a current role")

    # Contact info for principal
    address: Optional[Address] = Field(None, description="Principal's address")
    phone: Optional[Phone] = Field(None, description="Principal's phone")
    email: Optional[Email] = Field(None, description="Principal's email")

    confidence_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence in data accuracy"
    )


class Filing(BaseModel):
    """Business filing record"""

    filing_type: str = Field(..., description="Type of filing")
    filing_date: Optional[datetime] = Field(None, description="Date of filing")
    document_number: Optional[str] = Field(None, description="Document/case number")
    filing_state: Optional[str] = Field(None, description="State where filed")
    description: Optional[str] = Field(None, description="Filing description")
    status: Optional[str] = Field(None, description="Filing status")
    amount: Optional[float] = Field(None, description="Filing amount if applicable")

    # Document links
    document_url: Optional[str] = Field(None, description="URL to filing document")
    source_url: Optional[str] = Field(None, description="URL to source record")


class Registration(BaseModel):
    """Business registration information"""

    registration_number: Optional[str] = Field(None, description="Registration number")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    federal_ein: Optional[str] = Field(None, description="Federal EIN")
    state_id: Optional[str] = Field(None, description="State ID number")

    registration_date: Optional[datetime] = Field(None, description="Date registered")
    expiration_date: Optional[datetime] = Field(
        None, description="Registration expiration"
    )
    renewal_date: Optional[datetime] = Field(None, description="Next renewal date")

    registered_state: Optional[str] = Field(None, description="State of registration")
    registered_agent: Optional[str] = Field(None, description="Registered agent name")
    registered_address: Optional[Address] = Field(
        None, description="Registered address"
    )

    status: BusinessStatus = Field(
        BusinessStatus.UNKNOWN, description="Registration status"
    )

    @field_validator("federal_ein")
    @classmethod
    def validate_ein(cls, v):
        """Validate EIN format"""
        if v:
            # Remove any formatting
            ein = "".join(filter(str.isdigit, v))
            if len(ein) != 9:
                raise ValueError("EIN must be 9 digits")
            # Format as XX-XXXXXXX
            return f"{ein[:2]}-{ein[2:]}"
        return v


class License(BaseModel):
    """Business license information"""

    license_type: str = Field(..., description="Type of license")
    license_number: Optional[str] = Field(None, description="License number")
    issuing_authority: Optional[str] = Field(None, description="Issuing authority")
    issue_date: Optional[datetime] = Field(None, description="Issue date")
    expiration_date: Optional[datetime] = Field(None, description="Expiration date")
    status: Optional[str] = Field(None, description="License status")

    @property
    def is_expired(self) -> bool:
        """Check if license is expired"""
        if self.expiration_date:
            return self.expiration_date < datetime.utcnow()
        return False


class FinancialData(BaseModel):
    """Business financial information"""

    annual_revenue: Optional[float] = Field(None, description="Annual revenue")
    revenue_range: Optional[str] = Field(None, description="Revenue range")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    employee_range: Optional[str] = Field(None, description="Employee count range")
    credit_rating: Optional[str] = Field(None, description="Business credit rating")

    # Financial events
    bankruptcy_filed: bool = Field(False, description="Has bankruptcy been filed")
    bankruptcy_date: Optional[datetime] = Field(
        None, description="Bankruptcy filing date"
    )
    liens: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tax liens and judgments"
    )


class BusinessLocation(BaseModel):
    """Business location with operational details"""

    address: Address = Field(..., description="Location address")
    location_type: str = Field("primary", description="Type of location")
    is_headquarters: bool = Field(False, description="Whether this is headquarters")
    is_active: bool = Field(True, description="Whether location is active")

    # Operational details
    phone: Optional[Phone] = Field(None, description="Location phone")
    fax: Optional[str] = Field(None, description="Fax number")
    website: Optional[str] = Field(None, description="Website URL")
    hours: Optional[str] = Field(None, description="Operating hours")

    # Facility details
    square_footage: Optional[int] = Field(None, description="Facility size")
    property_type: Optional[str] = Field(None, description="Property type")
    year_established: Optional[int] = Field(
        None, description="Year established at location"
    )


class BusinessProfile(BaseModel):
    """Complete business profile from intelligence gathering"""

    # Core business identity
    business_name: str = Field(..., description="Primary business name")
    dba_names: List[str] = Field(
        default_factory=list, description="Doing business as names"
    )
    trade_names: List[str] = Field(default_factory=list, description="Trade names")
    former_names: List[str] = Field(
        default_factory=list, description="Previous business names"
    )

    # Entity information
    entity_type: EntityType = Field(
        EntityType.UNKNOWN, description="Business entity type"
    )
    industry: Optional[IndustryClassification] = Field(
        None, description="Industry classification"
    )
    description: Optional[str] = Field(None, description="Business description")

    # Contact information
    locations: List[BusinessLocation] = Field(
        default_factory=list, description="Business locations"
    )
    phones: List[Phone] = Field(default_factory=list, description="Phone numbers")
    emails: List[Email] = Field(default_factory=list, description="Email addresses")
    website: Optional[str] = Field(None, description="Primary website")
    social_media: Dict[str, str] = Field(
        default_factory=dict, description="Social media profiles"
    )

    # Legal and registration
    registration: Optional[Registration] = Field(
        None, description="Registration details"
    )
    licenses: List[License] = Field(
        default_factory=list, description="Business licenses"
    )
    filings: List[Filing] = Field(default_factory=list, description="Legal filings")

    # People and relationships
    principals: List[Principal] = Field(
        default_factory=list, description="Business principals"
    )
    subsidiaries: List[str] = Field(
        default_factory=list, description="Subsidiary companies"
    )
    parent_company: Optional[str] = Field(None, description="Parent company")

    # Financial and operational
    financial_data: Optional[FinancialData] = Field(
        None, description="Financial information"
    )
    years_in_business: Optional[int] = Field(None, description="Years in operation")
    founded_date: Optional[datetime] = Field(None, description="Date founded")

    # Metadata
    source_provider: str = Field(..., description="Data source provider")
    query_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When this data was retrieved"
    )
    confidence_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Overall profile confidence"
    )
    data_age: Optional[str] = Field(None, description="How recent the source data is")

    # Raw data
    raw_response: Optional[Dict[str, Any]] = Field(
        None, description="Original API response"
    )

    @property
    def primary_location(self) -> Optional[BusinessLocation]:
        """Get primary business location"""
        if not self.locations:
            return None

        # Look for headquarters first
        for location in self.locations:
            if location.is_headquarters:
                return location

        # Otherwise return first active location
        for location in self.locations:
            if location.is_active:
                return location

        return self.locations[0] if self.locations else None

    @property
    def primary_phone(self) -> Optional[Phone]:
        """Get primary phone number"""
        if not self.phones:
            return None

        # Sort by confidence and current status
        sorted_phones = sorted(
            self.phones, key=lambda p: (p.is_current, p.confidence_score), reverse=True
        )
        return sorted_phones[0]

    @property
    def is_active(self) -> bool:
        """Check if business appears to be active"""
        if self.registration and self.registration.status:
            return self.registration.status == BusinessStatus.ACTIVE

        # Fallback to checking if has active locations
        return any(loc.is_active for loc in self.locations)

    @property
    def current_principals(self) -> List[Principal]:
        """Get current business principals"""
        return [p for p in self.principals if p.is_current]

    @property
    def active_licenses(self) -> List[License]:
        """Get active (non-expired) licenses"""
        return [lic for lic in self.licenses if not lic.is_expired]

    def add_location(
        self, location_data: Union[Dict[str, Any], BusinessLocation]
    ) -> None:
        """Add business location"""
        if isinstance(location_data, dict):
            location = BusinessLocation(**location_data)
        else:
            location = location_data

        # Check for duplicates based on address
        for existing in self.locations:
            if existing.address.full_address == location.address.full_address:
                return

        self.locations.append(location)

    def add_principal(self, principal_data: Union[Dict[str, Any], Principal]) -> None:
        """Add business principal"""
        if isinstance(principal_data, dict):
            principal = Principal(**principal_data)
        else:
            principal = principal_data

        # Check for duplicates based on name and role
        for existing in self.principals:
            if (
                existing.name.display_name == principal.name.display_name
                and existing.title == principal.title
            ):
                return

        self.principals.append(principal)

    def add_filing(self, filing_data: Union[Dict[str, Any], Filing]) -> None:
        """Add business filing"""
        if isinstance(filing_data, dict):
            filing = Filing(**filing_data)
        else:
            filing = filing_data

        # Check for duplicates based on document number
        if filing.document_number:
            for existing in self.filings:
                if existing.document_number == filing.document_number:
                    return

        self.filings.append(filing)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Return summarized profile for display"""
        primary_loc = self.primary_location

        return {
            "business_name": self.business_name,
            "entity_type": self.entity_type.value if self.entity_type else "unknown",
            "status": self.registration.status.value
            if self.registration
            else "unknown",
            "phone": self.primary_phone.formatted if self.primary_phone else None,
            "address": primary_loc.address.full_address if primary_loc else None,
            "industry": self.industry.primary_industry if self.industry else None,
            "principals": len(self.current_principals),
            "locations": len(self.locations),
            "years_in_business": self.years_in_business,
            "confidence": self.confidence_score,
            "source": self.source_provider,
        }
