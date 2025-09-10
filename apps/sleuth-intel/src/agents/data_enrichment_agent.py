"""
DataEnrichmentAgent for Sleuth Intel
Orchestrates multiple intelligence agents to provide comprehensive data enrichment,
cross-referencing, deduplication, and confidence scoring across all data sources.
"""

import asyncio
import hashlib
import json
import logging
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any, Dict, List, Optional, Set, Tuple, Union

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
    Principal,
)
from ..models.intelligence import (
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
from ..models.person import (
    Address,
    Associate,
    Demographics,
    Email,
    PersonName,
    PersonProfile,
    Phone,
)
from ..models.query import BusinessSearchQuery, DataProvider, PersonSearchQuery

logger = logging.getLogger(__name__)


@dataclass
class DataEnrichmentConfig:
    """Configuration for data enrichment operations"""

    confidence_threshold: float = 0.7
    deduplication_threshold: float = 0.9
    correlation_threshold: float = 0.8
    max_sources_per_query: int = 5
    enable_deep_enrichment: bool = True
    enable_anomaly_detection: bool = True
    enable_pattern_recognition: bool = True
    freshness_penalty_days: int = 30
    min_cross_validation_sources: int = 2


@dataclass
class SourceReliabilityScore:
    """Track reliability of data sources over time"""

    provider: str
    total_queries: int = 0
    successful_queries: int = 0
    accuracy_rate: float = 0.0
    freshness_score: float = 0.0
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    @property
    def overall_reliability(self) -> float:
        """Calculate overall reliability score"""
        if self.total_queries == 0:
            return 0.5  # Default neutral score

        success_rate = self.successful_queries / self.total_queries
        return (
            success_rate * 0.3
            + self.accuracy_rate * 0.25
            + self.freshness_score * 0.2
            + self.completeness_score * 0.15
            + self.consistency_score * 0.1
        )


@dataclass
class EnrichmentMetrics:
    """Track enrichment process metrics"""

    sources_queried: int = 0
    sources_successful: int = 0
    duplicates_found: int = 0
    duplicates_merged: int = 0
    data_gaps_identified: int = 0
    data_gaps_filled: int = 0
    anomalies_detected: int = 0
    patterns_identified: int = 0
    confidence_improvements: int = 0
    total_processing_time: float = 0.0
    cross_validation_matches: int = 0
    data_quality_warnings: List[str] = field(default_factory=list)


class DataEnrichmentAgent(BaseIntelligenceAgent):
    """
    Advanced data enrichment agent that coordinates multiple intelligence agents
    to provide comprehensive, cross-referenced, and high-confidence intelligence results.

    Features:
    - Multi-source data correlation and cross-referencing
    - Intelligent deduplication with confidence scoring
    - Advanced data quality assessment and validation
    - Gap identification and intelligent filling strategies
    - Pattern recognition in data relationships
    - Anomaly detection for data integrity
    - Source reliability tracking and weighting
    - Data freshness scoring and aging penalties
    - Comprehensive lineage and attribution tracking
    """

    def __init__(
        self,
        person_search_agent: Optional["PersonSearchAgent"] = None,
        business_search_agent: Optional["BusinessSearchAgent"] = None,
        phone_search_agent: Optional["PhoneSearchAgent"] = None,
        email_search_agent: Optional["EmailSearchAgent"] = None,
        address_search_agent: Optional["AddressSearchAgent"] = None,
        enrichment_config: Optional[DataEnrichmentConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        cache_config: Optional[CacheConfig] = None,
    ):
        # Conservative rate limits for orchestration (manages multiple agents)
        default_rate_config = RateLimitConfig(
            requests_per_second=2.0,  # Higher throughput for orchestration
            requests_per_minute=100,
            requests_per_hour=2000,
            requests_per_day=10000,
            burst_size=10,
        )

        # Large cache for enriched results
        default_cache_config = CacheConfig(
            enabled=True, ttl_seconds=10800, max_entries=1000, compress=True  # 3 hours
        )

        super().__init__(
            provider="data-enrichment",
            agent_name="DataEnrichmentAgent",
            rate_limit_config=rate_limit_config or default_rate_config,
            retry_config=None,
            cache_config=cache_config or default_cache_config,
            custom_headers={"X-Agent-Type": "data-enrichment"},
            timeout=120,
        )

        # Agent dependencies
        self.person_agent = person_search_agent
        self.business_agent = business_search_agent
        self.phone_agent = phone_search_agent
        self.email_agent = email_search_agent
        self.address_agent = address_search_agent

        # Configuration
        self.config = enrichment_config or DataEnrichmentConfig()

        # Source reliability tracking
        self.source_reliability: Dict[str, SourceReliabilityScore] = {}

        # Pattern recognition cache
        self.known_patterns: Dict[str, Dict[str, Any]] = {}

        logger.info(
            "Initialized DataEnrichmentAgent with comprehensive enrichment capabilities"
        )

    def _apply_authentication(
        self, credential: APICredential, request_kwargs: Dict
    ) -> Dict:
        """No direct API authentication needed for orchestration agent"""
        return request_kwargs

    def get_credential(self):
        """Override to avoid credential requirement for orchestration agent"""
        return None  # Data enrichment agent doesn't need credentials

    def _calculate_similarity_score(self, text1: str, text2: str) -> float:
        """Calculate text similarity using multiple algorithms"""
        if not text1 or not text2:
            return 0.0

        # Normalize texts
        norm1 = text1.lower().strip()
        norm2 = text2.lower().strip()

        if norm1 == norm2:
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        sequence_ratio = SequenceMatcher(None, norm1, norm2).ratio()

        # Add Jaccard similarity for additional validation
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 and not words2:
            jaccard_ratio = 1.0
        elif not words1 or not words2:
            jaccard_ratio = 0.0
        else:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            jaccard_ratio = intersection / union if union > 0 else 0.0

        # Weighted combination
        return sequence_ratio * 0.7 + jaccard_ratio * 0.3

    def _calculate_phone_similarity(self, phone1: str, phone2: str) -> float:
        """Calculate phone number similarity with normalization"""
        if not phone1 or not phone2:
            return 0.0

        # Normalize phone numbers (digits only)
        norm1 = "".join(filter(str.isdigit, phone1))
        norm2 = "".join(filter(str.isdigit, phone2))

        # Handle US format normalization
        if len(norm1) == 11 and norm1.startswith("1"):
            norm1 = norm1[1:]
        if len(norm2) == 11 and norm2.startswith("1"):
            norm2 = norm2[1:]

        if norm1 == norm2:
            return 1.0

        # Check for partial matches (area code, prefix)
        if len(norm1) >= 10 and len(norm2) >= 10:
            if norm1[-7:] == norm2[-7:]:  # Last 7 digits match
                return 0.8
            if norm1[:3] == norm2[:3]:  # Area code match
                return 0.3

        return 0.0

    def _calculate_address_similarity(
        self, addr1: Dict[str, Any], addr2: Dict[str, Any]
    ) -> float:
        """Calculate address similarity with geographic context"""
        if not addr1 or not addr2:
            return 0.0

        scores = []
        weights = []

        # Street address comparison
        if addr1.get("street") and addr2.get("street"):
            street_score = self._calculate_similarity_score(
                addr1["street"], addr2["street"]
            )
            scores.append(street_score)
            weights.append(0.4)

        # City comparison
        if addr1.get("city") and addr2.get("city"):
            city_score = self._calculate_similarity_score(addr1["city"], addr2["city"])
            scores.append(city_score)
            weights.append(0.3)

        # State comparison
        if addr1.get("state") and addr2.get("state"):
            state_score = (
                1.0 if addr1["state"].upper() == addr2["state"].upper() else 0.0
            )
            scores.append(state_score)
            weights.append(0.2)

        # ZIP code comparison
        if addr1.get("zip_code") and addr2.get("zip_code"):
            zip1 = str(addr1["zip_code"])[:5]
            zip2 = str(addr2["zip_code"])[:5]
            zip_score = (
                1.0
                if zip1 == zip2
                else (0.7 if abs(int(zip1) - int(zip2)) <= 10 else 0.0)
            )
            scores.append(zip_score)
            weights.append(0.1)

        if scores and weights:
            return sum(s * w for s, w in zip(scores, weights)) / sum(weights)

        return 0.0

    def _detect_duplicates(
        self, profiles: List[Union[PersonProfile, BusinessProfile]]
    ) -> List[Tuple[int, int, float]]:
        """Detect duplicate profiles using multi-factor similarity analysis"""
        duplicates = []

        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                similarity = self._calculate_profile_similarity(
                    profiles[i], profiles[j]
                )

                if similarity >= self.config.deduplication_threshold:
                    duplicates.append((i, j, similarity))

        return duplicates

    def _calculate_profile_similarity(
        self,
        profile1: Union[PersonProfile, BusinessProfile],
        profile2: Union[PersonProfile, BusinessProfile],
    ) -> float:
        """Calculate overall similarity between two profiles"""
        if type(profile1) != type(profile2):
            return 0.0  # Different profile types

        scores = []
        weights = []

        if isinstance(profile1, PersonProfile):
            # Name similarity
            name_score = self._calculate_similarity_score(
                profile1.name.display_name, profile2.name.display_name
            )
            scores.append(name_score)
            weights.append(0.3)

            # Phone similarity
            phone_scores = []
            for phone1 in profile1.phones:
                for phone2 in profile2.phones:
                    phone_score = self._calculate_phone_similarity(
                        phone1.number, phone2.number
                    )
                    phone_scores.append(phone_score)

            if phone_scores:
                max_phone_score = max(phone_scores)
                scores.append(max_phone_score)
                weights.append(0.25)

            # Email similarity
            email_scores = []
            for email1 in profile1.emails:
                for email2 in profile2.emails:
                    email_score = (
                        1.0 if email1.address.lower() == email2.address.lower() else 0.0
                    )
                    email_scores.append(email_score)

            if email_scores:
                max_email_score = max(email_scores)
                scores.append(max_email_score)
                weights.append(0.2)

            # Address similarity
            addr_scores = []
            for addr1 in profile1.addresses:
                for addr2 in profile2.addresses:
                    addr_dict1 = {
                        "street": addr1.street,
                        "city": addr1.city,
                        "state": addr1.state,
                        "zip_code": addr1.zip_code,
                    }
                    addr_dict2 = {
                        "street": addr2.street,
                        "city": addr2.city,
                        "state": addr2.state,
                        "zip_code": addr2.zip_code,
                    }
                    addr_score = self._calculate_address_similarity(
                        addr_dict1, addr_dict2
                    )
                    addr_scores.append(addr_score)

            if addr_scores:
                max_addr_score = max(addr_scores)
                scores.append(max_addr_score)
                weights.append(0.25)

        elif isinstance(profile1, BusinessProfile):
            # Business name similarity
            name_score = self._calculate_similarity_score(
                profile1.business_name, profile2.business_name
            )
            scores.append(name_score)
            weights.append(0.4)

            # Location similarity
            if profile1.primary_location and profile2.primary_location:
                loc1_dict = {
                    "street": profile1.primary_location.street,
                    "city": profile1.primary_location.city,
                    "state": profile1.primary_location.state,
                    "zip_code": profile1.primary_location.zip_code,
                }
                loc2_dict = {
                    "street": profile2.primary_location.street,
                    "city": profile2.primary_location.city,
                    "state": profile2.primary_location.state,
                    "zip_code": profile2.primary_location.zip_code,
                }
                location_score = self._calculate_address_similarity(
                    loc1_dict, loc2_dict
                )
                scores.append(location_score)
                weights.append(0.3)

            # Industry/entity type similarity
            if hasattr(profile1, "entity_type") and hasattr(profile2, "entity_type"):
                entity_score = (
                    1.0 if profile1.entity_type == profile2.entity_type else 0.3
                )
                scores.append(entity_score)
                weights.append(0.15)

            # Registration numbers (if available)
            if hasattr(profile1, "tax_id") and hasattr(profile2, "tax_id"):
                if profile1.tax_id and profile2.tax_id:
                    tax_score = 1.0 if profile1.tax_id == profile2.tax_id else 0.0
                    scores.append(tax_score)
                    weights.append(0.15)

        if scores and weights:
            return sum(s * w for s, w in zip(scores, weights)) / sum(weights)

        return 0.0

    def _merge_duplicate_profiles(
        self,
        profiles: List[Union[PersonProfile, BusinessProfile]],
        duplicates: List[Tuple[int, int, float]],
    ) -> List[Union[PersonProfile, BusinessProfile]]:
        """Merge duplicate profiles intelligently"""
        merged_profiles = []
        processed_indices = set()

        # Group duplicates into clusters
        duplicate_clusters = defaultdict(list)
        for i, j, similarity in duplicates:
            duplicate_clusters[i].append((j, similarity))
            duplicate_clusters[j].append((i, similarity))

        for i, profile in enumerate(profiles):
            if i in processed_indices:
                continue

            # Find all profiles in this duplicate cluster
            cluster = self._find_duplicate_cluster(
                i, duplicate_clusters, processed_indices
            )
            cluster_profiles = [profiles[idx] for idx in cluster]

            # Merge profiles in cluster
            if len(cluster_profiles) > 1:
                merged_profile = self._merge_profile_cluster(cluster_profiles)
                merged_profiles.append(merged_profile)
            else:
                merged_profiles.append(profile)

            processed_indices.update(cluster)

        return merged_profiles

    def _find_duplicate_cluster(
        self,
        start_idx: int,
        duplicate_clusters: Dict[int, List[Tuple[int, float]]],
        processed: Set[int],
    ) -> Set[int]:
        """Find all profiles in a duplicate cluster using graph traversal"""
        cluster = {start_idx}
        to_process = [start_idx]

        while to_process:
            current = to_process.pop()
            if current in processed:
                continue

            for related_idx, _ in duplicate_clusters.get(current, []):
                if related_idx not in cluster:
                    cluster.add(related_idx)
                    to_process.append(related_idx)

        return cluster

    def _merge_profile_cluster(
        self, profiles: List[Union[PersonProfile, BusinessProfile]]
    ) -> Union[PersonProfile, BusinessProfile]:
        """Merge a cluster of duplicate profiles into a single enhanced profile"""
        if not profiles:
            raise ValueError("Cannot merge empty profile cluster")

        # Use the profile with highest confidence as base
        base_profile = max(profiles, key=lambda p: p.confidence_score)

        if isinstance(base_profile, PersonProfile):
            return self._merge_person_profiles(profiles)
        else:
            return self._merge_business_profiles(profiles)

    def _merge_person_profiles(self, profiles: List[PersonProfile]) -> PersonProfile:
        """Merge multiple person profiles"""
        base_profile = max(profiles, key=lambda p: p.confidence_score)

        # Merge names (keep most complete)
        best_name = base_profile.name
        for profile in profiles:
            if (profile.name.full and not best_name.full) or (
                profile.name.first
                and profile.name.last
                and not (best_name.first and best_name.last)
            ):
                best_name = profile.name

        # Merge demographics (use most recent/complete)
        demographics = base_profile.demographics
        for profile in profiles:
            if profile.demographics and (
                not demographics or (profile.demographics.age and not demographics.age)
            ):
                demographics = profile.demographics

        # Merge and deduplicate phones
        all_phones = []
        seen_phones = set()
        for profile in profiles:
            for phone in profile.phones:
                normalized = "".join(filter(str.isdigit, phone.number))
                if normalized not in seen_phones:
                    seen_phones.add(normalized)
                    all_phones.append(phone)

        # Merge and deduplicate emails
        all_emails = []
        seen_emails = set()
        for profile in profiles:
            for email in profile.emails:
                if email.address.lower() not in seen_emails:
                    seen_emails.add(email.address.lower())
                    all_emails.append(email)

        # Merge and deduplicate addresses
        all_addresses = []
        seen_addresses = set()
        for profile in profiles:
            for address in profile.addresses:
                addr_key = f"{address.street}|{address.city}|{address.state}|{address.zip_code}".lower()
                if addr_key not in seen_addresses:
                    seen_addresses.add(addr_key)
                    all_addresses.append(address)

        # Merge associates
        all_associates = []
        seen_associates = set()
        for profile in profiles:
            for associate in profile.associates:
                assoc_key = (
                    f"{associate.name.display_name}|{associate.relationship}".lower()
                )
                if assoc_key not in seen_associates:
                    seen_associates.add(assoc_key)
                    all_associates.append(associate)

        # Calculate enhanced confidence score
        confidence_scores = [p.confidence_score for p in profiles]
        enhanced_confidence = min(
            1.0, statistics.mean(confidence_scores) + 0.1
        )  # Boost for cross-validation

        # Create merged profile
        merged_profile = PersonProfile(
            name=best_name,
            demographics=demographics,
            phones=all_phones,
            emails=all_emails,
            addresses=all_addresses,
            associates=all_associates,
            source_provider="data-enrichment-merged",
            confidence_score=enhanced_confidence,
            raw_response={
                "merged_sources": len(profiles),
                "source_profiles": [p.source_provider for p in profiles],
            },
        )

        return merged_profile

    def _merge_business_profiles(
        self, profiles: List[BusinessProfile]
    ) -> BusinessProfile:
        """Merge multiple business profiles"""
        base_profile = max(profiles, key=lambda p: p.confidence_score)

        # Use base profile as starting point and enhance with additional data
        # This would follow similar pattern to person profile merging
        # Implementation would depend on BusinessProfile structure

        return base_profile  # Simplified for now

    def _cross_validate_data(
        self, profiles: List[Union[PersonProfile, BusinessProfile]]
    ) -> DataCorrelation:
        """Perform cross-validation across multiple data sources"""
        correlation = DataCorrelation()

        if len(profiles) < 2:
            return correlation

        # Cross-validate phones
        all_phones = []
        for profile in profiles:
            if isinstance(profile, PersonProfile) and hasattr(profile, "phones"):
                all_phones.extend([p.number for p in profile.phones])

        phone_counter = Counter(all_phones)
        correlation.phone_matches = sum(
            1 for count in phone_counter.values() if count > 1
        )

        # Cross-validate addresses
        all_addresses = []
        for profile in profiles:
            if isinstance(profile, PersonProfile) and hasattr(profile, "addresses"):
                for addr in profile.addresses:
                    addr_str = f"{addr.street}|{addr.city}|{addr.state}".lower()
                    all_addresses.append(addr_str)

        address_counter = Counter(all_addresses)
        correlation.address_matches = sum(
            1 for count in address_counter.values() if count > 1
        )

        # Cross-validate emails
        all_emails = []
        for profile in profiles:
            if isinstance(profile, PersonProfile) and hasattr(profile, "emails"):
                all_emails.extend([e.address.lower() for e in profile.emails])

        email_counter = Counter(all_emails)
        correlation.email_matches = sum(
            1 for count in email_counter.values() if count > 1
        )

        # Cross-validate names
        all_names = []
        for profile in profiles:
            # Skip if profile is not actually a profile (e.g., coroutine or exception)
            if not (hasattr(profile, "name") or hasattr(profile, "business_name")):
                continue
            if isinstance(profile, PersonProfile):
                all_names.append(profile.name.display_name.lower())
            elif hasattr(profile, "business_name"):
                all_names.append(profile.business_name.lower())
            elif hasattr(profile, "name"):
                all_names.append(profile.name.lower())

        name_counter = Counter(all_names)
        correlation.name_matches = sum(
            1 for count in name_counter.values() if count > 1
        )

        # Calculate overall correlation score
        total_matches = (
            correlation.phone_matches
            + correlation.address_matches
            + correlation.email_matches
            + correlation.name_matches
        )
        max_possible = len(profiles) * 4  # 4 types of data to match
        correlation.correlation_score = (
            min(1.0, total_matches / max_possible) if max_possible > 0 else 0.0
        )

        return correlation

    def _identify_data_gaps(
        self, profiles: List[Union[PersonProfile, BusinessProfile]]
    ) -> List[str]:
        """Identify gaps in data coverage"""
        gaps = []

        # Filter out non-profile objects (coroutines, exceptions, mocks, etc.)
        actual_profiles = [
            p
            for p in profiles
            if hasattr(p, "confidence_score")
            and isinstance(p.confidence_score, (int, float))
            and hasattr(p, "__class__")
            and "Profile" in p.__class__.__name__
        ]

        if not actual_profiles:
            return ["No profile data available"]

        # Check for common gaps in person profiles
        person_profiles = [p for p in actual_profiles if isinstance(p, PersonProfile)]
        if person_profiles:
            has_phone = any(
                hasattr(profile, "phones") and profile.phones
                for profile in person_profiles
            )
            has_email = any(
                hasattr(profile, "emails") and profile.emails
                for profile in person_profiles
            )
            has_address = any(
                hasattr(profile, "addresses") and profile.addresses
                for profile in person_profiles
            )
            has_demographics = any(
                hasattr(profile, "demographics") and profile.demographics
                for profile in person_profiles
            )

            if not has_phone:
                gaps.append("Missing phone number information")
            if not has_email:
                gaps.append("Missing email address information")
            if not has_address:
                gaps.append("Missing address information")
            if not has_demographics:
                gaps.append("Missing demographic information")

        # Check data quality gaps
        low_confidence_profiles = [
            p
            for p in actual_profiles
            if hasattr(p, "confidence_score") and p.confidence_score < 0.6
        ]
        if low_confidence_profiles:
            gaps.append(
                f"{len(low_confidence_profiles)} profiles have low confidence scores"
            )

        return gaps

    def _detect_anomalies(
        self, profiles: List[Union[PersonProfile, BusinessProfile]]
    ) -> List[str]:
        """Detect data anomalies and inconsistencies"""
        anomalies = []

        # Filter out non-profile objects
        actual_profiles = [
            p
            for p in profiles
            if hasattr(p, "confidence_score")
            and isinstance(p.confidence_score, (int, float))
            and hasattr(p, "__class__")
            and "Profile" in p.__class__.__name__
        ]

        if len(actual_profiles) < 2:
            return anomalies

        # Age consistency check for person profiles
        person_profiles = [p for p in actual_profiles if isinstance(p, PersonProfile)]
        if len(person_profiles) >= 2:
            ages = []
            for profile in person_profiles:
                if profile.demographics and profile.demographics.age:
                    ages.append(profile.demographics.age)

            if len(ages) >= 2:
                age_variance = statistics.variance(ages)
                if age_variance > 25:  # More than 5-year standard deviation
                    anomalies.append(
                        f"Inconsistent age data: ages vary by {max(ages) - min(ages)} years"
                    )

        # Phone number format anomalies
        all_phones = []
        for profile in person_profiles:
            all_phones.extend([p.number for p in profile.phones])

        invalid_phones = [
            p for p in all_phones if len("".join(filter(str.isdigit, p))) < 10
        ]
        if invalid_phones:
            anomalies.append(f"{len(invalid_phones)} invalid phone number(s) detected")

        # Geographic inconsistencies
        all_states = []
        for profile in person_profiles:
            for addr in profile.addresses:
                if addr.state:
                    all_states.append(addr.state.upper())

        unique_states = set(all_states)
        if len(unique_states) > 3:
            anomalies.append(
                f"Geographic spread across {len(unique_states)} states may indicate data quality issues"
            )

        return anomalies

    def _recognize_patterns(
        self, profiles: List[Union[PersonProfile, BusinessProfile]]
    ) -> Dict[str, Any]:
        """Recognize patterns in the data"""
        patterns = {}

        # Filter out non-profile objects
        actual_profiles = [
            p
            for p in profiles
            if hasattr(p, "confidence_score")
            and isinstance(p.confidence_score, (int, float))
            and hasattr(p, "__class__")
            and "Profile" in p.__class__.__name__
        ]
        person_profiles = [p for p in actual_profiles if isinstance(p, PersonProfile)]

        if person_profiles:
            # Phone number patterns
            area_codes = []
            for profile in person_profiles:
                for phone in profile.phones:
                    digits = "".join(filter(str.isdigit, phone.number))
                    if len(digits) >= 10:
                        area_codes.append(digits[:3])

            if area_codes:
                area_code_freq = Counter(area_codes)
                most_common_area = area_code_freq.most_common(1)[0]
                patterns["dominant_area_code"] = {
                    "code": most_common_area[0],
                    "frequency": most_common_area[1],
                    "percentage": most_common_area[1] / len(area_codes) * 100,
                }

            # Email domain patterns
            domains = []
            for profile in person_profiles:
                for email in profile.emails:
                    domain = email.address.split("@")[-1].lower()
                    domains.append(domain)

            if domains:
                domain_freq = Counter(domains)
                patterns["email_domains"] = dict(domain_freq.most_common(5))

            # Geographic patterns
            cities = []
            states = []
            for profile in person_profiles:
                for addr in profile.addresses:
                    if addr.city:
                        cities.append(addr.city.lower())
                    if addr.state:
                        states.append(addr.state.upper())

            if cities:
                city_freq = Counter(cities)
                patterns["geographic_distribution"] = {
                    "cities": dict(city_freq.most_common(5)),
                    "states": dict(Counter(states).most_common(5)) if states else {},
                }

        return patterns

    def _calculate_data_freshness_score(self, sources: List[DataSource]) -> float:
        """Calculate data freshness score based on source timestamps"""
        if not sources:
            return 0.0

        freshness_scores = []
        current_time = datetime.utcnow()

        for source in sources:
            age_days = (current_time - source.timestamp).days

            # Apply exponential decay for freshness
            if age_days <= 1:
                freshness = 1.0
            elif age_days <= 7:
                freshness = 0.9
            elif age_days <= 30:
                freshness = 0.7
            elif age_days <= 90:
                freshness = 0.5
            elif age_days <= 365:
                freshness = 0.3
            else:
                freshness = 0.1

            freshness_scores.append(freshness)

        return statistics.mean(freshness_scores)

    def _update_source_reliability(
        self,
        provider: str,
        success: bool,
        accuracy: float,
        freshness: float,
        completeness: float,
    ) -> None:
        """Update source reliability tracking"""
        if provider not in self.source_reliability:
            self.source_reliability[provider] = SourceReliabilityScore(
                provider=provider
            )

        reliability = self.source_reliability[provider]
        reliability.total_queries += 1

        if success:
            reliability.successful_queries += 1

        # Update running averages
        reliability.accuracy_rate = (reliability.accuracy_rate + accuracy) / 2
        reliability.freshness_score = (reliability.freshness_score + freshness) / 2
        reliability.completeness_score = (
            reliability.completeness_score + completeness
        ) / 2
        reliability.last_updated = datetime.utcnow()

    async def enrich_person_data(
        self, query: PersonSearchQuery
    ) -> PersonIntelligenceResult:
        """
        Perform comprehensive person data enrichment across all available sources

        Args:
            query: PersonSearchQuery with search parameters

        Returns:
            PersonIntelligenceResult with enriched, cross-validated data
        """
        start_time = time.time()
        metrics = EnrichmentMetrics()

        # Query all available person-related agents sequentially for now
        # (parallel execution would require async agents)
        results = []
        sources = []

        if self.person_agent:
            try:
                result = self.person_agent.search(query)
                results.append(result)
                sources.append("person-search")
                metrics.sources_queried += 1
            except Exception as e:
                logger.warning(f"Person agent failed: {e}")
                results.append(e)
                sources.append("person-search")

        if self.phone_agent and query.phone:
            try:
                result = self.phone_agent.query({"phone": query.phone})
                results.append(result)
                sources.append("phone-search")
                metrics.sources_queried += 1
            except Exception as e:
                logger.warning(f"Phone agent failed: {e}")
                results.append(e)
                sources.append("phone-search")

        if self.email_agent and hasattr(query, "email") and query.email:
            try:
                result = self.email_agent.query({"email": query.email})
                results.append(result)
                sources.append("email-search")
                metrics.sources_queried += 1
            except Exception as e:
                logger.warning(f"Email agent failed: {e}")
                results.append(e)
                sources.append("email-search")

        if self.address_agent and (query.street or query.city):
            try:
                addr_query = {
                    "street": query.street,
                    "city": query.city,
                    "state": query.state,
                    "zip_code": query.zip_code,
                }
                result = self.address_agent.query(addr_query)
                results.append(result)
                sources.append("address-search")
                metrics.sources_queried += 1
            except Exception as e:
                logger.warning(f"Address agent failed: {e}")
                results.append(e)
                sources.append("address-search")

        # Process results
        all_profiles = []
        data_sources = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Agent {sources[i]} failed: {result}")
                continue

            # Skip coroutines or other invalid objects
            if (
                not result
                or hasattr(result, "__aenter__")
                or str(type(result).__name__).endswith("_MockMixin")
            ):
                logger.warning(
                    f"Agent {sources[i]} returned invalid result: {type(result)}"
                )
                continue

            if isinstance(result, list):
                profiles = [
                    p
                    for p in result
                    if hasattr(p, "confidence_score")
                    and isinstance(p.confidence_score, (int, float))
                    and hasattr(p, "__class__")
                    and "Profile" in p.__class__.__name__
                ]
            else:
                profiles = (
                    [result]
                    if (
                        hasattr(result, "confidence_score")
                        and isinstance(result.confidence_score, (int, float))
                        and hasattr(result, "__class__")
                        and "Profile" in result.__class__.__name__
                    )
                    else []
                )

            if profiles:
                metrics.sources_successful += 1
                all_profiles.extend(profiles)

                # Create data source attribution
                data_source = DataSource(
                    provider=sources[i],
                    query_method="search",
                    query_params=query.model_dump(),
                    timestamp=datetime.utcnow(),
                )
                data_sources.append(data_source)

        # Detect and merge duplicates
        if len(all_profiles) > 1:
            duplicates = self._detect_duplicates(all_profiles)
            metrics.duplicates_found = len(duplicates)

            if duplicates:
                all_profiles = self._merge_duplicate_profiles(all_profiles, duplicates)
                metrics.duplicates_merged = len(duplicates)

        # Cross-validate data
        correlation = self._cross_validate_data(all_profiles)
        metrics.cross_validation_matches = (
            correlation.phone_matches
            + correlation.address_matches
            + correlation.email_matches
            + correlation.name_matches
        )

        # Identify gaps and anomalies
        data_gaps = self._identify_data_gaps(all_profiles)
        anomalies = self._detect_anomalies(all_profiles)
        patterns = self._recognize_patterns(all_profiles)

        metrics.data_gaps_identified = len(data_gaps)
        metrics.anomalies_detected = len(anomalies)
        metrics.patterns_identified = len(patterns)

        # Calculate enhanced confidence scoring
        if all_profiles:
            base_scores = [p.confidence_score for p in all_profiles]
            freshness_score = self._calculate_data_freshness_score(data_sources)

            # Boost confidence for cross-validation
            cross_val_boost = min(0.2, correlation.correlation_score * 0.2)

            # Penalize for anomalies
            anomaly_penalty = min(0.1, len(anomalies) * 0.02)

            enhanced_score = min(
                1.0, statistics.mean(base_scores) + cross_val_boost - anomaly_penalty
            )

            confidence = ConfidenceScoring(
                overall_score=enhanced_score,
                data_quality=statistics.mean(base_scores),
                data_recency=freshness_score,
                source_reliability=statistics.mean(
                    [
                        self.source_reliability.get(
                            src.provider, SourceReliabilityScore(src.provider)
                        ).overall_reliability
                        for src in data_sources
                    ]
                ),
                cross_validation=correlation.correlation_score,
                completeness=1.0 - (len(data_gaps) * 0.1),
                scoring_factors={
                    "sources_count": len(data_sources),
                    "cross_validation_matches": metrics.cross_validation_matches,
                    "duplicates_merged": metrics.duplicates_merged,
                    "patterns_found": patterns,
                },
                warnings=data_gaps + anomalies,
            )
        else:
            confidence = ConfidenceScoring(
                overall_score=0.0, warnings=["No data found across any sources"]
            )

        # Create query metadata
        execution_time = time.time() - start_time
        metrics.total_processing_time = execution_time

        query_metadata = QueryMetadata(
            query_id=hashlib.sha256(
                json.dumps(query.model_dump(), sort_keys=True).encode()
            ).hexdigest()[:16],
            query_type="person-enrichment",
            original_query=query.model_dump(),
            execution_time=execution_time,
            sources_queried=metrics.sources_queried,
            sources_successful=metrics.sources_successful,
        )

        # Select primary result (highest confidence)
        primary_result = (
            max(all_profiles, key=lambda p: p.confidence_score)
            if all_profiles
            else None
        )
        additional_results = (
            [p for p in all_profiles if p != primary_result] if primary_result else []
        )

        # Create intelligence result
        result = PersonIntelligenceResult(
            data=primary_result,
            additional_results=additional_results,
            confidence=confidence,
            correlation=correlation,
            sources=data_sources,
            primary_source=data_sources[0].provider if data_sources else "none",
            query_metadata=query_metadata,
        )

        # Update source reliability metrics
        for source in data_sources:
            self._update_source_reliability(
                source.provider,
                success=True,
                accuracy=confidence.data_quality,
                freshness=freshness_score,
                completeness=confidence.completeness,
            )

        logger.info(
            f"Person data enrichment completed in {execution_time:.2f}s: "
            f"{len(all_profiles)} profiles, {metrics.duplicates_merged} duplicates merged, "
            f"confidence: {confidence.overall_score:.2f}"
        )

        return result

    async def enrich_comprehensive_data(
        self, query: Union[PersonSearchQuery, BusinessSearchQuery, Dict[str, Any]]
    ) -> ComprehensiveIntelligenceResult:
        """
        Perform comprehensive data enrichment across both person and business sources

        Args:
            query: Search query (can be person, business, or mixed)

        Returns:
            ComprehensiveIntelligenceResult with enriched data from all sources
        """
        start_time = time.time()

        person_results = []
        business_results = []

        # Determine query types and execute appropriate enrichment
        if isinstance(query, PersonSearchQuery) or (
            isinstance(query, dict)
            and any(key in query for key in ["first_name", "last_name", "phone"])
        ):
            if isinstance(query, dict):
                person_query = PersonSearchQuery(
                    **{
                        k: v
                        for k, v in query.items()
                        if k in PersonSearchQuery.__fields__
                    }
                )
            else:
                person_query = query

            person_result = await self.enrich_person_data(person_query)
            person_results.append(person_result)

        if isinstance(query, BusinessSearchQuery) or (
            isinstance(query, dict)
            and any(key in query for key in ["business_name", "tax_id"])
        ):
            if self.business_agent:
                try:
                    if isinstance(query, dict):
                        business_query = BusinessSearchQuery(
                            **{
                                k: v
                                for k, v in query.items()
                                if k in BusinessSearchQuery.__annotations__
                            }
                        )
                    else:
                        business_query = query

                    # Execute business enrichment (would implement similar to person enrichment)
                    business_profiles = self.business_agent.search(business_query)

                    # Create business intelligence result (simplified for now)
                    business_result = BusinessIntelligenceResult(
                        data=business_profiles[0] if business_profiles else None,
                        additional_results=business_profiles[1:]
                        if len(business_profiles) > 1
                        else [],
                        confidence=ConfidenceScoring(overall_score=0.8),
                        sources=[],
                        primary_source="business-search",
                        query_metadata=QueryMetadata(
                            query_id="business-query",
                            query_type="business-enrichment",
                            original_query=business_query.model_dump()
                            if hasattr(business_query, "model_dump")
                            else query,
                            execution_time=0.0,
                            sources_queried=1,
                            sources_successful=1,
                        ),
                    )
                    business_results.append(business_result)
                except Exception as e:
                    logger.warning(f"Business agent failed: {e}")

        # Calculate overall confidence and metadata
        all_confidences = [r.confidence.overall_score for r in person_results] + [
            r.confidence.overall_score for r in business_results
        ]

        overall_confidence = ConfidenceScoring(
            overall_score=statistics.mean(all_confidences) if all_confidences else 0.0
        )

        execution_time = time.time() - start_time
        overall_metadata = QueryMetadata(
            query_id=hashlib.sha256(str(query).encode()).hexdigest()[:16],
            query_type="comprehensive-enrichment",
            original_query=query if isinstance(query, dict) else query.model_dump(),
            execution_time=execution_time,
            sources_queried=sum(
                r.query_metadata.sources_queried
                for r in person_results + business_results
            ),
            sources_successful=sum(
                r.query_metadata.sources_successful
                for r in person_results + business_results
            ),
        )

        result = ComprehensiveIntelligenceResult(
            person_results=person_results,
            business_results=business_results,
            overall_confidence=overall_confidence,
            query_metadata=overall_metadata,
        )

        logger.info(
            f"Comprehensive enrichment completed in {execution_time:.2f}s: "
            f"{len(person_results)} person results, {len(business_results)} business results"
        )

        return result

    def query(
        self, query_params: Dict[str, Any], **kwargs
    ) -> ComprehensiveIntelligenceResult:
        """
        Execute comprehensive query using dict parameters (BaseIntelligenceAgent interface)

        Args:
            query_params: Dictionary of query parameters
            **kwargs: Additional arguments

        Returns:
            ComprehensiveIntelligenceResult
        """
        # Run async enrichment in sync context
        return asyncio.run(self.enrich_comprehensive_data(query_params))

    def get_source_reliability_report(self) -> Dict[str, Any]:
        """Get comprehensive source reliability report"""
        report = {
            "sources": {},
            "summary": {
                "total_sources": len(self.source_reliability),
                "avg_reliability": 0.0,
                "most_reliable": None,
                "least_reliable": None,
            },
        }

        if self.source_reliability:
            reliabilities = []
            for provider, reliability in self.source_reliability.items():
                reliability_data = {
                    "provider": provider,
                    "total_queries": reliability.total_queries,
                    "success_rate": reliability.successful_queries
                    / max(1, reliability.total_queries),
                    "accuracy_rate": reliability.accuracy_rate,
                    "freshness_score": reliability.freshness_score,
                    "completeness_score": reliability.completeness_score,
                    "overall_reliability": reliability.overall_reliability,
                    "last_updated": reliability.last_updated.isoformat(),
                }
                report["sources"][provider] = reliability_data
                reliabilities.append(reliability.overall_reliability)

            report["summary"]["avg_reliability"] = statistics.mean(reliabilities)

            best_provider = max(
                self.source_reliability.items(), key=lambda x: x[1].overall_reliability
            )
            worst_provider = min(
                self.source_reliability.items(), key=lambda x: x[1].overall_reliability
            )

            report["summary"]["most_reliable"] = best_provider[0]
            report["summary"]["least_reliable"] = worst_provider[0]

        return report

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check for DataEnrichmentAgent"""
        try:
            agent_status = {
                "person_agent": self.person_agent is not None,
                "business_agent": self.business_agent is not None,
                "phone_agent": self.phone_agent is not None,
                "email_agent": self.email_agent is not None,
                "address_agent": self.address_agent is not None,
            }

            available_agents = sum(agent_status.values())

            health_status = {
                "status": "healthy",
                "provider": self.provider,
                "agent_name": self.agent_name,
                "credential_available": True,  # Override for orchestration agent
                "timestamp": datetime.utcnow().isoformat(),
                "data_enrichment_ready": available_agents > 0,
                "available_agents": available_agents,
                "agent_status": agent_status,
                "enrichment_config": {
                    "confidence_threshold": self.config.confidence_threshold,
                    "deduplication_threshold": self.config.deduplication_threshold,
                    "enable_deep_enrichment": self.config.enable_deep_enrichment,
                    "enable_anomaly_detection": self.config.enable_anomaly_detection,
                },
                "source_reliability_tracking": len(self.source_reliability),
                "known_patterns": len(self.known_patterns),
                "metrics": self.get_metrics(),
            }

            return health_status

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
