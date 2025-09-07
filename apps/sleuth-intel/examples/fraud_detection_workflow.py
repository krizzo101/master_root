#!/usr/bin/env python3
"""
Fraud Detection Workflow Example
=================================

This example demonstrates comprehensive fraud detection workflows
including identity verification, risk scoring, and pattern analysis.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python fraud_detection_workflow.py
"""

import asyncio
import hashlib
import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    AddressSearchRequest,
    BusinessSearchRequest,
    EmailVerificationRequest,
    IDVerificationRequest,
    PersonSearchRequest,
    PhoneLookupRequest,
)


class FraudType(Enum):
    """Types of fraud."""

    IDENTITY_THEFT = "identity_theft"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    ACCOUNT_TAKEOVER = "account_takeover"
    APPLICATION_FRAUD = "application_fraud"
    TRANSACTION_FRAUD = "transaction_fraud"
    BUSINESS_FRAUD = "business_fraud"


class RiskLevel(Enum):
    """Risk levels."""

    VERY_LOW = (0, 20, "Very Low Risk")
    LOW = (20, 40, "Low Risk")
    MEDIUM = (40, 60, "Medium Risk")
    HIGH = (60, 80, "High Risk")
    VERY_HIGH = (80, 100, "Very High Risk")

    @classmethod
    def from_score(cls, score: int) -> "RiskLevel":
        """Get risk level from score."""
        for level in cls:
            if level.value[0] <= score < level.value[1]:
                return level
        return cls.VERY_HIGH


class FraudIndicator:
    """Individual fraud indicator."""

    def __init__(
        self,
        indicator_type: str,
        description: str,
        severity: int,  # 1-10
        confidence: float,  # 0-1
        evidence: Dict[str, Any],
    ):
        self.indicator_type = indicator_type
        self.description = description
        self.severity = severity
        self.confidence = confidence
        self.evidence = evidence
        self.timestamp = datetime.now()

    @property
    def weighted_score(self) -> float:
        """Calculate weighted risk score."""
        return self.severity * self.confidence * 10


class FraudDetector:
    """Comprehensive fraud detection system."""

    def __init__(self):
        self.client = SleuthIntel()
        self.case_id = None
        self.fraud_indicators = []
        self.verification_results = {}
        self.risk_score = 0
        self.fraud_probability = 0
        self.recommendations = []

    async def analyze_transaction(
        self,
        transaction_data: Dict[str, Any],
        historical_data: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a transaction for fraud.

        Args:
            transaction_data: Current transaction details
            historical_data: Historical transaction patterns

        Returns:
            Fraud analysis results
        """
        self.case_id = self._generate_case_id(transaction_data)

        print(f"\n💳 Transaction Fraud Analysis")
        print(f"Case ID: {self.case_id}")
        print("=" * 60)

        analysis = {
            "case_id": self.case_id,
            "timestamp": datetime.now().isoformat(),
            "transaction": transaction_data,
            "checks": {},
            "indicators": [],
            "risk_score": 0,
            "decision": None,
        }

        # Step 1: Verify identity
        identity_check = await self._verify_identity(
            transaction_data.get("customer", {})
        )
        analysis["checks"]["identity"] = identity_check

        # Step 2: Verify contact information
        contact_check = await self._verify_contact_info(
            transaction_data.get("customer", {})
        )
        analysis["checks"]["contact"] = contact_check

        # Step 3: Check velocity patterns
        velocity_check = self._check_velocity_patterns(
            transaction_data, historical_data
        )
        analysis["checks"]["velocity"] = velocity_check

        # Step 4: Analyze behavioral patterns
        behavioral_check = self._analyze_behavioral_patterns(
            transaction_data, historical_data
        )
        analysis["checks"]["behavioral"] = behavioral_check

        # Step 5: Geographic analysis
        geo_check = await self._geographic_analysis(
            transaction_data.get("location", {}), transaction_data.get("customer", {})
        )
        analysis["checks"]["geographic"] = geo_check

        # Step 6: Device fingerprinting
        device_check = self._device_fingerprint_analysis(
            transaction_data.get("device", {})
        )
        analysis["checks"]["device"] = device_check

        # Calculate final risk score
        self._calculate_risk_score()
        analysis["risk_score"] = self.risk_score
        analysis["risk_level"] = RiskLevel.from_score(self.risk_score).value[2]
        analysis["indicators"] = [
            {
                "type": ind.indicator_type,
                "description": ind.description,
                "severity": ind.severity,
                "confidence": ind.confidence,
            }
            for ind in self.fraud_indicators
        ]

        # Make decision
        analysis["decision"] = self._make_decision()
        analysis["recommendations"] = self.recommendations

        # Generate report
        self._generate_transaction_report(analysis)

        return analysis

    async def detect_identity_fraud(
        self, identity_data: Dict[str, Any], documents: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Detect identity fraud.

        Args:
            identity_data: Identity information to verify
            documents: Optional document data for verification

        Returns:
            Identity fraud detection results
        """
        self.case_id = self._generate_case_id(identity_data)

        print(f"\n🆔 Identity Fraud Detection")
        print(f"Case ID: {self.case_id}")
        print("=" * 60)

        detection = {
            "case_id": self.case_id,
            "timestamp": datetime.now().isoformat(),
            "identity": identity_data,
            "verification_steps": {},
            "fraud_type_analysis": {},
            "indicators": [],
            "risk_score": 0,
        }

        # Step 1: Basic identity verification
        print("\n📋 Step 1: Identity Verification")
        identity_result = await self._comprehensive_identity_check(identity_data)
        detection["verification_steps"]["identity"] = identity_result

        # Step 2: Check for synthetic identity
        print("\n🤖 Step 2: Synthetic Identity Check")
        synthetic_check = await self._check_synthetic_identity(identity_data)
        detection["fraud_type_analysis"]["synthetic"] = synthetic_check

        # Step 3: Check for identity theft indicators
        print("\n🔓 Step 3: Identity Theft Check")
        theft_check = await self._check_identity_theft(identity_data)
        detection["fraud_type_analysis"]["theft"] = theft_check

        # Step 4: Document verification (if provided)
        if documents:
            print("\n📄 Step 4: Document Verification")
            doc_result = await self._verify_documents(documents, identity_data)
            detection["verification_steps"]["documents"] = doc_result

        # Step 5: Cross-reference checks
        print("\n🔗 Step 5: Cross-Reference Analysis")
        cross_ref = await self._cross_reference_identity(identity_data)
        detection["verification_steps"]["cross_reference"] = cross_ref

        # Calculate risk score
        self._calculate_risk_score()
        detection["risk_score"] = self.risk_score
        detection["risk_level"] = RiskLevel.from_score(self.risk_score).value[2]
        detection["indicators"] = self.fraud_indicators

        # Determine fraud probability
        detection["fraud_probability"] = self._calculate_fraud_probability()
        detection["recommendations"] = self._generate_recommendations()

        # Generate report
        self._generate_identity_report(detection)

        return detection

    async def detect_business_fraud(
        self, business_data: Dict[str, Any], financial_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Detect business fraud.

        Args:
            business_data: Business information
            financial_data: Optional financial data

        Returns:
            Business fraud detection results
        """
        self.case_id = self._generate_case_id(business_data)

        print(f"\n🏢 Business Fraud Detection")
        print(f"Case ID: {self.case_id}")
        print("=" * 60)

        detection = {
            "case_id": self.case_id,
            "timestamp": datetime.now().isoformat(),
            "business": business_data,
            "verification": {},
            "risk_factors": [],
            "indicators": [],
        }

        # Step 1: Business entity verification
        print("\n📋 Step 1: Business Entity Verification")
        entity_check = await self._verify_business_entity(business_data)
        detection["verification"]["entity"] = entity_check

        # Step 2: Officer/Director verification
        print("\n👥 Step 2: Officer Verification")
        officer_check = await self._verify_business_officers(business_data)
        detection["verification"]["officers"] = officer_check

        # Step 3: Address and location verification
        print("\n📍 Step 3: Location Verification")
        location_check = await self._verify_business_location(business_data)
        detection["verification"]["location"] = location_check

        # Step 4: Financial analysis
        if financial_data:
            print("\n💰 Step 4: Financial Analysis")
            financial_check = self._analyze_financial_data(financial_data)
            detection["verification"]["financial"] = financial_check

        # Step 5: Shell company indicators
        print("\n🐚 Step 5: Shell Company Analysis")
        shell_check = self._check_shell_company_indicators(
            business_data, detection["verification"]
        )
        detection["risk_factors"].extend(shell_check)

        # Calculate risk
        self._calculate_risk_score()
        detection["risk_score"] = self.risk_score
        detection["risk_level"] = RiskLevel.from_score(self.risk_score).value[2]
        detection["fraud_probability"] = self._calculate_fraud_probability()
        detection["recommendations"] = self._generate_recommendations()

        # Generate report
        self._generate_business_report(detection)

        return detection

    def _generate_case_id(self, data: Dict) -> str:
        """Generate unique case ID."""
        return (
            hashlib.sha256(f"{data}{datetime.now().isoformat()}".encode())
            .hexdigest()[:12]
            .upper()
        )

    async def _verify_identity(self, customer_data: Dict) -> Dict[str, Any]:
        """Verify customer identity."""
        try:
            request = PersonSearchRequest(
                first_name=customer_data.get("first_name"),
                last_name=customer_data.get("last_name"),
                date_of_birth=customer_data.get("date_of_birth"),
                ssn_last4=customer_data.get("ssn_last4"),
            )

            response = await self.client.person_search(request)

            if response.success and response.results:
                match = response.results[0]
                confidence = match.get("match_confidence", 0)

                if confidence < 70:
                    self._add_indicator(
                        "identity_mismatch",
                        "Low confidence identity match",
                        severity=7,
                        confidence=0.8,
                        evidence={"match_confidence": confidence},
                    )

                return {
                    "verified": confidence >= 70,
                    "confidence": confidence,
                    "match": match,
                }
            else:
                self._add_indicator(
                    "identity_not_found",
                    "Identity could not be verified",
                    severity=8,
                    confidence=0.9,
                    evidence={"search_data": customer_data},
                )
                return {"verified": False, "confidence": 0}

        except Exception as e:
            return {"verified": False, "error": str(e)}

    async def _verify_contact_info(self, customer_data: Dict) -> Dict[str, Any]:
        """Verify contact information."""
        results = {}

        # Verify phone
        if customer_data.get("phone"):
            try:
                request = PhoneLookupRequest(phone=customer_data["phone"])
                response = await self.client.phone_lookup(request)

                if response.success:
                    results["phone"] = {
                        "valid": response.is_valid,
                        "type": response.phone_type,
                        "carrier": response.carrier,
                    }

                    if not response.is_valid:
                        self._add_indicator(
                            "invalid_phone",
                            "Phone number is invalid",
                            severity=5,
                            confidence=0.9,
                            evidence={"phone": customer_data["phone"]},
                        )
                    elif response.phone_type == "VOIP":
                        self._add_indicator(
                            "voip_phone",
                            "VOIP phone number detected",
                            severity=3,
                            confidence=0.7,
                            evidence={"phone_type": "VOIP"},
                        )
            except:
                pass

        # Verify email
        if customer_data.get("email"):
            try:
                request = EmailVerificationRequest(email=customer_data["email"])
                response = await self.client.email_verification(request)

                if response.success:
                    results["email"] = {
                        "valid": response.is_valid,
                        "deliverable": response.is_deliverable,
                        "disposable": response.is_disposable,
                    }

                    if response.is_disposable:
                        self._add_indicator(
                            "disposable_email",
                            "Disposable email address detected",
                            severity=6,
                            confidence=1.0,
                            evidence={"email": customer_data["email"]},
                        )
            except:
                pass

        return results

    def _check_velocity_patterns(
        self, transaction: Dict, historical: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Check transaction velocity patterns."""
        if not historical:
            return {"checked": False}

        # Calculate velocity metrics
        now = datetime.now()
        last_hour = [
            t
            for t in historical
            if (now - datetime.fromisoformat(t["timestamp"])).seconds < 3600
        ]
        last_day = [
            t
            for t in historical
            if (now - datetime.fromisoformat(t["timestamp"])).days < 1
        ]

        velocity = {
            "transactions_last_hour": len(last_hour),
            "transactions_last_day": len(last_day),
            "amount_last_hour": sum(t.get("amount", 0) for t in last_hour),
            "amount_last_day": sum(t.get("amount", 0) for t in last_day),
        }

        # Check for velocity spikes
        if velocity["transactions_last_hour"] > 5:
            self._add_indicator(
                "high_velocity",
                f"High transaction velocity: {velocity['transactions_last_hour']} in last hour",
                severity=7,
                confidence=0.9,
                evidence=velocity,
            )

        if velocity["amount_last_day"] > 10000:
            self._add_indicator(
                "high_amount_velocity",
                f"High amount velocity: ${velocity['amount_last_day']} in last day",
                severity=8,
                confidence=0.9,
                evidence=velocity,
            )

        return velocity

    def _analyze_behavioral_patterns(
        self, transaction: Dict, historical: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Analyze behavioral patterns."""
        if not historical:
            return {"analyzed": False}

        patterns = {
            "typical_amount": 0,
            "typical_time": None,
            "typical_location": None,
            "anomalies": [],
        }

        if historical:
            amounts = [t.get("amount", 0) for t in historical]
            patterns["typical_amount"] = statistics.median(amounts) if amounts else 0

            # Check for amount anomaly
            if transaction.get("amount", 0) > patterns["typical_amount"] * 3:
                self._add_indicator(
                    "amount_anomaly",
                    "Transaction amount significantly higher than typical",
                    severity=6,
                    confidence=0.8,
                    evidence={
                        "current": transaction.get("amount"),
                        "typical": patterns["typical_amount"],
                    },
                )
                patterns["anomalies"].append("amount")

        return patterns

    async def _geographic_analysis(
        self, location: Dict, customer: Dict
    ) -> Dict[str, Any]:
        """Analyze geographic factors."""
        analysis = {
            "location_verified": False,
            "distance_from_home": None,
            "high_risk_location": False,
        }

        # Check if location matches customer address
        if customer.get("address") and location.get("address"):
            try:
                request = AddressSearchRequest(
                    address=location.get("address"),
                    city=location.get("city"),
                    state=location.get("state"),
                )

                response = await self.client.address_search(request)

                if response.success:
                    analysis["location_verified"] = True

                    # Check for high-risk locations
                    # This would integrate with geo-risk databases

            except:
                pass

        return analysis

    def _device_fingerprint_analysis(self, device: Dict) -> Dict[str, Any]:
        """Analyze device fingerprint."""
        analysis = {"device_id": device.get("id"), "trusted": False, "risk_factors": []}

        # Check for VPN/Proxy
        if device.get("using_vpn") or device.get("using_proxy"):
            self._add_indicator(
                "masked_connection",
                "VPN or proxy detected",
                severity=5,
                confidence=0.8,
                evidence={
                    "vpn": device.get("using_vpn"),
                    "proxy": device.get("using_proxy"),
                },
            )
            analysis["risk_factors"].append("masked_connection")

        # Check for emulator
        if device.get("is_emulator"):
            self._add_indicator(
                "emulator_detected",
                "Device emulator detected",
                severity=7,
                confidence=0.9,
                evidence={"emulator": True},
            )
            analysis["risk_factors"].append("emulator")

        return analysis

    async def _comprehensive_identity_check(self, identity: Dict) -> Dict[str, Any]:
        """Comprehensive identity verification."""
        result = {
            "verified": False,
            "confidence": 0,
            "checks_passed": [],
            "checks_failed": [],
        }

        # Person search
        try:
            request = PersonSearchRequest(
                first_name=identity.get("first_name"),
                last_name=identity.get("last_name"),
                date_of_birth=identity.get("date_of_birth"),
                ssn_last4=identity.get("ssn_last4"),
            )

            response = await self.client.person_search(request)

            if response.success and response.results:
                match = response.results[0]
                confidence = match.get("match_confidence", 0)

                result["confidence"] = confidence
                result["verified"] = confidence >= 80

                if result["verified"]:
                    result["checks_passed"].append("identity_match")
                    print(f"  ✅ Identity verified (confidence: {confidence}%)")
                else:
                    result["checks_failed"].append("identity_match")
                    print(f"  ❌ Identity match failed (confidence: {confidence}%)")

                    self._add_indicator(
                        "low_identity_confidence",
                        f"Identity match confidence too low: {confidence}%",
                        severity=8,
                        confidence=0.9,
                        evidence={"match_confidence": confidence},
                    )
            else:
                result["checks_failed"].append("identity_not_found")
                print("  ❌ Identity not found")

                self._add_indicator(
                    "identity_not_found",
                    "No matching identity records found",
                    severity=9,
                    confidence=1.0,
                    evidence={"search_criteria": identity},
                )

        except Exception as e:
            result["error"] = str(e)
            result["checks_failed"].append("identity_check_error")

        return result

    async def _check_synthetic_identity(self, identity: Dict) -> Dict[str, Any]:
        """Check for synthetic identity indicators."""
        indicators = []
        risk_score = 0

        # Check for thin file (limited history)
        if identity.get("credit_history_years", 0) < 2:
            indicators.append("thin_credit_file")
            risk_score += 20

            self._add_indicator(
                "thin_file",
                "Limited credit history suggests possible synthetic identity",
                severity=6,
                confidence=0.7,
                evidence={"credit_years": identity.get("credit_history_years", 0)},
            )

        # Check for SSN inconsistencies
        if identity.get("ssn_issue_date"):
            birth_date = datetime.fromisoformat(
                identity.get("date_of_birth", "1900-01-01")
            )
            ssn_date = datetime.fromisoformat(identity["ssn_issue_date"])

            if ssn_date < birth_date:
                indicators.append("ssn_before_birth")
                risk_score += 30

                self._add_indicator(
                    "ssn_anomaly",
                    "SSN issued before birth date",
                    severity=9,
                    confidence=1.0,
                    evidence={
                        "birth_date": identity.get("date_of_birth"),
                        "ssn_issue_date": identity["ssn_issue_date"],
                    },
                )

        # Check for address proliferation
        if identity.get("address_count", 0) > 10:
            indicators.append("excessive_addresses")
            risk_score += 15

            self._add_indicator(
                "address_proliferation",
                "Excessive number of addresses",
                severity=5,
                confidence=0.8,
                evidence={"address_count": identity.get("address_count")},
            )

        return {
            "risk_score": risk_score,
            "indicators": indicators,
            "likely_synthetic": risk_score > 40,
        }

    async def _check_identity_theft(self, identity: Dict) -> Dict[str, Any]:
        """Check for identity theft indicators."""
        indicators = []
        risk_score = 0

        # Check for recent address changes
        if identity.get("recent_address_changes", 0) > 2:
            indicators.append("frequent_address_changes")
            risk_score += 15

            self._add_indicator(
                "address_changes",
                "Frequent recent address changes",
                severity=5,
                confidence=0.7,
                evidence={"changes": identity.get("recent_address_changes")},
            )

        # Check for inquiry spike
        if identity.get("recent_inquiries", 0) > 5:
            indicators.append("inquiry_spike")
            risk_score += 20

            self._add_indicator(
                "inquiry_spike",
                "Spike in credit inquiries",
                severity=6,
                confidence=0.8,
                evidence={"inquiries": identity.get("recent_inquiries")},
            )

        return {
            "risk_score": risk_score,
            "indicators": indicators,
            "likely_theft": risk_score > 30,
        }

    async def _verify_documents(
        self, documents: List[Dict], identity: Dict
    ) -> Dict[str, Any]:
        """Verify identity documents."""
        results = {
            "documents_verified": 0,
            "documents_failed": 0,
            "verification_details": [],
        }

        for doc in documents:
            # This would integrate with document verification APIs
            # For demo, we'll simulate
            verification = {
                "document_type": doc.get("type"),
                "document_id": doc.get("id"),
                "verified": True,  # Simulated
                "matches_identity": True,
            }

            if verification["verified"]:
                results["documents_verified"] += 1
            else:
                results["documents_failed"] += 1

                self._add_indicator(
                    "document_failed",
                    f"Document verification failed: {doc.get('type')}",
                    severity=7,
                    confidence=0.9,
                    evidence={"document": doc},
                )

            results["verification_details"].append(verification)

        return results

    async def _cross_reference_identity(self, identity: Dict) -> Dict[str, Any]:
        """Cross-reference identity across data sources."""
        cross_refs = {"sources_checked": [], "matches": [], "discrepancies": []}

        # Check multiple data sources
        # This would integrate with various APIs

        # For demo, simulate some checks
        cross_refs["sources_checked"] = [
            "credit_bureau",
            "public_records",
            "social_media",
        ]
        cross_refs["matches"] = ["name", "dob", "address"]

        if cross_refs["discrepancies"]:
            for discrepancy in cross_refs["discrepancies"]:
                self._add_indicator(
                    "data_discrepancy",
                    f"Data discrepancy found: {discrepancy}",
                    severity=6,
                    confidence=0.8,
                    evidence={"discrepancy": discrepancy},
                )

        return cross_refs

    async def _verify_business_entity(self, business: Dict) -> Dict[str, Any]:
        """Verify business entity."""
        try:
            request = BusinessSearchRequest(
                business_name=business.get("name"),
                ein=business.get("ein"),
                state=business.get("state"),
            )

            response = await self.client.business_search(request)

            if response.success and response.results:
                match = response.results[0]

                return {
                    "verified": True,
                    "entity_type": match.get("entity_type"),
                    "status": match.get("status"),
                    "formation_date": match.get("formation_date"),
                    "good_standing": match.get("status") == "ACTIVE",
                }
            else:
                self._add_indicator(
                    "business_not_found",
                    "Business entity could not be verified",
                    severity=8,
                    confidence=0.9,
                    evidence={"business": business.get("name")},
                )

                return {"verified": False}

        except Exception as e:
            return {"verified": False, "error": str(e)}

    async def _verify_business_officers(self, business: Dict) -> Dict[str, Any]:
        """Verify business officers."""
        officers = business.get("officers", [])

        if not officers:
            self._add_indicator(
                "no_officers",
                "No officers listed for business",
                severity=6,
                confidence=0.8,
                evidence={"business": business.get("name")},
            )
            return {"verified": False, "reason": "No officers listed"}

        verified_officers = []

        for officer in officers:
            # Verify each officer
            try:
                request = PersonSearchRequest(
                    first_name=officer.get("first_name"),
                    last_name=officer.get("last_name"),
                )

                response = await self.client.person_search(request)

                if response.success and response.results:
                    verified_officers.append(
                        {
                            "name": f"{officer.get('first_name')} {officer.get('last_name')}",
                            "verified": True,
                        }
                    )
                else:
                    self._add_indicator(
                        "officer_not_verified",
                        f"Officer could not be verified: {officer.get('first_name')} {officer.get('last_name')}",
                        severity=5,
                        confidence=0.7,
                        evidence={"officer": officer},
                    )

            except:
                pass

        return {
            "total_officers": len(officers),
            "verified_officers": len(verified_officers),
            "verification_rate": len(verified_officers) / len(officers)
            if officers
            else 0,
        }

    async def _verify_business_location(self, business: Dict) -> Dict[str, Any]:
        """Verify business location."""
        try:
            request = AddressSearchRequest(
                address=business.get("address"),
                city=business.get("city"),
                state=business.get("state"),
                zip_code=business.get("zip"),
            )

            response = await self.client.address_search(request)

            if response.success:
                result = {
                    "verified": True,
                    "address": response.formatted_address,
                    "type": "commercial" if response.is_commercial else "residential",
                }

                # Flag if residential address for business
                if not response.is_commercial:
                    self._add_indicator(
                        "residential_business_address",
                        "Business uses residential address",
                        severity=4,
                        confidence=0.8,
                        evidence={"address_type": "residential"},
                    )

                return result
            else:
                self._add_indicator(
                    "address_not_verified",
                    "Business address could not be verified",
                    severity=6,
                    confidence=0.8,
                    evidence={"address": business.get("address")},
                )

                return {"verified": False}

        except Exception as e:
            return {"verified": False, "error": str(e)}

    def _analyze_financial_data(self, financial: Dict) -> Dict[str, Any]:
        """Analyze financial data for fraud indicators."""
        analysis = {"risk_factors": [], "anomalies": []}

        # Check for round number transactions
        if financial.get("transactions"):
            round_numbers = [
                t for t in financial["transactions"] if t["amount"] % 100 == 0
            ]
            if len(round_numbers) > len(financial["transactions"]) * 0.5:
                analysis["anomalies"].append("excessive_round_numbers")

                self._add_indicator(
                    "round_number_pattern",
                    "Excessive round number transactions",
                    severity=5,
                    confidence=0.7,
                    evidence={
                        "percentage": len(round_numbers)
                        / len(financial["transactions"])
                    },
                )

        # Check for structuring
        if financial.get("deposits"):
            just_under_10k = [
                d for d in financial["deposits"] if 9000 <= d["amount"] < 10000
            ]
            if just_under_10k:
                analysis["risk_factors"].append("potential_structuring")

                self._add_indicator(
                    "structuring_pattern",
                    "Potential structuring detected",
                    severity=8,
                    confidence=0.8,
                    evidence={"suspicious_deposits": len(just_under_10k)},
                )

        return analysis

    def _check_shell_company_indicators(
        self, business: Dict, verification: Dict
    ) -> List[str]:
        """Check for shell company indicators."""
        indicators = []

        # No real business address
        if not verification.get("location", {}).get("verified"):
            indicators.append("no_verified_address")

            self._add_indicator(
                "shell_company_indicator",
                "No verified business address",
                severity=7,
                confidence=0.8,
                evidence={"indicator": "no_address"},
            )

        # No employees
        if business.get("employee_count", 0) == 0:
            indicators.append("no_employees")

            self._add_indicator(
                "shell_company_indicator",
                "No reported employees",
                severity=6,
                confidence=0.7,
                evidence={"employees": 0},
            )

        # Recently formed
        if business.get("formation_date"):
            formation = datetime.fromisoformat(business["formation_date"])
            if (datetime.now() - formation).days < 90:
                indicators.append("recently_formed")

                self._add_indicator(
                    "shell_company_indicator",
                    "Recently formed business",
                    severity=5,
                    confidence=0.6,
                    evidence={"formation_date": business["formation_date"]},
                )

        return indicators

    def _add_indicator(
        self,
        indicator_type: str,
        description: str,
        severity: int,
        confidence: float,
        evidence: Dict[str, Any],
    ):
        """Add fraud indicator."""
        indicator = FraudIndicator(
            indicator_type=indicator_type,
            description=description,
            severity=severity,
            confidence=confidence,
            evidence=evidence,
        )
        self.fraud_indicators.append(indicator)

    def _calculate_risk_score(self):
        """Calculate overall risk score."""
        if not self.fraud_indicators:
            self.risk_score = 0
            return

        # Weight indicators by severity and confidence
        total_score = sum(ind.weighted_score for ind in self.fraud_indicators)
        max_possible = len(self.fraud_indicators) * 100

        # Normalize to 0-100
        self.risk_score = (
            min(100, int((total_score / max_possible) * 100)) if max_possible > 0 else 0
        )

    def _calculate_fraud_probability(self) -> float:
        """Calculate fraud probability."""
        # Simple probability based on risk score and indicators
        base_probability = self.risk_score / 100

        # Adjust based on high-severity indicators
        high_severity = [ind for ind in self.fraud_indicators if ind.severity >= 8]
        if high_severity:
            adjustment = len(high_severity) * 0.1
            base_probability = min(1.0, base_probability + adjustment)

        self.fraud_probability = base_probability
        return self.fraud_probability

    def _make_decision(self) -> str:
        """Make fraud decision."""
        if self.risk_score < 20:
            decision = "APPROVE"
        elif self.risk_score < 40:
            decision = "REVIEW"
        elif self.risk_score < 60:
            decision = "MANUAL_REVIEW"
        elif self.risk_score < 80:
            decision = "DECLINE"
        else:
            decision = "BLOCK"

        # Add recommendations based on decision
        if decision == "REVIEW":
            self.recommendations.append("Additional verification recommended")
        elif decision == "MANUAL_REVIEW":
            self.recommendations.append("Escalate to fraud team for manual review")
            self.recommendations.append("Request additional documentation")
        elif decision in ["DECLINE", "BLOCK"]:
            self.recommendations.append("Transaction should be declined")
            self.recommendations.append("Flag account for monitoring")

            if decision == "BLOCK":
                self.recommendations.append("Consider account suspension")

        return decision

    def _generate_recommendations(self) -> List[str]:
        """Generate fraud prevention recommendations."""
        recommendations = []

        if self.risk_score > 60:
            recommendations.append("Immediate manual review required")
            recommendations.append("Request additional identity verification")
            recommendations.append("Flag for ongoing monitoring")
        elif self.risk_score > 40:
            recommendations.append("Enhanced due diligence recommended")
            recommendations.append("Verify contact information")
            recommendations.append("Monitor account activity closely")
        elif self.risk_score > 20:
            recommendations.append("Standard verification procedures")
            recommendations.append("Periodic review recommended")
        else:
            recommendations.append("Low risk - standard procedures apply")

        # Add specific recommendations based on indicators
        for indicator in self.fraud_indicators:
            if indicator.severity >= 8:
                if indicator.indicator_type == "identity_not_found":
                    recommendations.append("Require government-issued ID verification")
                elif indicator.indicator_type == "synthetic_identity":
                    recommendations.append("Require in-person verification")
                elif indicator.indicator_type == "document_tampering":
                    recommendations.append("Require certified document copies")

        self.recommendations = list(set(recommendations))  # Remove duplicates
        return self.recommendations

    def _generate_transaction_report(self, analysis: Dict):
        """Generate transaction fraud report."""
        print("\n" + "=" * 60)
        print("TRANSACTION FRAUD ANALYSIS REPORT")
        print("=" * 60)
        print(f"Case ID: {analysis['case_id']}")
        print(f"Risk Score: {analysis['risk_score']}/100")
        print(f"Risk Level: {analysis['risk_level']}")
        print(f"Decision: {analysis['decision']}")

        if analysis["indicators"]:
            print("\nFraud Indicators:")
            for ind in analysis["indicators"][:5]:
                print(f"  • [{ind['severity']}/10] {ind['description']}")

        if analysis["recommendations"]:
            print("\nRecommendations:")
            for rec in analysis["recommendations"]:
                print(f"  • {rec}")

        # Save report
        report_file = f"fraud_transaction_{analysis['case_id']}.json"
        with open(report_file, "w") as f:
            json.dump(analysis, f, indent=2)
        print(f"\n💾 Report saved to: {report_file}")

    def _generate_identity_report(self, detection: Dict):
        """Generate identity fraud report."""
        print("\n" + "=" * 60)
        print("IDENTITY FRAUD DETECTION REPORT")
        print("=" * 60)
        print(f"Case ID: {detection['case_id']}")
        print(f"Risk Score: {detection['risk_score']}/100")
        print(f"Risk Level: {detection['risk_level']}")
        print(f"Fraud Probability: {detection['fraud_probability']:.1%}")

        # Save report
        report_file = f"fraud_identity_{detection['case_id']}.json"
        with open(report_file, "w") as f:
            json.dump(detection, f, indent=2, default=str)
        print(f"\n💾 Report saved to: {report_file}")

    def _generate_business_report(self, detection: Dict):
        """Generate business fraud report."""
        print("\n" + "=" * 60)
        print("BUSINESS FRAUD DETECTION REPORT")
        print("=" * 60)
        print(f"Case ID: {detection['case_id']}")
        print(f"Business: {detection['business'].get('name')}")
        print(f"Risk Score: {detection['risk_score']}/100")
        print(f"Risk Level: {detection['risk_level']}")
        print(f"Fraud Probability: {detection['fraud_probability']:.1%}")

        if detection["risk_factors"]:
            print("\nRisk Factors:")
            for factor in detection["risk_factors"]:
                print(f"  • {factor}")

        # Save report
        report_file = f"fraud_business_{detection['case_id']}.json"
        with open(report_file, "w") as f:
            json.dump(detection, f, indent=2, default=str)
        print(f"\n💾 Report saved to: {report_file}")

    async def close(self):
        """Clean up resources."""
        await self.client.close()


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Fraud Detection Workflow Example")
    print("=" * 60)

    detector = FraudDetector()

    # Example 1: Transaction fraud detection
    print("\n📌 Example 1: Transaction Fraud Detection")
    print("-" * 40)

    transaction = {
        "transaction_id": "TXN123456",
        "amount": 5000,
        "timestamp": datetime.now().isoformat(),
        "customer": {
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1980-01-15",
            "ssn_last4": "1234",
            "phone": "5551234567",
            "email": "john.smith@tempmail.com",
            "address": "123 Main St",
            "city": "Los Angeles",
            "state": "CA",
        },
        "location": {"address": "456 Oak Ave", "city": "New York", "state": "NY"},
        "device": {"id": "device123", "using_vpn": True, "is_emulator": False},
    }

    # Historical transactions for pattern analysis
    historical = [
        {"amount": 100, "timestamp": (datetime.now() - timedelta(days=30)).isoformat()},
        {"amount": 150, "timestamp": (datetime.now() - timedelta(days=20)).isoformat()},
        {"amount": 200, "timestamp": (datetime.now() - timedelta(days=10)).isoformat()},
        {"amount": 180, "timestamp": (datetime.now() - timedelta(days=5)).isoformat()},
        {"amount": 220, "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()},
    ]

    try:
        transaction_result = await detector.analyze_transaction(
            transaction_data=transaction, historical_data=historical
        )

        print("\n✅ Transaction analysis complete!")

    except Exception as e:
        print(f"❌ Transaction analysis failed: {str(e)}")

    # Example 2: Identity fraud detection
    print("\n📌 Example 2: Identity Fraud Detection")
    print("-" * 40)

    # Reset detector for new case
    detector = FraudDetector()

    identity = {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-05-20",
        "ssn_last4": "5678",
        "address": "789 Pine St",
        "city": "Chicago",
        "state": "IL",
        "credit_history_years": 1,
        "address_count": 15,
        "recent_address_changes": 4,
        "recent_inquiries": 8,
    }

    try:
        identity_result = await detector.detect_identity_fraud(
            identity_data=identity,
            documents=[
                {"type": "drivers_license", "id": "DL123456"},
                {"type": "passport", "id": "P987654"},
            ],
        )

        print("\n✅ Identity fraud detection complete!")

    except Exception as e:
        print(f"❌ Identity fraud detection failed: {str(e)}")

    finally:
        await detector.close()

    # Example 3: Business fraud detection
    print("\n📌 Example 3: Business Fraud Detection")
    print("-" * 40)

    detector = FraudDetector()

    business = {
        "name": "Quick Cash LLC",
        "ein": "12-3456789",
        "address": "PO Box 123",
        "city": "Miami",
        "state": "FL",
        "formation_date": (datetime.now() - timedelta(days=30)).isoformat(),
        "employee_count": 0,
        "officers": [{"first_name": "Bob", "last_name": "Jones", "title": "CEO"}],
    }

    financial = {
        "transactions": [
            {"amount": 10000, "date": datetime.now().isoformat()},
            {"amount": 5000, "date": datetime.now().isoformat()},
            {"amount": 15000, "date": datetime.now().isoformat()},
        ],
        "deposits": [
            {"amount": 9500, "date": datetime.now().isoformat()},
            {"amount": 9900, "date": datetime.now().isoformat()},
            {"amount": 9700, "date": datetime.now().isoformat()},
        ],
    }

    try:
        business_result = await detector.detect_business_fraud(
            business_data=business, financial_data=financial
        )

        print("\n✅ Business fraud detection complete!")

    except Exception as e:
        print(f"❌ Business fraud detection failed: {str(e)}")

    finally:
        await detector.close()

    print("\n✨ All fraud detection examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
