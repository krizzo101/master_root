"""
EmailSearchAgent for Sleuth Intel
Implements email intelligence using EnformionGO /email-search endpoint with advanced features
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import dns.resolver
import requests

from ..agents.base_agent import (
    BaseIntelligenceAgent,
    CacheConfig,
    RateLimitConfig,
    RetryConfig,
)
from ..core.secure_api_locker import APICredential
from ..models.query import DataProvider, EmailLookupQuery
from ..providers.enformion_client import EnformionAPIError, EnformionClient

logger = logging.getLogger(__name__)


class EmailSearchAgent(BaseIntelligenceAgent):
    """
    Advanced email search and intelligence agent using EnformionGO API

    Features:
    - Email address validation (format and deliverability)
    - Reverse email lookup for person identification
    - Domain analysis and business affiliation
    - Social media profile correlation
    - Email breach/compromise detection
    - Professional vs personal email classification
    - Disposable email detection
    - Cross-reference with PersonSearchAgent results
    - Privacy-compliant data handling
    """

    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        "10minutemail.com",
        "guerrillamail.com",
        "mailinator.com",
        "tempmail.org",
        "yopmail.com",
        "throwaway.email",
        "temp-mail.org",
        "getnada.com",
        "emailondeck.com",
        "maildrop.cc",
        "mohmal.com",
        "sharklasers.com",
        "fakeinbox.com",
        "dispostable.com",
        "bugmenot.com",
    }

    # Professional email domain patterns
    PROFESSIONAL_DOMAINS = {
        "gmail.com",
        "outlook.com",
        "yahoo.com",
        "hotmail.com",
        "icloud.com",
        "aol.com",
        "protonmail.com",
    }

    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        enable_breach_detection: bool = True,
        enable_social_correlation: bool = False,  # Privacy-safe default
        enable_mx_validation: bool = True,
    ):
        # Email search specific rate limits
        default_rate_config = RateLimitConfig(
            requests_per_second=0.3,  # 3+ seconds between requests
            requests_per_minute=15,
            requests_per_hour=200,
            requests_per_day=1000,
            burst_size=2,
        )

        # Extended cache for email searches
        default_cache_config = CacheConfig(
            enabled=True,
            ttl_seconds=3600,  # 1 hour for email data
            max_entries=200,
            compress=True,
        )

        super().__init__(
            provider="enformion",
            agent_name="EmailSearchAgent",
            rate_limit_config=rate_limit_config or default_rate_config,
            retry_config=retry_config,
            cache_config=cache_config or default_cache_config,
            custom_headers={"X-Agent-Type": "email-search"},
            timeout=30,
        )

        # Feature configuration
        self.enable_breach_detection = enable_breach_detection
        self.enable_social_correlation = enable_social_correlation
        self.enable_mx_validation = enable_mx_validation

        # Initialize EnformionGO client
        self.enformion_client = EnformionClient()

        # Compile regex patterns for efficiency
        self.email_pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        self.business_email_pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@(?!(?:gmail|yahoo|hotmail|outlook|aol|icloud)\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        logger.info(
            f"Initialized EmailSearchAgent with breach_detection={enable_breach_detection}"
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

    def validate_email_format(self, email: str) -> Dict[str, Any]:
        """
        Validate email address format and structure

        Args:
            email: Email address to validate

        Returns:
            Dict containing validation results
        """
        result = {
            "email": email,
            "is_valid": False,
            "format_valid": False,
            "local_part": "",
            "domain_part": "",
            "tld": "",
            "issues": [],
        }

        if not email or not isinstance(email, str):
            result["issues"].append("Email is empty or invalid type")
            return result

        email = email.strip().lower()

        # Basic format check
        if not self.email_pattern.match(email):
            result["issues"].append("Invalid email format")
            return result

        result["format_valid"] = True

        # Split email parts
        try:
            local_part, domain_part = email.split("@", 1)
            result["local_part"] = local_part
            result["domain_part"] = domain_part

            # Extract TLD
            domain_parts = domain_part.split(".")
            if len(domain_parts) >= 2:
                result["tld"] = domain_parts[-1]

            # Validate local part
            if len(local_part) == 0:
                result["issues"].append("Empty local part")
            elif len(local_part) > 64:
                result["issues"].append("Local part too long")
            elif local_part.startswith(".") or local_part.endswith("."):
                result["issues"].append("Local part cannot start/end with dot")
            elif ".." in local_part:
                result["issues"].append("Local part contains consecutive dots")

            # Validate domain part
            if len(domain_part) == 0:
                result["issues"].append("Empty domain part")
            elif len(domain_part) > 253:
                result["issues"].append("Domain part too long")
            elif not all(len(part) <= 63 for part in domain_parts):
                result["issues"].append("Domain label too long")

            # If no issues found, mark as valid
            if not result["issues"]:
                result["is_valid"] = True

        except ValueError:
            result["issues"].append("Could not split email address")

        return result

    def validate_email_deliverability(self, email: str) -> Dict[str, Any]:
        """
        Validate email deliverability through MX record checks

        Args:
            email: Email address to validate

        Returns:
            Dict containing deliverability results
        """
        result = {
            "email": email,
            "deliverable": False,
            "mx_valid": False,
            "mx_records": [],
            "issues": [],
        }

        if not self.enable_mx_validation:
            result["issues"].append("MX validation disabled")
            return result

        # First check format
        format_result = self.validate_email_format(email)
        if not format_result["is_valid"]:
            result["issues"].extend(format_result["issues"])
            return result

        domain = format_result["domain_part"]

        try:
            # Check MX records
            mx_records = dns.resolver.resolve(domain, "MX")
            result["mx_records"] = [str(mx) for mx in mx_records]
            result["mx_valid"] = len(result["mx_records"]) > 0

            if result["mx_valid"]:
                result["deliverable"] = True
            else:
                result["issues"].append("No MX records found")

        except dns.resolver.NXDOMAIN:
            result["issues"].append("Domain does not exist")
        except dns.resolver.NoAnswer:
            result["issues"].append("No MX records returned")
        except Exception as e:
            result["issues"].append(f"DNS lookup error: {str(e)}")

        return result

    def classify_email_type(self, email: str) -> Dict[str, Any]:
        """
        Classify email as professional, personal, or disposable

        Args:
            email: Email address to classify

        Returns:
            Dict containing classification results
        """
        result = {
            "email": email,
            "type": "unknown",
            "is_professional": False,
            "is_personal": False,
            "is_disposable": False,
            "is_business": False,
            "confidence": 0.0,
            "indicators": [],
        }

        format_result = self.validate_email_format(email)
        if not format_result["is_valid"]:
            return result

        domain = format_result["domain_part"]
        local_part = format_result["local_part"]

        # Check for disposable domains
        if domain in self.DISPOSABLE_DOMAINS:
            result["type"] = "disposable"
            result["is_disposable"] = True
            result["confidence"] = 0.95
            result["indicators"].append("Known disposable domain")
            return result

        # Check for common personal email domains
        if domain in self.PROFESSIONAL_DOMAINS:
            result["type"] = "personal"
            result["is_personal"] = True
            result["confidence"] = 0.8
            result["indicators"].append("Common personal email provider")

            # Look for business-like local parts
            business_patterns = [
                "info",
                "contact",
                "support",
                "admin",
                "sales",
                "marketing",
            ]
            if any(pattern in local_part for pattern in business_patterns):
                result["indicators"].append("Business-like local part")
                result["confidence"] = 0.6  # Less certain

        # Check for business domains (not in common personal providers)
        elif self.business_email_pattern.match(email):
            result["type"] = "professional"
            result["is_professional"] = True
            result["is_business"] = True
            result["confidence"] = 0.9
            result["indicators"].append("Business domain")

            # Look for role-based addresses
            role_patterns = [
                "info",
                "contact",
                "support",
                "admin",
                "sales",
                "marketing",
                "hr",
                "legal",
            ]
            if any(pattern in local_part for pattern in role_patterns):
                result["indicators"].append("Role-based email address")
                result["confidence"] = 0.95

        return result

    def extract_domain_info(self, email: str) -> Dict[str, Any]:
        """
        Extract and analyze domain information

        Args:
            email: Email address to analyze

        Returns:
            Dict containing domain analysis
        """
        result = {
            "email": email,
            "domain": "",
            "registrar": "",
            "organization": "",
            "country": "",
            "created_date": None,
            "updated_date": None,
            "expires_date": None,
            "whois_data": {},
            "error": None,
        }

        format_result = self.validate_email_format(email)
        if not format_result["is_valid"]:
            result["error"] = "Invalid email format"
            return result

        domain = format_result["domain_part"]
        result["domain"] = domain

        try:
            # For production, you would use a WHOIS library like python-whois
            # This is a simplified implementation
            import whois

            domain_info = whois.whois(domain)

            if domain_info:
                result["registrar"] = domain_info.get("registrar", "")
                result["organization"] = domain_info.get("org", "")
                result["country"] = domain_info.get("country", "")
                result["created_date"] = domain_info.get("creation_date")
                result["updated_date"] = domain_info.get("updated_date")
                result["expires_date"] = domain_info.get("expiration_date")
                result["whois_data"] = dict(domain_info) if domain_info else {}

        except ImportError:
            result["error"] = "WHOIS library not available"
        except Exception as e:
            result["error"] = f"WHOIS lookup failed: {str(e)}"

        return result

    def reverse_email_lookup(
        self, email: str, include_social: bool = None
    ) -> Dict[str, Any]:
        """
        Perform reverse email lookup to find associated person/business

        Args:
            email: Email address to lookup
            include_social: Whether to include social media profiles

        Returns:
            Dict containing lookup results
        """
        if include_social is None:
            include_social = self.enable_social_correlation

        # Generate cache key
        cache_key = f"email_reverse_{hashlib.sha256(email.encode()).hexdigest()[:16]}"

        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            self.logger.info(
                f"Returning cached reverse email lookup for {email[:5]}***"
            )
            return cached_result

        try:
            # Use EnformionGO client for reverse email lookup
            self.logger.info(f"Performing reverse email lookup for {email[:5]}***")

            # Note: Actual API call would depend on EnformionGO's email search endpoint
            # This is a structured example of what the response would look like
            raw_response = self.enformion_client._make_request(
                "GET",
                "/email-search",
                params={"email": email, "include_social": include_social},
            )

            # Process and structure the response
            result = self._process_reverse_lookup_response(raw_response, email)

            # Cache the results
            self.cache.set(cache_key, result, ttl_seconds=self.cache_config.ttl_seconds)

            return result

        except EnformionAPIError as e:
            self.logger.error(f"EnformionGO API error during reverse email lookup: {e}")
            return {
                "email": email,
                "found": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Unexpected error during reverse email lookup: {e}")
            return {
                "email": email,
                "found": False,
                "error": f"Lookup failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    def _process_reverse_lookup_response(
        self, raw_response: Dict, email: str
    ) -> Dict[str, Any]:
        """Process API response from reverse email lookup"""
        result = {
            "email": email,
            "found": False,
            "person_info": {},
            "business_info": {},
            "social_profiles": [],
            "breach_info": {},
            "confidence_score": 0.0,
            "timestamp": datetime.now().isoformat(),
            "raw_response": raw_response,
        }

        if not raw_response or not raw_response.get("results"):
            return result

        data = raw_response["results"][0] if raw_response.get("results") else {}
        result["found"] = True

        # Extract person information
        if data.get("person"):
            person = data["person"]
            result["person_info"] = {
                "first_name": person.get("first_name", "").strip(),
                "last_name": person.get("last_name", "").strip(),
                "full_name": person.get("full_name", "").strip(),
                "age": person.get("age"),
                "phones": person.get("phones", []),
                "addresses": person.get("addresses", []),
                "relatives": person.get("relatives", []),
            }

            # Remove empty values
            result["person_info"] = {
                k: v for k, v in result["person_info"].items() if v
            }

        # Extract business information
        if data.get("business"):
            business = data["business"]
            result["business_info"] = {
                "name": business.get("name", "").strip(),
                "industry": business.get("industry", "").strip(),
                "website": business.get("website", "").strip(),
                "phones": business.get("phones", []),
                "addresses": business.get("addresses", []),
            }

            # Remove empty values
            result["business_info"] = {
                k: v for k, v in result["business_info"].items() if v
            }

        # Extract social profiles (if enabled and available)
        if self.enable_social_correlation and data.get("social_profiles"):
            result["social_profiles"] = [
                {
                    "platform": profile.get("platform", "").strip(),
                    "username": profile.get("username", "").strip(),
                    "url": profile.get("url", "").strip(),
                    "verified": profile.get("verified", False),
                }
                for profile in data["social_profiles"]
                if profile.get("platform") and profile.get("username")
            ]

        # Extract breach information (if enabled and available)
        if self.enable_breach_detection and data.get("breach_data"):
            breach_data = data["breach_data"]
            result["breach_info"] = {
                "found_in_breaches": breach_data.get("found", False),
                "breach_count": breach_data.get("breach_count", 0),
                "breaches": [
                    {
                        "name": breach.get("name", "").strip(),
                        "date": breach.get("date"),
                        "compromised_data": breach.get("compromised_data", []),
                    }
                    for breach in breach_data.get("breaches", [])
                ],
            }

        # Calculate confidence score based on available data
        confidence_factors = 0
        total_factors = 5

        if result["person_info"]:
            confidence_factors += 2  # Person info is highly valuable
        if result["business_info"]:
            confidence_factors += 1
        if result["social_profiles"]:
            confidence_factors += 1
        if result.get("found"):
            confidence_factors += 1

        result["confidence_score"] = confidence_factors / total_factors

        return result

    def detect_email_breaches(self, email: str) -> Dict[str, Any]:
        """
        Check if email appears in known data breaches

        Args:
            email: Email address to check

        Returns:
            Dict containing breach detection results
        """
        if not self.enable_breach_detection:
            return {
                "email": email,
                "breach_detection_enabled": False,
                "message": "Breach detection is disabled",
            }

        # Generate cache key
        cache_key = f"email_breach_{hashlib.sha256(email.encode()).hexdigest()[:16]}"

        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        result = {
            "email": email,
            "found_in_breaches": False,
            "breach_count": 0,
            "breaches": [],
            "risk_level": "unknown",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # This would integrate with breach databases like HaveIBeenPwned
            # For EnformionGO, this data might be included in their email search
            breach_response = self.reverse_email_lookup(email)

            if breach_response.get("breach_info"):
                breach_info = breach_response["breach_info"]
                result.update(
                    {
                        "found_in_breaches": breach_info.get(
                            "found_in_breaches", False
                        ),
                        "breach_count": breach_info.get("breach_count", 0),
                        "breaches": breach_info.get("breaches", []),
                    }
                )

                # Determine risk level
                if result["breach_count"] == 0:
                    result["risk_level"] = "low"
                elif result["breach_count"] <= 2:
                    result["risk_level"] = "medium"
                else:
                    result["risk_level"] = "high"

            # Cache the results (shorter TTL for breach data as it can change)
            self.cache.set(cache_key, result, ttl_seconds=1800)  # 30 minutes

        except Exception as e:
            self.logger.error(f"Error during breach detection: {e}")
            result["error"] = str(e)

        return result

    def find_social_profiles(self, email: str) -> List[Dict[str, Any]]:
        """
        Find social media profiles associated with email

        Args:
            email: Email address to search

        Returns:
            List of social media profile information
        """
        if not self.enable_social_correlation:
            return []

        try:
            lookup_result = self.reverse_email_lookup(email, include_social=True)
            return lookup_result.get("social_profiles", [])

        except Exception as e:
            self.logger.error(f"Error finding social profiles: {e}")
            return []

    def cross_reference_with_person(
        self, email: str, person_agent=None
    ) -> Dict[str, Any]:
        """
        Cross-reference email results with PersonSearchAgent

        Args:
            email: Email address to cross-reference
            person_agent: PersonSearchAgent instance (optional)

        Returns:
            Dict containing cross-referenced results
        """
        result = {
            "email": email,
            "cross_reference_performed": False,
            "matching_persons": [],
            "confidence_score": 0.0,
        }

        try:
            # Get email lookup results
            email_result = self.reverse_email_lookup(email)

            if not email_result.get("found") or not email_result.get("person_info"):
                return result

            person_info = email_result["person_info"]

            # If person agent provided, search for matching persons
            if person_agent:
                from ..models.query import PersonSearchQuery

                # Create search query based on email results
                search_query = PersonSearchQuery(
                    first_name=person_info.get("first_name"),
                    last_name=person_info.get("last_name"),
                    email=email,
                    max_results=5,
                )

                if search_query.has_sufficient_params():
                    matching_persons = person_agent.search(search_query)
                    result["matching_persons"] = [
                        {
                            "name": person.name.display_name,
                            "confidence": person.confidence_score,
                            "phones": [phone.formatted for phone in person.phones],
                            "addresses": [addr.formatted for addr in person.addresses],
                        }
                        for person in matching_persons
                    ]
                    result["cross_reference_performed"] = True

                    # Calculate overall confidence
                    if matching_persons:
                        result["confidence_score"] = max(
                            p.confidence_score for p in matching_persons
                        )

        except Exception as e:
            self.logger.error(f"Error during cross-reference: {e}")
            result["error"] = str(e)

        return result

    def comprehensive_email_analysis(
        self, email: str, person_agent=None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive email analysis combining all available methods

        Args:
            email: Email address to analyze
            person_agent: PersonSearchAgent for cross-referencing

        Returns:
            Dict containing comprehensive analysis results
        """
        start_time = time.time()

        result = {
            "email": email,
            "analysis_timestamp": datetime.now().isoformat(),
            "format_validation": {},
            "deliverability": {},
            "classification": {},
            "domain_info": {},
            "reverse_lookup": {},
            "breach_detection": {},
            "social_profiles": [],
            "cross_reference": {},
            "overall_confidence": 0.0,
            "processing_time": 0.0,
        }

        try:
            # 1. Format validation
            result["format_validation"] = self.validate_email_format(email)

            if not result["format_validation"]["is_valid"]:
                result["processing_time"] = time.time() - start_time
                return result

            # 2. Deliverability check
            result["deliverability"] = self.validate_email_deliverability(email)

            # 3. Email classification
            result["classification"] = self.classify_email_type(email)

            # 4. Domain analysis
            result["domain_info"] = self.extract_domain_info(email)

            # 5. Reverse email lookup
            result["reverse_lookup"] = self.reverse_email_lookup(email)

            # 6. Breach detection
            result["breach_detection"] = self.detect_email_breaches(email)

            # 7. Social profiles
            result["social_profiles"] = self.find_social_profiles(email)

            # 8. Cross-reference with person search
            result["cross_reference"] = self.cross_reference_with_person(
                email, person_agent
            )

            # Calculate overall confidence score
            confidence_scores = [
                result["classification"].get("confidence", 0.0),
                result["reverse_lookup"].get("confidence_score", 0.0),
                result["cross_reference"].get("confidence_score", 0.0),
            ]

            valid_scores = [score for score in confidence_scores if score > 0]
            if valid_scores:
                result["overall_confidence"] = sum(valid_scores) / len(valid_scores)

        except Exception as e:
            self.logger.error(f"Error during comprehensive email analysis: {e}")
            result["error"] = str(e)

        result["processing_time"] = time.time() - start_time
        return result

    def query(self, query_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute email query (BaseIntelligenceAgent interface)

        Args:
            query_params: Dictionary of query parameters
            **kwargs: Additional arguments

        Returns:
            Email analysis results
        """
        # Convert dict to EmailLookupQuery if needed
        if "email_address" in query_params:
            email = query_params["email_address"]
        elif "email" in query_params:
            email = query_params["email"]
        else:
            raise ValueError("Query must contain 'email_address' or 'email' parameter")

        # Get person agent if provided
        person_agent = kwargs.get("person_agent")

        return self.comprehensive_email_analysis(email, person_agent)

    def health_check(self) -> Dict[str, Any]:
        """Perform health check for EmailSearchAgent"""
        base_health = super().health_check()

        try:
            # Test email validation
            test_email = "test@example.com"
            format_result = self.validate_email_format(test_email)

            base_health.update(
                {
                    "email_validation_ready": format_result["format_valid"],
                    "breach_detection_enabled": self.enable_breach_detection,
                    "social_correlation_enabled": self.enable_social_correlation,
                    "mx_validation_enabled": self.enable_mx_validation,
                    "disposable_domains_count": len(self.DISPOSABLE_DOMAINS),
                }
            )

        except Exception as e:
            base_health.update({"email_search_ready": False, "error": str(e)})

        return base_health
