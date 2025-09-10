#!/usr/bin/env python3
"""
Business Research Example
=========================

This example demonstrates business research and verification
capabilities using the sleuth-intel library.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python business_research.py
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    AddressSearchRequest,
    BusinessSearchRequest,
    PersonSearchRequest,
    PhoneLookupRequest,
)


class BusinessResearcher:
    """Comprehensive business research handler."""

    def __init__(self):
        self.client = SleuthIntel()
        self.research_data = {}

    async def research_business(
        self,
        business_name: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        ein: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive business research.

        Args:
            business_name: Name of the business
            address: Optional street address
            city: Optional city
            state: Optional state code
            zip_code: Optional ZIP code
            ein: Optional Employer Identification Number
            phone: Optional business phone number

        Returns:
            Dictionary with research results
        """
        print(f"🏢 Starting research for: {business_name}")
        print("=" * 60)

        self.research_data = {
            "business": {
                "name": business_name,
                "address": address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "ein": ein,
                "phone": phone,
            },
            "timestamp": datetime.now().isoformat(),
            "results": {},
        }

        # Step 1: Business entity search
        await self._business_search(business_name, city, state, zip_code)

        # Step 2: Address verification
        if address or (city and state):
            await self._verify_business_address(address, city, state, zip_code)

        # Step 3: Phone verification
        if phone:
            await self._verify_business_phone(phone)

        # Step 4: Find key personnel
        await self._find_key_personnel()

        # Step 5: Check business registrations
        await self._check_registrations()

        # Step 6: Financial indicators
        await self._analyze_financial_indicators()

        # Step 7: Online presence analysis
        await self._analyze_online_presence()

        # Step 8: Risk and compliance check
        await self._compliance_check()

        # Generate research report
        self._generate_report()

        return self.research_data

    async def _business_search(
        self,
        business_name: str,
        city: Optional[str],
        state: Optional[str],
        zip_code: Optional[str],
    ):
        """Search for business entities."""
        print("\n📋 Step 1: Business Entity Search")
        print("-" * 40)

        try:
            request = BusinessSearchRequest(
                business_name=business_name,
                city=city,
                state=state,
                zip_code=zip_code,
                include_officers=True,
                include_filings=True,
                include_dba=True,
            )

            response = await self.client.business_search(request)

            if response.success and response.results:
                print(f"  ✅ Found {len(response.results)} matching businesses")

                # Process matches
                self.research_data["results"]["business_search"] = {
                    "total_matches": len(response.results),
                    "matches": [],
                }

                for match in response.results[:5]:  # Top 5 matches
                    business_data = {
                        "name": match.get("business_name"),
                        "type": match.get("entity_type"),
                        "status": match.get("status"),
                        "formation_date": match.get("formation_date"),
                        "address": match.get("address"),
                        "officers": match.get("officers", []),
                        "dbas": match.get("dba_names", []),
                        "ein": match.get("ein"),
                        "state_id": match.get("state_id"),
                    }
                    self.research_data["results"]["business_search"]["matches"].append(
                        business_data
                    )

                    print(f"    • {business_data['name']}")
                    print(f"      Type: {business_data['type']}")
                    print(f"      Status: {business_data['status']}")
                    print(f"      Formed: {business_data['formation_date']}")
            else:
                print("  ⚠️ No matching businesses found")
                self.research_data["results"]["business_search"] = {
                    "total_matches": 0,
                    "message": "No matching businesses found",
                }

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.research_data["results"]["business_search"] = {"error": str(e)}

    async def _verify_business_address(
        self,
        address: Optional[str],
        city: Optional[str],
        state: Optional[str],
        zip_code: Optional[str],
    ):
        """Verify business address and get property information."""
        print("\n🏠 Step 2: Address Verification")
        print("-" * 40)

        try:
            request = AddressSearchRequest(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                include_property_info=True,
                include_neighbors=True,
            )

            response = await self.client.address_search(request)

            if response.success:
                self.research_data["results"]["address_verification"] = {
                    "verified": True,
                    "formatted_address": response.formatted_address,
                    "property_type": response.property_info.get("property_type"),
                    "property_value": response.property_info.get("assessed_value"),
                    "owner": response.property_info.get("owner_name"),
                    "year_built": response.property_info.get("year_built"),
                    "square_footage": response.property_info.get("square_footage"),
                }

                print(f"  ✅ Address verified: {response.formatted_address}")
                print(
                    f"    • Property Type: {response.property_info.get('property_type', 'N/A')}"
                )
                print(f"    • Owner: {response.property_info.get('owner_name', 'N/A')}")
            else:
                print("  ⚠️ Address verification failed")
                self.research_data["results"]["address_verification"] = {
                    "verified": False,
                    "message": "Address could not be verified",
                }

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.research_data["results"]["address_verification"] = {"error": str(e)}

    async def _verify_business_phone(self, phone: str):
        """Verify business phone number."""
        print("\n📞 Step 3: Phone Verification")
        print("-" * 40)

        try:
            request = PhoneLookupRequest(
                phone=phone, include_carrier=True, include_owner=True
            )

            response = await self.client.phone_lookup(request)

            if response.success:
                self.research_data["results"]["phone_verification"] = {
                    "verified": True,
                    "number": response.phone_number,
                    "type": response.phone_type,
                    "carrier": response.carrier,
                    "valid": response.is_valid,
                    "owner": response.owner_info,
                }

                print(f"  ✅ Phone verified: {response.phone_number}")
                print(f"    • Type: {response.phone_type}")
                print(
                    f"    • Owner: {response.owner_info.get('name', 'N/A') if response.owner_info else 'N/A'}"
                )
            else:
                print("  ⚠️ Phone verification failed")
                self.research_data["results"]["phone_verification"] = {
                    "verified": False,
                    "message": response.error_message,
                }

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.research_data["results"]["phone_verification"] = {"error": str(e)}

    async def _find_key_personnel(self):
        """Find key personnel associated with the business."""
        print("\n👥 Step 4: Key Personnel Search")
        print("-" * 40)

        key_personnel = []

        # Extract officers from business search results
        if "business_search" in self.research_data["results"]:
            matches = self.research_data["results"]["business_search"].get(
                "matches", []
            )
            if matches:
                officers = matches[0].get("officers", [])

                print(f"  📋 Found {len(officers)} officers/directors")

                for officer in officers[:5]:  # Limit to 5 for example
                    # Search for additional information about each officer
                    try:
                        request = PersonSearchRequest(
                            first_name=officer.get("first_name"),
                            last_name=officer.get("last_name"),
                            state=self.research_data["business"].get("state"),
                        )

                        response = await self.client.person_search(request)

                        if response.success and response.results:
                            person_data = response.results[0]
                            key_personnel.append(
                                {
                                    "name": f"{officer.get('first_name')} {officer.get('last_name')}",
                                    "title": officer.get("title"),
                                    "age": person_data.get("age"),
                                    "addresses": len(person_data.get("addresses", [])),
                                    "other_businesses": person_data.get(
                                        "business_associations", []
                                    ),
                                }
                            )

                            print(
                                f"    • {officer.get('first_name')} {officer.get('last_name')}"
                            )
                            print(f"      Title: {officer.get('title')}")

                    except Exception as e:
                        print(
                            f"    ❌ Error searching for {officer.get('first_name')} {officer.get('last_name')}: {str(e)}"
                        )

                    await asyncio.sleep(0.5)  # Rate limiting

        self.research_data["results"]["key_personnel"] = key_personnel

    async def _check_registrations(self):
        """Check business registrations and licenses."""
        print("\n📑 Step 5: Registration & License Check")
        print("-" * 40)

        registrations = {
            "state_registration": None,
            "federal_ein": None,
            "business_licenses": [],
            "professional_licenses": [],
            "permits": [],
        }

        # Extract registration info from business search
        if "business_search" in self.research_data["results"]:
            matches = self.research_data["results"]["business_search"].get(
                "matches", []
            )
            if matches:
                top_match = matches[0]
                registrations["state_registration"] = top_match.get("state_id")
                registrations["federal_ein"] = top_match.get("ein")

        print("  🔍 Checking registrations:")
        print(
            f"    • State Registration: {registrations['state_registration'] or 'Not found'}"
        )
        print(f"    • Federal EIN: {registrations['federal_ein'] or 'Not found'}")
        print("    • Business Licenses: Pending verification")
        print("    • Professional Licenses: Pending verification")

        self.research_data["results"]["registrations"] = registrations

    async def _analyze_financial_indicators(self):
        """Analyze financial indicators and creditworthiness."""
        print("\n💰 Step 6: Financial Indicators")
        print("-" * 40)

        financial_indicators = {
            "estimated_revenue": None,
            "employee_count": None,
            "years_in_business": None,
            "financial_stress_indicators": [],
            "growth_indicators": [],
        }

        # Calculate years in business
        if "business_search" in self.research_data["results"]:
            matches = self.research_data["results"]["business_search"].get(
                "matches", []
            )
            if matches and matches[0].get("formation_date"):
                formation_date = datetime.strptime(
                    matches[0]["formation_date"], "%Y-%m-%d"
                )
                years_in_business = (datetime.now() - formation_date).days / 365
                financial_indicators["years_in_business"] = round(years_in_business, 1)

        # Check for financial stress indicators
        if (
            financial_indicators["years_in_business"]
            and financial_indicators["years_in_business"] < 2
        ):
            financial_indicators["financial_stress_indicators"].append(
                "New business (< 2 years)"
            )

        print("  📊 Financial Analysis:")
        print(
            f"    • Years in Business: {financial_indicators['years_in_business'] or 'Unknown'}"
        )
        print(
            f"    • Stress Indicators: {len(financial_indicators['financial_stress_indicators'])}"
        )

        self.research_data["results"]["financial_indicators"] = financial_indicators

    async def _analyze_online_presence(self):
        """Analyze business online presence."""
        print("\n🌐 Step 7: Online Presence Analysis")
        print("-" * 40)

        online_presence = {
            "website": None,
            "social_media": {"facebook": None, "linkedin": None, "twitter": None},
            "reviews": {"google": None, "yelp": None, "bbb": None},
            "domain_age": None,
        }

        # This would integrate with web scraping and social media APIs
        print("  🔍 Analyzing online presence:")
        print("    • Website: Checking...")
        print("    • Social Media: Scanning platforms...")
        print("    • Reviews: Aggregating ratings...")

        self.research_data["results"]["online_presence"] = online_presence

    async def _compliance_check(self):
        """Check compliance and risk factors."""
        print("\n⚠️ Step 8: Compliance & Risk Check")
        print("-" * 40)

        compliance = {
            "status": "ACTIVE",
            "risk_level": "LOW",
            "compliance_issues": [],
            "litigation": [],
            "sanctions_check": False,
            "bankruptcy_check": False,
        }

        risk_score = 0
        risk_factors = []

        # Check business status
        if "business_search" in self.research_data["results"]:
            matches = self.research_data["results"]["business_search"].get(
                "matches", []
            )
            if matches:
                status = matches[0].get("status", "").upper()
                if status != "ACTIVE":
                    risk_factors.append(f"Business status: {status}")
                    risk_score += 20

        # Check address verification
        if "address_verification" in self.research_data["results"]:
            if not self.research_data["results"]["address_verification"].get(
                "verified"
            ):
                risk_factors.append("Address not verified")
                risk_score += 15

        # Check years in business
        if "financial_indicators" in self.research_data["results"]:
            years = self.research_data["results"]["financial_indicators"].get(
                "years_in_business"
            )
            if years and years < 1:
                risk_factors.append("New business (< 1 year)")
                risk_score += 10

        # Determine risk level
        if risk_score <= 10:
            compliance["risk_level"] = "LOW"
        elif risk_score <= 30:
            compliance["risk_level"] = "MEDIUM"
        else:
            compliance["risk_level"] = "HIGH"

        compliance["compliance_issues"] = risk_factors

        print(f"  📊 Risk Level: {compliance['risk_level']}")
        if risk_factors:
            print("  Risk Factors:")
            for factor in risk_factors:
                print(f"    • {factor}")

        self.research_data["results"]["compliance"] = compliance

    def _generate_report(self):
        """Generate comprehensive research report."""
        print("\n📄 Research Report")
        print("=" * 60)

        report = {
            "research_complete": True,
            "timestamp": self.research_data["timestamp"],
            "business": self.research_data["business"],
            "summary": {},
        }

        # Generate executive summary
        results = self.research_data["results"]

        # Business verification status
        if "business_search" in results and results["business_search"].get("matches"):
            top_match = results["business_search"]["matches"][0]
            report["summary"]["verified"] = True
            report["summary"]["entity_type"] = top_match.get("type")
            report["summary"]["status"] = top_match.get("status")
            report["summary"]["formation_date"] = top_match.get("formation_date")
        else:
            report["summary"]["verified"] = False

        # Risk assessment
        if "compliance" in results:
            report["summary"]["risk_level"] = results["compliance"]["risk_level"]
            report["summary"]["compliance_issues"] = len(
                results["compliance"]["compliance_issues"]
            )

        # Key personnel
        if "key_personnel" in results:
            report["summary"]["key_personnel_count"] = len(results["key_personnel"])

        self.research_data["report"] = report

        print(f"  ✅ Research completed at {report['timestamp']}")
        print(f"  📊 Business Verified: {report['summary'].get('verified', False)}")
        print(f"  ⚠️ Risk Level: {report['summary'].get('risk_level', 'N/A')}")

        # Save full report
        report_file = f"business_research_{self.research_data['business']['name'].replace(' ', '_')}_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(report_file, "w") as f:
            json.dump(self.research_data, f, indent=2)
        print(f"  💾 Full report saved to: {report_file}")

    async def close(self):
        """Clean up resources."""
        await self.client.close()


async def competitor_analysis(business_names: List[str], location: Dict[str, str]):
    """
    Analyze multiple competitors in a market.

    Args:
        business_names: List of competitor business names
        location: Dictionary with city and state
    """
    print("🏢 Competitor Analysis")
    print("=" * 60)

    researcher = BusinessResearcher()
    competitors = []

    for name in business_names:
        print(f"\n📍 Analyzing: {name}")
        print("-" * 40)

        try:
            results = await researcher.research_business(
                business_name=name,
                city=location.get("city"),
                state=location.get("state"),
            )

            # Extract key metrics for comparison
            competitor_data = {
                "name": name,
                "verified": False,
                "years_in_business": None,
                "risk_level": None,
                "employees": None,
            }

            if results["results"].get("business_search", {}).get("matches"):
                competitor_data["verified"] = True

            if results["results"].get("financial_indicators"):
                competitor_data["years_in_business"] = results["results"][
                    "financial_indicators"
                ].get("years_in_business")

            if results["results"].get("compliance"):
                competitor_data["risk_level"] = results["results"]["compliance"].get(
                    "risk_level"
                )

            competitors.append(competitor_data)

        except Exception as e:
            print(f"  ❌ Error analyzing {name}: {str(e)}")
            competitors.append({"name": name, "error": str(e)})

        await asyncio.sleep(2)  # Rate limiting between searches

    # Generate comparison report
    print("\n📊 Competitor Comparison")
    print("=" * 60)

    for comp in competitors:
        print(f"\n{comp['name']}:")
        if "error" in comp:
            print(f"  ❌ Error: {comp['error']}")
        else:
            print(f"  • Verified: {comp['verified']}")
            print(f"  • Years in Business: {comp['years_in_business'] or 'Unknown'}")
            print(f"  • Risk Level: {comp['risk_level'] or 'Unknown'}")

    # Save comparison report
    report_file = f"competitor_analysis_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_file, "w") as f:
        json.dump(
            {
                "analysis_date": datetime.now().isoformat(),
                "location": location,
                "competitors": competitors,
            },
            f,
            indent=2,
        )
    print(f"\n💾 Comparison report saved to: {report_file}")

    await researcher.close()


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Business Research Example")
    print("=" * 60)

    # Example 1: Single business research
    print("\n📌 Example 1: Single Business Research")
    print("-" * 40)

    researcher = BusinessResearcher()

    try:
        results = await researcher.research_business(
            business_name="Acme Corporation", city="New York", state="NY"
        )

        print("\n✨ Research completed successfully!")

    except Exception as e:
        print(f"\n❌ Research failed: {str(e)}")

    finally:
        await researcher.close()

    # Example 2: Competitor analysis
    print("\n📌 Example 2: Competitor Analysis")
    print("-" * 40)

    competitors = ["TechStart Inc", "Digital Solutions LLC", "Innovation Partners"]

    await competitor_analysis(
        business_names=competitors, location={"city": "San Francisco", "state": "CA"}
    )

    print("\n✨ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
