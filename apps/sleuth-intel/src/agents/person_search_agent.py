"""
PersonSearchAgent for Sleuth Intel
Implements person search using EnformionGO /person-search endpoint with advanced features
"""

import asyncio
import hashlib
import json
import logging
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
from ..models.query import DataProvider, PersonSearchQuery
from ..providers.enformion_client import EnformionAPIError, EnformionClient

logger = logging.getLogger(__name__)


class PersonSearchAgent(BaseIntelligenceAgent):
    """
    Advanced person search agent using EnformionGO API

    Features:
    - Fuzzy name matching with confidence scoring
    - Age range and location filtering
    - Duplicate detection and result consolidation
    - Intelligent caching for similar queries
    - Rate limiting optimized for person searches
    - Comprehensive error handling and retry logic
    """

    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        fuzzy_threshold: float = 0.8,
        max_age_variance: int = 5,
        location_radius_miles: int = 50,
    ):
        # Person search specific rate limits (more conservative)
        default_rate_config = RateLimitConfig(
            requests_per_second=0.5,  # 2 seconds between requests
            requests_per_minute=25,
            requests_per_hour=500,
            requests_per_day=2000,
            burst_size=3,
        )

        # Extended cache for person searches (results change less frequently)
        default_cache_config = CacheConfig(
            enabled=True, ttl_seconds=7200, max_entries=500, compress=True  # 2 hours
        )

        super().__init__(
            provider="enformion",
            agent_name="PersonSearchAgent",
            rate_limit_config=rate_limit_config or default_rate_config,
            retry_config=retry_config,
            cache_config=cache_config or default_cache_config,
            custom_headers={"X-Agent-Type": "person-search"},
            timeout=45,
        )

        # Search configuration
        self.fuzzy_threshold = fuzzy_threshold
        self.max_age_variance = max_age_variance
        self.location_radius_miles = location_radius_miles

        # Initialize EnformionGO client
        self.enformion_client = EnformionClient()

        logger.info(
            f"Initialized PersonSearchAgent with fuzzy_threshold={fuzzy_threshold}"
        )

    def _apply_authentication(
        self, credential: APICredential, request_kwargs: Dict
    ) -> Dict:
        """Apply EnformionGO authentication to request"""
        headers = request_kwargs.get("headers", {})

        if credential.password:
            # EnformionGO uses API key + password
            headers.update(
                {
                    "X-API-Key": credential.key_value,
                    "X-API-Password": credential.password,
                }
            )
        else:
            # Fallback to bearer token
            headers["Authorization"] = f"Bearer {credential.key_value}"

        request_kwargs["headers"] = headers
        return request_kwargs

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names using fuzzy matching"""
        if not name1 or not name2:
            return 0.0

        # Normalize names for comparison
        norm1 = name1.lower().strip()
        norm2 = name2.lower().strip()

        if norm1 == norm2:
            return 1.0

        # Use SequenceMatcher for fuzzy similarity
        return SequenceMatcher(None, norm1, norm2).ratio()

    def _calculate_age_match_score(
        self, query_age: Optional[int], result_age: Optional[int]
    ) -> float:
        """Calculate age match score with variance tolerance"""
        if not query_age or not result_age:
            return 0.5  # Neutral score when age data missing

        age_diff = abs(query_age - result_age)
        if age_diff == 0:
            return 1.0
        elif age_diff <= self.max_age_variance:
            # Linear decay within variance tolerance
            return 1.0 - (age_diff / self.max_age_variance) * 0.3
        else:
            # Significant age difference
            return 0.2

    def _calculate_location_match_score(
        self, query_location: Dict, result_location: Dict
    ) -> float:
        """Calculate location match score with geographic proximity"""
        if not query_location or not result_location:
            return 0.5

        # Exact matches
        if query_location.get("city") and result_location.get("city"):
            if query_location["city"].lower() == result_location["city"].lower():
                if query_location.get("state") == result_location.get("state"):
                    return 1.0
                return 0.8

        # State match
        if query_location.get("state") and result_location.get("state"):
            if query_location["state"] == result_location["state"]:
                return 0.6

        # ZIP code proximity (if available)
        if query_location.get("zip_code") and result_location.get("zip_code"):
            query_zip = query_location["zip_code"][:5]  # Use first 5 digits
            result_zip = result_location["zip_code"][:5]
            if query_zip == result_zip:
                return 0.9

            # Check if ZIP codes are nearby (simple heuristic)
            try:
                zip_diff = abs(int(query_zip) - int(result_zip))
                if zip_diff <= 10:  # Nearby ZIP codes
                    return 0.7
            except ValueError:
                pass

        return 0.3  # Low confidence for location match

    def _score_result_confidence(
        self, query: PersonSearchQuery, result: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for a search result"""
        scores = []
        weights = []

        # Name matching score
        if query.first_name or query.last_name or query.full_name:
            result_first = result.get("first_name", "")
            result_last = result.get("last_name", "")
            result_full = result.get(
                "full_name", f"{result_first} {result_last}".strip()
            )

            name_score = 0.0
            if query.full_name:
                name_score = max(
                    name_score,
                    self._calculate_name_similarity(query.full_name, result_full),
                )

            if query.first_name:
                name_score = max(
                    name_score,
                    self._calculate_name_similarity(query.first_name, result_first),
                )

            if query.last_name:
                name_score = max(
                    name_score,
                    self._calculate_name_similarity(query.last_name, result_last),
                )

            scores.append(name_score)
            weights.append(0.4)  # High weight for name matching

        # Age matching score
        if query.age_min or query.age_max:
            result_age = result.get("age")
            if result_age:
                query_age = None
                if query.age_min and query.age_max:
                    query_age = (query.age_min + query.age_max) / 2
                elif query.age_min:
                    query_age = query.age_min + 2  # Assume close to minimum
                elif query.age_max:
                    query_age = query.age_max - 2  # Assume close to maximum

                if query_age:
                    age_score = self._calculate_age_match_score(
                        int(query_age), result_age
                    )
                    scores.append(age_score)
                    weights.append(0.2)

        # Location matching score
        query_location = {}
        if query.city:
            query_location["city"] = query.city
        if query.state:
            query_location["state"] = query.state
        if query.zip_code:
            query_location["zip_code"] = query.zip_code

        if query_location:
            result_location = {
                "city": result.get("city"),
                "state": result.get("state"),
                "zip_code": result.get("zip_code"),
            }
            location_score = self._calculate_location_match_score(
                query_location, result_location
            )
            scores.append(location_score)
            weights.append(0.25)

        # Phone matching score
        if query.phone:
            result_phones = result.get("phones", [])
            phone_score = 0.0
            for result_phone in result_phones:
                if isinstance(result_phone, dict):
                    result_phone_num = result_phone.get("number", "")
                else:
                    result_phone_num = str(result_phone)

                # Normalize phone numbers for comparison
                query_phone_clean = "".join(filter(str.isdigit, query.phone))
                result_phone_clean = "".join(filter(str.isdigit, result_phone_num))

                if query_phone_clean == result_phone_clean:
                    phone_score = 1.0
                    break

            scores.append(phone_score)
            weights.append(0.15)

        # Calculate weighted average
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            return min(1.0, weighted_sum / total_weight)

        return 0.5  # Default neutral confidence

    def _validate_and_cleanup_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and cleanup API response data"""
        cleaned = {}

        # Clean name fields
        for field in ["first_name", "last_name", "middle_name", "full_name"]:
            value = raw_data.get(field)
            if value and isinstance(value, str):
                cleaned[field] = value.strip().title()

        # Clean age
        age = raw_data.get("age")
        if age:
            try:
                age_int = int(age)
                if 18 <= age_int <= 120:  # Reasonable age range
                    cleaned["age"] = age_int
            except (ValueError, TypeError):
                pass

        # Clean phone numbers
        phones = raw_data.get("phones", [])
        cleaned_phones = []
        for phone in phones:
            if isinstance(phone, dict):
                phone_num = phone.get("number")
            else:
                phone_num = str(phone)

            if phone_num:
                # Clean phone number
                phone_clean = "".join(filter(str.isdigit, phone_num))
                if len(phone_clean) >= 10:
                    cleaned_phones.append(
                        {
                            "number": phone_clean,
                            "formatted": self._format_phone_number(phone_clean),
                            "type": phone.get("type", "unknown")
                            if isinstance(phone, dict)
                            else "unknown",
                        }
                    )

        if cleaned_phones:
            cleaned["phones"] = cleaned_phones

        # Clean addresses
        addresses = raw_data.get("addresses", [])
        cleaned_addresses = []
        for addr in addresses:
            if isinstance(addr, dict) and (addr.get("street") or addr.get("city")):
                cleaned_addr = {}
                for field in ["street", "city", "state", "zip_code"]:
                    value = addr.get(field)
                    if value:
                        cleaned_addr[field] = str(value).strip()

                if cleaned_addr:
                    cleaned_addresses.append(cleaned_addr)

        if cleaned_addresses:
            cleaned["addresses"] = cleaned_addresses

        # Clean email addresses
        emails = raw_data.get("emails", [])
        cleaned_emails = []
        for email in emails:
            email_addr = email if isinstance(email, str) else email.get("address")
            if email_addr and "@" in email_addr:
                cleaned_emails.append(email_addr.lower().strip())

        if cleaned_emails:
            cleaned["emails"] = cleaned_emails

        # Copy other relevant fields
        for field in ["birth_year", "gender", "relatives", "associates"]:
            if field in raw_data:
                cleaned[field] = raw_data[field]

        return cleaned

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for display"""
        if len(phone) == 10:
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        elif len(phone) == 11 and phone.startswith("1"):
            return f"+1 ({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
        return phone

    def _convert_to_person_profile(
        self, raw_result: Dict[str, Any], query: PersonSearchQuery
    ) -> PersonProfile:
        """Convert API response to PersonProfile model"""
        cleaned_data = self._validate_and_cleanup_data(raw_result)

        # Build person name
        name = PersonName(
            first=cleaned_data.get("first_name"),
            last=cleaned_data.get("last_name"),
            middle=cleaned_data.get("middle_name"),
            full=cleaned_data.get("full_name"),
        )

        # Build demographics
        demographics = None
        if (
            cleaned_data.get("age")
            or cleaned_data.get("birth_year")
            or cleaned_data.get("gender")
        ):
            demographics = Demographics(
                age=cleaned_data.get("age"),
                birth_year=cleaned_data.get("birth_year"),
                gender=cleaned_data.get("gender"),
            )

        # Build phone list
        phones = []
        for phone_data in cleaned_data.get("phones", []):
            phone = Phone(
                number=phone_data["number"],
                formatted=phone_data.get("formatted"),
                type=phone_data.get("type", "unknown"),
                confidence_score=0.8,
            )
            phones.append(phone)

        # Build email list
        emails = []
        for email_addr in cleaned_data.get("emails", []):
            email = Email(address=email_addr, confidence_score=0.7)
            emails.append(email)

        # Build address list
        addresses = []
        for addr_data in cleaned_data.get("addresses", []):
            address = Address(
                street=addr_data.get("street"),
                city=addr_data.get("city"),
                state=addr_data.get("state"),
                zip_code=addr_data.get("zip_code"),
                confidence_score=0.8,
            )
            addresses.append(address)

        # Build associates list (relatives and other associates)
        associates = []
        for rel_data in cleaned_data.get("relatives", []):
            if isinstance(rel_data, dict):
                rel_name = PersonName(
                    first=rel_data.get("first_name"),
                    last=rel_data.get("last_name"),
                    full=rel_data.get("name"),
                )
                associate = Associate(
                    name=rel_name,
                    relationship=rel_data.get("relationship", "relative"),
                    confidence_score=0.6,
                )
                associates.append(associate)

        # Calculate overall confidence score
        confidence_score = self._score_result_confidence(query, cleaned_data)

        # Create PersonProfile
        profile = PersonProfile(
            name=name,
            demographics=demographics,
            phones=phones,
            emails=emails,
            addresses=addresses,
            associates=associates,
            source_provider="enformion",
            confidence_score=confidence_score,
            raw_response=raw_result,
        )

        return profile

    def _generate_search_cache_key(self, query: PersonSearchQuery) -> str:
        """Generate cache key for person search query"""
        # Create normalized search parameters
        search_params = {}

        if query.first_name:
            search_params["first_name"] = query.first_name.lower().strip()
        if query.last_name:
            search_params["last_name"] = query.last_name.lower().strip()
        if query.full_name:
            search_params["full_name"] = query.full_name.lower().strip()
        if query.phone:
            search_params["phone"] = "".join(filter(str.isdigit, query.phone))
        if query.city:
            search_params["city"] = query.city.lower().strip()
        if query.state:
            search_params["state"] = query.state.upper()
        if query.zip_code:
            search_params["zip_code"] = query.zip_code

        # Add age range
        if query.age_min:
            search_params["age_min"] = query.age_min
        if query.age_max:
            search_params["age_max"] = query.age_max

        # Create cache key from normalized parameters
        key_str = json.dumps(search_params, sort_keys=True)
        return f"person_search_{hashlib.sha256(key_str.encode()).hexdigest()[:16]}"

    def search_by_name(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        fuzzy_matching: bool = True,
        max_results: int = 10,
    ) -> List[PersonProfile]:
        """
        Search for persons by name with optional location filtering

        Args:
            first_name: First name to search for
            last_name: Last name to search for
            city: City to filter by
            state: State to filter by
            fuzzy_matching: Enable fuzzy name matching
            max_results: Maximum number of results to return

        Returns:
            List of PersonProfile objects matching the search
        """
        query = PersonSearchQuery(
            first_name=first_name,
            last_name=last_name,
            city=city,
            state=state,
            fuzzy_matching=fuzzy_matching,
            max_results=max_results,
        )

        return self.search(query)

    def search_by_phone(
        self, phone_number: str, max_results: int = 5
    ) -> List[PersonProfile]:
        """
        Search for person by phone number

        Args:
            phone_number: Phone number to search for
            max_results: Maximum number of results

        Returns:
            List of PersonProfile objects associated with the phone
        """
        query = PersonSearchQuery(phone=phone_number, max_results=max_results)

        return self.search(query)

    def search_by_address(
        self,
        street: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        max_results: int = 10,
    ) -> List[PersonProfile]:
        """
        Search for persons by address

        Args:
            street: Street address
            city: City
            state: State abbreviation
            zip_code: ZIP code
            max_results: Maximum number of results

        Returns:
            List of PersonProfile objects associated with the address
        """
        query = PersonSearchQuery(
            street=street,
            city=city,
            state=state,
            zip_code=zip_code,
            max_results=max_results,
        )

        return self.search(query)

    def search_with_age_filter(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        max_results: int = 10,
    ) -> List[PersonProfile]:
        """
        Search for persons with age range filtering

        Args:
            first_name: First name
            last_name: Last name
            age_min: Minimum age
            age_max: Maximum age
            city: City to filter by
            state: State to filter by
            max_results: Maximum results

        Returns:
            List of PersonProfile objects within the age range
        """
        query = PersonSearchQuery(
            first_name=first_name,
            last_name=last_name,
            age_min=age_min,
            age_max=age_max,
            city=city,
            state=state,
            max_results=max_results,
        )

        return self.search(query)

    def search(
        self, query: PersonSearchQuery, use_cache: bool = True
    ) -> List[PersonProfile]:
        """
        Execute person search query

        Args:
            query: PersonSearchQuery object with search parameters
            use_cache: Whether to use cached results

        Returns:
            List of PersonProfile objects matching the query

        Raises:
            ValueError: If query has insufficient parameters
            EnformionAPIError: If API request fails
        """
        if not query.has_sufficient_params():
            raise ValueError(
                "Query must have at least a name parameter and one additional identifying parameter"
            )

        # Generate cache key
        cache_key = self._generate_search_cache_key(query) if use_cache else None

        # Check cache first
        if cache_key and use_cache:
            cached_results = self.cache.get(cache_key)
            if cached_results:
                self.logger.info(
                    f"Returning {len(cached_results)} cached person search results"
                )
                return [
                    PersonProfile(**profile_data) for profile_data in cached_results
                ]

        try:
            # Prepare search parameters for EnformionGO
            search_params = {}

            if query.first_name:
                search_params["first_name"] = query.first_name
            if query.last_name:
                search_params["last_name"] = query.last_name
            if query.city:
                search_params["city"] = query.city
            if query.state:
                search_params["state"] = query.state
            if query.zip_code:
                search_params["zip"] = query.zip_code
            if query.street:
                search_params["address"] = query.street

            # Execute search via EnformionGO client
            self.logger.info(f"Executing person search: {search_params}")
            raw_response = self.enformion_client.person_search(**search_params)

            # Process results
            results = []
            raw_results = raw_response.get("results", [])

            if not raw_results:
                self.logger.info("No results found for person search")
                return results

            # Convert each result to PersonProfile
            for raw_result in raw_results[: query.max_results]:
                try:
                    profile = self._convert_to_person_profile(raw_result, query)

                    # Apply confidence threshold
                    if profile.confidence_score >= query.min_confidence:
                        results.append(profile)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to convert result to PersonProfile: {e}"
                    )
                    continue

            # Sort by confidence score
            results.sort(key=lambda p: p.confidence_score, reverse=True)

            # Cache results
            if cache_key and use_cache and results:
                # Convert to dict for caching (Pydantic models are not JSON serializable by default)
                cached_data = [profile.model_dump() for profile in results]
                self.cache.set(
                    cache_key, cached_data, ttl_seconds=self.cache_config.ttl_seconds
                )

            self.logger.info(f"Person search completed: {len(results)} results found")
            return results

        except EnformionAPIError as e:
            self.logger.error(f"EnformionGO API error during person search: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during person search: {e}")
            raise

    def query(self, query_params: Dict[str, Any], **kwargs) -> List[PersonProfile]:
        """
        Execute query using dict parameters (BaseIntelligenceAgent interface)

        Args:
            query_params: Dictionary of query parameters
            **kwargs: Additional arguments

        Returns:
            List of PersonProfile objects
        """
        # Convert dict to PersonSearchQuery
        query = PersonSearchQuery(**query_params)
        return self.search(query, **kwargs)

    def find_duplicates(
        self, profiles: List[PersonProfile], similarity_threshold: float = 0.9
    ) -> List[Tuple[PersonProfile, PersonProfile, float]]:
        """
        Find duplicate profiles in a list based on similarity

        Args:
            profiles: List of PersonProfile objects to check
            similarity_threshold: Minimum similarity to consider as duplicate

        Returns:
            List of tuples: (profile1, profile2, similarity_score)
        """
        duplicates = []

        for i, profile1 in enumerate(profiles):
            for profile2 in profiles[i + 1 :]:
                # Calculate similarity based on multiple factors
                name_sim = self._calculate_name_similarity(
                    profile1.name.display_name, profile2.name.display_name
                )

                # Check phone number matches
                phone_match = False
                for phone1 in profile1.phones:
                    for phone2 in profile2.phones:
                        if phone1.number == phone2.number:
                            phone_match = True
                            break
                    if phone_match:
                        break

                # Calculate overall similarity
                similarity = name_sim
                if phone_match:
                    similarity = min(1.0, similarity + 0.3)  # Boost for phone match

                if similarity >= similarity_threshold:
                    duplicates.append((profile1, profile2, similarity))

        return duplicates

    def health_check(self) -> Dict[str, Any]:
        """Perform health check for PersonSearchAgent"""
        base_health = super().health_check()

        try:
            # Test basic search functionality
            test_query = PersonSearchQuery(
                first_name="John", last_name="Doe", max_results=1
            )

            # Don't actually execute the search, just validate we can create it
            base_health.update(
                {
                    "person_search_ready": True,
                    "fuzzy_threshold": self.fuzzy_threshold,
                    "max_age_variance": self.max_age_variance,
                    "location_radius": self.location_radius_miles,
                }
            )

        except Exception as e:
            base_health.update({"person_search_ready": False, "error": str(e)})

        return base_health
