"""
Person data models for Sleuth Intel
Contains models for person profiles, addresses, phones, emails, and related data
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class PhoneType(str, Enum):
    """Phone number types"""

    MOBILE = "mobile"
    LANDLINE = "landline"
    VOIP = "voip"
    TOLL_FREE = "toll_free"
    UNKNOWN = "unknown"


class AddressType(str, Enum):
    """Address types"""

    CURRENT = "current"
    PREVIOUS = "previous"
    BUSINESS = "business"
    MAILING = "mailing"
    UNKNOWN = "unknown"


class Phone(BaseModel):
    """Phone number model with metadata"""

    number: str = Field(..., description="Phone number in standard format")
    formatted: Optional[str] = Field(None, description="Formatted phone number")
    type: PhoneType = Field(PhoneType.UNKNOWN, description="Phone type classification")
    carrier: Optional[str] = Field(None, description="Phone carrier/provider")
    line_type: Optional[str] = Field(None, description="Line type from carrier")
    is_current: bool = Field(True, description="Whether this is a current number")
    first_seen: Optional[datetime] = Field(
        None, description="First time this number was seen"
    )
    last_seen: Optional[datetime] = Field(
        None, description="Last time this number was verified"
    )
    confidence_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence in data accuracy"
    )

    @field_validator("number")
    @classmethod
    def validate_phone_number(cls, v):
        """Clean and validate phone number"""
        # Remove all non-digits
        cleaned = "".join(filter(str.isdigit, v))
        if len(cleaned) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return cleaned

    @model_validator(mode="after")
    def format_phone_if_needed(self):
        """Auto-format phone number if not provided"""
        if self.formatted is None and self.number:
            number = self.number
            if len(number) == 10:
                self.formatted = f"({number[:3]}) {number[3:6]}-{number[6:]}"
            elif len(number) == 11 and number.startswith("1"):
                self.formatted = f"+1 ({number[1:4]}) {number[4:7]}-{number[7:]}"
        return self


class Address(BaseModel):
    """Address model with geocoding and validation"""

    street: Optional[str] = Field(None, description="Street address")
    unit: Optional[str] = Field(None, description="Unit/apartment number")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State abbreviation")
    zip_code: Optional[str] = Field(None, description="ZIP/postal code")
    zip4: Optional[str] = Field(None, description="ZIP+4 extension")
    county: Optional[str] = Field(None, description="County name")
    country: str = Field("US", description="Country code")

    type: AddressType = Field(AddressType.UNKNOWN, description="Address classification")
    is_current: bool = Field(True, description="Whether this is current address")

    # Geographic data
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")

    # Metadata
    first_seen: Optional[datetime] = Field(
        None, description="First time this address was seen"
    )
    last_seen: Optional[datetime] = Field(
        None, description="Last time this address was verified"
    )
    confidence_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence in data accuracy"
    )

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Ensure state is uppercase and valid format"""
        if v:
            v = v.upper().strip()
            if len(v) != 2:
                raise ValueError("State must be 2-letter abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        """Validate ZIP code format"""
        if v:
            v = v.strip()
            if not v.replace("-", "").isdigit():
                raise ValueError("ZIP code must contain only digits and hyphens")
        return v

    @property
    def full_address(self) -> str:
        """Return formatted full address"""
        parts = []
        if self.street:
            street_part = self.street
            if self.unit:
                street_part += f" {self.unit}"
            parts.append(street_part)

        if self.city and self.state:
            city_state = f"{self.city}, {self.state}"
            if self.zip_code:
                city_state += f" {self.zip_code}"
            parts.append(city_state)

        return ", ".join(parts)


class Email(BaseModel):
    """Email model with validation and metadata"""

    address: EmailStr = Field(..., description="Email address")
    domain: Optional[str] = Field(None, description="Email domain")
    is_current: bool = Field(True, description="Whether this email is current")
    is_verified: bool = Field(False, description="Whether email has been verified")
    first_seen: Optional[datetime] = Field(
        None, description="First time this email was seen"
    )
    last_seen: Optional[datetime] = Field(
        None, description="Last time this email was verified"
    )
    confidence_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence in data accuracy"
    )

    @model_validator(mode="after")
    def extract_domain(self):
        """Extract domain from email address"""
        if self.address and self.domain is None:
            self.domain = str(self.address).split("@")[1]
        return self


class PersonName(BaseModel):
    """Person name model with variations"""

    first: Optional[str] = Field(None, description="First name")
    middle: Optional[str] = Field(None, description="Middle name or initial")
    last: Optional[str] = Field(None, description="Last name")
    suffix: Optional[str] = Field(None, description="Name suffix (Jr, Sr, III, etc)")
    prefix: Optional[str] = Field(None, description="Name prefix (Dr, Mr, Ms, etc)")
    full: Optional[str] = Field(None, description="Full name as single string")

    # Name variations and aliases
    aliases: List[str] = Field(default_factory=list, description="Known aliases")
    maiden_name: Optional[str] = Field(None, description="Maiden name")

    @model_validator(mode="after")
    def build_full_name(self):
        """Build full name from components if not provided"""
        if not self.full and (self.first or self.last):
            parts = []
            if self.prefix:
                parts.append(self.prefix)
            if self.first:
                parts.append(self.first)
            if self.middle:
                parts.append(self.middle)
            if self.last:
                parts.append(self.last)
            if self.suffix:
                parts.append(self.suffix)
            self.full = " ".join(parts)
        return self

    @property
    def display_name(self) -> str:
        """Return best display name"""
        if self.full:
            return self.full
        if self.first and self.last:
            return f"{self.first} {self.last}"
        if self.first:
            return self.first
        if self.last:
            return self.last
        return "Unknown"


class Demographics(BaseModel):
    """Demographic information"""

    age: Optional[int] = Field(None, ge=0, le=150, description="Current age")
    age_range: Optional[str] = Field(None, description="Age range (e.g., '25-35')")
    birth_year: Optional[int] = Field(None, description="Year of birth")
    birth_date: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    marital_status: Optional[str] = Field(None, description="Marital status")
    education: Optional[str] = Field(None, description="Education level")
    occupation: Optional[str] = Field(None, description="Primary occupation")
    income_range: Optional[str] = Field(None, description="Estimated income range")


class Associate(BaseModel):
    """Associated person (relative, roommate, etc.)"""

    name: PersonName = Field(..., description="Associate's name")
    relationship: Optional[str] = Field(None, description="Relationship type")
    phones: List[Phone] = Field(
        default_factory=list, description="Associate's phone numbers"
    )
    addresses: List[Address] = Field(
        default_factory=list, description="Shared addresses"
    )
    confidence_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence in association"
    )


class PersonProfile(BaseModel):
    """Complete person profile from intelligence gathering"""

    # Core identity
    name: PersonName = Field(..., description="Person's name and variations")
    demographics: Optional[Demographics] = Field(
        None, description="Demographic information"
    )

    # Contact information
    phones: List[Phone] = Field(default_factory=list, description="Phone numbers")
    emails: List[Email] = Field(default_factory=list, description="Email addresses")
    addresses: List[Address] = Field(
        default_factory=list, description="Current and previous addresses"
    )

    # Associations
    associates: List[Associate] = Field(
        default_factory=list, description="Known associates"
    )
    relatives: List[Associate] = Field(
        default_factory=list, description="Family members"
    )

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
    def current_phone(self) -> Optional[Phone]:
        """Get most likely current phone number"""
        if not self.phones:
            return None

        # Sort by confidence and recency
        sorted_phones = sorted(
            self.phones,
            key=lambda p: (
                p.is_current,
                p.confidence_score,
                p.last_seen or datetime.min,
            ),
            reverse=True,
        )
        return sorted_phones[0]

    @property
    def current_address(self) -> Optional[Address]:
        """Get most likely current address"""
        if not self.addresses:
            return None

        # Sort by confidence and recency
        sorted_addresses = sorted(
            self.addresses,
            key=lambda a: (
                a.is_current,
                a.confidence_score,
                a.last_seen or datetime.min,
            ),
            reverse=True,
        )
        return sorted_addresses[0]

    @property
    def primary_email(self) -> Optional[Email]:
        """Get most likely primary email"""
        if not self.emails:
            return None

        # Sort by verification status and confidence
        sorted_emails = sorted(
            self.emails,
            key=lambda e: (e.is_verified, e.is_current, e.confidence_score),
            reverse=True,
        )
        return sorted_emails[0]

    def add_phone(self, phone_data: Union[str, Dict[str, Any], Phone]) -> None:
        """Add phone number to profile"""
        if isinstance(phone_data, str):
            phone = Phone(number=phone_data)
        elif isinstance(phone_data, dict):
            phone = Phone(**phone_data)
        else:
            phone = phone_data

        # Check for duplicates
        for existing in self.phones:
            if existing.number == phone.number:
                return

        self.phones.append(phone)

    def add_address(self, address_data: Union[Dict[str, Any], Address]) -> None:
        """Add address to profile"""
        if isinstance(address_data, dict):
            address = Address(**address_data)
        else:
            address = address_data

        # Check for duplicates (basic check on full address)
        for existing in self.addresses:
            if existing.full_address == address.full_address:
                return

        self.addresses.append(address)

    def add_email(self, email_data: Union[str, Dict[str, Any], Email]) -> None:
        """Add email to profile"""
        if isinstance(email_data, str):
            email = Email(address=email_data)
        elif isinstance(email_data, dict):
            email = Email(**email_data)
        else:
            email = email_data

        # Check for duplicates
        for existing in self.emails:
            if existing.address == email.address:
                return

        self.emails.append(email)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Return summarized profile for display"""
        return {
            "name": self.name.display_name,
            "phone": self.current_phone.formatted if self.current_phone else None,
            "email": str(self.primary_email.address) if self.primary_email else None,
            "address": self.current_address.full_address
            if self.current_address
            else None,
            "age": self.demographics.age if self.demographics else None,
            "total_phones": len(self.phones),
            "total_emails": len(self.emails),
            "total_addresses": len(self.addresses),
            "confidence": self.confidence_score,
            "source": self.source_provider,
        }
