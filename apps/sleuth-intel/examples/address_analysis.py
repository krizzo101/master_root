#!/usr/bin/env python3
"""
Address Analysis Example
========================

This example demonstrates address verification, property analysis,
and neighborhood research capabilities.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python address_analysis.py
"""

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    AddressSearchRequest,
    PersonSearchRequest,
    PropertySearchRequest,
)


class AddressAnalyzer:
    """Comprehensive address analysis handler."""

    def __init__(self):
        self.client = SleuthIntel()
        self.analysis_data = {}

    async def analyze_address(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
        radius_miles: int = 0.5,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive address analysis.

        Args:
            address: Street address
            city: City name
            state: State code
            zip_code: Optional ZIP code
            radius_miles: Radius for neighborhood analysis

        Returns:
            Dictionary with analysis results
        """
        print(f"🏠 Analyzing address: {address}, {city}, {state}")
        print("=" * 60)

        self.analysis_data = {
            "target_address": {
                "address": address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
            },
            "timestamp": datetime.now().isoformat(),
            "results": {},
        }

        # Step 1: Verify and standardize address
        await self._verify_address(address, city, state, zip_code)

        # Step 2: Get property information
        await self._get_property_info()

        # Step 3: Find current and past residents
        await self._find_residents()

        # Step 4: Analyze neighborhood
        await self._analyze_neighborhood(radius_miles)

        # Step 5: Check property history
        await self._check_property_history()

        # Step 6: Assess property value and trends
        await self._assess_property_value()

        # Step 7: Environmental and risk factors
        await self._check_environmental_factors()

        # Generate analysis report
        self._generate_report()

        return self.analysis_data

    async def _verify_address(
        self, address: str, city: str, state: str, zip_code: Optional[str]
    ):
        """Verify and standardize the address."""
        print("\n📍 Step 1: Address Verification")
        print("-" * 40)

        try:
            request = AddressSearchRequest(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                standardize=True,
            )

            response = await self.client.address_search(request)

            if response.success:
                self.analysis_data["results"]["address_verification"] = {
                    "verified": True,
                    "formatted_address": response.formatted_address,
                    "standardized": {
                        "street_number": response.street_number,
                        "street_name": response.street_name,
                        "street_type": response.street_type,
                        "unit": response.unit_number,
                        "city": response.city,
                        "state": response.state,
                        "zip": response.zip_code,
                        "zip_plus4": response.zip_plus4,
                        "county": response.county,
                    },
                    "coordinates": {
                        "latitude": response.latitude,
                        "longitude": response.longitude,
                    },
                    "delivery_info": {
                        "residential": response.is_residential,
                        "commercial": response.is_commercial,
                        "deliverable": response.is_deliverable,
                        "vacant": response.is_vacant,
                    },
                }

                print(f"  ✅ Address verified: {response.formatted_address}")
                print(
                    f"    • Type: {'Residential' if response.is_residential else 'Commercial'}"
                )
                print(f"    • Deliverable: {response.is_deliverable}")
                print(f"    • Coordinates: ({response.latitude}, {response.longitude})")
            else:
                print(f"  ❌ Address verification failed: {response.error_message}")
                self.analysis_data["results"]["address_verification"] = {
                    "verified": False,
                    "error": response.error_message,
                }

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.analysis_data["results"]["address_verification"] = {"error": str(e)}

    async def _get_property_info(self):
        """Get detailed property information."""
        print("\n🏘️ Step 2: Property Information")
        print("-" * 40)

        if (
            not self.analysis_data["results"]
            .get("address_verification", {})
            .get("verified")
        ):
            print("  ⚠️ Skipping - address not verified")
            return

        try:
            formatted_address = self.analysis_data["results"]["address_verification"][
                "formatted_address"
            ]

            request = PropertySearchRequest(
                address=formatted_address,
                include_ownership=True,
                include_tax_info=True,
                include_mortgage=True,
                include_foreclosure=True,
            )

            response = await self.client.property_search(request)

            if response.success:
                self.analysis_data["results"]["property_info"] = {
                    "property_type": response.property_type,
                    "year_built": response.year_built,
                    "bedrooms": response.bedrooms,
                    "bathrooms": response.bathrooms,
                    "square_footage": response.square_footage,
                    "lot_size": response.lot_size,
                    "stories": response.stories,
                    "garage": response.garage_spaces,
                    "pool": response.has_pool,
                    "assessed_value": response.assessed_value,
                    "tax_amount": response.annual_tax,
                    "last_sale": {
                        "date": response.last_sale_date,
                        "price": response.last_sale_price,
                    },
                    "ownership": {
                        "owner_name": response.owner_name,
                        "owner_type": response.owner_type,
                        "ownership_length": response.ownership_years,
                        "mailing_address": response.owner_mailing_address,
                    },
                    "mortgage_info": {
                        "has_mortgage": response.has_mortgage,
                        "lender": response.mortgage_lender,
                        "loan_amount": response.mortgage_amount,
                    },
                    "foreclosure_info": {
                        "in_foreclosure": response.in_foreclosure,
                        "foreclosure_date": response.foreclosure_date,
                    },
                }

                print(f"  ✅ Property data retrieved")
                print(f"    • Type: {response.property_type}")
                print(f"    • Year Built: {response.year_built}")
                print(f"    • Size: {response.square_footage} sq ft")
                print(
                    f"    • Bedrooms/Bathrooms: {response.bedrooms}/{response.bathrooms}"
                )
                print(f"    • Assessed Value: ${response.assessed_value:,.0f}")
                print(f"    • Owner: {response.owner_name}")
            else:
                print("  ⚠️ Property information not available")
                self.analysis_data["results"]["property_info"] = {
                    "available": False,
                    "message": response.error_message,
                }

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.analysis_data["results"]["property_info"] = {"error": str(e)}

    async def _find_residents(self):
        """Find current and past residents."""
        print("\n👥 Step 3: Resident History")
        print("-" * 40)

        if (
            not self.analysis_data["results"]
            .get("address_verification", {})
            .get("verified")
        ):
            print("  ⚠️ Skipping - address not verified")
            return

        try:
            formatted_address = self.analysis_data["results"]["address_verification"][
                "formatted_address"
            ]

            request = AddressSearchRequest(
                address=formatted_address,
                include_residents=True,
                include_historical=True,
                historical_years=10,
            )

            response = await self.client.address_search(request)

            if response.success:
                residents_data = {
                    "current_residents": [],
                    "past_residents": [],
                    "total_residents": 0,
                }

                # Process current residents
                for resident in response.current_residents[:10]:
                    residents_data["current_residents"].append(
                        {
                            "name": f"{resident.get('first_name', '')} {resident.get('last_name', '')}",
                            "age": resident.get("age"),
                            "phone": resident.get("phone"),
                            "email": resident.get("email"),
                            "length_of_residence": resident.get("residence_years"),
                        }
                    )

                # Process past residents
                for resident in response.past_residents[:10]:
                    residents_data["past_residents"].append(
                        {
                            "name": f"{resident.get('first_name', '')} {resident.get('last_name', '')}",
                            "date_range": f"{resident.get('move_in_date', 'Unknown')} - {resident.get('move_out_date', 'Unknown')}",
                        }
                    )

                residents_data["total_residents"] = len(
                    response.current_residents
                ) + len(response.past_residents)

                self.analysis_data["results"]["residents"] = residents_data

                print(f"  ✅ Found {len(response.current_residents)} current residents")
                print(f"  📅 Found {len(response.past_residents)} past residents")

                if response.current_residents:
                    print("  Current Residents:")
                    for res in residents_data["current_residents"][:3]:
                        print(f"    • {res['name']} (Age: {res['age']})")

            else:
                print("  ⚠️ Resident information not available")
                self.analysis_data["results"]["residents"] = {"available": False}

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.analysis_data["results"]["residents"] = {"error": str(e)}

    async def _analyze_neighborhood(self, radius_miles: float):
        """Analyze the neighborhood within specified radius."""
        print(f"\n🏘️ Step 4: Neighborhood Analysis ({radius_miles} mile radius)")
        print("-" * 40)

        if (
            not self.analysis_data["results"]
            .get("address_verification", {})
            .get("verified")
        ):
            print("  ⚠️ Skipping - address not verified")
            return

        try:
            coords = self.analysis_data["results"]["address_verification"][
                "coordinates"
            ]

            request = AddressSearchRequest(
                latitude=coords["latitude"],
                longitude=coords["longitude"],
                radius_miles=radius_miles,
                include_neighbors=True,
                include_demographics=True,
                include_crime_stats=True,
            )

            response = await self.client.address_search(request)

            if response.success:
                neighborhood_data = {
                    "neighbors": [],
                    "demographics": {},
                    "crime_stats": {},
                    "property_stats": {},
                }

                # Process neighbors
                for neighbor in response.neighbors[:20]:
                    neighborhood_data["neighbors"].append(
                        {
                            "address": neighbor.get("address"),
                            "distance": neighbor.get("distance_miles"),
                            "residents": neighbor.get("resident_count"),
                            "property_type": neighbor.get("property_type"),
                            "year_built": neighbor.get("year_built"),
                        }
                    )

                # Demographics
                if response.demographics:
                    neighborhood_data["demographics"] = {
                        "population": response.demographics.get("population"),
                        "median_age": response.demographics.get("median_age"),
                        "median_income": response.demographics.get("median_income"),
                        "owner_occupied": response.demographics.get(
                            "owner_occupied_pct"
                        ),
                        "renter_occupied": response.demographics.get(
                            "renter_occupied_pct"
                        ),
                        "vacancy_rate": response.demographics.get("vacancy_rate"),
                    }

                # Crime statistics
                if response.crime_stats:
                    neighborhood_data["crime_stats"] = {
                        "crime_index": response.crime_stats.get("crime_index"),
                        "violent_crime_rate": response.crime_stats.get(
                            "violent_crime_rate"
                        ),
                        "property_crime_rate": response.crime_stats.get(
                            "property_crime_rate"
                        ),
                        "comparison": response.crime_stats.get("vs_national_avg"),
                    }

                # Property statistics
                property_values = [
                    n.get("assessed_value", 0)
                    for n in response.neighbors
                    if n.get("assessed_value")
                ]
                if property_values:
                    neighborhood_data["property_stats"] = {
                        "median_value": sum(property_values) / len(property_values),
                        "min_value": min(property_values),
                        "max_value": max(property_values),
                        "sample_size": len(property_values),
                    }

                self.analysis_data["results"]["neighborhood"] = neighborhood_data

                print(f"  ✅ Analyzed {len(response.neighbors)} neighboring properties")
                if response.demographics:
                    print(
                        f"    • Median Income: ${response.demographics.get('median_income', 0):,.0f}"
                    )
                    print(
                        f"    • Owner Occupied: {response.demographics.get('owner_occupied_pct', 0):.1f}%"
                    )
                if response.crime_stats:
                    print(
                        f"    • Crime Index: {response.crime_stats.get('crime_index', 'N/A')}"
                    )

            else:
                print("  ⚠️ Neighborhood data not available")
                self.analysis_data["results"]["neighborhood"] = {"available": False}

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.analysis_data["results"]["neighborhood"] = {"error": str(e)}

    async def _check_property_history(self):
        """Check property transaction and ownership history."""
        print("\n📜 Step 5: Property History")
        print("-" * 40)

        if not self.analysis_data["results"].get("property_info"):
            print("  ⚠️ Skipping - property info not available")
            return

        try:
            # Simulated property history
            property_history = {
                "ownership_transfers": [
                    {
                        "date": "2020-03-15",
                        "type": "Sale",
                        "price": 450000,
                        "buyer": "Current Owner",
                        "seller": "Previous Owner LLC",
                    },
                    {
                        "date": "2015-07-22",
                        "type": "Sale",
                        "price": 380000,
                        "buyer": "Previous Owner LLC",
                        "seller": "Original Developer",
                    },
                ],
                "tax_history": [
                    {"year": 2023, "assessed_value": 475000, "tax_amount": 5700},
                    {"year": 2022, "assessed_value": 460000, "tax_amount": 5520},
                    {"year": 2021, "assessed_value": 455000, "tax_amount": 5460},
                ],
                "permits": [
                    {
                        "date": "2022-06-10",
                        "type": "Building Permit",
                        "description": "Kitchen renovation",
                        "value": 25000,
                    }
                ],
                "liens": [],
            }

            self.analysis_data["results"]["property_history"] = property_history

            print(
                f"  ✅ Found {len(property_history['ownership_transfers'])} ownership transfers"
            )
            print(f"  📊 Tax history for {len(property_history['tax_history'])} years")
            print(f"  🔨 {len(property_history['permits'])} permits on record")
            print(f"  ⚖️ {len(property_history['liens'])} liens")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.analysis_data["results"]["property_history"] = {"error": str(e)}

    async def _assess_property_value(self):
        """Assess property value and market trends."""
        print("\n💰 Step 6: Property Value Assessment")
        print("-" * 40)

        if not self.analysis_data["results"].get("property_info"):
            print("  ⚠️ Skipping - property info not available")
            return

        try:
            property_info = self.analysis_data["results"]["property_info"]
            neighborhood = self.analysis_data["results"].get("neighborhood", {})

            assessment = {
                "current_assessed_value": property_info.get("assessed_value"),
                "last_sale_price": property_info.get("last_sale", {}).get("price"),
                "estimated_market_value": None,
                "value_trend": None,
                "price_per_sqft": None,
                "neighborhood_comparison": None,
            }

            # Calculate price per square foot
            if property_info.get("square_footage") and property_info.get(
                "assessed_value"
            ):
                assessment["price_per_sqft"] = (
                    property_info["assessed_value"] / property_info["square_footage"]
                )

            # Compare to neighborhood
            if neighborhood.get("property_stats"):
                median_value = neighborhood["property_stats"].get("median_value", 0)
                if median_value and property_info.get("assessed_value"):
                    diff_pct = (
                        (property_info["assessed_value"] - median_value) / median_value
                    ) * 100
                    assessment["neighborhood_comparison"] = {
                        "median_neighborhood_value": median_value,
                        "difference_percent": diff_pct,
                        "relative_position": "Above" if diff_pct > 0 else "Below",
                    }

            # Determine value trend
            if property_info.get("last_sale", {}).get("price") and property_info.get(
                "assessed_value"
            ):
                change = (
                    property_info["assessed_value"]
                    - property_info["last_sale"]["price"]
                )
                change_pct = (change / property_info["last_sale"]["price"]) * 100
                assessment["value_trend"] = {
                    "change_amount": change,
                    "change_percent": change_pct,
                    "trend": "Appreciating" if change > 0 else "Depreciating",
                }

            self.analysis_data["results"]["value_assessment"] = assessment

            print(f"  ✅ Value Assessment Complete")
            print(f"    • Assessed Value: ${assessment['current_assessed_value']:,.0f}")
            if assessment["price_per_sqft"]:
                print(f"    • Price/sqft: ${assessment['price_per_sqft']:.2f}")
            if assessment["value_trend"]:
                print(
                    f"    • Trend: {assessment['value_trend']['trend']} ({assessment['value_trend']['change_percent']:.1f}%)"
                )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.analysis_data["results"]["value_assessment"] = {"error": str(e)}

    async def _check_environmental_factors(self):
        """Check environmental and risk factors."""
        print("\n🌍 Step 7: Environmental & Risk Factors")
        print("-" * 40)

        try:
            # Simulated environmental data
            environmental_factors = {
                "flood_zone": "X",
                "flood_risk": "Minimal",
                "earthquake_risk": "Low",
                "fire_risk": "Moderate",
                "environmental_hazards": [],
                "nearby_facilities": [
                    {
                        "type": "School",
                        "name": "Lincoln Elementary",
                        "distance": "0.3 miles",
                    },
                    {
                        "type": "Hospital",
                        "name": "General Hospital",
                        "distance": "2.1 miles",
                    },
                    {
                        "type": "Fire Station",
                        "name": "Station 42",
                        "distance": "1.5 miles",
                    },
                ],
                "walkability_score": 72,
                "transit_score": 45,
                "noise_level": "Moderate",
            }

            self.analysis_data["results"][
                "environmental_factors"
            ] = environmental_factors

            print(f"  ✅ Environmental assessment complete")
            print(
                f"    • Flood Zone: {environmental_factors['flood_zone']} ({environmental_factors['flood_risk']} risk)"
            )
            print(f"    • Fire Risk: {environmental_factors['fire_risk']}")
            print(
                f"    • Walkability Score: {environmental_factors['walkability_score']}/100"
            )
            print(
                f"    • Nearby Facilities: {len(environmental_factors['nearby_facilities'])}"
            )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.analysis_data["results"]["environmental_factors"] = {"error": str(e)}

    def _generate_report(self):
        """Generate comprehensive analysis report."""
        print("\n📄 Analysis Report")
        print("=" * 60)

        report = {
            "analysis_complete": True,
            "timestamp": self.analysis_data["timestamp"],
            "address": self.analysis_data["target_address"],
            "summary": {},
        }

        results = self.analysis_data["results"]

        # Address verification
        if results.get("address_verification", {}).get("verified"):
            report["summary"]["address_verified"] = True
            report["summary"]["property_type"] = (
                results["address_verification"]["delivery_info"].get("residential")
                and "Residential"
                or "Commercial"
            )

        # Property details
        if results.get("property_info"):
            report["summary"]["property"] = {
                "type": results["property_info"].get("property_type"),
                "year_built": results["property_info"].get("year_built"),
                "size": results["property_info"].get("square_footage"),
                "value": results["property_info"].get("assessed_value"),
            }

        # Residents
        if results.get("residents"):
            report["summary"]["occupancy"] = {
                "current_residents": len(
                    results["residents"].get("current_residents", [])
                ),
                "past_residents": len(results["residents"].get("past_residents", [])),
            }

        # Neighborhood
        if results.get("neighborhood", {}).get("demographics"):
            report["summary"]["neighborhood"] = {
                "median_income": results["neighborhood"]["demographics"].get(
                    "median_income"
                ),
                "owner_occupied_rate": results["neighborhood"]["demographics"].get(
                    "owner_occupied"
                ),
            }

        self.analysis_data["report"] = report

        print(f"  ✅ Analysis completed at {report['timestamp']}")
        print(
            f"  📍 Address Verified: {report['summary'].get('address_verified', False)}"
        )
        if report["summary"].get("property"):
            print(
                f"  🏠 Property Value: ${report['summary']['property'].get('value', 0):,.0f}"
            )

        # Save full report
        report_file = f"address_analysis_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(report_file, "w") as f:
            json.dump(self.analysis_data, f, indent=2)
        print(f"  💾 Full report saved to: {report_file}")

    async def close(self):
        """Clean up resources."""
        await self.client.close()


async def batch_address_analysis(addresses: List[Dict[str, str]]):
    """
    Analyze multiple addresses in batch.

    Args:
        addresses: List of address dictionaries
    """
    print("🏘️ Batch Address Analysis")
    print("=" * 60)

    analyzer = AddressAnalyzer()
    results = []

    for i, addr in enumerate(addresses, 1):
        print(
            f"\n[{i}/{len(addresses)}] Analyzing: {addr['address']}, {addr['city']}, {addr['state']}"
        )
        print("-" * 40)

        try:
            analysis = await analyzer.analyze_address(
                address=addr["address"],
                city=addr["city"],
                state=addr["state"],
                zip_code=addr.get("zip_code"),
                radius_miles=0.25,
            )

            results.append(
                {
                    "address": addr,
                    "verified": analysis["results"]
                    .get("address_verification", {})
                    .get("verified", False),
                    "property_value": analysis["results"]
                    .get("property_info", {})
                    .get("assessed_value"),
                    "residents": len(
                        analysis["results"]
                        .get("residents", {})
                        .get("current_residents", [])
                    ),
                    "analysis_file": f"address_{i}_analysis.json",
                }
            )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append({"address": addr, "error": str(e)})

        await asyncio.sleep(2)  # Rate limiting

    # Summary report
    print("\n📊 Batch Analysis Summary")
    print("=" * 60)

    verified_count = sum(1 for r in results if r.get("verified"))
    print(f"  • Total Addresses: {len(results)}")
    print(f"  • Verified: {verified_count}")
    print(f"  • Failed: {len(results) - verified_count}")

    # Save batch report
    batch_file = f"batch_address_analysis_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(batch_file, "w") as f:
        json.dump(
            {
                "analysis_date": datetime.now().isoformat(),
                "total_addresses": len(addresses),
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"  💾 Batch report saved to: {batch_file}")

    await analyzer.close()


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Address Analysis Example")
    print("=" * 60)

    # Example 1: Single address analysis
    print("\n📌 Example 1: Single Address Analysis")
    print("-" * 40)

    analyzer = AddressAnalyzer()

    try:
        results = await analyzer.analyze_address(
            address="123 Main Street",
            city="Los Angeles",
            state="CA",
            zip_code="90001",
            radius_miles=0.5,
        )

        print("\n✨ Analysis completed successfully!")

    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")

    finally:
        await analyzer.close()

    # Example 2: Batch address analysis
    print("\n📌 Example 2: Batch Address Analysis")
    print("-" * 40)

    test_addresses = [
        {"address": "456 Oak Avenue", "city": "San Francisco", "state": "CA"},
        {"address": "789 Pine Street", "city": "Seattle", "state": "WA"},
        {"address": "321 Elm Boulevard", "city": "Portland", "state": "OR"},
    ]

    await batch_address_analysis(test_addresses)

    print("\n✨ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
