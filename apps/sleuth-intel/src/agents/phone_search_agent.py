"""
PhoneSearchAgent for Sleuth Intel
Implements comprehensive phone lookup using EnformionGO /reverse-phone-search endpoint
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..agents.base_agent import (
    BaseIntelligenceAgent,
    CacheConfig,
    RateLimitConfig,
    RetryConfig,
)
from ..core.secure_api_locker import APICredential
from ..models.person import (
    Address,
    Demographics,
    Email,
    PersonName,
    PersonProfile,
    Phone,
    PhoneType,
)
from ..providers.enformion_client import EnformionAPIError, EnformionClient

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk assessment levels for phone numbers"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PhoneLineType(str, Enum):
    """Enhanced phone line type classifications"""

    MOBILE = "mobile"
    LANDLINE = "landline"
    VOIP = "voip"
    TOLL_FREE = "toll_free"
    PAGING = "paging"
    PAYPHONE = "payphone"
    SATELLITE = "satellite"
    UNKNOWN = "unknown"


@dataclass
class PhoneCarrierInfo:
    """Phone carrier information"""

    name: Optional[str] = None
    type: Optional[str] = None  # wireless, wireline, voip
    location: Optional[str] = None
    original_network: Optional[str] = None
    is_ported: bool = False
    port_date: Optional[datetime] = None
    confidence: float = 0.0


@dataclass
class PhoneMetadata:
    """Enhanced phone number metadata"""

    area_code: str
    exchange: str
    subscriber: str
    country_code: str = "1"
    formatted_national: str = ""
    formatted_international: str = ""
    is_valid: bool = True
    is_possible: bool = True
    number_type: PhoneLineType = PhoneLineType.UNKNOWN
    geographic_description: Optional[str] = None
    timezone: Optional[str] = None


@dataclass
class FraudRiskAssessment:
    """Fraud risk assessment for phone number"""

    overall_risk: RiskLevel = RiskLevel.LOW
    spam_score: float = 0.0
    fraud_indicators: List[str] = None
    suspicious_patterns: List[str] = None
    reputation_score: float = 0.0
    complaint_count: int = 0
    blacklist_matches: List[str] = None

    def __post_init__(self):
        if self.fraud_indicators is None:
            self.fraud_indicators = []
        if self.suspicious_patterns is None:
            self.suspicious_patterns = []
        if self.blacklist_matches is None:
            self.blacklist_matches = []


@dataclass
class PhoneHistoryEntry:
    """Historical phone number data entry"""

    timestamp: datetime
    owner_name: Optional[str] = None
    carrier: Optional[str] = None
    line_type: Optional[str] = None
    location: Optional[str] = None
    status: str = "active"  # active, disconnected, ported
    confidence: float = 0.0


@dataclass
class PhoneLookupResult:
    """Comprehensive phone lookup result"""

    phone_number: str
    formatted_number: str
    metadata: PhoneMetadata
    carrier_info: PhoneCarrierInfo
    owner_info: Optional[PersonProfile] = None
    fraud_assessment: Optional[FraudRiskAssessment] = None
    history: List[PhoneHistoryEntry] = None
    related_numbers: List[str] = None
    confidence_score: float = 0.0
    lookup_timestamp: datetime = None
    raw_response: Optional[Dict] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.related_numbers is None:
            self.related_numbers = []
        if self.lookup_timestamp is None:
            self.lookup_timestamp = datetime.now()


class PhoneSearchAgent(BaseIntelligenceAgent):
    """
    Advanced phone search agent using EnformionGO API

    Features:
    - Phone number validation and formatting
    - Reverse phone lookup with owner identification
    - Carrier and line type detection
    - Historical phone data analysis
    - Spam/fraud risk assessment
    - Integration with PersonSearchAgent for detailed owner info
    - Comprehensive phone number utilities
    """

    # Known spam/fraud patterns
    FRAUD_PATTERNS = [
        r"^1?8(00|33|44|55|66|77|88)\d{7}$",  # Common spam toll-free patterns
        r"^1?900\d{7}$",  # Premium rate numbers
        r"^(\d)\1{9}$",  # Repeated digits (e.g., 1111111111)
    ]

    # Common spam area codes (update based on current data)
    HIGH_RISK_AREA_CODES = {
        "216",
        "218",
        "712",
        "319",
        "563",  # Known spam hotspots
        "000",
        "911",
        "411",
        "555",  # Invalid/test codes
    }

    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        enable_person_enrichment: bool = True,
        fraud_detection_threshold: float = 0.7,
        include_historical_data: bool = True,
    ):
        # Phone search specific rate limits (conservative for phone lookups)
        default_rate_config = RateLimitConfig(
            requests_per_second=0.33,  # 3 seconds between requests
            requests_per_minute=18,
            requests_per_hour=400,
            requests_per_day=1500,
            burst_size=2,
        )

        # Extended cache for phone searches (phone data changes less frequently)
        default_cache_config = CacheConfig(
            enabled=True, ttl_seconds=10800, max_entries=1000, compress=True  # 3 hours
        )

        super().__init__(
            provider="enformion",
            agent_name="PhoneSearchAgent",
            rate_limit_config=rate_limit_config or default_rate_config,
            retry_config=retry_config,
            cache_config=cache_config or default_cache_config,
            custom_headers={"X-Agent-Type": "phone-search"},
            timeout=45,
        )

        # Configuration
        self.enable_person_enrichment = enable_person_enrichment
        self.fraud_detection_threshold = fraud_detection_threshold
        self.include_historical_data = include_historical_data

        # Initialize EnformionGO client
        self.enformion_client = EnformionClient()

        # Initialize PersonSearchAgent if enrichment enabled
        self._person_agent = None
        if enable_person_enrichment:
            try:
                from .person_search_agent import PersonSearchAgent

                self._person_agent = PersonSearchAgent()
                logger.info("PersonSearchAgent integration enabled")
            except ImportError:
                logger.warning(
                    "PersonSearchAgent not available, owner enrichment disabled"
                )
                self.enable_person_enrichment = False

        logger.info(
            f"Initialized PhoneSearchAgent with fraud_threshold={fraud_detection_threshold}"
        )

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

    def _validate_phone_number(self, phone: str) -> bool:
        """Basic phone number validation"""
        if not phone:
            return False

        # Clean phone number
        cleaned = self._clean_phone_number(phone)

        # Check length (US numbers should be 10-11 digits)
        if len(cleaned) < 10 or len(cleaned) > 11:
            return False

        # Check for 11-digit numbers starting with 1
        if len(cleaned) == 11 and not cleaned.startswith("1"):
            return False

        # Check for invalid area codes
        area_code = cleaned[-10:-7] if len(cleaned) == 11 else cleaned[:3]
        if area_code in ("000", "911", "411", "555"):
            return False

        # Check for valid area code format (first digit 2-9, second digit 0-9)
        if not (area_code[0] in "23456789" and area_code[1].isdigit()):
            return False

        return True

    def _clean_phone_number(self, phone: str) -> str:
        """Clean phone number to digits only"""
        return "".join(filter(str.isdigit, phone))

    def _format_phone_number(self, phone: str, format_type: str = "national") -> str:
        """Format phone number for display"""
        cleaned = self._clean_phone_number(phone)

        if len(cleaned) == 10:
            if format_type == "international":
                return f"+1 ({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
            else:  # national format
                return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned.startswith("1"):
            if format_type == "international":
                return f"+1 ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"
            else:  # national format
                return f"({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"

        return cleaned  # Return as-is if can't format

    def _parse_phone_number(self, phone: str) -> PhoneMetadata:
        """Parse phone number into components"""
        cleaned = self._clean_phone_number(phone)

        if len(cleaned) == 10:
            country_code = "1"
            national = cleaned
        elif len(cleaned) == 11 and cleaned.startswith("1"):
            country_code = "1"
            national = cleaned[1:]
        else:
            raise ValueError(f"Invalid phone number format: {phone}")

        area_code = national[:3]
        exchange = national[3:6]
        subscriber = national[6:]

        # Determine basic phone type based on area code
        phone_type = self._classify_phone_type(area_code, exchange)

        # Generate formatted versions
        formatted_national = f"({area_code}) {exchange}-{subscriber}"
        formatted_international = (
            f"+{country_code} ({area_code}) {exchange}-{subscriber}"
        )

        # Get geographic info
        geo_description = self._get_geographic_description(area_code)

        return PhoneMetadata(
            area_code=area_code,
            exchange=exchange,
            subscriber=subscriber,
            country_code=country_code,
            formatted_national=formatted_national,
            formatted_international=formatted_international,
            is_valid=self._validate_phone_number(phone),
            is_possible=True,  # Already validated above
            number_type=phone_type,
            geographic_description=geo_description,
        )

    def _classify_phone_type(self, area_code: str, exchange: str) -> PhoneLineType:
        """Classify phone type based on numbering patterns"""
        # Toll-free numbers
        if area_code in ("800", "833", "844", "855", "866", "877", "888"):
            return PhoneLineType.TOLL_FREE

        # Premium rate
        if area_code == "900":
            return PhoneLineType.UNKNOWN  # Premium rate, not common in modern usage

        # This is a simplified classification - actual carrier data is more accurate
        return PhoneLineType.UNKNOWN

    def _get_geographic_description(self, area_code: str) -> Optional[str]:
        """Get basic geographic description for area code"""
        # This is a simplified mapping - in production, use a comprehensive database
        area_code_map = {
            "212": "New York, NY",
            "213": "Los Angeles, CA",
            "214": "Dallas, TX",
            "305": "Miami, FL",
            "415": "San Francisco, CA",
            "617": "Boston, MA",
            "702": "Las Vegas, NV",
            "713": "Houston, TX",
            "773": "Chicago, IL",
            "800": "Toll Free",
            "833": "Toll Free",
            "844": "Toll Free",
            "855": "Toll Free",
            "866": "Toll Free",
            "877": "Toll Free",
            "888": "Toll Free",
        }

        return area_code_map.get(area_code)

    def _assess_fraud_risk(
        self,
        phone: str,
        carrier_info: PhoneCarrierInfo,
        owner_info: Optional[PersonProfile] = None,
    ) -> FraudRiskAssessment:
        """Assess fraud risk for phone number"""
        assessment = FraudRiskAssessment()
        risk_score = 0.0

        cleaned_phone = self._clean_phone_number(phone)

        # Check against known fraud patterns
        for pattern in self.FRAUD_PATTERNS:
            if re.match(pattern, cleaned_phone):
                assessment.fraud_indicators.append(f"Matches fraud pattern: {pattern}")
                risk_score += 0.3

        # Check high-risk area codes
        area_code = (
            cleaned_phone[-10:-7] if len(cleaned_phone) == 11 else cleaned_phone[:3]
        )
        if area_code in self.HIGH_RISK_AREA_CODES:
            assessment.fraud_indicators.append(f"High-risk area code: {area_code}")
            risk_score += 0.4

        # Check for VOIP indicators (higher risk)
        if carrier_info and carrier_info.type == "voip":
            assessment.suspicious_patterns.append("VOIP number")
            risk_score += 0.2

        # Check for recently ported numbers
        if carrier_info and carrier_info.is_ported:
            if (
                carrier_info.port_date
                and carrier_info.port_date > datetime.now() - timedelta(days=30)
            ):
                assessment.suspicious_patterns.append("Recently ported number")
                risk_score += 0.15

        # Check owner information availability
        if not owner_info:
            assessment.suspicious_patterns.append("No owner information available")
            risk_score += 0.1

        # Calculate spam score and risk level
        assessment.spam_score = min(1.0, risk_score)
        assessment.reputation_score = max(0.0, 1.0 - risk_score)

        if risk_score >= 0.8:
            assessment.overall_risk = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            assessment.overall_risk = RiskLevel.HIGH
        elif risk_score >= 0.3:
            assessment.overall_risk = RiskLevel.MEDIUM
        else:
            assessment.overall_risk = RiskLevel.LOW

        return assessment

    def _extract_carrier_info(self, raw_response: Dict) -> PhoneCarrierInfo:
        """Extract carrier information from API response"""
        carrier_info = PhoneCarrierInfo()

        # Extract carrier name
        carrier_info.name = raw_response.get(
            "carrier", raw_response.get("service_provider")
        )

        # Extract line type
        line_type = raw_response.get("line_type", raw_response.get("phone_type", ""))
        if "wireless" in line_type.lower() or "mobile" in line_type.lower():
            carrier_info.type = "wireless"
        elif "landline" in line_type.lower() or "wireline" in line_type.lower():
            carrier_info.type = "wireline"
        elif "voip" in line_type.lower():
            carrier_info.type = "voip"

        # Extract location
        carrier_info.location = raw_response.get(
            "carrier_location", raw_response.get("location")
        )

        # Check for porting information
        if raw_response.get("ported") or raw_response.get("is_ported"):
            carrier_info.is_ported = True
            port_date = raw_response.get("port_date")
            if port_date:
                try:
                    carrier_info.port_date = datetime.fromisoformat(port_date)
                except (ValueError, TypeError):
                    pass

        # Set confidence based on available data
        data_points = sum(
            [
                bool(carrier_info.name),
                bool(carrier_info.type),
                bool(carrier_info.location),
                bool(carrier_info.is_ported),
            ]
        )
        carrier_info.confidence = min(1.0, data_points / 4.0)

        return carrier_info

    def _enrich_with_person_data(self, phone: str) -> Optional[PersonProfile]:
        """Enrich phone data with person information"""
        if not self._person_agent:
            return None

        try:
            from ..models.query import PersonSearchQuery

            # Search for person by phone
            query = PersonSearchQuery(phone=phone, max_results=1)
            results = self._person_agent.search(query)

            if results:
                return results[0]  # Return best match

        except Exception as e:
            logger.warning(f"Failed to enrich phone data with person info: {e}")

        return None

    def _generate_phone_cache_key(self, phone: str) -> str:
        """Generate cache key for phone search"""
        cleaned = self._clean_phone_number(phone)
        return f"phone_lookup_{hashlib.sha256(cleaned.encode()).hexdigest()[:16]}"

    def reverse_phone_lookup(
        self,
        phone: str,
        include_owner_details: bool = None,
        include_fraud_assessment: bool = True,
        use_cache: bool = True,
    ) -> PhoneLookupResult:
        """
        Perform reverse phone lookup

        Args:
            phone: Phone number to lookup
            include_owner_details: Whether to include detailed owner information
            include_fraud_assessment: Whether to perform fraud risk assessment
            use_cache: Whether to use cached results

        Returns:
            PhoneLookupResult with comprehensive phone information

        Raises:
            ValueError: If phone number is invalid
            EnformionAPIError: If API request fails
        """
        # Validate phone number
        if not self._validate_phone_number(phone):
            raise ValueError(f"Invalid phone number: {phone}")

        cleaned_phone = self._clean_phone_number(phone)

        # Set default for owner details
        if include_owner_details is None:
            include_owner_details = self.enable_person_enrichment

        # Check cache
        cache_key = self._generate_phone_cache_key(phone) if use_cache else None
        if cache_key:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached phone lookup for {phone}")
                return PhoneLookupResult(**cached_result)

        try:
            # Parse phone metadata
            metadata = self._parse_phone_number(phone)

            # Perform API lookup
            logger.info(f"Performing reverse phone lookup for {cleaned_phone}")
            raw_response = self.enformion_client.reverse_phone_search(cleaned_phone)

            # Extract carrier information
            carrier_info = self._extract_carrier_info(raw_response)

            # Get owner information if requested
            owner_info = None
            if include_owner_details:
                owner_info = self._enrich_with_person_data(cleaned_phone)

            # Perform fraud assessment if requested
            fraud_assessment = None
            if include_fraud_assessment:
                fraud_assessment = self._assess_fraud_risk(
                    cleaned_phone, carrier_info, owner_info
                )

            # Calculate overall confidence score
            confidence_factors = [
                metadata.is_valid,
                bool(carrier_info.name),
                bool(owner_info),
                fraud_assessment.overall_risk in [RiskLevel.LOW, RiskLevel.MEDIUM]
                if fraud_assessment
                else True,
            ]
            confidence_score = sum(confidence_factors) / len(confidence_factors)

            # Create result
            result = PhoneLookupResult(
                phone_number=cleaned_phone,
                formatted_number=metadata.formatted_national,
                metadata=metadata,
                carrier_info=carrier_info,
                owner_info=owner_info,
                fraud_assessment=fraud_assessment,
                confidence_score=confidence_score,
                raw_response=raw_response,
            )

            # Cache result
            if cache_key:
                # Convert to dict for caching
                result_dict = {
                    "phone_number": result.phone_number,
                    "formatted_number": result.formatted_number,
                    "metadata": result.metadata.__dict__,
                    "carrier_info": result.carrier_info.__dict__,
                    "owner_info": result.owner_info.model_dump()
                    if result.owner_info
                    else None,
                    "fraud_assessment": result.fraud_assessment.__dict__
                    if result.fraud_assessment
                    else None,
                    "confidence_score": result.confidence_score,
                    "lookup_timestamp": result.lookup_timestamp.isoformat(),
                    "raw_response": result.raw_response,
                }
                self.cache.set(cache_key, result_dict)

            logger.info(
                f"Phone lookup completed for {phone} with confidence {confidence_score:.2f}"
            )
            return result

        except EnformionAPIError as e:
            logger.error(f"EnformionGO API error during phone lookup: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during phone lookup: {e}")
            raise

    def get_carrier_info(self, phone: str) -> PhoneCarrierInfo:
        """Get carrier information for phone number"""
        result = self.reverse_phone_lookup(
            phone, include_owner_details=False, include_fraud_assessment=False
        )
        return result.carrier_info

    def get_line_type(self, phone: str) -> PhoneLineType:
        """Determine line type for phone number"""
        result = self.reverse_phone_lookup(
            phone, include_owner_details=False, include_fraud_assessment=False
        )
        return result.metadata.number_type

    def identify_owner(self, phone: str) -> Optional[PersonProfile]:
        """Identify owner of phone number"""
        result = self.reverse_phone_lookup(
            phone, include_owner_details=True, include_fraud_assessment=False
        )
        return result.owner_info

    def assess_spam_risk(self, phone: str) -> FraudRiskAssessment:
        """Assess spam/fraud risk for phone number"""
        result = self.reverse_phone_lookup(
            phone, include_owner_details=False, include_fraud_assessment=True
        )
        return result.fraud_assessment

    def batch_phone_lookup(
        self,
        phone_numbers: List[str],
        max_concurrent: int = 3,
        include_owner_details: bool = None,
    ) -> Dict[str, PhoneLookupResult]:
        """
        Perform batch phone lookups with rate limiting

        Args:
            phone_numbers: List of phone numbers to lookup
            max_concurrent: Maximum concurrent requests
            include_owner_details: Whether to include owner details

        Returns:
            Dictionary mapping phone numbers to lookup results
        """
        results = {}

        if include_owner_details is None:
            include_owner_details = self.enable_person_enrichment

        # Process in batches to respect rate limits
        for i in range(0, len(phone_numbers), max_concurrent):
            batch = phone_numbers[i : i + max_concurrent]

            for phone in batch:
                try:
                    result = self.reverse_phone_lookup(
                        phone, include_owner_details=include_owner_details
                    )
                    results[phone] = result
                except Exception as e:
                    logger.error(f"Failed to lookup phone {phone}: {e}")
                    continue

                # Small delay between requests in batch
                if len(batch) > 1:
                    time.sleep(0.5)

        logger.info(
            f"Completed batch lookup for {len(results)} of {len(phone_numbers)} phone numbers"
        )
        return results

    def find_related_numbers(self, phone: str) -> List[str]:
        """Find phone numbers related to the given number"""
        # Get owner information
        owner_info = self.identify_owner(phone)

        if not owner_info:
            return []

        # Extract all phone numbers associated with the owner
        related = []
        for phone_obj in owner_info.phones:
            if phone_obj.number != self._clean_phone_number(phone):
                related.append(phone_obj.number)

        return related

    def validate_phone_format(self, phone: str) -> Tuple[bool, str]:
        """
        Validate phone number format

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return False, "Phone number is empty"

        cleaned = self._clean_phone_number(phone)

        if len(cleaned) < 10:
            return False, "Phone number too short (minimum 10 digits)"

        if len(cleaned) > 11:
            return False, "Phone number too long (maximum 11 digits)"

        if len(cleaned) == 11 and not cleaned.startswith("1"):
            return False, "11-digit numbers must start with 1"

        area_code = cleaned[-10:-7] if len(cleaned) == 11 else cleaned[:3]

        if not area_code[0] in "23456789":
            return False, f"Invalid area code: {area_code} (first digit must be 2-9)"

        if area_code in self.HIGH_RISK_AREA_CODES:
            return False, f"Invalid area code: {area_code}"

        return True, "Phone number is valid"

    def normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number to standard format"""
        if not self._validate_phone_number(phone):
            raise ValueError(f"Cannot normalize invalid phone number: {phone}")

        cleaned = self._clean_phone_number(phone)

        # Ensure 10-digit format for US numbers
        if len(cleaned) == 11 and cleaned.startswith("1"):
            return cleaned[1:]  # Remove country code

        return cleaned

    def query(self, query_params: Dict[str, Any], **kwargs) -> PhoneLookupResult:
        """
        Execute query using dict parameters (BaseIntelligenceAgent interface)

        Args:
            query_params: Dictionary with 'phone' key
            **kwargs: Additional arguments

        Returns:
            PhoneLookupResult
        """
        phone = query_params.get("phone")
        if not phone:
            raise ValueError("Query must include 'phone' parameter")

        return self.reverse_phone_lookup(phone, **kwargs)

    def health_check(self) -> Dict[str, Any]:
        """Perform health check for PhoneSearchAgent"""
        base_health = super().health_check()

        try:
            # Test phone validation
            test_phone = "5551234567"
            is_valid, _ = self.validate_phone_format(test_phone)

            base_health.update(
                {
                    "phone_validation_ready": is_valid,
                    "person_enrichment_enabled": self.enable_person_enrichment,
                    "fraud_detection_enabled": True,
                    "fraud_threshold": self.fraud_detection_threshold,
                    "historical_data_enabled": self.include_historical_data,
                }
            )

        except Exception as e:
            base_health.update({"phone_search_ready": False, "error": str(e)})

        return base_health
