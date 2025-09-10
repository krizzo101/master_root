"""
Real Estate Use Case Examples for AddressSearchAgent
Demonstrates practical applications of address intelligence in real estate scenarios
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Import the AddressSearchAgent and related models
from src.agents.address_search_agent import AddressSearchAgent
from src.agents.person_search_agent import PersonSearchAgent
from src.models.person import PersonProfile
from src.models.query import AddressLookupQuery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealEstateIntelligenceService:
    """
    Service class demonstrating real estate intelligence use cases
    """

    def __init__(self):
        # Initialize agents with integration
        self.person_agent = PersonSearchAgent()
        self.address_agent = AddressSearchAgent(person_search_agent=self.person_agent)

        logger.info("Real Estate Intelligence Service initialized")

    def property_due_diligence(
        self, address: str, include_demographics: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive property due diligence for real estate transactions

        Use Case: Before purchasing a property, buyers want to know:
        - Who currently lives there
        - Property ownership history
        - Neighborhood characteristics
        - Potential issues or red flags

        Args:
            address: Property address to investigate
            include_demographics: Whether to include neighborhood demographics

        Returns:
            Comprehensive due diligence report
        """
        logger.info(f"Starting property due diligence for: {address}")

        try:
            # Create comprehensive query
            query = AddressLookupQuery(
                full_address=address,
                include_residents=True,
                include_property_data=True,
                include_demographics=include_demographics,
                min_confidence=0.6,
            )

            # Get full intelligence report
            report = self.address_agent.search_comprehensive(query)

            # Create due diligence summary
            due_diligence = {
                "property_address": address,
                "analysis_date": datetime.now().isoformat(),
                "overall_confidence": report.confidence_score,
                "validation_status": {
                    "address_valid": report.validation_result.is_valid
                    if report.validation_result
                    else False,
                    "deliverable": report.verification_status.get(
                        "is_deliverable", False
                    )
                    if report.verification_status
                    else False,
                    "verification_level": report.verification_status.get(
                        "verification_level"
                    )
                    if report.verification_status
                    else "unknown",
                },
                "current_occupancy": {
                    "resident_count": len(report.current_residents),
                    "residents": [
                        {
                            "name": resident.name,
                            "age": resident.age,
                            "relationship": resident.relationship_to_property,
                            "confidence": resident.confidence_score,
                        }
                        for resident in report.current_residents[
                            :3
                        ]  # Limit for privacy
                    ],
                    "occupancy_type": self._determine_occupancy_type(
                        report.current_residents
                    ),
                },
                "ownership_analysis": {
                    "current_owner": report.ownership_records[0].current_owner
                    if report.ownership_records
                    else "Unknown",
                    "ownership_type": report.ownership_records[0].ownership_type
                    if report.ownership_records
                    else "Unknown",
                    "property_details": report.ownership_records[0].property_details
                    if report.ownership_records
                    else {},
                    "tax_assessment": report.ownership_records[0].tax_assessment
                    if report.ownership_records
                    else {},
                },
                "stability_indicators": {
                    "resident_turnover": self._calculate_turnover_risk(
                        report.current_residents, report.historical_residents
                    ),
                    "movement_patterns": [
                        {
                            "person": pattern.person_name,
                            "stability_score": pattern.stability_score,
                            "geographic_mobility": pattern.geographic_mobility,
                        }
                        for pattern in report.movement_patterns
                    ],
                },
                "risk_assessment": {
                    "identified_risks": report.risk_indicators,
                    "risk_level": self._assess_overall_risk(report),
                    "red_flags": self._identify_red_flags(report),
                },
            }

            # Add neighborhood analysis if available
            if report.demographic_profile:
                due_diligence["neighborhood_profile"] = {
                    "median_home_value": report.demographic_profile.housing_characteristics.get(
                        "median_home_value"
                    ),
                    "homeownership_rate": report.demographic_profile.housing_characteristics.get(
                        "homeownership_rate"
                    ),
                    "median_income": report.demographic_profile.income_statistics.get(
                        "median_household_income"
                    ),
                    "population_stability": self._assess_neighborhood_stability(
                        report.demographic_profile
                    ),
                    "investment_attractiveness": self._rate_investment_potential(
                        report.demographic_profile
                    ),
                }

            logger.info(
                f"Due diligence completed with {due_diligence['overall_confidence']:.2f} confidence"
            )
            return due_diligence

        except Exception as e:
            logger.error(f"Due diligence failed: {e}")
            return {
                "property_address": address,
                "error": str(e),
                "analysis_date": datetime.now().isoformat(),
                "status": "failed",
            }

    def rental_property_screening(
        self, address: str, prospective_tenant: str = None
    ) -> Dict[str, Any]:
        """
        Screen rental property and optionally verify prospective tenant

        Use Case: Landlords want to:
        - Verify property condition and current occupancy
        - Check if prospective tenant has address history indicating stability
        - Identify any issues with the property or neighborhood

        Args:
            address: Rental property address
            prospective_tenant: Optional tenant name to investigate

        Returns:
            Rental screening report
        """
        logger.info(f"Screening rental property: {address}")

        try:
            # Get property intelligence
            query = AddressLookupQuery(
                full_address=address,
                include_residents=True,
                include_property_data=True,
                include_demographics=False,  # Less important for rentals
            )

            report = self.address_agent.search_comprehensive(query)

            screening_report = {
                "property_address": address,
                "screening_date": datetime.now().isoformat(),
                "property_status": {
                    "currently_occupied": len(report.current_residents) > 0,
                    "occupant_count": len(report.current_residents),
                    "vacancy_indicators": self._assess_vacancy_indicators(report),
                    "property_condition_flags": self._identify_property_flags(report),
                },
                "rental_history": {
                    "turnover_rate": self._calculate_rental_turnover(
                        report.historical_residents
                    ),
                    "average_tenancy_length": self._estimate_tenancy_length(
                        report.historical_residents
                    ),
                    "recent_tenant_changes": len(
                        [
                            r
                            for r in report.historical_residents
                            if r.occupancy_period.get("end_date", "").startswith("2023")
                        ]
                    ),
                },
                "landlord_verification": {
                    "owner_name": report.ownership_records[0].current_owner
                    if report.ownership_records
                    else "Unknown",
                    "ownership_type": report.ownership_records[0].ownership_type
                    if report.ownership_records
                    else "Unknown",
                    "is_corporate_owned": self._is_corporate_ownership(
                        report.ownership_records
                    ),
                    "property_management_indicators": self._detect_property_management(
                        report
                    ),
                },
            }

            # Prospective tenant screening if provided
            if prospective_tenant:
                tenant_analysis = self._analyze_prospective_tenant(
                    prospective_tenant, address
                )
                screening_report["prospective_tenant_analysis"] = tenant_analysis

            # Risk assessment for rental
            screening_report["rental_risk_assessment"] = {
                "overall_risk_level": self._assess_rental_risk(report),
                "stability_score": self._calculate_property_stability(report),
                "recommended_actions": self._generate_rental_recommendations(report),
            }

            return screening_report

        except Exception as e:
            logger.error(f"Rental screening failed: {e}")
            return {"property_address": address, "error": str(e), "status": "failed"}

    def market_analysis_by_address(self, addresses: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple addresses for market intelligence

        Use Case: Real estate agents and investors want to:
        - Compare properties in different neighborhoods
        - Identify market trends and opportunities
        - Assess relative property values and demographics

        Args:
            addresses: List of addresses to analyze

        Returns:
            Comparative market analysis
        """
        logger.info(f"Analyzing {len(addresses)} addresses for market intelligence")

        address_reports = {}
        market_metrics = {
            "median_home_values": [],
            "income_levels": [],
            "homeownership_rates": [],
            "population_densities": [],
        }

        for address in addresses:
            try:
                query = AddressLookupQuery(
                    full_address=address,
                    include_residents=False,  # Privacy-focused
                    include_property_data=True,
                    include_demographics=True,
                )

                report = self.address_agent.search_comprehensive(query)

                # Extract key market data
                property_data = {}
                if report.ownership_records:
                    prop_details = report.ownership_records[0].property_details
                    tax_info = report.ownership_records[0].tax_assessment

                    property_data = {
                        "property_type": prop_details.get("property_type"),
                        "square_footage": prop_details.get("square_footage"),
                        "year_built": prop_details.get("year_built"),
                        "assessed_value": tax_info.get("assessed_value"),
                        "annual_taxes": tax_info.get("annual_taxes"),
                    }

                demographic_data = {}
                if report.demographic_profile:
                    demographic_data = {
                        "median_home_value": report.demographic_profile.housing_characteristics.get(
                            "median_home_value"
                        ),
                        "median_income": report.demographic_profile.income_statistics.get(
                            "median_household_income"
                        ),
                        "homeownership_rate": report.demographic_profile.housing_characteristics.get(
                            "homeownership_rate"
                        ),
                        "population_density": report.demographic_profile.population_data.get(
                            "population_density"
                        ),
                    }

                    # Collect metrics for comparison
                    if demographic_data.get("median_home_value"):
                        market_metrics["median_home_values"].append(
                            demographic_data["median_home_value"]
                        )
                    if demographic_data.get("median_income"):
                        market_metrics["income_levels"].append(
                            demographic_data["median_income"]
                        )
                    if demographic_data.get("homeownership_rate"):
                        market_metrics["homeownership_rates"].append(
                            demographic_data["homeownership_rate"]
                        )
                    if demographic_data.get("population_density"):
                        market_metrics["population_densities"].append(
                            demographic_data["population_density"]
                        )

                address_reports[address] = {
                    "confidence": report.confidence_score,
                    "property_data": property_data,
                    "demographic_data": demographic_data,
                    "investment_score": self._calculate_investment_score(
                        property_data, demographic_data
                    ),
                }

            except Exception as e:
                logger.warning(f"Failed to analyze {address}: {e}")
                address_reports[address] = {"error": str(e)}

        # Generate comparative analysis
        market_analysis = {
            "analysis_date": datetime.now().isoformat(),
            "properties_analyzed": len(addresses),
            "successful_analyses": len(
                [r for r in address_reports.values() if "error" not in r]
            ),
            "individual_properties": address_reports,
            "market_comparison": {
                "median_home_value_range": {
                    "min": min(market_metrics["median_home_values"])
                    if market_metrics["median_home_values"]
                    else None,
                    "max": max(market_metrics["median_home_values"])
                    if market_metrics["median_home_values"]
                    else None,
                    "avg": sum(market_metrics["median_home_values"])
                    / len(market_metrics["median_home_values"])
                    if market_metrics["median_home_values"]
                    else None,
                },
                "income_range": {
                    "min": min(market_metrics["income_levels"])
                    if market_metrics["income_levels"]
                    else None,
                    "max": max(market_metrics["income_levels"])
                    if market_metrics["income_levels"]
                    else None,
                    "avg": sum(market_metrics["income_levels"])
                    / len(market_metrics["income_levels"])
                    if market_metrics["income_levels"]
                    else None,
                },
            },
            "investment_recommendations": self._generate_investment_recommendations(
                address_reports
            ),
        }

        return market_analysis

    def neighborhood_gentrification_analysis(
        self, address: str, historical_years: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze neighborhood for gentrification indicators

        Use Case: Investors and researchers want to identify:
        - Areas experiencing rapid demographic change
        - Gentrification patterns and displacement risks
        - Investment opportunities in emerging neighborhoods

        Args:
            address: Address in neighborhood to analyze
            historical_years: Years of historical data to analyze

        Returns:
            Gentrification analysis report
        """
        logger.info(f"Analyzing gentrification patterns around: {address}")

        try:
            # Get current neighborhood profile
            query = AddressLookupQuery(
                full_address=address,
                include_residents=True,
                include_property_data=True,
                include_demographics=True,
            )

            report = self.address_agent.search_comprehensive(query)

            # Analyze movement patterns of residents
            gentrification_indicators = {
                "address_analyzed": address,
                "analysis_date": datetime.now().isoformat(),
                "demographic_shifts": {},
                "housing_pressure_indicators": {},
                "population_mobility": {},
                "gentrification_risk_score": 0.0,
            }

            if report.demographic_profile:
                # Housing cost pressure indicators
                demographics = report.demographic_profile
                median_home_value = demographics.housing_characteristics.get(
                    "median_home_value", 0
                )
                median_income = demographics.income_statistics.get(
                    "median_household_income", 0
                )

                if median_home_value and median_income:
                    # Price-to-income ratio (higher = more pressure)
                    price_income_ratio = median_home_value / median_income
                    gentrification_indicators["housing_pressure_indicators"] = {
                        "price_to_income_ratio": price_income_ratio,
                        "affordability_pressure": "high"
                        if price_income_ratio > 5
                        else "moderate"
                        if price_income_ratio > 3
                        else "low",
                        "median_home_value": median_home_value,
                        "median_income": median_income,
                        "homeownership_rate": demographics.housing_characteristics.get(
                            "homeownership_rate"
                        ),
                    }

                # Demographic composition indicators
                gentrification_indicators["demographic_shifts"] = {
                    "age_distribution": demographics.age_distribution,
                    "education_levels": demographics.education_levels,
                    "income_distribution": demographics.income_statistics.get(
                        "income_distribution", {}
                    ),
                    "young_professional_indicator": demographics.age_distribution.get(
                        "25-34", 0
                    )
                    + demographics.age_distribution.get("35-44", 0),
                }

            # Analyze resident mobility patterns
            if report.movement_patterns:
                mobility_scores = [
                    pattern.geographic_mobility for pattern in report.movement_patterns
                ]
                stability_scores = [
                    pattern.stability_score for pattern in report.movement_patterns
                ]

                gentrification_indicators["population_mobility"] = {
                    "average_mobility": sum(mobility_scores) / len(mobility_scores)
                    if mobility_scores
                    else 0,
                    "average_stability": sum(stability_scores) / len(stability_scores)
                    if stability_scores
                    else 0,
                    "high_mobility_residents": len(
                        [s for s in mobility_scores if s > 0.6]
                    ),
                    "displacement_risk_indicators": self._identify_displacement_risks(
                        report.movement_patterns
                    ),
                }

            # Calculate overall gentrification risk score
            risk_factors = []

            # High property values relative to income
            if (
                gentrification_indicators["housing_pressure_indicators"].get(
                    "price_to_income_ratio", 0
                )
                > 4
            ):
                risk_factors.append(0.3)

            # High young professional population
            young_prof_pct = gentrification_indicators["demographic_shifts"].get(
                "young_professional_indicator", 0
            )
            if young_prof_pct > 40:
                risk_factors.append(0.25)

            # High resident mobility
            avg_mobility = gentrification_indicators["population_mobility"].get(
                "average_mobility", 0
            )
            if avg_mobility > 0.5:
                risk_factors.append(0.2)

            # Low homeownership rate (indicates rental pressure)
            homeownership_rate = gentrification_indicators[
                "housing_pressure_indicators"
            ].get("homeownership_rate", 100)
            if homeownership_rate < 50:
                risk_factors.append(0.15)

            # High education levels (indicator of demographic change)
            high_ed_pct = gentrification_indicators["demographic_shifts"].get(
                "education_levels", {}
            ).get("bachelors", 0) + gentrification_indicators["demographic_shifts"].get(
                "education_levels", {}
            ).get(
                "masters", 0
            )
            if high_ed_pct > 50:
                risk_factors.append(0.1)

            gentrification_indicators["gentrification_risk_score"] = sum(risk_factors)
            gentrification_indicators["risk_level"] = (
                "high"
                if gentrification_indicators["gentrification_risk_score"] > 0.7
                else "moderate"
                if gentrification_indicators["gentrification_risk_score"] > 0.4
                else "low"
            )

            # Investment and policy recommendations
            gentrification_indicators["recommendations"] = {
                "investment_timing": self._assess_gentrification_investment_timing(
                    gentrification_indicators
                ),
                "community_impact_concerns": self._identify_community_impact_risks(
                    gentrification_indicators
                ),
                "monitoring_suggestions": self._suggest_gentrification_monitoring(
                    gentrification_indicators
                ),
            }

            return gentrification_indicators

        except Exception as e:
            logger.error(f"Gentrification analysis failed: {e}")
            return {"address_analyzed": address, "error": str(e), "status": "failed"}

    def commercial_real_estate_intelligence(self, address: str) -> Dict[str, Any]:
        """
        Analyze address for commercial real estate opportunities

        Use Case: Commercial real estate professionals want to:
        - Identify business district characteristics
        - Assess foot traffic and economic activity potential
        - Evaluate commercial property investment opportunities

        Args:
            address: Commercial address to analyze

        Returns:
            Commercial real estate intelligence report
        """
        logger.info(f"Analyzing commercial real estate potential for: {address}")

        try:
            query = AddressLookupQuery(
                full_address=address,
                include_residents=True,  # May include business occupants
                include_property_data=True,
                include_demographics=True,
            )

            report = self.address_agent.search_comprehensive(query)

            commercial_analysis = {
                "property_address": address,
                "analysis_date": datetime.now().isoformat(),
                "property_classification": {
                    "is_commercial": report.verification_status.get(
                        "is_business", False
                    )
                    if report.verification_status
                    else False,
                    "zoning_indicators": self._identify_zoning_from_property(report),
                    "building_characteristics": self._analyze_commercial_building_features(
                        report
                    ),
                },
                "business_environment": {
                    "current_business_occupants": self._identify_business_occupants(
                        report.current_residents
                    ),
                    "business_turnover_indicators": self._assess_commercial_stability(
                        report.historical_residents
                    ),
                    "industry_mix": self._analyze_industry_composition(
                        report.current_residents
                    ),
                },
                "market_factors": {},
                "investment_potential": {},
            }

            # Market demographic factors for commercial success
            if report.demographic_profile:
                demo = report.demographic_profile
                commercial_analysis["market_factors"] = {
                    "population_density": demo.population_data.get(
                        "population_density"
                    ),
                    "median_income": demo.income_statistics.get(
                        "median_household_income"
                    ),
                    "employment_rate": demo.economic_indicators.get("employment_rate"),
                    "major_employers": demo.economic_indicators.get(
                        "major_employers", []
                    ),
                    "economic_indicators": {
                        "consumer_spending_potential": self._estimate_consumer_spending_potential(
                            demo
                        ),
                        "business_support_environment": self._assess_business_environment(
                            demo
                        ),
                        "foot_traffic_potential": self._estimate_foot_traffic_potential(
                            demo
                        ),
                    },
                }

            # Investment potential scoring
            commercial_analysis["investment_potential"] = {
                "location_score": self._score_commercial_location(report),
                "market_demand_score": self._score_market_demand(
                    commercial_analysis["market_factors"]
                ),
                "competitive_landscape": self._assess_commercial_competition(report),
                "overall_investment_rating": 0.0,  # Will be calculated
                "recommended_business_types": self._recommend_business_types(
                    commercial_analysis
                ),
            }

            # Calculate overall investment rating
            location_score = commercial_analysis["investment_potential"][
                "location_score"
            ]
            market_score = commercial_analysis["investment_potential"][
                "market_demand_score"
            ]
            commercial_analysis["investment_potential"]["overall_investment_rating"] = (
                location_score + market_score
            ) / 2

            return commercial_analysis

        except Exception as e:
            logger.error(f"Commercial real estate analysis failed: {e}")
            return {"property_address": address, "error": str(e), "status": "failed"}

    # Helper methods for analysis

    def _determine_occupancy_type(self, residents: List) -> str:
        """Determine type of occupancy based on resident data"""
        if not residents:
            return "vacant"

        if len(residents) == 1:
            return "single_occupant"
        elif len(residents) == 2:
            # Check if same last name (likely couple/family)
            if (
                residents[0].name
                and residents[1].name
                and residents[0].name.split()[-1] == residents[1].name.split()[-1]
            ):
                return "couple_family"
            else:
                return "roommates_shared"
        else:
            return "multi_occupant"

    def _calculate_turnover_risk(
        self, current_residents: List, historical_residents: List
    ) -> str:
        """Calculate resident turnover risk"""
        historical_count = len(historical_residents)
        if historical_count == 0:
            return "unknown"
        elif historical_count < 2:
            return "low"
        elif historical_count < 5:
            return "moderate"
        else:
            return "high"

    def _assess_overall_risk(self, report) -> str:
        """Assess overall property risk level"""
        risk_count = len(report.risk_indicators)
        high_severity = len(
            [r for r in report.risk_indicators if r.get("severity") == "high"]
        )

        if high_severity > 0 or risk_count > 3:
            return "high"
        elif risk_count > 1:
            return "moderate"
        else:
            return "low"

    def _identify_red_flags(self, report) -> List[str]:
        """Identify potential red flags for property purchase"""
        red_flags = []

        # Address verification issues
        if report.verification_status and report.verification_status.get(
            "verification_level"
        ) in ["questionable", "invalid"]:
            red_flags.append("Address verification issues")

        # Multiple recent residents (instability)
        if len(report.historical_residents) > 3:
            red_flags.append("High resident turnover")

        # Property ownership issues
        if report.ownership_records:
            ownership = report.ownership_records[0]
            if ownership.confidence_score < 0.7:
                red_flags.append("Uncertain ownership records")

        # No current residents but property should be residential
        if (
            len(report.current_residents) == 0
            and report.verification_status
            and report.verification_status.get("is_residential", False)
        ):
            red_flags.append("Vacant residential property")

        return red_flags

    def _assess_neighborhood_stability(self, demographic_profile) -> str:
        """Assess neighborhood population stability"""
        homeownership_rate = demographic_profile.housing_characteristics.get(
            "homeownership_rate", 0
        )

        if homeownership_rate > 70:
            return "high"
        elif homeownership_rate > 50:
            return "moderate"
        else:
            return "low"

    def _rate_investment_potential(self, demographic_profile) -> str:
        """Rate neighborhood investment potential"""
        median_income = demographic_profile.income_statistics.get(
            "median_household_income", 0
        )
        median_home_value = demographic_profile.housing_characteristics.get(
            "median_home_value", 0
        )
        employment_rate = demographic_profile.economic_indicators.get(
            "employment_rate", 0
        )

        score = 0
        if median_income > 75000:
            score += 1
        if median_home_value > 300000:
            score += 1
        if employment_rate > 90:
            score += 1

        return "high" if score >= 2 else "moderate" if score == 1 else "low"

    def _assess_vacancy_indicators(self, report) -> List[str]:
        """Assess property vacancy indicators"""
        indicators = []

        if len(report.current_residents) == 0:
            indicators.append("No current residents identified")

        if report.verification_status and not report.verification_status.get(
            "is_deliverable", True
        ):
            indicators.append("Mail delivery issues")

        return indicators

    def _identify_property_flags(self, report) -> List[str]:
        """Identify potential property condition flags"""
        flags = []

        for risk in report.risk_indicators:
            if risk.get("type") == "verification_issue":
                flags.append("Address verification concerns")
            elif risk.get("type") == "overcrowding":
                flags.append("Potential overcrowding")

        return flags

    def _calculate_rental_turnover(self, historical_residents: List) -> str:
        """Calculate rental property turnover rate"""
        return self._calculate_turnover_risk([], historical_residents)

    def _estimate_tenancy_length(self, historical_residents: List) -> str:
        """Estimate average tenancy length"""
        if len(historical_residents) <= 1:
            return "unknown"
        elif len(historical_residents) <= 3:
            return "long_term"  # 3+ years average
        elif len(historical_residents) <= 6:
            return "medium_term"  # 1-3 years average
        else:
            return "short_term"  # < 1 year average

    def _is_corporate_ownership(self, ownership_records: List) -> bool:
        """Check if property has corporate ownership"""
        if not ownership_records:
            return False

        ownership_type = ownership_records[0].ownership_type
        return ownership_type in ["corporation", "llc", "trust", "partnership"]

    def _detect_property_management(self, report) -> List[str]:
        """Detect property management indicators"""
        indicators = []

        if self._is_corporate_ownership(report.ownership_records):
            indicators.append("Corporate ownership")

        # Multiple units at same address might indicate apartment complex
        unique_residents = len(set(r.name for r in report.current_residents if r.name))
        if unique_residents > 2:
            indicators.append("Multi-unit property indicators")

        return indicators

    def _analyze_prospective_tenant(
        self, tenant_name: str, rental_address: str
    ) -> Dict[str, Any]:
        """Analyze prospective tenant stability and history"""
        try:
            # This would use PersonSearchAgent to get tenant history
            # For demo purposes, return placeholder
            return {
                "tenant_name": tenant_name,
                "stability_assessment": "requires_person_search_integration",
                "address_history_available": False,
                "recommendation": "Complete person search for full analysis",
            }
        except Exception as e:
            return {"error": str(e)}

    def _assess_rental_risk(self, report) -> str:
        """Assess rental property risk level"""
        return self._assess_overall_risk(report)

    def _calculate_property_stability(self, report) -> float:
        """Calculate property stability score (0-1)"""
        factors = []

        # Low turnover = higher stability
        historical_count = len(report.historical_residents)
        if historical_count <= 2:
            factors.append(0.8)
        elif historical_count <= 4:
            factors.append(0.6)
        else:
            factors.append(0.3)

        # Address verification
        if (
            report.verification_status
            and report.verification_status.get("verification_level") == "confirmed"
        ):
            factors.append(0.9)
        else:
            factors.append(0.5)

        # Property ownership clarity
        if (
            report.ownership_records
            and report.ownership_records[0].confidence_score > 0.8
        ):
            factors.append(0.8)
        else:
            factors.append(0.4)

        return sum(factors) / len(factors) if factors else 0.0

    def _generate_rental_recommendations(self, report) -> List[str]:
        """Generate rental property recommendations"""
        recommendations = []

        if len(report.current_residents) > 0:
            recommendations.append("Verify current lease status and occupancy rights")

        if len(report.historical_residents) > 3:
            recommendations.append("Investigate causes of high tenant turnover")

        if not report.ownership_records:
            recommendations.append("Verify property ownership and landlord authority")

        return recommendations

    def _calculate_investment_score(
        self, property_data: Dict, demographic_data: Dict
    ) -> float:
        """Calculate investment attractiveness score"""
        score = 0.0
        max_score = 10.0

        # Property value factors
        if demographic_data.get("median_home_value", 0) > 400000:
            score += 2.0
        elif demographic_data.get("median_home_value", 0) > 250000:
            score += 1.0

        # Income factors
        if demographic_data.get("median_income", 0) > 80000:
            score += 2.0
        elif demographic_data.get("median_income", 0) > 50000:
            score += 1.0

        # Homeownership rate (stability indicator)
        homeownership_rate = demographic_data.get("homeownership_rate", 0)
        if homeownership_rate > 70:
            score += 1.5
        elif homeownership_rate > 50:
            score += 1.0

        # Property characteristics
        if property_data.get("year_built", 0) > 2000:
            score += 1.0
        elif property_data.get("year_built", 0) > 1980:
            score += 0.5

        # Property size (larger generally better for families)
        if property_data.get("square_footage", 0) > 2500:
            score += 1.0
        elif property_data.get("square_footage", 0) > 1800:
            score += 0.5

        return min(score / max_score, 1.0)

    def _generate_investment_recommendations(self, address_reports: Dict) -> List[str]:
        """Generate investment recommendations from market analysis"""
        recommendations = []

        # Find highest scoring properties
        valid_reports = {
            addr: report
            for addr, report in address_reports.items()
            if "error" not in report and "investment_score" in report
        }

        if not valid_reports:
            return ["Insufficient data for investment recommendations"]

        # Sort by investment score
        sorted_properties = sorted(
            valid_reports.items(), key=lambda x: x[1]["investment_score"], reverse=True
        )

        if sorted_properties:
            best_property = sorted_properties[0]
            recommendations.append(
                f"Highest investment potential: {best_property[0]} (score: {best_property[1]['investment_score']:.2f})"
            )

        # Look for value opportunities
        avg_score = sum(
            report["investment_score"] for report in valid_reports.values()
        ) / len(valid_reports)
        undervalued = [
            addr
            for addr, report in valid_reports.items()
            if report["investment_score"] > avg_score
            and report["demographic_data"].get("median_home_value", float("inf"))
            < 350000
        ]

        if undervalued:
            recommendations.append(
                f"Potential value opportunities: {', '.join(undervalued[:3])}"
            )

        return recommendations

    def _identify_displacement_risks(self, movement_patterns: List) -> List[str]:
        """Identify displacement risk indicators from movement patterns"""
        risks = []

        high_mobility_count = len(
            [p for p in movement_patterns if p.geographic_mobility > 0.7]
        )
        if high_mobility_count > len(movement_patterns) * 0.5:
            risks.append("High resident mobility may indicate displacement pressure")

        short_tenancy = len([p for p in movement_patterns if p.stability_score < 0.4])
        if short_tenancy > len(movement_patterns) * 0.3:
            risks.append("Frequent moves suggest housing instability")

        return risks

    def _assess_gentrification_investment_timing(self, indicators: Dict) -> str:
        """Assess investment timing based on gentrification indicators"""
        risk_score = indicators["gentrification_risk_score"]

        if risk_score < 0.3:
            return "early_opportunity"  # Before gentrification
        elif risk_score < 0.6:
            return "active_gentrification"  # During gentrification
        else:
            return "post_gentrification"  # After gentrification peak

    def _identify_community_impact_risks(self, indicators: Dict) -> List[str]:
        """Identify community impact concerns"""
        concerns = []

        if indicators["gentrification_risk_score"] > 0.6:
            concerns.append("High displacement risk for existing residents")

        price_income_ratio = indicators["housing_pressure_indicators"].get(
            "price_to_income_ratio", 0
        )
        if price_income_ratio > 5:
            concerns.append("Severe housing affordability crisis")

        return concerns

    def _suggest_gentrification_monitoring(self, indicators: Dict) -> List[str]:
        """Suggest ongoing monitoring for gentrification"""
        suggestions = []

        suggestions.append("Monitor rent increases and property value appreciation")
        suggestions.append("Track business changes and new development permits")

        if indicators["population_mobility"]["average_mobility"] > 0.5:
            suggestions.append("Monitor resident displacement and demographic shifts")

        return suggestions

    def _identify_business_occupants(self, residents: List) -> List[Dict]:
        """Identify business occupants from resident data"""
        businesses = []

        for resident in residents:
            # Look for business-like names or relationships
            if resident.name and any(
                indicator in resident.name.lower()
                for indicator in ["llc", "inc", "corp", "company", "business"]
            ):
                businesses.append(
                    {
                        "name": resident.name,
                        "relationship": resident.relationship_to_property,
                        "confidence": resident.confidence_score,
                    }
                )

        return businesses

    def _assess_commercial_stability(self, historical_residents: List) -> str:
        """Assess commercial tenant stability"""
        return self._calculate_turnover_risk([], historical_residents)

    def _analyze_industry_composition(self, residents: List) -> Dict[str, int]:
        """Analyze industry composition of business occupants"""
        # This is a simplified analysis - in practice would use more sophisticated
        # business classification
        industries = {}

        for resident in residents:
            if resident.name:
                name_lower = resident.name.lower()
                if any(word in name_lower for word in ["tech", "software", "digital"]):
                    industries["technology"] = industries.get("technology", 0) + 1
                elif any(
                    word in name_lower for word in ["medical", "health", "dental"]
                ):
                    industries["healthcare"] = industries.get("healthcare", 0) + 1
                elif any(word in name_lower for word in ["law", "legal", "attorney"]):
                    industries["legal"] = industries.get("legal", 0) + 1
                else:
                    industries["other"] = industries.get("other", 0) + 1

        return industries

    def _identify_zoning_from_property(self, report) -> str:
        """Identify likely zoning from property characteristics"""
        if report.ownership_records:
            property_type = report.ownership_records[0].property_details.get(
                "property_type"
            )
            if property_type in ["commercial_office", "retail", "industrial"]:
                return "commercial"
            elif property_type in ["single_family", "multi_family"]:
                return "residential"

        return "unknown"

    def _analyze_commercial_building_features(self, report) -> Dict[str, Any]:
        """Analyze commercial building characteristics"""
        features = {}

        if report.ownership_records:
            prop_details = report.ownership_records[0].property_details
            features = {
                "square_footage": prop_details.get("square_footage"),
                "year_built": prop_details.get("year_built"),
                "property_type": prop_details.get("property_type"),
                "parking_availability": "unknown",  # Would need additional data
                "accessibility_features": "unknown",  # Would need additional data
            }

        return features

    def _estimate_consumer_spending_potential(self, demographic_profile) -> str:
        """Estimate consumer spending potential from demographics"""
        median_income = demographic_profile.income_statistics.get(
            "median_household_income", 0
        )

        if median_income > 100000:
            return "high"
        elif median_income > 60000:
            return "moderate"
        else:
            return "low"

    def _assess_business_environment(self, demographic_profile) -> str:
        """Assess business support environment"""
        employment_rate = demographic_profile.economic_indicators.get(
            "employment_rate", 0
        )
        major_employers = len(
            demographic_profile.economic_indicators.get("major_employers", [])
        )

        if employment_rate > 95 and major_employers > 2:
            return "excellent"
        elif employment_rate > 90 and major_employers > 1:
            return "good"
        else:
            return "fair"

    def _estimate_foot_traffic_potential(self, demographic_profile) -> str:
        """Estimate foot traffic potential"""
        population_density = demographic_profile.population_data.get(
            "population_density", 0
        )

        if population_density > 5000:
            return "high"
        elif population_density > 2000:
            return "moderate"
        else:
            return "low"

    def _score_commercial_location(self, report) -> float:
        """Score commercial location factors (0-1)"""
        score = 0.5  # Base score

        # Address verification adds to location quality
        if (
            report.verification_status
            and report.verification_status.get("verification_level") == "confirmed"
        ):
            score += 0.2

        # Property characteristics
        if report.ownership_records:
            prop_details = report.ownership_records[0].property_details
            if prop_details.get("square_footage", 0) > 3000:
                score += 0.15
            if prop_details.get("year_built", 0) > 1990:
                score += 0.15

        return min(score, 1.0)

    def _score_market_demand(self, market_factors: Dict) -> float:
        """Score market demand factors (0-1)"""
        score = 0.0

        # Population density
        pop_density = market_factors.get("population_density", 0)
        if pop_density > 5000:
            score += 0.3
        elif pop_density > 2000:
            score += 0.2
        else:
            score += 0.1

        # Income levels
        median_income = market_factors.get("median_income", 0)
        if median_income > 80000:
            score += 0.3
        elif median_income > 50000:
            score += 0.2
        else:
            score += 0.1

        # Employment rate
        employment_rate = market_factors.get("employment_rate", 0)
        if employment_rate > 95:
            score += 0.2
        elif employment_rate > 90:
            score += 0.15
        else:
            score += 0.1

        # Major employers presence
        major_employers = len(market_factors.get("major_employers", []))
        if major_employers > 3:
            score += 0.2
        elif major_employers > 1:
            score += 0.15
        else:
            score += 0.1

        return min(score, 1.0)

    def _assess_commercial_competition(self, report) -> str:
        """Assess commercial competition level"""
        # This would require additional data about nearby businesses
        # For demo, return placeholder
        business_count = len(
            self._identify_business_occupants(report.current_residents)
        )

        if business_count > 3:
            return "high_competition"
        elif business_count > 1:
            return "moderate_competition"
        else:
            return "low_competition"

    def _recommend_business_types(self, commercial_analysis: Dict) -> List[str]:
        """Recommend suitable business types"""
        recommendations = []

        market_factors = commercial_analysis["market_factors"]
        median_income = market_factors.get("median_income", 0)
        pop_density = market_factors.get("population_density", 0)

        if median_income > 80000:
            recommendations.extend(
                ["Professional services", "High-end retail", "Restaurants"]
            )

        if pop_density > 3000:
            recommendations.extend(
                ["Coffee shops", "Convenience stores", "Personal services"]
            )

        if len(market_factors.get("major_employers", [])) > 2:
            recommendations.extend(
                ["Business services", "Lunch restaurants", "Office supplies"]
            )

        return recommendations[:5]  # Limit to top 5


# Example usage and demonstrations
def run_real_estate_examples():
    """
    Run example scenarios to demonstrate AddressSearchAgent capabilities
    """
    print("=== Real Estate Intelligence Service Examples ===\\n")

    # Initialize service
    service = RealEstateIntelligenceService()

    # Example addresses for demonstration
    sample_addresses = [
        "123 Maple Street, Suburbia, TX 75001",
        "456 Oak Lane, Metropolitan City, NY 10025",
        "789 Pine Avenue, Coastal Town, CA 90210",
        "321 Commerce Boulevard, Business District, IL 60601",
    ]

    print("1. Property Due Diligence Example")
    print("-" * 40)
    try:
        due_diligence = service.property_due_diligence(sample_addresses[0])
        print(f"Address: {due_diligence['property_address']}")
        print(f"Confidence: {due_diligence['overall_confidence']:.2f}")
        print(f"Risk Level: {due_diligence['risk_assessment']['risk_level']}")
        print(f"Occupancy Type: {due_diligence['current_occupancy']['occupancy_type']}")
    except Exception as e:
        print(f"Due diligence example failed: {e}")

    print("\\n2. Rental Property Screening Example")
    print("-" * 40)
    try:
        rental_screening = service.rental_property_screening(
            sample_addresses[1], prospective_tenant="John Smith"
        )
        print(f"Property: {rental_screening['property_address']}")
        print(
            f"Currently Occupied: {rental_screening['property_status']['currently_occupied']}"
        )
        print(f"Turnover Rate: {rental_screening['rental_history']['turnover_rate']}")
    except Exception as e:
        print(f"Rental screening example failed: {e}")

    print("\\n3. Market Analysis Example")
    print("-" * 40)
    try:
        market_analysis = service.market_analysis_by_address(sample_addresses[:3])
        print(f"Properties Analyzed: {market_analysis['properties_analyzed']}")
        print(f"Successful Analyses: {market_analysis['successful_analyses']}")
        if market_analysis["market_comparison"]["median_home_value_range"]["avg"]:
            print(
                f"Average Home Value: ${market_analysis['market_comparison']['median_home_value_range']['avg']:,.0f}"
            )
    except Exception as e:
        print(f"Market analysis example failed: {e}")

    print("\\n4. Gentrification Analysis Example")
    print("-" * 40)
    try:
        gentrification = service.neighborhood_gentrification_analysis(
            sample_addresses[1]
        )
        print(f"Address: {gentrification['address_analyzed']}")
        print(f"Gentrification Risk: {gentrification['risk_level']}")
        print(f"Risk Score: {gentrification['gentrification_risk_score']:.2f}")
    except Exception as e:
        print(f"Gentrification analysis example failed: {e}")

    print("\\n5. Commercial Real Estate Intelligence Example")
    print("-" * 40)
    try:
        commercial = service.commercial_real_estate_intelligence(sample_addresses[3])
        print(f"Property: {commercial['property_address']}")
        print(
            f"Is Commercial: {commercial['property_classification']['is_commercial']}"
        )
        if commercial["investment_potential"]["overall_investment_rating"]:
            print(
                f"Investment Rating: {commercial['investment_potential']['overall_investment_rating']:.2f}"
            )
    except Exception as e:
        print(f"Commercial analysis example failed: {e}")

    print("\\n=== Examples Complete ===")


# Save example results to files
def save_example_outputs():
    """Save example outputs to JSON files for reference"""
    service = RealEstateIntelligenceService()

    examples_dir = Path("examples/real_estate_outputs")
    examples_dir.mkdir(parents=True, exist_ok=True)

    sample_address = "123 Main Street, Example City, NY 12345"

    try:
        # Due diligence example
        due_diligence = service.property_due_diligence(sample_address)
        with open(examples_dir / "due_diligence_example.json", "w") as f:
            json.dump(due_diligence, f, indent=2, default=str)

        # Rental screening example
        rental = service.rental_property_screening(sample_address, "John Doe")
        with open(examples_dir / "rental_screening_example.json", "w") as f:
            json.dump(rental, f, indent=2, default=str)

        # Market analysis example
        market = service.market_analysis_by_address([sample_address])
        with open(examples_dir / "market_analysis_example.json", "w") as f:
            json.dump(market, f, indent=2, default=str)

        # Gentrification analysis example
        gentrification = service.neighborhood_gentrification_analysis(sample_address)
        with open(examples_dir / "gentrification_analysis_example.json", "w") as f:
            json.dump(gentrification, f, indent=2, default=str)

        # Commercial analysis example
        commercial = service.commercial_real_estate_intelligence(sample_address)
        with open(examples_dir / "commercial_analysis_example.json", "w") as f:
            json.dump(commercial, f, indent=2, default=str)

        print(f"Example outputs saved to {examples_dir}")

    except Exception as e:
        print(f"Failed to save examples: {e}")


if __name__ == "__main__":
    """
    Run the real estate examples if this file is executed directly
    """
    print("AddressSearchAgent Real Estate Use Case Examples")
    print("=" * 50)
    print()

    # Run the examples
    run_real_estate_examples()

    # Save outputs
    print("\\nSaving example outputs...")
    save_example_outputs()
