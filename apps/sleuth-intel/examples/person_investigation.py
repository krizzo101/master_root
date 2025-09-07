#!/usr/bin/env python3
"""
Person Investigation Example
============================

This example demonstrates comprehensive person investigation
using multiple data sources and enrichment techniques.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python person_investigation.py
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    AddressSearchRequest,
    EmailVerificationRequest,
    PersonSearchRequest,
    PhoneLookupRequest,
)


class PersonInvestigator:
    """Comprehensive person investigation handler."""

    def __init__(self):
        self.client = SleuthIntel()
        self.investigation_data = {}

    async def investigate_person(
        self,
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        ssn_last4: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive person investigation.

        Args:
            first_name: Person's first name
            last_name: Person's last name
            middle_name: Optional middle name
            date_of_birth: Optional DOB (YYYY-MM-DD)
            ssn_last4: Optional last 4 digits of SSN
            address: Optional street address
            city: Optional city
            state: Optional state code
            zip_code: Optional ZIP code

        Returns:
            Dictionary with investigation results
        """
        print(f"🔍 Starting investigation for: {first_name} {last_name}")
        print("=" * 60)

        self.investigation_data = {
            "subject": {
                "first_name": first_name,
                "last_name": last_name,
                "middle_name": middle_name,
                "date_of_birth": date_of_birth,
                "ssn_last4": ssn_last4,
            },
            "timestamp": datetime.now().isoformat(),
            "results": {},
        }

        # Step 1: Basic person search
        await self._person_search(
            first_name, last_name, middle_name, city, state, zip_code
        )

        # Step 2: Address history
        if address or (city and state):
            await self._address_history(address, city, state, zip_code)

        # Step 3: Phone number associations
        await self._phone_associations()

        # Step 4: Email associations
        await self._email_associations()

        # Step 5: Social media presence
        await self._social_media_search()

        # Step 6: Public records
        await self._public_records_search()

        # Step 7: Risk assessment
        await self._risk_assessment()

        # Generate summary report
        self._generate_summary()

        return self.investigation_data

    async def _person_search(
        self,
        first_name: str,
        last_name: str,
        middle_name: Optional[str],
        city: Optional[str],
        state: Optional[str],
        zip_code: Optional[str],
    ):
        """Perform basic person search."""
        print("\n📋 Step 1: Person Search")
        print("-" * 40)

        try:
            request = PersonSearchRequest(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                city=city,
                state=state,
                zip_code=zip_code,
                include_relatives=True,
                include_associates=True,
                include_addresses=True,
                include_phones=True,
                include_emails=True,
            )

            response = await self.client.person_search(request)

            if response.success and response.results:
                print(f"  ✅ Found {len(response.results)} matching records")

                # Process top matches
                top_matches = response.results[:3]
                self.investigation_data["results"]["person_search"] = {
                    "total_matches": len(response.results),
                    "top_matches": [],
                }

                for match in top_matches:
                    match_data = {
                        "name": f"{match.get('first_name', '')} {match.get('last_name', '')}",
                        "age": match.get("age"),
                        "addresses": match.get("addresses", []),
                        "phones": match.get("phones", []),
                        "emails": match.get("emails", []),
                        "relatives": match.get("relatives", []),
                        "associates": match.get("associates", []),
                    }
                    self.investigation_data["results"]["person_search"][
                        "top_matches"
                    ].append(match_data)

                    print(f"    • {match_data['name']} (Age: {match_data['age']})")
                    print(f"      Addresses: {len(match_data['addresses'])}")
                    print(f"      Phones: {len(match_data['phones'])}")
                    print(f"      Relatives: {len(match_data['relatives'])}")
            else:
                print("  ⚠️ No matching records found")
                self.investigation_data["results"]["person_search"] = {
                    "total_matches": 0,
                    "message": "No matching records found",
                }

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.investigation_data["results"]["person_search"] = {"error": str(e)}

    async def _address_history(
        self,
        address: Optional[str],
        city: Optional[str],
        state: Optional[str],
        zip_code: Optional[str],
    ):
        """Get address history and associated information."""
        print("\n🏠 Step 2: Address History")
        print("-" * 40)

        try:
            if not (address or (city and state)):
                print("  ⚠️ Insufficient address information")
                return

            request = AddressSearchRequest(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                include_residents=True,
                include_neighbors=True,
                include_property_info=True,
            )

            response = await self.client.address_search(request)

            if response.success:
                self.investigation_data["results"]["address_history"] = {
                    "current_address": response.formatted_address,
                    "residents": response.residents,
                    "property_info": response.property_info,
                    "neighbors": response.neighbors[:5] if response.neighbors else [],
                }

                print(f"  ✅ Address verified: {response.formatted_address}")
                if response.residents:
                    print(f"    • Current residents: {len(response.residents)}")
                if response.neighbors:
                    print(f"    • Neighbors identified: {len(response.neighbors)}")
            else:
                print("  ⚠️ Address not found or incomplete data")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.investigation_data["results"]["address_history"] = {"error": str(e)}

    async def _phone_associations(self):
        """Find and verify phone associations."""
        print("\n📞 Step 3: Phone Associations")
        print("-" * 40)

        phones = []
        if "person_search" in self.investigation_data["results"]:
            for match in self.investigation_data["results"]["person_search"].get(
                "top_matches", []
            ):
                phones.extend(match.get("phones", []))

        if not phones:
            print("  ⚠️ No phone numbers found")
            return

        print(f"  📱 Found {len(phones)} phone numbers")

        verified_phones = []
        for phone in phones[:5]:  # Limit to 5 for example
            try:
                request = PhoneLookupRequest(phone=phone)
                response = await self.client.phone_lookup(request)

                if response.success:
                    phone_data = {
                        "number": phone,
                        "type": response.phone_type,
                        "carrier": response.carrier,
                        "valid": response.is_valid,
                        "owner": response.owner_info,
                    }
                    verified_phones.append(phone_data)
                    print(f"    ✅ {phone} - {response.phone_type} ({response.carrier})")

            except Exception as e:
                print(f"    ❌ {phone} - Error: {str(e)}")

            await asyncio.sleep(0.5)  # Rate limiting

        self.investigation_data["results"]["phone_associations"] = verified_phones

    async def _email_associations(self):
        """Find and verify email associations."""
        print("\n✉️ Step 4: Email Associations")
        print("-" * 40)

        emails = []
        if "person_search" in self.investigation_data["results"]:
            for match in self.investigation_data["results"]["person_search"].get(
                "top_matches", []
            ):
                emails.extend(match.get("emails", []))

        if not emails:
            print("  ⚠️ No email addresses found")
            return

        print(f"  📧 Found {len(emails)} email addresses")

        verified_emails = []
        for email in emails[:5]:  # Limit to 5 for example
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
                    }
                    verified_emails.append(email_data)
                    status = "✅" if response.is_valid else "❌"
                    print(
                        f"    {status} {email} - Deliverable: {response.is_deliverable}"
                    )

            except Exception as e:
                print(f"    ❌ {email} - Error: {str(e)}")

            await asyncio.sleep(0.5)  # Rate limiting

        self.investigation_data["results"]["email_associations"] = verified_emails

    async def _social_media_search(self):
        """Search for social media presence."""
        print("\n🌐 Step 5: Social Media Search")
        print("-" * 40)

        # This would integrate with social media APIs
        # For demonstration, we'll simulate the search

        social_profiles = {
            "facebook": None,
            "twitter": None,
            "linkedin": None,
            "instagram": None,
        }

        # Check if we have any verified emails to search with
        if "email_associations" in self.investigation_data["results"]:
            for email_data in self.investigation_data["results"]["email_associations"]:
                if email_data.get("social_profiles"):
                    for platform, profile in email_data["social_profiles"].items():
                        if profile:
                            social_profiles[platform] = profile

        active_profiles = [k for k, v in social_profiles.items() if v]
        if active_profiles:
            print(f"  ✅ Found profiles on: {', '.join(active_profiles)}")
        else:
            print("  ⚠️ No social media profiles found")

        self.investigation_data["results"]["social_media"] = social_profiles

    async def _public_records_search(self):
        """Search public records."""
        print("\n📑 Step 6: Public Records Search")
        print("-" * 40)

        # This would integrate with public records APIs
        # For demonstration, we'll indicate what types of records to check

        records_to_check = [
            "Court Records",
            "Property Records",
            "Business Registrations",
            "Professional Licenses",
            "Voter Registration",
        ]

        print("  🔍 Checking:")
        for record_type in records_to_check:
            print(f"    • {record_type}")

        # Simulated results
        self.investigation_data["results"]["public_records"] = {
            "court_records": [],
            "property_records": [],
            "business_registrations": [],
            "professional_licenses": [],
            "voter_registration": None,
        }

        print("  ✅ Public records check completed")

    async def _risk_assessment(self):
        """Perform risk assessment based on collected data."""
        print("\n⚠️ Step 7: Risk Assessment")
        print("-" * 40)

        risk_factors = []
        risk_score = 0

        # Check for multiple addresses
        if "person_search" in self.investigation_data["results"]:
            matches = self.investigation_data["results"]["person_search"].get(
                "top_matches", []
            )
            if matches:
                addresses = matches[0].get("addresses", [])
                if len(addresses) > 5:
                    risk_factors.append("High mobility (multiple addresses)")
                    risk_score += 10

        # Check for unverified phones
        if "phone_associations" in self.investigation_data["results"]:
            phones = self.investigation_data["results"]["phone_associations"]
            invalid_phones = [p for p in phones if not p.get("valid", True)]
            if invalid_phones:
                risk_factors.append(f"Invalid phone numbers ({len(invalid_phones)})")
                risk_score += 15

        # Check for undeliverable emails
        if "email_associations" in self.investigation_data["results"]:
            emails = self.investigation_data["results"]["email_associations"]
            undeliverable = [e for e in emails if not e.get("deliverable", True)]
            if undeliverable:
                risk_factors.append(f"Undeliverable emails ({len(undeliverable)})")
                risk_score += 10

        # Determine risk level
        if risk_score == 0:
            risk_level = "LOW"
        elif risk_score <= 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        self.investigation_data["results"]["risk_assessment"] = {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
        }

        print(f"  📊 Risk Level: {risk_level} (Score: {risk_score})")
        if risk_factors:
            print("  Risk Factors:")
            for factor in risk_factors:
                print(f"    • {factor}")

    def _generate_summary(self):
        """Generate investigation summary."""
        print("\n📄 Investigation Summary")
        print("=" * 60)

        summary = {
            "investigation_complete": True,
            "timestamp": self.investigation_data["timestamp"],
            "subject": self.investigation_data["subject"],
            "key_findings": {},
        }

        # Extract key findings
        results = self.investigation_data["results"]

        if "person_search" in results and results["person_search"].get("top_matches"):
            top_match = results["person_search"]["top_matches"][0]
            summary["key_findings"]["primary_match"] = {
                "name": top_match["name"],
                "age": top_match["age"],
                "address_count": len(top_match.get("addresses", [])),
                "phone_count": len(top_match.get("phones", [])),
                "relative_count": len(top_match.get("relatives", [])),
            }

        if "risk_assessment" in results:
            summary["key_findings"]["risk"] = results["risk_assessment"]["risk_level"]

        self.investigation_data["summary"] = summary

        print(f"  ✅ Investigation completed at {summary['timestamp']}")
        print(f"  📊 Risk Level: {summary['key_findings'].get('risk', 'N/A')}")

        # Save full report
        report_file = f"investigation_{self.investigation_data['subject']['last_name']}_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(report_file, "w") as f:
            json.dump(self.investigation_data, f, indent=2)
        print(f"  💾 Full report saved to: {report_file}")

    async def close(self):
        """Clean up resources."""
        await self.client.close()


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Person Investigation Example")
    print("=" * 60)

    investigator = PersonInvestigator()

    try:
        # Example investigation
        results = await investigator.investigate_person(
            first_name="John", last_name="Smith", city="Los Angeles", state="CA"
        )

        print("\n✨ Investigation completed successfully!")

    except Exception as e:
        print(f"\n❌ Investigation failed: {str(e)}")

    finally:
        await investigator.close()


if __name__ == "__main__":
    asyncio.run(main())
