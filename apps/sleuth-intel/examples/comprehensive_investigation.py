#!/usr/bin/env python3
"""
Comprehensive Investigation Example
===================================

This example demonstrates a full-scale investigation workflow
combining multiple data sources and analysis techniques.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python comprehensive_investigation.py
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    AddressSearchRequest,
    BusinessSearchRequest,
    EmailVerificationRequest,
    PersonSearchRequest,
    PhoneLookupRequest,
    PublicRecordsRequest,
    SocialMediaSearchRequest,
)


class InvestigationType(Enum):
    """Types of investigations."""

    BACKGROUND_CHECK = "background_check"
    FRAUD_INVESTIGATION = "fraud_investigation"
    DUE_DILIGENCE = "due_diligence"
    SKIP_TRACE = "skip_trace"
    ASSET_SEARCH = "asset_search"


class ComprehensiveInvestigator:
    """Full-scale investigation orchestrator."""

    def __init__(self):
        self.client = SleuthIntel()
        self.investigation_id = None
        self.investigation_data = {}
        self.evidence_chain = []
        self.risk_score = 0
        self.confidence_level = 0

    async def conduct_investigation(
        self,
        investigation_type: InvestigationType,
        subject_info: Dict[str, Any],
        depth_level: int = 3,
        include_associates: bool = True,
        include_businesses: bool = True,
        include_assets: bool = True,
    ) -> Dict[str, Any]:
        """
        Conduct a comprehensive investigation.

        Args:
            investigation_type: Type of investigation
            subject_info: Subject identification information
            depth_level: Investigation depth (1-5, higher = more thorough)
            include_associates: Include associate investigations
            include_businesses: Include business connections
            include_assets: Include asset searches

        Returns:
            Complete investigation report
        """
        # Generate investigation ID
        self.investigation_id = self._generate_investigation_id(subject_info)

        print(f"\n🔍 COMPREHENSIVE INVESTIGATION")
        print(f"Investigation ID: {self.investigation_id}")
        print(f"Type: {investigation_type.value}")
        print(f"Depth Level: {depth_level}/5")
        print("=" * 70)

        # Initialize investigation structure
        self.investigation_data = {
            "investigation_id": self.investigation_id,
            "type": investigation_type.value,
            "started_at": datetime.now().isoformat(),
            "subject": subject_info,
            "depth_level": depth_level,
            "phases": {},
            "findings": {},
            "risk_assessment": {},
            "recommendations": [],
            "evidence_chain": [],
        }

        # Phase 1: Identity Verification
        await self._phase_identity_verification(subject_info)

        # Phase 2: Contact Information Gathering
        await self._phase_contact_gathering()

        # Phase 3: Address and Location History
        await self._phase_location_history()

        # Phase 4: Associates and Relationships
        if include_associates and depth_level >= 2:
            await self._phase_associates_analysis()

        # Phase 5: Business Connections
        if include_businesses and depth_level >= 3:
            await self._phase_business_connections()

        # Phase 6: Asset Discovery
        if include_assets and depth_level >= 4:
            await self._phase_asset_discovery()

        # Phase 7: Public Records Deep Dive
        if depth_level >= 3:
            await self._phase_public_records()

        # Phase 8: Social Media and Online Presence
        if depth_level >= 2:
            await self._phase_online_presence()

        # Phase 9: Risk Assessment
        await self._phase_risk_assessment()

        # Phase 10: Generate Final Report
        await self._generate_final_report()

        return self.investigation_data

    def _generate_investigation_id(self, subject_info: Dict) -> str:
        """Generate unique investigation ID."""
        data = f"{subject_info}{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12].upper()

    async def _phase_identity_verification(self, subject_info: Dict):
        """Phase 1: Verify and establish subject identity."""
        print("\n📋 PHASE 1: Identity Verification")
        print("-" * 50)

        phase_data = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "primary_identity": None,
            "alternate_identities": [],
            "verification_confidence": 0,
        }

        try:
            # Search for primary identity
            request = PersonSearchRequest(
                first_name=subject_info.get("first_name"),
                last_name=subject_info.get("last_name"),
                middle_name=subject_info.get("middle_name"),
                date_of_birth=subject_info.get("date_of_birth"),
                ssn_last4=subject_info.get("ssn_last4"),
                city=subject_info.get("city"),
                state=subject_info.get("state"),
                include_aka=True,
                include_relatives=True,
            )

            response = await self.client.person_search(request)

            if response.success and response.results:
                print(f"  ✅ Found {len(response.results)} potential matches")

                # Analyze matches and determine primary identity
                best_match = response.results[0]
                phase_data["primary_identity"] = {
                    "full_name": f"{best_match.get('first_name', '')} {best_match.get('middle_name', '')} {best_match.get('last_name', '')}".strip(),
                    "age": best_match.get("age"),
                    "date_of_birth": best_match.get("date_of_birth"),
                    "ssn_last4": best_match.get("ssn_last4"),
                    "aka_names": best_match.get("aka_names", []),
                    "confidence_score": best_match.get("match_confidence", 0),
                }

                # Store alternate identities
                for match in response.results[1:5]:
                    phase_data["alternate_identities"].append(
                        {
                            "name": f"{match.get('first_name', '')} {match.get('last_name', '')}",
                            "confidence": match.get("match_confidence", 0),
                        }
                    )

                phase_data["verification_confidence"] = best_match.get(
                    "match_confidence", 0
                )
                self.confidence_level = phase_data["verification_confidence"]

                # Add to evidence chain
                self._add_evidence(
                    "identity_verification",
                    "Primary identity established",
                    phase_data["primary_identity"],
                )

                print(
                    f"  👤 Primary Identity: {phase_data['primary_identity']['full_name']}"
                )
                print(f"  📊 Confidence: {phase_data['verification_confidence']}%")
            else:
                print("  ⚠️ No identity matches found")
                phase_data["status"] = "incomplete"

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            phase_data["status"] = "error"
            phase_data["error"] = str(e)

        phase_data["completed_at"] = datetime.now().isoformat()
        phase_data["status"] = (
            "completed" if phase_data.get("primary_identity") else "incomplete"
        )
        self.investigation_data["phases"]["identity_verification"] = phase_data

    async def _phase_contact_gathering(self):
        """Phase 2: Gather all contact information."""
        print("\n📞 PHASE 2: Contact Information Gathering")
        print("-" * 50)

        phase_data = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "phone_numbers": [],
            "email_addresses": [],
            "verified_contacts": 0,
        }

        if (
            not self.investigation_data["phases"]
            .get("identity_verification", {})
            .get("primary_identity")
        ):
            print("  ⚠️ Skipping - no primary identity established")
            phase_data["status"] = "skipped"
            self.investigation_data["phases"]["contact_gathering"] = phase_data
            return

        try:
            # Get contact info from identity phase
            identity = self.investigation_data["phases"]["identity_verification"][
                "primary_identity"
            ]

            # Verify phone numbers
            print("  📱 Verifying phone numbers...")
            phones = identity.get("phones", [])
            for phone in phones[:10]:
                try:
                    request = PhoneLookupRequest(phone=phone)
                    response = await self.client.phone_lookup(request)

                    if response.success:
                        phone_data = {
                            "number": phone,
                            "type": response.phone_type,
                            "carrier": response.carrier,
                            "valid": response.is_valid,
                            "current": response.is_current,
                            "verified": True,
                        }
                        phase_data["phone_numbers"].append(phone_data)

                        if response.is_valid:
                            phase_data["verified_contacts"] += 1
                            print(f"    ✅ {phone} - {response.phone_type}")

                except Exception as e:
                    print(f"    ❌ {phone} - Error: {str(e)}")

                await asyncio.sleep(0.3)

            # Verify email addresses
            print("  ✉️ Verifying email addresses...")
            emails = identity.get("emails", [])
            for email in emails[:10]:
                try:
                    request = EmailVerificationRequest(email=email)
                    response = await self.client.email_verification(request)

                    if response.success:
                        email_data = {
                            "email": email,
                            "valid": response.is_valid,
                            "deliverable": response.is_deliverable,
                            "domain": response.domain,
                            "social_profiles": response.social_profiles,
                            "verified": True,
                        }
                        phase_data["email_addresses"].append(email_data)

                        if response.is_valid:
                            phase_data["verified_contacts"] += 1
                            print(f"    ✅ {email} - Valid")

                except Exception as e:
                    print(f"    ❌ {email} - Error: {str(e)}")

                await asyncio.sleep(0.3)

            print(f"\n  📊 Verified Contacts: {phase_data['verified_contacts']}")

            # Add to evidence chain
            self._add_evidence(
                "contact_verification",
                f"Verified {phase_data['verified_contacts']} contact methods",
                {
                    "phones": len(phase_data["phone_numbers"]),
                    "emails": len(phase_data["email_addresses"]),
                },
            )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            phase_data["status"] = "error"
            phase_data["error"] = str(e)

        phase_data["completed_at"] = datetime.now().isoformat()
        phase_data["status"] = "completed"
        self.investigation_data["phases"]["contact_gathering"] = phase_data

    async def _phase_location_history(self):
        """Phase 3: Analyze address and location history."""
        print("\n🏠 PHASE 3: Location History Analysis")
        print("-" * 50)

        phase_data = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "current_address": None,
            "previous_addresses": [],
            "location_timeline": [],
            "stability_score": 0,
        }

        try:
            # Get addresses from identity
            identity = (
                self.investigation_data["phases"]
                .get("identity_verification", {})
                .get("primary_identity", {})
            )
            addresses = identity.get("addresses", [])

            print(f"  📍 Found {len(addresses)} addresses")

            for i, address in enumerate(addresses[:10]):
                try:
                    request = AddressSearchRequest(
                        address=address.get("street"),
                        city=address.get("city"),
                        state=address.get("state"),
                        zip_code=address.get("zip"),
                        include_property_info=True,
                        include_residents=True,
                    )

                    response = await self.client.address_search(request)

                    if response.success:
                        addr_data = {
                            "address": response.formatted_address,
                            "type": response.property_type,
                            "current": i == 0,
                            "dates": address.get("date_range", "Unknown"),
                            "property_value": response.property_info.get(
                                "assessed_value"
                            )
                            if response.property_info
                            else None,
                            "verified": True,
                        }

                        if i == 0:
                            phase_data["current_address"] = addr_data
                            print(f"    ✅ Current: {response.formatted_address}")
                        else:
                            phase_data["previous_addresses"].append(addr_data)
                            print(f"    📍 Previous: {response.formatted_address}")

                except Exception as e:
                    print(f"    ❌ Address verification error: {str(e)}")

                await asyncio.sleep(0.5)

            # Calculate stability score
            if addresses:
                years_at_current = 2  # Placeholder
                move_frequency = len(addresses) / 10  # Moves per decade
                phase_data["stability_score"] = min(
                    100, int(years_at_current * 20 / (move_frequency + 1))
                )

                print(f"\n  📊 Stability Score: {phase_data['stability_score']}/100")

            # Add to evidence chain
            self._add_evidence(
                "location_history",
                f"Verified {len(addresses)} addresses",
                {
                    "current": phase_data["current_address"],
                    "stability_score": phase_data["stability_score"],
                },
            )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            phase_data["status"] = "error"
            phase_data["error"] = str(e)

        phase_data["completed_at"] = datetime.now().isoformat()
        phase_data["status"] = "completed"
        self.investigation_data["phases"]["location_history"] = phase_data

    async def _phase_associates_analysis(self):
        """Phase 4: Analyze associates and relationships."""
        print("\n👥 PHASE 4: Associates & Relationships")
        print("-" * 50)

        phase_data = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "relatives": [],
            "associates": [],
            "network_size": 0,
            "key_relationships": [],
        }

        try:
            identity = (
                self.investigation_data["phases"]
                .get("identity_verification", {})
                .get("primary_identity", {})
            )

            # Process relatives
            relatives = identity.get("relatives", [])
            print(f"  👨‍👩‍👧‍👦 Found {len(relatives)} relatives")

            for relative in relatives[:20]:
                rel_data = {
                    "name": relative.get("name"),
                    "relationship": relative.get("relationship"),
                    "age": relative.get("age"),
                    "location": relative.get("location"),
                }
                phase_data["relatives"].append(rel_data)

                # Flag key relationships
                if relative.get("relationship") in ["spouse", "parent", "child"]:
                    phase_data["key_relationships"].append(rel_data)

            # Process associates
            associates = identity.get("associates", [])
            print(f"  🤝 Found {len(associates)} associates")

            for associate in associates[:20]:
                assoc_data = {
                    "name": associate.get("name"),
                    "connection_type": associate.get("connection_type"),
                    "shared_addresses": associate.get("shared_addresses", []),
                    "duration": associate.get("association_duration"),
                }
                phase_data["associates"].append(assoc_data)

            phase_data["network_size"] = len(relatives) + len(associates)
            print(f"\n  📊 Total Network Size: {phase_data['network_size']} connections")

            # Add to evidence chain
            self._add_evidence(
                "associates_analysis",
                f"Identified {phase_data['network_size']} connections",
                {
                    "relatives": len(phase_data["relatives"]),
                    "associates": len(phase_data["associates"]),
                    "key_relationships": len(phase_data["key_relationships"]),
                },
            )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            phase_data["status"] = "error"
            phase_data["error"] = str(e)

        phase_data["completed_at"] = datetime.now().isoformat()
        phase_data["status"] = "completed"
        self.investigation_data["phases"]["associates_analysis"] = phase_data

    async def _phase_business_connections(self):
        """Phase 5: Investigate business connections."""
        print("\n🏢 PHASE 5: Business Connections")
        print("-" * 50)

        phase_data = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "businesses": [],
            "employment_history": [],
            "business_roles": [],
        }

        try:
            identity = (
                self.investigation_data["phases"]
                .get("identity_verification", {})
                .get("primary_identity", {})
            )
            full_name = identity.get("full_name", "")

            # Search for business affiliations
            request = BusinessSearchRequest(
                officer_name=full_name, include_inactive=True
            )

            response = await self.client.business_search(request)

            if response.success and response.results:
                print(f"  🏢 Found {len(response.results)} business connections")

                for business in response.results[:10]:
                    biz_data = {
                        "name": business.get("business_name"),
                        "type": business.get("entity_type"),
                        "status": business.get("status"),
                        "role": business.get("officer_role"),
                        "state": business.get("state"),
                        "formation_date": business.get("formation_date"),
                    }
                    phase_data["businesses"].append(biz_data)

                    print(f"    • {biz_data['name']} - {biz_data['role']}")

                # Add to evidence chain
                self._add_evidence(
                    "business_connections",
                    f"Found {len(phase_data['businesses'])} business affiliations",
                    phase_data["businesses"],
                )
            else:
                print("  ℹ️ No business connections found")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            phase_data["status"] = "error"
            phase_data["error"] = str(e)

        phase_data["completed_at"] = datetime.now().isoformat()
        phase_data["status"] = "completed"
        self.investigation_data["phases"]["business_connections"] = phase_data

    async def _phase_asset_discovery(self):
        """Phase 6: Discover and analyze assets."""
        print("\n💰 PHASE 6: Asset Discovery")
        print("-" * 50)

        phase_data = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "real_estate": [],
            "vehicles": [],
            "watercraft": [],
            "aircraft": [],
            "estimated_net_worth": None,
        }

        try:
            # Real estate assets from address history
            location_history = self.investigation_data["phases"].get(
                "location_history", {}
            )
            current_address = location_history.get("current_address")

            if current_address and current_address.get("property_value"):
                phase_data["real_estate"].append(
                    {
                        "address": current_address["address"],
                        "type": "Primary Residence",
                        "estimated_value": current_address["property_value"],
                        "owned": True,  # Assumption for demo
                    }
                )
                print(f"  🏠 Real Estate: ${current_address['property_value']:,.0f}")

            # Vehicle assets (would integrate with DMV data)
            print("  🚗 Searching for vehicle registrations...")
            # Simulated vehicle data
            phase_data["vehicles"] = []

            # Calculate estimated net worth
            total_assets = sum(
                prop.get("estimated_value", 0) for prop in phase_data["real_estate"]
            )
            phase_data["estimated_net_worth"] = total_assets

            if total_assets > 0:
                print(f"\n  💵 Estimated Assets: ${total_assets:,.0f}")

            # Add to evidence chain
            self._add_evidence(
                "asset_discovery",
                f"Identified assets worth ${total_assets:,.0f}",
                {
                    "real_estate": len(phase_data["real_estate"]),
                    "vehicles": len(phase_data["vehicles"]),
                },
            )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            phase_data["status"] = "error"
            phase_data["error"] = str(e)

        phase_data["completed_at"] = datetime.now().isoformat()
        phase_data["status"] = "completed"
        self.investigation_data["phases"]["asset_discovery"] = phase_data

    async def _phase_public_records(self):
        """Phase 7: Deep dive into public records."""
        print("\n📑 PHASE 7: Public Records Analysis")
        print("-" * 50)

        phase_data = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "court_records": [],
            "liens": [],
            "judgments": [],
            "bankruptcies": [],
            "criminal_records": [],
            "professional_licenses": [],
        }

        try:
            identity = (
                self.investigation_data["phases"]
                .get("identity_verification", {})
                .get("primary_identity", {})
            )

            # Search public records
            request = PublicRecordsRequest(
                first_name=identity.get("full_name", "").split()[0]
                if identity.get("full_name")
                else None,
                last_name=identity.get("full_name", "").split()[-1]
                if identity.get("full_name")
                else None,
                include_criminal=True,
                include_civil=True,
                include_bankruptcy=True,
                include_liens=True,
                include_licenses=True,
            )

            response = await self.client.public_records_search(request)

            if response.success:
                # Process criminal records
                if response.criminal_records:
                    print(
                        f"  ⚖️ Found {len(response.criminal_records)} criminal records"
                    )
                    phase_data["criminal_records"] = response.criminal_records
                    self.risk_score += len(response.criminal_records) * 10

                # Process civil records
                if response.civil_records:
                    print(f"  📋 Found {len(response.civil_records)} civil records")
                    phase_data["court_records"] = response.civil_records

                # Process bankruptcies
                if response.bankruptcies:
                    print(f"  💸 Found {len(response.bankruptcies)} bankruptcy records")
                    phase_data["bankruptcies"] = response.bankruptcies
                    self.risk_score += len(response.bankruptcies) * 15

                # Process liens
                if response.liens:
                    print(f"  🔗 Found {len(response.liens)} liens")
                    phase_data["liens"] = response.liens
                    self.risk_score += len(response.liens) * 5

                # Process professional licenses
                if response.professional_licenses:
                    print(
                        f"  📜 Found {len(response.professional_licenses)} professional licenses"
                    )
                    phase_data["professional_licenses"] = response.professional_licenses

                # Add to evidence chain
                total_records = (
                    len(phase_data["criminal_records"])
                    + len(phase_data["court_records"])
                    + len(phase_data["bankruptcies"])
                    + len(phase_data["liens"])
                )

                self._add_evidence(
                    "public_records",
                    f"Found {total_records} public records",
                    {
                        "criminal": len(phase_data["criminal_records"]),
                        "civil": len(phase_data["court_records"]),
                        "bankruptcy": len(phase_data["bankruptcies"]),
                        "liens": len(phase_data["liens"]),
                    },
                )
            else:
                print("  ℹ️ No public records found")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            phase_data["status"] = "error"
            phase_data["error"] = str(e)

        phase_data["completed_at"] = datetime.now().isoformat()
        phase_data["status"] = "completed"
        self.investigation_data["phases"]["public_records"] = phase_data

    async def _phase_online_presence(self):
        """Phase 8: Analyze online and social media presence."""
        print("\n🌐 PHASE 8: Online Presence Analysis")
        print("-" * 50)

        phase_data = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "social_profiles": {},
            "web_mentions": [],
            "digital_footprint_score": 0,
        }

        try:
            # Check emails for social profiles
            contact_data = self.investigation_data["phases"].get(
                "contact_gathering", {}
            )
            emails = contact_data.get("email_addresses", [])

            social_platforms = set()
            for email_data in emails:
                if email_data.get("social_profiles"):
                    for platform, profile in email_data["social_profiles"].items():
                        if profile:
                            phase_data["social_profiles"][platform] = profile
                            social_platforms.add(platform)

            print(f"  📱 Found profiles on {len(social_platforms)} platforms")
            for platform in social_platforms:
                print(f"    • {platform}")

            # Calculate digital footprint score
            phase_data["digital_footprint_score"] = min(100, len(social_platforms) * 15)

            print(
                f"\n  📊 Digital Footprint Score: {phase_data['digital_footprint_score']}/100"
            )

            # Add to evidence chain
            self._add_evidence(
                "online_presence",
                f"Found {len(social_platforms)} social media profiles",
                list(social_platforms),
            )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            phase_data["status"] = "error"
            phase_data["error"] = str(e)

        phase_data["completed_at"] = datetime.now().isoformat()
        phase_data["status"] = "completed"
        self.investigation_data["phases"]["online_presence"] = phase_data

    async def _phase_risk_assessment(self):
        """Phase 9: Comprehensive risk assessment."""
        print("\n⚠️ PHASE 9: Risk Assessment")
        print("-" * 50)

        assessment = {
            "overall_risk_score": 0,
            "risk_level": "LOW",
            "risk_factors": [],
            "positive_indicators": [],
            "recommendations": [],
        }

        try:
            # Analyze all phases for risk factors
            phases = self.investigation_data["phases"]

            # Identity verification risks
            if (
                phases.get("identity_verification", {}).get(
                    "verification_confidence", 0
                )
                < 70
            ):
                assessment["risk_factors"].append(
                    "Low identity verification confidence"
                )
                self.risk_score += 10
            else:
                assessment["positive_indicators"].append("Strong identity verification")

            # Contact verification
            contact_phase = phases.get("contact_gathering", {})
            if contact_phase.get("verified_contacts", 0) < 2:
                assessment["risk_factors"].append(
                    "Limited verified contact information"
                )
                self.risk_score += 5

            # Location stability
            location_phase = phases.get("location_history", {})
            if location_phase.get("stability_score", 0) < 30:
                assessment["risk_factors"].append("High residential mobility")
                self.risk_score += 10
            elif location_phase.get("stability_score", 0) > 70:
                assessment["positive_indicators"].append("Stable residential history")

            # Public records
            public_records = phases.get("public_records", {})
            if public_records.get("criminal_records"):
                assessment["risk_factors"].append(
                    f"{len(public_records['criminal_records'])} criminal records found"
                )
            if public_records.get("bankruptcies"):
                assessment["risk_factors"].append(
                    f"{len(public_records['bankruptcies'])} bankruptcy records"
                )
            if public_records.get("professional_licenses"):
                assessment["positive_indicators"].append(
                    "Professional licenses on file"
                )

            # Business connections
            business_phase = phases.get("business_connections", {})
            if business_phase.get("businesses"):
                assessment["positive_indicators"].append(
                    f"{len(business_phase['businesses'])} business affiliations"
                )

            # Calculate final risk score
            assessment["overall_risk_score"] = min(100, self.risk_score)

            # Determine risk level
            if assessment["overall_risk_score"] < 20:
                assessment["risk_level"] = "LOW"
            elif assessment["overall_risk_score"] < 50:
                assessment["risk_level"] = "MODERATE"
            elif assessment["overall_risk_score"] < 75:
                assessment["risk_level"] = "HIGH"
            else:
                assessment["risk_level"] = "VERY HIGH"

            # Generate recommendations
            if assessment["risk_level"] in ["HIGH", "VERY HIGH"]:
                assessment["recommendations"].append(
                    "Additional verification recommended"
                )
                assessment["recommendations"].append("Request additional documentation")
                assessment["recommendations"].append("Consider enhanced due diligence")
            elif assessment["risk_level"] == "MODERATE":
                assessment["recommendations"].append(
                    "Standard verification procedures sufficient"
                )
                assessment["recommendations"].append("Monitor for changes")
            else:
                assessment["recommendations"].append(
                    "Low risk - standard procedures apply"
                )

            print(f"  📊 Overall Risk Score: {assessment['overall_risk_score']}/100")
            print(f"  ⚠️ Risk Level: {assessment['risk_level']}")
            print(f"\n  Risk Factors ({len(assessment['risk_factors'])}):")
            for factor in assessment["risk_factors"][:5]:
                print(f"    ❌ {factor}")
            print(
                f"\n  Positive Indicators ({len(assessment['positive_indicators'])}):"
            )
            for indicator in assessment["positive_indicators"][:5]:
                print(f"    ✅ {indicator}")

            self.investigation_data["risk_assessment"] = assessment

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            assessment["error"] = str(e)

        self.investigation_data["risk_assessment"] = assessment

    async def _generate_final_report(self):
        """Generate comprehensive final report."""
        print("\n📄 FINAL REPORT GENERATION")
        print("=" * 70)

        # Complete investigation data
        self.investigation_data["completed_at"] = datetime.now().isoformat()

        # Calculate investigation duration
        start_time = datetime.fromisoformat(self.investigation_data["started_at"])
        end_time = datetime.now()
        duration = end_time - start_time

        self.investigation_data["duration"] = str(duration)
        self.investigation_data["evidence_chain"] = self.evidence_chain

        # Generate executive summary
        executive_summary = {
            "investigation_id": self.investigation_id,
            "subject": self.investigation_data["subject"],
            "investigation_type": self.investigation_data["type"],
            "risk_level": self.investigation_data["risk_assessment"]["risk_level"],
            "confidence_level": f"{self.confidence_level}%",
            "phases_completed": len(
                [
                    p
                    for p in self.investigation_data["phases"].values()
                    if p.get("status") == "completed"
                ]
            ),
            "total_phases": len(self.investigation_data["phases"]),
            "key_findings": [],
        }

        # Extract key findings
        if (
            self.investigation_data["phases"]
            .get("identity_verification", {})
            .get("primary_identity")
        ):
            executive_summary["key_findings"].append("Identity verified")

        if (
            self.investigation_data["phases"]
            .get("public_records", {})
            .get("criminal_records")
        ):
            executive_summary["key_findings"].append("Criminal records found")

        if (
            self.investigation_data["phases"]
            .get("asset_discovery", {})
            .get("estimated_net_worth")
        ):
            net_worth = self.investigation_data["phases"]["asset_discovery"][
                "estimated_net_worth"
            ]
            executive_summary["key_findings"].append(
                f"Estimated assets: ${net_worth:,.0f}"
            )

        self.investigation_data["executive_summary"] = executive_summary

        # Save report
        report_file = (
            f"investigation_{self.investigation_id}_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        with open(report_file, "w") as f:
            json.dump(self.investigation_data, f, indent=2)

        print(f"  ✅ Investigation Complete")
        print(f"  📊 Risk Level: {executive_summary['risk_level']}")
        print(f"  🎯 Confidence: {executive_summary['confidence_level']}")
        print(f"  ⏱️ Duration: {duration}")
        print(f"  📁 Report saved to: {report_file}")

        # Generate summary for display
        print("\n" + "=" * 70)
        print("INVESTIGATION SUMMARY")
        print("=" * 70)
        print(f"ID: {self.investigation_id}")
        print(f"Type: {self.investigation_data['type']}")
        print(
            f"Subject: {self.investigation_data['subject'].get('first_name')} {self.investigation_data['subject'].get('last_name')}"
        )
        print(f"Risk Assessment: {executive_summary['risk_level']}")
        print(
            f"Phases Completed: {executive_summary['phases_completed']}/{executive_summary['total_phases']}"
        )
        print("\nKey Findings:")
        for finding in executive_summary["key_findings"]:
            print(f"  • {finding}")
        print("\nRecommendations:")
        for rec in self.investigation_data["risk_assessment"]["recommendations"]:
            print(f"  • {rec}")

    def _add_evidence(self, evidence_type: str, description: str, data: Any):
        """Add evidence to the chain of evidence."""
        evidence = {
            "timestamp": datetime.now().isoformat(),
            "type": evidence_type,
            "description": description,
            "data": data,
            "hash": hashlib.sha256(str(data).encode()).hexdigest()[:16],
        }
        self.evidence_chain.append(evidence)

    async def close(self):
        """Clean up resources."""
        await self.client.close()


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Comprehensive Investigation Example")
    print("=" * 70)

    investigator = ComprehensiveInvestigator()

    try:
        # Example: Due diligence investigation
        subject_info = {
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1980-01-15",
            "city": "Los Angeles",
            "state": "CA",
        }

        results = await investigator.conduct_investigation(
            investigation_type=InvestigationType.DUE_DILIGENCE,
            subject_info=subject_info,
            depth_level=3,
            include_associates=True,
            include_businesses=True,
            include_assets=True,
        )

        print("\n✨ Investigation completed successfully!")

    except Exception as e:
        print(f"\n❌ Investigation failed: {str(e)}")

    finally:
        await investigator.close()


if __name__ == "__main__":
    asyncio.run(main())
