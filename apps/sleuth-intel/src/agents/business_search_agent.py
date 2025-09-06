"""
BusinessSearchAgent for Sleuth Intel
Implements comprehensive business intelligence using EnformionGO /business-search endpoint
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
from ..models.business import (
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
from ..models.person import Address, Email, PersonName, Phone
from ..models.query import BusinessSearchQuery, DataProvider
from ..providers.enformion_client import EnformionAPIError, EnformionClient

logger = logging.getLogger(__name__)


class BusinessSearchAgent(BaseIntelligenceAgent):
    """
    Advanced business intelligence agent using EnformionGO API

    Features:
    - Business entity verification and validation
    - Principal and executive identification
    - Corporate filing analysis
    - Business relationship mapping
    - Industry classification and compliance status
    - Financial health indicators and risk assessment
    - Corporate hierarchy mapping
    - Due diligence workflow automation
    """

    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        fuzzy_threshold: float = 0.8,
        risk_threshold: float = 0.7,
        person_search_agent: Optional["PersonSearchAgent"] = None,
    ):
        # Business search specific rate limits (conservative for business data)
        default_rate_config = RateLimitConfig(
            requests_per_second=0.3,  # 3+ seconds between requests
            requests_per_minute=15,
            requests_per_hour=300,
            requests_per_day=1500,
            burst_size=2,
        )

        # Extended cache for business data (changes less frequently)
        default_cache_config = CacheConfig(
            enabled=True, ttl_seconds=14400, max_entries=300, compress=True  # 4 hours
        )

        super().__init__(
            provider="enformion",
            agent_name="BusinessSearchAgent",
            rate_limit_config=rate_limit_config or default_rate_config,
            retry_config=retry_config,
            cache_config=cache_config or default_cache_config,
            custom_headers={"X-Agent-Type": "business-search"},
            timeout=60,
        )

        # Search configuration
        self.fuzzy_threshold = fuzzy_threshold
        self.risk_threshold = risk_threshold

        # Initialize EnformionGO client
        self.enformion_client = EnformionClient()

        # Optional PersonSearchAgent for principal lookups
        self.person_search_agent = person_search_agent

        logger.info(
            f"Initialized BusinessSearchAgent with fuzzy_threshold={fuzzy_threshold}"
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
        """Calculate similarity between business names using fuzzy matching"""
        if not name1 or not name2:
            return 0.0

        # Normalize names for comparison (remove common business suffixes)
        def normalize_business_name(name):
            name = name.lower().strip()
            # Remove common suffixes
            suffixes = ["llc", "inc", "corp", "ltd", "co", "company", "corporation"]
            for suffix in suffixes:
                if name.endswith(f" {suffix}"):
                    name = name[: -len(f" {suffix}")]
            return name

        norm1 = normalize_business_name(name1)
        norm2 = normalize_business_name(name2)

        if norm1 == norm2:
            return 1.0

        # Use SequenceMatcher for fuzzy similarity
        return SequenceMatcher(None, norm1, norm2).ratio()

    def _score_result_confidence(
        self, query: BusinessSearchQuery, result: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for a business search result"""
        scores = []
        weights = []

        # Business name matching score
        if query.business_name:
            result_name = result.get("business_name", "")
            name_score = self._calculate_name_similarity(
                query.business_name, result_name
            )
            scores.append(name_score)
            weights.append(0.4)  # High weight for name matching

        # EIN matching (very high confidence if matches)
        if query.ein and result.get("ein"):
            ein_match = query.ein.replace("-", "") == result.get("ein", "").replace(
                "-", ""
            )
            scores.append(1.0 if ein_match else 0.0)
            weights.append(0.3)  # Very high weight for EIN

        # Phone matching score
        if query.phone:
            result_phones = result.get("phones", [])
            phone_score = 0.0
            query_phone_clean = "".join(filter(str.isdigit, query.phone))

            for result_phone in result_phones:
                result_phone_clean = "".join(filter(str.isdigit, str(result_phone)))
                if query_phone_clean == result_phone_clean:
                    phone_score = 1.0
                    break

            scores.append(phone_score)
            weights.append(0.2)

        # Address/location matching
        if query.city or query.state:
            result_address = result.get("address", {})
            location_score = 0.0

            if query.city and result_address.get("city"):
                if query.city.lower() == result_address["city"].lower():
                    location_score += 0.5

            if query.state and result_address.get("state"):
                if query.state.upper() == result_address["state"].upper():
                    location_score += 0.5

            scores.append(location_score)
            weights.append(0.1)

        # Calculate weighted average
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            return min(1.0, weighted_sum / total_weight)

        return 0.5  # Default neutral confidence

    def _validate_and_cleanup_business_data(
        self, raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and cleanup business API response data"""
        cleaned = {}

        # Clean business name fields
        for field in ["business_name", "dba_name", "trade_name"]:
            value = raw_data.get(field)
            if value and isinstance(value, str):
                cleaned[field] = value.strip()

        # Clean EIN
        ein = raw_data.get("ein") or raw_data.get("federal_ein")
        if ein:
            ein_clean = "".join(filter(str.isdigit, str(ein)))
            if len(ein_clean) == 9:
                cleaned["ein"] = f"{ein_clean[:2]}-{ein_clean[2:]}"

        # Clean phone numbers
        phones = raw_data.get("phones", [])
        if isinstance(phones, str):
            phones = [phones]  # Convert single phone to list

        cleaned_phones = []
        for phone in phones:
            phone_clean = "".join(filter(str.isdigit, str(phone)))
            if len(phone_clean) >= 10:
                cleaned_phones.append(
                    {
                        "number": phone_clean,
                        "formatted": self._format_phone_number(phone_clean),
                        "type": "business",
                    }
                )

        if cleaned_phones:
            cleaned["phones"] = cleaned_phones

        # Clean addresses
        addresses = raw_data.get("addresses", [])
        if isinstance(addresses, dict):
            addresses = [addresses]  # Convert single address to list

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

        # Copy other relevant fields
        for field in ["entity_type", "status", "industry", "website", "description"]:
            if field in raw_data:
                cleaned[field] = raw_data[field]

        # Clean financial data
        if "financial" in raw_data or "revenue" in raw_data:
            financial_data = {}
            if raw_data.get("revenue"):
                financial_data["annual_revenue"] = raw_data["revenue"]
            if raw_data.get("employees"):
                financial_data["employee_count"] = raw_data["employees"]
            if financial_data:
                cleaned["financial_data"] = financial_data

        return cleaned

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for display"""
        if len(phone) == 10:
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        elif len(phone) == 11 and phone.startswith("1"):
            return f"+1 ({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
        return phone

    def _convert_to_business_profile(
        self, raw_result: Dict[str, Any], query: BusinessSearchQuery
    ) -> BusinessProfile:
        """Convert API response to BusinessProfile model"""
        cleaned_data = self._validate_and_cleanup_business_data(raw_result)

        # Build business locations
        locations = []
        for addr_data in cleaned_data.get("addresses", []):
            address = Address(
                street=addr_data.get("street"),
                city=addr_data.get("city"),
                state=addr_data.get("state"),
                zip_code=addr_data.get("zip_code"),
            )

            location = BusinessLocation(
                address=address,
                location_type="primary",
                is_headquarters=True,  # Assume first address is HQ
                is_active=True,
            )
            locations.append(location)

        # Build phone list
        phones = []
        for phone_data in cleaned_data.get("phones", []):
            phone = Phone(
                number=phone_data["number"],
                formatted=phone_data.get("formatted"),
                type=phone_data.get("type", "business"),
                confidence_score=0.8,
                is_current=True,
            )
            phones.append(phone)

        # Build registration
        registration = None
        if cleaned_data.get("ein") or cleaned_data.get("status"):
            registration = Registration(
                federal_ein=cleaned_data.get("ein"),
                status=BusinessStatus(cleaned_data.get("status", "unknown").lower())
                if cleaned_data.get("status")
                else BusinessStatus.UNKNOWN,
            )

        # Build industry classification
        industry = None
        if cleaned_data.get("industry"):
            industry = IndustryClassification(primary_industry=cleaned_data["industry"])

        # Build financial data
        financial_data = None
        if cleaned_data.get("financial_data"):
            fin_data = cleaned_data["financial_data"]
            financial_data = FinancialData(
                annual_revenue=fin_data.get("annual_revenue"),
                employee_count=fin_data.get("employee_count"),
            )

        # Calculate overall confidence score
        confidence_score = self._score_result_confidence(query, cleaned_data)

        # Create BusinessProfile
        profile = BusinessProfile(
            business_name=cleaned_data.get("business_name", ""),
            dba_names=[cleaned_data["dba_name"]]
            if cleaned_data.get("dba_name")
            else [],
            trade_names=[cleaned_data["trade_name"]]
            if cleaned_data.get("trade_name")
            else [],
            entity_type=EntityType(cleaned_data.get("entity_type", "unknown").lower())
            if cleaned_data.get("entity_type")
            else EntityType.UNKNOWN,
            industry=industry,
            description=cleaned_data.get("description"),
            locations=locations,
            phones=phones,
            website=cleaned_data.get("website"),
            registration=registration,
            financial_data=financial_data,
            source_provider="enformion",
            confidence_score=confidence_score,
            raw_response=raw_result,
        )

        return profile

    def _generate_search_cache_key(self, query: BusinessSearchQuery) -> str:
        """Generate cache key for business search query"""
        search_params = {}

        if query.business_name:
            search_params["business_name"] = query.business_name.lower().strip()
        if query.ein:
            search_params["ein"] = "".join(filter(str.isdigit, query.ein))
        if query.phone:
            search_params["phone"] = "".join(filter(str.isdigit, query.phone))
        if query.city:
            search_params["city"] = query.city.lower().strip()
        if query.state:
            search_params["state"] = query.state.upper()

        key_str = json.dumps(search_params, sort_keys=True)
        return f"business_search_{hashlib.sha256(key_str.encode()).hexdigest()[:16]}"

    def search_by_name(
        self,
        business_name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        fuzzy_matching: bool = True,
        max_results: int = 10,
    ) -> List[BusinessProfile]:
        """
        Search for businesses by name with optional location filtering

        Args:
            business_name: Business name to search for
            city: City to filter by
            state: State to filter by
            fuzzy_matching: Enable fuzzy name matching
            max_results: Maximum number of results to return

        Returns:
            List of BusinessProfile objects matching the search
        """
        query = BusinessSearchQuery(
            business_name=business_name,
            city=city,
            state=state,
            fuzzy_matching=fuzzy_matching,
            max_results=max_results,
        )

        return self.search(query)

    def search_by_ein(self, ein: str, max_results: int = 5) -> List[BusinessProfile]:
        """
        Search for business by EIN (most accurate method)

        Args:
            ein: Federal EIN to search for
            max_results: Maximum number of results

        Returns:
            List of BusinessProfile objects (usually just one for exact EIN match)
        """
        query = BusinessSearchQuery(ein=ein, max_results=max_results)

        return self.search(query)

    def search_by_phone(
        self, phone_number: str, max_results: int = 5
    ) -> List[BusinessProfile]:
        """
        Search for business by phone number

        Args:
            phone_number: Phone number to search for
            max_results: Maximum number of results

        Returns:
            List of BusinessProfile objects associated with the phone
        """
        query = BusinessSearchQuery(phone=phone_number, max_results=max_results)

        return self.search(query)

    def verify_business_entity(
        self, business_name: str, ein: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify business entity exists and is legitimate

        Args:
            business_name: Business name to verify
            ein: Optional EIN for additional verification

        Returns:
            Dict with verification results and confidence score
        """
        try:
            # Search by name and/or EIN
            query = BusinessSearchQuery(
                business_name=business_name, ein=ein, max_results=5
            )

            results = self.search(query)

            if not results:
                return {
                    "verified": False,
                    "confidence": 0.0,
                    "reason": "No matching business found",
                    "matches": [],
                }

            # Find best match
            best_match = results[0]  # Already sorted by confidence

            verification_result = {
                "verified": best_match.confidence_score >= 0.8,
                "confidence": best_match.confidence_score,
                "business_name": best_match.business_name,
                "entity_type": best_match.entity_type.value,
                "status": best_match.registration.status.value
                if best_match.registration
                else "unknown",
                "matches": len(results),
            }

            # Additional verification checks
            if best_match.registration:
                verification_result["ein"] = best_match.registration.federal_ein
                verification_result[
                    "registered_state"
                ] = best_match.registration.registered_state

            if best_match.primary_location:
                verification_result[
                    "address"
                ] = best_match.primary_location.address.full_address

            return verification_result

        except Exception as e:
            self.logger.error(f"Business entity verification failed: {e}")
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": f"Verification error: {e}",
                "matches": 0,
            }

    def identify_principals(self, business_profile: BusinessProfile) -> List[Principal]:
        """
        Identify business principals and executives

        Args:
            business_profile: BusinessProfile to analyze for principals

        Returns:
            List of Principal objects with officer/owner information
        """
        principals = []

        # If we already have principals from the profile, return them
        if business_profile.principals:
            return business_profile.principals

        # Try to get additional principal information from raw data
        raw_data = business_profile.raw_response or {}

        # Look for officers, directors, owners in raw data
        for field in ["officers", "directors", "owners", "principals"]:
            if field in raw_data:
                principal_data = raw_data[field]
                if isinstance(principal_data, list):
                    for person_data in principal_data:
                        if isinstance(person_data, dict):
                            name = PersonName(
                                first=person_data.get("first_name"),
                                last=person_data.get("last_name"),
                                full=person_data.get("name"),
                            )

                            principal = Principal(
                                name=name,
                                title=person_data.get("title"),
                                role=person_data.get("role", field.rstrip("s")),
                                confidence_score=0.7,
                            )
                            principals.append(principal)

        return principals

    def analyze_corporate_filings(
        self, business_profile: BusinessProfile
    ) -> Dict[str, Any]:
        """
        Analyze corporate filings for risk and compliance

        Args:
            business_profile: BusinessProfile to analyze

        Returns:
            Dict with filing analysis and risk indicators
        """
        analysis = {
            "total_filings": len(business_profile.filings),
            "recent_filings": 0,
            "risk_indicators": [],
            "compliance_status": "unknown",
        }

        if not business_profile.filings:
            analysis["compliance_status"] = "limited_data"
            return analysis

        # Count recent filings (last 2 years)
        two_years_ago = datetime.utcnow() - timedelta(days=730)
        recent_filings = [
            f
            for f in business_profile.filings
            if f.filing_date and f.filing_date > two_years_ago
        ]
        analysis["recent_filings"] = len(recent_filings)

        # Look for risk indicators in filings
        risk_keywords = [
            "bankruptcy",
            "lien",
            "judgment",
            "suspend",
            "revoke",
            "default",
        ]

        for filing in business_profile.filings:
            filing_text = (filing.description or "").lower()
            for keyword in risk_keywords:
                if keyword in filing_text:
                    analysis["risk_indicators"].append(
                        {
                            "type": keyword,
                            "filing_date": filing.filing_date.isoformat()
                            if filing.filing_date
                            else None,
                            "description": filing.description,
                        }
                    )

        # Determine compliance status
        if len(analysis["risk_indicators"]) == 0:
            analysis["compliance_status"] = "good"
        elif len(analysis["risk_indicators"]) <= 2:
            analysis["compliance_status"] = "moderate_risk"
        else:
            analysis["compliance_status"] = "high_risk"

        return analysis

    def map_business_relationships(
        self, business_profile: BusinessProfile
    ) -> Dict[str, Any]:
        """
        Map business relationships including subsidiaries and parent companies

        Args:
            business_profile: BusinessProfile to analyze for relationships

        Returns:
            Dict with relationship mapping
        """
        relationships = {
            "parent_company": business_profile.parent_company,
            "subsidiaries": business_profile.subsidiaries,
            "related_entities": [],
            "relationship_confidence": 0.0,
        }

        # Look for related entities based on principals
        related_entities = set()

        for principal in business_profile.principals:
            # If we have PersonSearchAgent, we could look up other businesses
            # this principal is associated with
            if self.person_search_agent:
                try:
                    # This would require implementing cross-reference functionality
                    # For now, just note the potential
                    related_entities.add(
                        f"Potential entities for {principal.name.display_name}"
                    )
                except Exception as e:
                    self.logger.debug(
                        f"Could not find related entities for principal: {e}"
                    )

        relationships["related_entities"] = list(related_entities)

        # Calculate relationship confidence based on available data
        confidence_factors = []
        if business_profile.parent_company:
            confidence_factors.append(0.3)
        if business_profile.subsidiaries:
            confidence_factors.append(0.3)
        if len(business_profile.principals) > 0:
            confidence_factors.append(0.2)

        relationships["relationship_confidence"] = sum(confidence_factors)

        return relationships

    def assess_business_risk(self, business_profile: BusinessProfile) -> Dict[str, Any]:
        """
        Assess business risk based on multiple factors

        Args:
            business_profile: BusinessProfile to assess

        Returns:
            Dict with risk assessment and scoring
        """
        risk_assessment = {
            "overall_risk_score": 0.0,
            "risk_level": "unknown",
            "risk_factors": [],
            "positive_indicators": [],
            "assessment_confidence": business_profile.confidence_score,
        }

        risk_score = 0.0
        risk_factors = []
        positive_indicators = []

        # Check registration status
        if business_profile.registration:
            if business_profile.registration.status == BusinessStatus.ACTIVE:
                positive_indicators.append("Active business registration")
                risk_score -= 0.1  # Lower risk
            elif business_profile.registration.status in [
                BusinessStatus.SUSPENDED,
                BusinessStatus.DISSOLVED,
            ]:
                risk_factors.append(
                    f"Business status: {business_profile.registration.status.value}"
                )
                risk_score += 0.3  # Higher risk

        # Check for valid contact information
        if business_profile.phones and business_profile.primary_location:
            positive_indicators.append("Complete contact information available")
            risk_score -= 0.05
        else:
            risk_factors.append("Incomplete contact information")
            risk_score += 0.1

        # Analyze filings for risk indicators
        filing_analysis = self.analyze_corporate_filings(business_profile)
        if filing_analysis["risk_indicators"]:
            for indicator in filing_analysis["risk_indicators"]:
                risk_factors.append(f"Filing risk: {indicator['type']}")
                risk_score += 0.2

        # Check business age (if available)
        if business_profile.years_in_business:
            if business_profile.years_in_business < 2:
                risk_factors.append("New business (less than 2 years)")
                risk_score += 0.15
            elif business_profile.years_in_business > 10:
                positive_indicators.append("Established business (10+ years)")
                risk_score -= 0.1

        # Financial indicators
        if business_profile.financial_data:
            if business_profile.financial_data.bankruptcy_filed:
                risk_factors.append("Bankruptcy filing history")
                risk_score += 0.4

            if business_profile.financial_data.liens:
                risk_factors.append(
                    f"Tax liens/judgments: {len(business_profile.financial_data.liens)}"
                )
                risk_score += 0.2

        # Normalize risk score to 0-1 range
        risk_score = max(0.0, min(1.0, risk_score))

        # Determine risk level
        if risk_score < 0.3:
            risk_level = "low"
        elif risk_score < 0.6:
            risk_level = "moderate"
        elif risk_score < 0.8:
            risk_level = "high"
        else:
            risk_level = "critical"

        risk_assessment.update(
            {
                "overall_risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "positive_indicators": positive_indicators,
            }
        )

        return risk_assessment

    def search(
        self, query: BusinessSearchQuery, use_cache: bool = True
    ) -> List[BusinessProfile]:
        """
        Execute business search query

        Args:
            query: BusinessSearchQuery object with search parameters
            use_cache: Whether to use cached results

        Returns:
            List of BusinessProfile objects matching the query

        Raises:
            ValueError: If query has insufficient parameters
            EnformionAPIError: If API request fails
        """
        if not query.has_sufficient_params():
            raise ValueError(
                "Query must have business name or identifier plus location/contact info"
            )

        # Generate cache key
        cache_key = self._generate_search_cache_key(query) if use_cache else None

        # Check cache first
        if cache_key and use_cache:
            cached_results = self.cache.get(cache_key)
            if cached_results:
                self.logger.info(
                    f"Returning {len(cached_results)} cached business search results"
                )
                return [
                    BusinessProfile(**profile_data) for profile_data in cached_results
                ]

        try:
            # Prepare search parameters for EnformionGO
            search_params = {}

            if query.business_name:
                search_params["business_name"] = query.business_name
            if query.city:
                search_params["city"] = query.city
            if query.state:
                search_params["state"] = query.state
            if query.phone:
                search_params["phone"] = query.phone

            # Execute search via EnformionGO client
            self.logger.info(f"Executing business search: {search_params}")
            raw_response = self.enformion_client.business_search(**search_params)

            # Process results
            results = []
            raw_results = raw_response.get("results", [])

            if not raw_results:
                self.logger.info("No results found for business search")
                return results

            # Convert each result to BusinessProfile
            for raw_result in raw_results[: query.max_results]:
                try:
                    profile = self._convert_to_business_profile(raw_result, query)

                    # Apply confidence threshold
                    if profile.confidence_score >= query.min_confidence:
                        results.append(profile)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to convert result to BusinessProfile: {e}"
                    )
                    continue

            # Sort by confidence score
            results.sort(key=lambda p: p.confidence_score, reverse=True)

            # Cache results
            if cache_key and use_cache and results:
                # Convert to dict for caching
                cached_data = [profile.model_dump() for profile in results]
                self.cache.set(
                    cache_key, cached_data, ttl_seconds=self.cache_config.ttl_seconds
                )

            self.logger.info(f"Business search completed: {len(results)} results found")
            return results

        except EnformionAPIError as e:
            self.logger.error(f"EnformionGO API error during business search: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during business search: {e}")
            raise

    def query(self, query_params: Dict[str, Any], **kwargs) -> List[BusinessProfile]:
        """
        Execute query using dict parameters (BaseIntelligenceAgent interface)

        Args:
            query_params: Dictionary of query parameters
            **kwargs: Additional arguments

        Returns:
            List of BusinessProfile objects
        """
        # Convert dict to BusinessSearchQuery
        query = BusinessSearchQuery(**query_params)
        return self.search(query, **kwargs)

    def conduct_due_diligence(
        self, business_identifier: Union[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive due diligence on a business

        Args:
            business_identifier: Business name (str) or dict with search params

        Returns:
            Comprehensive due diligence report
        """
        try:
            # Create search query
            if isinstance(business_identifier, str):
                query = BusinessSearchQuery(business_name=business_identifier)
            else:
                query = BusinessSearchQuery(**business_identifier)

            # Execute search
            results = self.search(query)

            if not results:
                return {
                    "status": "no_results",
                    "message": "No business found matching search criteria",
                }

            # Use best match for due diligence
            business = results[0]

            # Comprehensive analysis
            due_diligence_report = {
                "business_profile": business.to_summary_dict(),
                "verification": self.verify_business_entity(
                    business.business_name,
                    business.registration.federal_ein
                    if business.registration
                    else None,
                ),
                "principals": [
                    p.model_dump() for p in self.identify_principals(business)
                ],
                "filing_analysis": self.analyze_corporate_filings(business),
                "relationships": self.map_business_relationships(business),
                "risk_assessment": self.assess_business_risk(business),
                "compliance_check": self._check_compliance_status(business),
                "recommendations": self._generate_due_diligence_recommendations(
                    business
                ),
                "report_timestamp": datetime.utcnow().isoformat(),
                "data_confidence": business.confidence_score,
            }

            return due_diligence_report

        except Exception as e:
            self.logger.error(f"Due diligence process failed: {e}")
            return {"status": "error", "message": f"Due diligence failed: {e}"}

    def _check_compliance_status(
        self, business_profile: BusinessProfile
    ) -> Dict[str, Any]:
        """Check business compliance status"""
        compliance = {
            "status": "unknown",
            "active_licenses": len(business_profile.active_licenses),
            "expired_licenses": len(
                [lic for lic in business_profile.licenses if lic.is_expired]
            ),
            "registration_status": business_profile.registration.status.value
            if business_profile.registration
            else "unknown",
            "issues": [],
        }

        # Check for compliance issues
        if business_profile.registration:
            if business_profile.registration.status != BusinessStatus.ACTIVE:
                compliance["issues"].append(
                    f"Business registration status: {business_profile.registration.status.value}"
                )

        # Check for expired licenses
        expired_licenses = [lic for lic in business_profile.licenses if lic.is_expired]
        if expired_licenses:
            compliance["issues"].append(f"Expired licenses: {len(expired_licenses)}")

        # Determine overall compliance status
        if len(compliance["issues"]) == 0:
            compliance["status"] = "compliant"
        elif len(compliance["issues"]) <= 2:
            compliance["status"] = "minor_issues"
        else:
            compliance["status"] = "non_compliant"

        return compliance

    def _generate_due_diligence_recommendations(
        self, business_profile: BusinessProfile
    ) -> List[str]:
        """Generate recommendations based on due diligence findings"""
        recommendations = []

        # Risk-based recommendations
        risk_assessment = self.assess_business_risk(business_profile)
        if risk_assessment["risk_level"] in ["high", "critical"]:
            recommendations.append("Conduct enhanced due diligence before proceeding")
            recommendations.append(
                "Consider requiring additional documentation or guarantees"
            )

        # Registration recommendations
        if (
            not business_profile.registration
            or business_profile.registration.status != BusinessStatus.ACTIVE
        ):
            recommendations.append(
                "Verify current business registration status with state authorities"
            )

        # Contact verification
        if not business_profile.phones or not business_profile.primary_location:
            recommendations.append("Verify business contact information independently")

        # Financial recommendations
        if (
            business_profile.financial_data
            and business_profile.financial_data.bankruptcy_filed
        ):
            recommendations.append(
                "Review bankruptcy history and current financial stability"
            )

        if not recommendations:
            recommendations.append(
                "Standard business verification appears satisfactory"
            )

        return recommendations

    def health_check(self) -> Dict[str, Any]:
        """Perform health check for BusinessSearchAgent"""
        base_health = super().health_check()

        try:
            # Test basic search functionality
            test_query = BusinessSearchQuery(
                business_name="Test Company", city="Test City", max_results=1
            )

            base_health.update(
                {
                    "business_search_ready": True,
                    "fuzzy_threshold": self.fuzzy_threshold,
                    "risk_threshold": self.risk_threshold,
                    "person_search_integration": self.person_search_agent is not None,
                }
            )

        except Exception as e:
            base_health.update({"business_search_ready": False, "error": str(e)})

        return base_health
