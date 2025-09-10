"""
AddressSearchAgent for Sleuth Intel
Implements comprehensive address intelligence using EnformionGO /address-search endpoint
"""

import asyncio
import hashlib
import json
import logging
import re
import statistics
import time
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple, Union

from ..agents.base_agent import (
    BaseIntelligenceAgent,
    CacheConfig,
    RateLimitConfig,
    RetryConfig,
)
from ..core.secure_api_locker import APICredential
from ..models.person import (
    Address,
    Associate,
    Demographics,
    Email,
    PersonName,
    PersonProfile,
    Phone,
)
from ..models.query import AddressLookupQuery, DataProvider
from ..providers.enformion_client import EnformionAPIError, EnformionClient

logger = logging.getLogger(__name__)


class AddressValidationResult:
    """Result from address validation and standardization"""

    def __init__(self, address_input: str):
        self.input_address = address_input
        self.is_valid = False
        self.standardized_address = None
        self.parsed_components = {}
        self.quality_score = 0.0
        self.validation_errors = []
        self.suggested_corrections = []
        self.geocode = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_address": self.input_address,
            "is_valid": self.is_valid,
            "standardized_address": self.standardized_address,
            "parsed_components": self.parsed_components,
            "quality_score": self.quality_score,
            "validation_errors": self.validation_errors,
            "suggested_corrections": self.suggested_corrections,
            "geocode": self.geocode,
        }


class ResidentProfile:
    """Profile of a resident at an address"""

    def __init__(self):
        self.name = None
        self.age = None
        self.phone_numbers = []
        self.email_addresses = []
        self.occupancy_period = {}
        self.relationship_to_property = None  # owner, renter, relative, etc.
        self.confidence_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "age": self.age,
            "phone_numbers": self.phone_numbers,
            "email_addresses": self.email_addresses,
            "occupancy_period": self.occupancy_period,
            "relationship_to_property": self.relationship_to_property,
            "confidence_score": self.confidence_score,
        }


class PropertyOwnershipRecord:
    """Property ownership information"""

    def __init__(self):
        self.current_owner = None
        self.ownership_type = None  # individual, corporation, trust, etc.
        self.ownership_date = None
        self.previous_owners = []
        self.mortgage_info = {}
        self.tax_assessment = {}
        self.property_details = {}
        self.confidence_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_owner": self.current_owner,
            "ownership_type": self.ownership_type,
            "ownership_date": self.ownership_date,
            "previous_owners": self.previous_owners,
            "mortgage_info": self.mortgage_info,
            "tax_assessment": self.tax_assessment,
            "property_details": self.property_details,
            "confidence_score": self.confidence_score,
        }


class DemographicProfile:
    """Neighborhood demographic information"""

    def __init__(self):
        self.population_data = {}
        self.income_statistics = {}
        self.age_distribution = {}
        self.education_levels = {}
        self.housing_characteristics = {}
        self.crime_statistics = {}
        self.school_district_info = {}
        self.economic_indicators = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "population_data": self.population_data,
            "income_statistics": self.income_statistics,
            "age_distribution": self.age_distribution,
            "education_levels": self.education_levels,
            "housing_characteristics": self.housing_characteristics,
            "crime_statistics": self.crime_statistics,
            "school_district_info": self.school_district_info,
            "economic_indicators": self.economic_indicators,
        }


class MovementPattern:
    """Address movement pattern analysis"""

    def __init__(self):
        self.person_name = None
        self.address_history = []
        self.geographic_mobility = 0.0  # score 0-1
        self.average_residence_duration = None
        self.movement_triggers = []  # job, family, financial, etc.
        self.stability_score = 0.0
        self.prediction_confidence = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "person_name": self.person_name,
            "address_history": self.address_history,
            "geographic_mobility": self.geographic_mobility,
            "average_residence_duration": self.average_residence_duration,
            "movement_triggers": self.movement_triggers,
            "stability_score": self.stability_score,
            "prediction_confidence": self.prediction_confidence,
        }


class AddressIntelligenceReport:
    """Comprehensive address intelligence report"""

    def __init__(self, address: str):
        self.query_address = address
        self.validation_result = None
        self.current_residents = []
        self.historical_residents = []
        self.ownership_records = []
        self.demographic_profile = None
        self.movement_patterns = []
        self.verification_status = None
        self.risk_indicators = []
        self.confidence_score = 0.0
        self.query_timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_address": self.query_address,
            "validation_result": self.validation_result.to_dict()
            if self.validation_result
            else None,
            "current_residents": [r.to_dict() for r in self.current_residents],
            "historical_residents": [r.to_dict() for r in self.historical_residents],
            "ownership_records": [o.to_dict() for o in self.ownership_records],
            "demographic_profile": self.demographic_profile.to_dict()
            if self.demographic_profile
            else None,
            "movement_patterns": [p.to_dict() for p in self.movement_patterns],
            "verification_status": self.verification_status,
            "risk_indicators": self.risk_indicators,
            "confidence_score": self.confidence_score,
            "query_timestamp": self.query_timestamp.isoformat(),
        }


class AddressSearchAgent(BaseIntelligenceAgent):
    """
    Comprehensive address intelligence agent using EnformionGO API

    Features:
    - Address validation and standardization
    - Current and historical resident identification
    - Property ownership analysis
    - Neighborhood demographic profiling
    - Movement pattern analysis
    - Address verification and quality scoring
    - Real estate intelligence
    """

    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        person_search_agent=None,
    ):
        # Address search specific rate limits
        default_rate_config = RateLimitConfig(
            requests_per_second=0.8,  # 1.25 seconds between requests
            requests_per_minute=40,
            requests_per_hour=800,
            requests_per_day=5000,
            burst_size=4,
        )

        # Extended cache for address searches
        default_cache_config = CacheConfig(
            enabled=True,
            ttl_seconds=10800,  # 3 hours (addresses change less frequently)
            max_entries=1000,
            compress=True,
        )

        super().__init__(
            provider="enformion",
            agent_name="AddressSearchAgent",
            rate_limit_config=rate_limit_config or default_rate_config,
            retry_config=retry_config,
            cache_config=cache_config or default_cache_config,
            custom_headers={"X-Agent-Type": "address-search"},
            timeout=60,  # Address searches may take longer
        )

        # Initialize EnformionGO client
        self.enformion_client = EnformionClient()

        # Integration with PersonSearchAgent for resident details
        self.person_search_agent = person_search_agent

        # Address parsing patterns
        self._setup_address_patterns()

        logger.info(
            "Initialized AddressSearchAgent with comprehensive address intelligence"
        )

    def _setup_address_patterns(self):
        """Setup regex patterns for address parsing"""
        self.street_patterns = {
            "number": r"^(\d+[-\d]*)",
            "street_name": r"(\b[A-Za-z\s]+?)(?:\s+(St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Ln|Lane|Rd|Road|Ct|Court|Pl|Place|Way|Circle|Cir)\.?)?$",
            "unit": r"(Apt|Apartment|Unit|Suite|Ste|#)\s*([A-Za-z0-9\-]+)",
            "directional": r"\b(N|North|S|South|E|East|W|West|NE|NW|SE|SW|Northeast|Northwest|Southeast|Southwest)\b",
        }

        self.city_state_patterns = {
            "city_state_zip": r"^(.+?),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)?\s*$",
            "state_abbrev": r"\b([A-Z]{2})\b",
            "zip_code": r"\b(\d{5}(?:-\d{4})?)\b",
        }

    def _apply_authentication(
        self, credential: APICredential, request_kwargs: Dict
    ) -> Dict:
        """Apply EnformionGO authentication to request"""
        headers = request_kwargs.get("headers", {})

        if credential.password:
            headers.update(
                {
                    "X-API-Key": credential.key_value,
                    "X-API-Password": credential.password,
                }
            )
        else:
            headers["Authorization"] = f"Bearer {credential.key_value}"

        request_kwargs["headers"] = headers
        return request_kwargs

    def parse_address(self, address_string: str) -> Dict[str, str]:
        """
        Parse address string into components

        Args:
            address_string: Full address string to parse

        Returns:
            Dictionary with parsed address components
        """
        if not address_string:
            return {}

        address = address_string.strip()
        components = {
            "original": address,
            "street_number": None,
            "street_name": None,
            "unit": None,
            "city": None,
            "state": None,
            "zip_code": None,
        }

        try:
            # Split by comma to separate street from city/state/zip
            parts = [part.strip() for part in address.split(",")]

            if len(parts) >= 2:
                street_part = parts[0]
                city_state_zip = ", ".join(parts[1:])

                # Parse street portion
                street_number_match = re.match(
                    self.street_patterns["number"], street_part
                )
                if street_number_match:
                    components["street_number"] = street_number_match.group(1)
                    street_remainder = street_part[
                        len(street_number_match.group(1)) :
                    ].strip()

                    # Check for unit information
                    unit_match = re.search(
                        self.street_patterns["unit"], street_remainder, re.IGNORECASE
                    )
                    if unit_match:
                        components[
                            "unit"
                        ] = f"{unit_match.group(1)} {unit_match.group(2)}"
                        street_remainder = re.sub(
                            self.street_patterns["unit"],
                            "",
                            street_remainder,
                            flags=re.IGNORECASE,
                        ).strip()

                    components["street_name"] = street_remainder.strip()

                # Parse city/state/zip portion
                city_state_zip_match = re.match(
                    self.city_state_patterns["city_state_zip"], city_state_zip
                )
                if city_state_zip_match:
                    components["city"] = city_state_zip_match.group(1).strip()
                    components["state"] = city_state_zip_match.group(2)
                    if city_state_zip_match.group(3):
                        components["zip_code"] = city_state_zip_match.group(3)

            # Clean up components
            for key, value in components.items():
                if isinstance(value, str) and value:
                    components[key] = " ".join(value.split())  # Normalize whitespace

        except Exception as e:
            logger.warning(f"Failed to parse address '{address}': {e}")

        return components

    def validate_address(self, address: str) -> AddressValidationResult:
        """
        Validate and standardize address

        Args:
            address: Address string to validate

        Returns:
            AddressValidationResult with validation details
        """
        result = AddressValidationResult(address)

        try:
            # Parse the address
            parsed = self.parse_address(address)
            result.parsed_components = parsed

            # Basic validation checks
            validation_score = 0.0
            max_score = 100.0

            # Check for street number
            if parsed.get("street_number"):
                validation_score += 20

            # Check for street name
            if parsed.get("street_name"):
                validation_score += 25

            # Check for city
            if parsed.get("city"):
                validation_score += 20

            # Check for state
            if parsed.get("state") and len(parsed["state"]) == 2:
                validation_score += 20
            elif parsed.get("state"):
                result.validation_errors.append("State should be 2-letter abbreviation")

            # Check for ZIP code
            if parsed.get("zip_code"):
                if re.match(r"^\d{5}(?:-\d{4})?$", parsed["zip_code"]):
                    validation_score += 15
                else:
                    result.validation_errors.append("Invalid ZIP code format")

            result.quality_score = validation_score / max_score
            result.is_valid = result.quality_score >= 0.7

            # Generate standardized address
            if result.is_valid:
                std_parts = []
                if parsed.get("street_number") and parsed.get("street_name"):
                    street = f"{parsed['street_number']} {parsed['street_name']}"
                    if parsed.get("unit"):
                        street += f", {parsed['unit']}"
                    std_parts.append(street)

                if parsed.get("city") and parsed.get("state"):
                    city_state = f"{parsed['city']}, {parsed['state']}"
                    if parsed.get("zip_code"):
                        city_state += f" {parsed['zip_code']}"
                    std_parts.append(city_state)

                result.standardized_address = ", ".join(std_parts)

        except Exception as e:
            logger.error(f"Address validation failed: {e}")
            result.validation_errors.append(str(e))

        return result

    def normalize_address(self, address: str) -> str:
        """
        Normalize address for consistent comparison

        Args:
            address: Address to normalize

        Returns:
            Normalized address string
        """
        if not address:
            return ""

        # Convert to lowercase and normalize whitespace
        normalized = " ".join(address.lower().split())

        # Common abbreviation normalization
        abbreviations = {
            " street": " st",
            " avenue": " ave",
            " boulevard": " blvd",
            " drive": " dr",
            " lane": " ln",
            " road": " rd",
            " court": " ct",
            " place": " pl",
            " circle": " cir",
            " apartment": " apt",
            " suite": " ste",
            " unit": " unit",
            " number": " #",
        }

        for full, abbrev in abbreviations.items():
            normalized = normalized.replace(full, abbrev)

        return normalized

    def calculate_address_similarity(self, address1: str, address2: str) -> float:
        """
        Calculate similarity score between two addresses

        Args:
            address1: First address
            address2: Second address

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not address1 or not address2:
            return 0.0

        # Normalize both addresses
        norm1 = self.normalize_address(address1)
        norm2 = self.normalize_address(address2)

        if norm1 == norm2:
            return 1.0

        # Use sequence matcher for fuzzy similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        # Parse both addresses and compare components
        parsed1 = self.parse_address(address1)
        parsed2 = self.parse_address(address2)

        component_matches = 0
        total_components = 0

        for component in ["street_number", "street_name", "city", "state", "zip_code"]:
            val1 = parsed1.get(component, "").lower()
            val2 = parsed2.get(component, "").lower()

            if val1 or val2:
                total_components += 1
                if val1 == val2:
                    component_matches += 1

        if total_components > 0:
            component_similarity = component_matches / total_components
            # Weight component similarity higher than string similarity
            similarity = (similarity * 0.3) + (component_similarity * 0.7)

        return similarity

    def identify_current_residents(self, address: str) -> List[ResidentProfile]:
        """
        Identify current residents at an address

        Args:
            address: Address to search

        Returns:
            List of current resident profiles
        """
        residents = []

        try:
            # Use EnformionGO address search
            search_params = {}
            parsed = self.parse_address(address)

            if parsed.get("street_number") and parsed.get("street_name"):
                search_params[
                    "address"
                ] = f"{parsed['street_number']} {parsed['street_name']}"
            if parsed.get("city"):
                search_params["city"] = parsed["city"]
            if parsed.get("state"):
                search_params["state"] = parsed["state"]
            if parsed.get("zip_code"):
                search_params["zip"] = parsed["zip_code"]

            # Make API call to address search endpoint
            response = self.make_request(
                method="GET",
                url=f"{self.enformion_client.base_url}/address-search",
                params=search_params,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                for result in results:
                    resident = ResidentProfile()

                    # Extract resident information
                    if result.get("first_name") or result.get("last_name"):
                        name_parts = []
                        if result.get("first_name"):
                            name_parts.append(result["first_name"])
                        if result.get("last_name"):
                            name_parts.append(result["last_name"])
                        resident.name = " ".join(name_parts)

                    if result.get("age"):
                        resident.age = result["age"]

                    # Extract phone numbers
                    if result.get("phones"):
                        for phone in result["phones"]:
                            if isinstance(phone, dict):
                                phone_num = phone.get("number")
                            else:
                                phone_num = str(phone)

                            if phone_num:
                                resident.phone_numbers.append(phone_num)

                    # Extract email addresses
                    if result.get("emails"):
                        for email in result["emails"]:
                            email_addr = (
                                email
                                if isinstance(email, str)
                                else email.get("address")
                            )
                            if email_addr:
                                resident.email_addresses.append(email_addr)

                    # Set occupancy information
                    resident.occupancy_period = {
                        "start_date": result.get("first_seen"),
                        "end_date": result.get("last_seen"),
                        "current": result.get("is_current", True),
                    }

                    # Relationship to property
                    resident.relationship_to_property = result.get(
                        "relationship", "resident"
                    )

                    # Calculate confidence based on data completeness
                    confidence_factors = [
                        bool(resident.name),
                        bool(resident.age),
                        len(resident.phone_numbers) > 0,
                        len(resident.email_addresses) > 0,
                    ]
                    resident.confidence_score = sum(confidence_factors) / len(
                        confidence_factors
                    )

                    residents.append(resident)

        except Exception as e:
            logger.error(f"Failed to identify current residents for {address}: {e}")

        return residents

    def identify_historical_residents(
        self, address: str, years_back: int = 5
    ) -> List[ResidentProfile]:
        """
        Identify historical residents at an address

        Args:
            address: Address to search
            years_back: How many years of history to search

        Returns:
            List of historical resident profiles
        """
        historical_residents = []

        try:
            # Similar to current residents but with historical flag
            search_params = {}
            parsed = self.parse_address(address)

            if parsed.get("street_number") and parsed.get("street_name"):
                search_params[
                    "address"
                ] = f"{parsed['street_number']} {parsed['street_name']}"
            if parsed.get("city"):
                search_params["city"] = parsed["city"]
            if parsed.get("state"):
                search_params["state"] = parsed["state"]
            if parsed.get("zip_code"):
                search_params["zip"] = parsed["zip_code"]

            # Add historical search parameters
            search_params["include_historical"] = True
            search_params["years_back"] = years_back

            response = self.make_request(
                method="GET",
                url=f"{self.enformion_client.base_url}/address-search",
                params=search_params,
            )

            if response.status_code == 200:
                data = response.json()
                historical_results = data.get("historical_results", [])

                for result in historical_results:
                    resident = ResidentProfile()

                    # Similar processing as current residents
                    if result.get("first_name") or result.get("last_name"):
                        name_parts = []
                        if result.get("first_name"):
                            name_parts.append(result["first_name"])
                        if result.get("last_name"):
                            name_parts.append(result["last_name"])
                        resident.name = " ".join(name_parts)

                    if result.get("age"):
                        resident.age = result["age"]

                    # Set as historical resident
                    resident.occupancy_period = {
                        "start_date": result.get("residence_start"),
                        "end_date": result.get("residence_end"),
                        "current": False,
                    }

                    # Extract contact info
                    if result.get("phones"):
                        resident.phone_numbers = [
                            phone.get("number")
                            if isinstance(phone, dict)
                            else str(phone)
                            for phone in result["phones"]
                        ]

                    if result.get("emails"):
                        resident.email_addresses = [
                            email if isinstance(email, str) else email.get("address")
                            for email in result["emails"]
                        ]

                    resident.relationship_to_property = result.get(
                        "relationship", "former_resident"
                    )

                    # Lower confidence for historical data
                    confidence_factors = [
                        bool(resident.name),
                        bool(resident.occupancy_period.get("start_date")),
                        len(resident.phone_numbers) > 0,
                    ]
                    resident.confidence_score = (
                        sum(confidence_factors) / len(confidence_factors)
                    ) * 0.8

                    historical_residents.append(resident)

        except Exception as e:
            logger.error(f"Failed to identify historical residents for {address}: {e}")

        return historical_residents

    def analyze_property_ownership(self, address: str) -> List[PropertyOwnershipRecord]:
        """
        Analyze property ownership information

        Args:
            address: Address to analyze

        Returns:
            List of property ownership records
        """
        ownership_records = []

        try:
            parsed = self.parse_address(address)
            search_params = {
                "include_property_data": True,
                "include_ownership_history": True,
            }

            if parsed.get("street_number") and parsed.get("street_name"):
                search_params[
                    "address"
                ] = f"{parsed['street_number']} {parsed['street_name']}"
            if parsed.get("city"):
                search_params["city"] = parsed["city"]
            if parsed.get("state"):
                search_params["state"] = parsed["state"]
            if parsed.get("zip_code"):
                search_params["zip"] = parsed["zip_code"]

            response = self.make_request(
                method="GET",
                url=f"{self.enformion_client.base_url}/property-search",
                params=search_params,
            )

            if response.status_code == 200:
                data = response.json()
                property_data = data.get("property_info", {})

                # Current ownership
                if property_data.get("current_owner"):
                    current_record = PropertyOwnershipRecord()
                    current_record.current_owner = property_data["current_owner"]
                    current_record.ownership_type = property_data.get(
                        "ownership_type", "unknown"
                    )
                    current_record.ownership_date = property_data.get("ownership_date")

                    # Mortgage information
                    if property_data.get("mortgage_info"):
                        current_record.mortgage_info = property_data["mortgage_info"]

                    # Tax assessment
                    if property_data.get("tax_assessment"):
                        current_record.tax_assessment = property_data["tax_assessment"]

                    # Property details
                    current_record.property_details = {
                        "property_type": property_data.get("property_type"),
                        "square_footage": property_data.get("square_footage"),
                        "bedrooms": property_data.get("bedrooms"),
                        "bathrooms": property_data.get("bathrooms"),
                        "year_built": property_data.get("year_built"),
                        "lot_size": property_data.get("lot_size"),
                    }

                    current_record.confidence_score = (
                        0.9 if property_data.get("verified") else 0.7
                    )
                    ownership_records.append(current_record)

                # Historical ownership
                historical_owners = property_data.get("previous_owners", [])
                for prev_owner in historical_owners:
                    historical_record = PropertyOwnershipRecord()
                    historical_record.current_owner = prev_owner.get("name")
                    historical_record.ownership_type = prev_owner.get("ownership_type")
                    historical_record.ownership_date = prev_owner.get("ownership_start")

                    if prev_owner.get("ownership_end"):
                        historical_record.previous_owners = [
                            {
                                "name": prev_owner["name"],
                                "ownership_period": {
                                    "start": prev_owner.get("ownership_start"),
                                    "end": prev_owner.get("ownership_end"),
                                },
                            }
                        ]

                    historical_record.confidence_score = (
                        0.6  # Lower for historical data
                    )
                    ownership_records.append(historical_record)

        except Exception as e:
            logger.error(f"Failed to analyze property ownership for {address}: {e}")

        return ownership_records

    def profile_neighborhood_demographics(
        self, address: str, radius_miles: float = 0.5
    ) -> DemographicProfile:
        """
        Generate demographic profile for neighborhood around address

        Args:
            address: Address to center demographic analysis on
            radius_miles: Radius in miles for demographic analysis

        Returns:
            DemographicProfile with neighborhood statistics
        """
        demographic_profile = DemographicProfile()

        try:
            parsed = self.parse_address(address)
            search_params = {"include_demographics": True, "radius_miles": radius_miles}

            if parsed.get("city"):
                search_params["city"] = parsed["city"]
            if parsed.get("state"):
                search_params["state"] = parsed["state"]
            if parsed.get("zip_code"):
                search_params["zip"] = parsed["zip_code"]

            response = self.make_request(
                method="GET",
                url=f"{self.enformion_client.base_url}/demographics-search",
                params=search_params,
            )

            if response.status_code == 200:
                data = response.json()
                demographics = data.get("demographics", {})

                # Population data
                demographic_profile.population_data = {
                    "total_population": demographics.get("total_population"),
                    "population_density": demographics.get("population_density"),
                    "households": demographics.get("total_households"),
                    "average_household_size": demographics.get(
                        "average_household_size"
                    ),
                }

                # Income statistics
                demographic_profile.income_statistics = {
                    "median_household_income": demographics.get(
                        "median_household_income"
                    ),
                    "mean_household_income": demographics.get("mean_household_income"),
                    "income_distribution": demographics.get("income_brackets", {}),
                    "poverty_rate": demographics.get("poverty_rate"),
                }

                # Age distribution
                demographic_profile.age_distribution = demographics.get(
                    "age_distribution", {}
                )

                # Education levels
                demographic_profile.education_levels = demographics.get(
                    "education_levels", {}
                )

                # Housing characteristics
                demographic_profile.housing_characteristics = {
                    "median_home_value": demographics.get("median_home_value"),
                    "median_rent": demographics.get("median_rent"),
                    "homeownership_rate": demographics.get("homeownership_rate"),
                    "housing_types": demographics.get("housing_types", {}),
                }

                # Crime statistics
                if demographics.get("crime_stats"):
                    demographic_profile.crime_statistics = demographics["crime_stats"]

                # School district information
                if demographics.get("school_district"):
                    demographic_profile.school_district_info = demographics[
                        "school_district"
                    ]

                # Economic indicators
                demographic_profile.economic_indicators = {
                    "employment_rate": demographics.get("employment_rate"),
                    "major_employers": demographics.get("major_employers", []),
                    "economic_growth_rate": demographics.get("economic_growth_rate"),
                }

        except Exception as e:
            logger.error(
                f"Failed to profile neighborhood demographics for {address}: {e}"
            )

        return demographic_profile

    def analyze_movement_patterns(
        self, person_name: str, current_address: str
    ) -> MovementPattern:
        """
        Analyze movement patterns for a person

        Args:
            person_name: Name of person to analyze
            current_address: Current known address

        Returns:
            MovementPattern analysis
        """
        pattern = MovementPattern()
        pattern.person_name = person_name

        try:
            # If we have PersonSearchAgent integration, use it
            if self.person_search_agent:
                # Search for the person to get address history
                from ..models.query import PersonSearchQuery

                name_parts = person_name.split()
                query = PersonSearchQuery(
                    first_name=name_parts[0] if len(name_parts) > 0 else None,
                    last_name=name_parts[-1] if len(name_parts) > 1 else None,
                    include_relatives=False,
                    historical_addresses=True,
                    max_results=5,
                )

                profiles = self.person_search_agent.search(query)

                if profiles:
                    # Use the first profile with the highest confidence
                    primary_profile = max(profiles, key=lambda p: p.confidence_score)

                    # Extract address history
                    addresses = primary_profile.addresses
                    if addresses:
                        # Sort by date (most recent first)
                        addresses.sort(
                            key=lambda a: a.last_seen or datetime.min, reverse=True
                        )

                        pattern.address_history = []
                        residence_durations = []

                        for i, addr in enumerate(addresses):
                            address_info = {
                                "address": addr.full_address,
                                "city": addr.city,
                                "state": addr.state,
                                "zip_code": addr.zip_code,
                                "start_date": addr.first_seen.isoformat()
                                if addr.first_seen
                                else None,
                                "end_date": addr.last_seen.isoformat()
                                if addr.last_seen
                                else None,
                                "is_current": addr.is_current,
                                "confidence": addr.confidence_score,
                            }
                            pattern.address_history.append(address_info)

                            # Calculate residence duration
                            if addr.first_seen and addr.last_seen:
                                duration = (
                                    addr.last_seen - addr.first_seen
                                ).days / 365.25  # years
                                residence_durations.append(duration)

                        # Calculate mobility metrics
                        if len(addresses) > 1:
                            # Geographic mobility: number of unique states/cities
                            unique_states = len(
                                set(addr.state for addr in addresses if addr.state)
                            )
                            unique_cities = len(
                                set(addr.city for addr in addresses if addr.city)
                            )

                            # Normalize mobility score
                            pattern.geographic_mobility = min(
                                1.0, (unique_states * 0.3 + unique_cities * 0.1)
                            )

                            # Average residence duration
                            if residence_durations:
                                pattern.average_residence_duration = statistics.mean(
                                    residence_durations
                                )

                            # Stability score (inverse of mobility)
                            pattern.stability_score = 1.0 - pattern.geographic_mobility

                        else:
                            pattern.geographic_mobility = 0.0
                            pattern.stability_score = 1.0

                        # Movement pattern analysis
                        movement_triggers = []

                        # Look for patterns in timing and geography
                        if len(addresses) >= 3:
                            # Check for regular intervals (job-related moves)
                            intervals = []
                            for i in range(len(addresses) - 1):
                                if (
                                    addresses[i].last_seen
                                    and addresses[i + 1].first_seen
                                ):
                                    interval = abs(
                                        (
                                            addresses[i].last_seen
                                            - addresses[i + 1].first_seen
                                        ).days
                                    )
                                    intervals.append(interval)

                            if intervals:
                                avg_interval = statistics.mean(intervals)
                                if 350 <= avg_interval <= 400:  # ~1 year intervals
                                    movement_triggers.append("regular_employment")
                                elif avg_interval < 180:  # < 6 months
                                    movement_triggers.append("instability_financial")

                        # Geographic patterns
                        if len(set(addr.state for addr in addresses if addr.state)) > 2:
                            movement_triggers.append("geographic_mobility")

                        # Urban to suburban patterns
                        city_sizes = []
                        for addr in addresses:
                            if addr.city:
                                # This is a simple heuristic - in reality you'd use population data
                                if any(
                                    metro in addr.city.lower()
                                    for metro in [
                                        "new york",
                                        "los angeles",
                                        "chicago",
                                        "houston",
                                    ]
                                ):
                                    city_sizes.append("large")
                                elif any(
                                    mid in addr.city.lower()
                                    for mid in ["austin", "denver", "atlanta"]
                                ):
                                    city_sizes.append("medium")
                                else:
                                    city_sizes.append("small")

                        if (
                            len(city_sizes) >= 2
                            and city_sizes[0] == "large"
                            and "small" in city_sizes[1:]
                        ):
                            movement_triggers.append("urban_to_suburban")

                        pattern.movement_triggers = movement_triggers
                        pattern.prediction_confidence = min(0.9, len(addresses) * 0.2)

        except Exception as e:
            logger.error(f"Failed to analyze movement patterns for {person_name}: {e}")
            pattern.prediction_confidence = 0.0

        return pattern

    def verify_address(self, address: str) -> Dict[str, Any]:
        """
        Verify address existence and deliverability

        Args:
            address: Address to verify

        Returns:
            Verification result with status and details
        """
        verification_result = {
            "address": address,
            "is_deliverable": False,
            "is_residential": False,
            "is_business": False,
            "verification_level": None,  # 'confirmed', 'likely', 'possible', 'invalid'
            "postal_service_status": None,
            "suggestions": [],
        }

        try:
            # First validate the address format
            validation = self.validate_address(address)

            if not validation.is_valid:
                verification_result["verification_level"] = "invalid"
                verification_result["suggestions"] = validation.suggested_corrections
                return verification_result

            # Use standardized address for API call
            search_address = validation.standardized_address or address
            parsed = self.parse_address(search_address)

            search_params = {"verification_only": True, "include_postal_status": True}

            if parsed.get("street_number") and parsed.get("street_name"):
                search_params[
                    "address"
                ] = f"{parsed['street_number']} {parsed['street_name']}"
            if parsed.get("city"):
                search_params["city"] = parsed["city"]
            if parsed.get("state"):
                search_params["state"] = parsed["state"]
            if parsed.get("zip_code"):
                search_params["zip"] = parsed["zip_code"]

            response = self.make_request(
                method="GET",
                url=f"{self.enformion_client.base_url}/address-verification",
                params=search_params,
            )

            if response.status_code == 200:
                data = response.json()

                verification_result["is_deliverable"] = data.get(
                    "is_deliverable", False
                )
                verification_result["is_residential"] = (
                    data.get("property_type") == "residential"
                )
                verification_result["is_business"] = (
                    data.get("property_type") == "commercial"
                )
                verification_result["postal_service_status"] = data.get("postal_status")

                # Determine verification level
                confidence_score = data.get("confidence_score", 0.0)
                if confidence_score >= 0.9:
                    verification_result["verification_level"] = "confirmed"
                elif confidence_score >= 0.7:
                    verification_result["verification_level"] = "likely"
                elif confidence_score >= 0.5:
                    verification_result["verification_level"] = "possible"
                else:
                    verification_result["verification_level"] = "questionable"

                # Add any suggestions from the API
                if data.get("suggested_address"):
                    verification_result["suggestions"].append(data["suggested_address"])

        except Exception as e:
            logger.error(f"Address verification failed for {address}: {e}")
            verification_result["verification_level"] = "error"

        return verification_result

    def search_comprehensive(
        self, query: AddressLookupQuery
    ) -> AddressIntelligenceReport:
        """
        Perform comprehensive address intelligence search

        Args:
            query: AddressLookupQuery with search parameters

        Returns:
            AddressIntelligenceReport with complete intelligence
        """
        if not query.has_sufficient_params():
            raise ValueError("Query must have sufficient address parameters")

        # Determine the address to search
        search_address = query.full_address
        if not search_address and query.street and query.city:
            address_parts = [query.street]
            if query.city and query.state:
                city_state = f"{query.city}, {query.state}"
                if query.zip_code:
                    city_state += f" {query.zip_code}"
                address_parts.append(city_state)
            search_address = ", ".join(address_parts)

        if not search_address:
            raise ValueError(
                "Could not construct searchable address from query parameters"
            )

        # Create comprehensive report
        report = AddressIntelligenceReport(search_address)

        try:
            # 1. Address validation and standardization
            self.logger.info(f"Validating address: {search_address}")
            report.validation_result = self.validate_address(search_address)

            # 2. Current residents identification
            if query.include_residents:
                self.logger.info("Identifying current residents")
                report.current_residents = self.identify_current_residents(
                    search_address
                )

                # Also get historical residents
                report.historical_residents = self.identify_historical_residents(
                    search_address
                )

            # 3. Property ownership analysis
            if query.include_property_data:
                self.logger.info("Analyzing property ownership")
                report.ownership_records = self.analyze_property_ownership(
                    search_address
                )

            # 4. Neighborhood demographic profiling
            if query.include_demographics:
                self.logger.info("Profiling neighborhood demographics")
                report.demographic_profile = self.profile_neighborhood_demographics(
                    search_address
                )

            # 5. Movement pattern analysis for current residents
            for resident in report.current_residents:
                if resident.name:
                    pattern = self.analyze_movement_patterns(
                        resident.name, search_address
                    )
                    if pattern.address_history:
                        report.movement_patterns.append(pattern)

            # 6. Address verification
            self.logger.info("Performing address verification")
            verification = self.verify_address(search_address)
            report.verification_status = verification

            # 7. Risk indicators assessment
            risk_indicators = []

            # High turnover risk
            if len(report.historical_residents) > 5:
                risk_indicators.append(
                    {
                        "type": "high_turnover",
                        "description": "High resident turnover rate",
                        "severity": "medium",
                    }
                )

            # Verification issues
            if verification.get("verification_level") in ["questionable", "invalid"]:
                risk_indicators.append(
                    {
                        "type": "verification_issue",
                        "description": "Address verification concerns",
                        "severity": "high",
                    }
                )

            # Multiple current residents (potential overcrowding)
            if len(report.current_residents) > 4:
                risk_indicators.append(
                    {
                        "type": "overcrowding",
                        "description": "Multiple residents at single address",
                        "severity": "low",
                    }
                )

            report.risk_indicators = risk_indicators

            # 8. Calculate overall confidence score
            confidence_factors = []

            if report.validation_result:
                confidence_factors.append(report.validation_result.quality_score)

            if report.current_residents:
                avg_resident_confidence = statistics.mean(
                    r.confidence_score for r in report.current_residents
                )
                confidence_factors.append(avg_resident_confidence)

            if report.ownership_records:
                avg_ownership_confidence = statistics.mean(
                    o.confidence_score for o in report.ownership_records
                )
                confidence_factors.append(avg_ownership_confidence)

            if verification.get("verification_level") == "confirmed":
                confidence_factors.append(0.95)
            elif verification.get("verification_level") == "likely":
                confidence_factors.append(0.8)
            elif verification.get("verification_level") == "possible":
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.3)

            if confidence_factors:
                report.confidence_score = statistics.mean(confidence_factors)
            else:
                report.confidence_score = 0.0

            self.logger.info(
                f"Address intelligence completed with confidence {report.confidence_score:.2f}"
            )

        except Exception as e:
            logger.error(f"Comprehensive address search failed: {e}")
            report.confidence_score = 0.0

        return report

    def query(
        self, query_params: Dict[str, Any], **kwargs
    ) -> AddressIntelligenceReport:
        """
        Execute query using dict parameters (BaseIntelligenceAgent interface)

        Args:
            query_params: Dictionary of query parameters
            **kwargs: Additional arguments

        Returns:
            AddressIntelligenceReport
        """
        # Convert dict to AddressLookupQuery
        query = AddressLookupQuery(**query_params)
        return self.search_comprehensive(query)

    def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Get latitude/longitude coordinates for address

        Args:
            address: Address to geocode

        Returns:
            Dictionary with latitude and longitude, or None if not found
        """
        try:
            parsed = self.parse_address(address)
            search_params = {"geocode_only": True}

            if parsed.get("street_number") and parsed.get("street_name"):
                search_params[
                    "address"
                ] = f"{parsed['street_number']} {parsed['street_name']}"
            if parsed.get("city"):
                search_params["city"] = parsed["city"]
            if parsed.get("state"):
                search_params["state"] = parsed["state"]
            if parsed.get("zip_code"):
                search_params["zip"] = parsed["zip_code"]

            response = self.make_request(
                method="GET",
                url=f"{self.enformion_client.base_url}/geocode",
                params=search_params,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("latitude") and data.get("longitude"):
                    return {
                        "latitude": float(data["latitude"]),
                        "longitude": float(data["longitude"]),
                        "accuracy": data.get("accuracy", "unknown"),
                    }

        except Exception as e:
            logger.error(f"Geocoding failed for {address}: {e}")

        return None

    def health_check(self) -> Dict[str, Any]:
        """Perform health check for AddressSearchAgent"""
        base_health = super().health_check()

        try:
            # Test basic address validation functionality
            test_address = "123 Main Street, Anytown, NY 12345"
            validation = self.validate_address(test_address)

            base_health.update(
                {
                    "address_search_ready": True,
                    "validation_functional": validation.quality_score > 0,
                    "person_search_integration": self.person_search_agent is not None,
                }
            )

        except Exception as e:
            base_health.update({"address_search_ready": False, "error": str(e)})

        return base_health
