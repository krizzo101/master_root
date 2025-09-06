"""
Business Due Diligence Workflow Examples
Demonstrates comprehensive business intelligence workflows using BusinessSearchAgent
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

from src.agents.business_search_agent import BusinessSearchAgent
from src.agents.person_search_agent import PersonSearchAgent
from src.models.business import BusinessProfile
from src.models.query import BusinessSearchQuery


class BusinessDueDiligenceWorkflow:
    """
    Comprehensive business due diligence workflow automation

    This class demonstrates how to use BusinessSearchAgent for various
    due diligence scenarios including vendor verification, partnership
    analysis, and investment screening.
    """

    def __init__(self):
        self.business_agent = BusinessSearchAgent()
        self.person_agent = PersonSearchAgent()

        # Configure business agent to work with person agent
        self.business_agent.person_search_agent = self.person_agent

    async def vendor_verification_workflow(
        self, vendor_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Complete vendor verification workflow

        Args:
            vendor_info: Dict with vendor details (name, address, contact info)

        Returns:
            Comprehensive vendor verification report
        """
        print(
            f"🔍 Starting vendor verification for: {vendor_info.get('name', 'Unknown')}"
        )

        try:
            # Step 1: Basic business search and verification
            business_results = self.business_agent.search_by_name(
                business_name=vendor_info["name"],
                city=vendor_info.get("city"),
                state=vendor_info.get("state"),
            )

            if not business_results:
                return {
                    "status": "failed",
                    "reason": "Business not found in databases",
                    "risk_level": "high",
                    "recommendations": [
                        "Verify business registration independently",
                        "Request additional documentation",
                    ],
                }

            vendor_profile = business_results[0]
            print(f"✅ Business found: {vendor_profile.business_name}")

            # Step 2: Entity verification
            verification = self.business_agent.verify_business_entity(
                vendor_profile.business_name,
                vendor_profile.registration.federal_ein
                if vendor_profile.registration
                else None,
            )
            print(
                f"📋 Entity verification: {'PASSED' if verification['verified'] else 'FAILED'}"
            )

            # Step 3: Risk assessment
            risk_assessment = self.business_agent.assess_business_risk(vendor_profile)
            print(f"⚠️ Risk level: {risk_assessment['risk_level'].upper()}")

            # Step 4: Compliance check
            compliance = self.business_agent._check_compliance_status(vendor_profile)
            print(f"📜 Compliance status: {compliance['status'].upper()}")

            # Step 5: Principal verification (if needed for high-value vendors)
            principals_verified = []
            if vendor_info.get("verify_principals", False):
                principals = self.business_agent.identify_principals(vendor_profile)
                for principal in principals[:3]:  # Verify top 3 principals
                    person_results = self.person_agent.search_by_name(
                        first_name=principal.name.first, last_name=principal.name.last
                    )
                    principals_verified.append(
                        {
                            "name": principal.name.display_name,
                            "title": principal.title,
                            "verified": len(person_results) > 0,
                            "confidence": person_results[0].confidence_score
                            if person_results
                            else 0.0,
                        }
                    )

                print(f"👥 Verified {len(principals_verified)} principals")

            # Step 6: Generate comprehensive report
            report = {
                "vendor_name": vendor_profile.business_name,
                "verification_status": "PASSED"
                if verification["verified"]
                else "FAILED",
                "risk_level": risk_assessment["risk_level"],
                "compliance_status": compliance["status"],
                "overall_score": self._calculate_vendor_score(
                    verification, risk_assessment, compliance
                ),
                "business_details": {
                    "entity_type": vendor_profile.entity_type.value,
                    "status": vendor_profile.registration.status.value
                    if vendor_profile.registration
                    else "unknown",
                    "years_in_business": vendor_profile.years_in_business,
                    "employees": vendor_profile.financial_data.employee_count
                    if vendor_profile.financial_data
                    else None,
                    "locations": len(vendor_profile.locations),
                    "phone": vendor_profile.primary_phone.formatted
                    if vendor_profile.primary_phone
                    else None,
                    "address": vendor_profile.primary_location.address.full_address
                    if vendor_profile.primary_location
                    else None,
                },
                "risk_factors": risk_assessment["risk_factors"],
                "positive_indicators": risk_assessment["positive_indicators"],
                "principals_verified": principals_verified,
                "recommendations": self._generate_vendor_recommendations(
                    verification, risk_assessment, compliance
                ),
                "report_date": datetime.utcnow().isoformat(),
                "data_confidence": vendor_profile.confidence_score,
            }

            print(
                f"📊 Vendor verification completed - Overall score: {report['overall_score']}/100"
            )
            return report

        except Exception as e:
            print(f"❌ Vendor verification failed: {e}")
            return {
                "status": "error",
                "reason": f"Verification process failed: {e}",
                "risk_level": "unknown",
            }

    def partnership_analysis_workflow(
        self, partner_companies: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze potential business partners for strategic partnerships

        Args:
            partner_companies: List of company names to analyze

        Returns:
            Partnership analysis report with rankings and recommendations
        """
        print(f"🤝 Analyzing {len(partner_companies)} potential partners")

        partner_analyses = []

        for company_name in partner_companies:
            print(f"\n📈 Analyzing: {company_name}")

            try:
                # Search for the company
                results = self.business_agent.search_by_name(company_name)

                if not results:
                    partner_analyses.append(
                        {
                            "company_name": company_name,
                            "found": False,
                            "partnership_score": 0,
                            "reason": "Company not found",
                        }
                    )
                    continue

                company = results[0]

                # Comprehensive analysis
                due_diligence = self.business_agent.conduct_due_diligence(company_name)
                relationships = self.business_agent.map_business_relationships(company)

                # Calculate partnership compatibility score
                partnership_score = self._calculate_partnership_score(
                    company, due_diligence
                )

                analysis = {
                    "company_name": company.business_name,
                    "found": True,
                    "partnership_score": partnership_score,
                    "financial_stability": self._assess_financial_stability(company),
                    "market_reputation": self._assess_market_reputation(company),
                    "operational_capacity": self._assess_operational_capacity(company),
                    "risk_factors": due_diligence["risk_assessment"]["risk_factors"],
                    "growth_indicators": self._identify_growth_indicators(company),
                    "strategic_fit": self._analyze_strategic_fit(company),
                    "key_personnel": [
                        {"name": p.name.display_name, "title": p.title}
                        for p in company.current_principals[:5]
                    ],
                }

                partner_analyses.append(analysis)
                print(f"   Partnership Score: {partnership_score}/100")

            except Exception as e:
                print(f"   ❌ Analysis failed: {e}")
                partner_analyses.append(
                    {
                        "company_name": company_name,
                        "found": False,
                        "partnership_score": 0,
                        "reason": f"Analysis error: {e}",
                    }
                )

        # Rank partners by score
        successful_analyses = [p for p in partner_analyses if p["found"]]
        successful_analyses.sort(key=lambda x: x["partnership_score"], reverse=True)

        report = {
            "total_companies_analyzed": len(partner_companies),
            "successful_analyses": len(successful_analyses),
            "top_partners": successful_analyses[:5],  # Top 5 candidates
            "all_analyses": partner_analyses,
            "recommendations": self._generate_partnership_recommendations(
                successful_analyses
            ),
            "analysis_date": datetime.utcnow().isoformat(),
        }

        print(
            f"\n🏆 Top partner: {successful_analyses[0]['company_name']} (Score: {successful_analyses[0]['partnership_score']})"
        )
        return report

    def investment_screening_workflow(
        self, target_company: str, investment_type: str = "acquisition"
    ) -> Dict[str, Any]:
        """
        Comprehensive investment/acquisition screening workflow

        Args:
            target_company: Company name to screen
            investment_type: Type of investment (acquisition, partnership, investment)

        Returns:
            Investment screening report with recommendation
        """
        print(f"💰 Investment screening for: {target_company}")
        print(f"   Investment type: {investment_type}")

        try:
            # Step 1: Find and verify the target company
            results = self.business_agent.search_by_name(target_company)

            if not results:
                return {
                    "recommendation": "DO NOT PROCEED",
                    "reason": "Target company not found in business databases",
                    "risk_level": "critical",
                }

            target = results[0]
            print(f"✅ Target found: {target.business_name}")

            # Step 2: Comprehensive due diligence
            due_diligence = self.business_agent.conduct_due_diligence(target_company)

            # Step 3: Deep principal analysis
            principals = self.business_agent.identify_principals(target)
            principal_backgrounds = []

            for principal in principals[:5]:  # Analyze top 5 principals
                person_results = self.person_agent.search_by_name(
                    first_name=principal.name.first, last_name=principal.name.last
                )

                if person_results:
                    person_profile = person_results[0]
                    principal_backgrounds.append(
                        {
                            "name": principal.name.display_name,
                            "title": principal.title,
                            "background_verified": True,
                            "addresses": len(person_profile.addresses),
                            "associates": len(person_profile.associates),
                            "confidence": person_profile.confidence_score,
                        }
                    )
                else:
                    principal_backgrounds.append(
                        {
                            "name": principal.name.display_name,
                            "title": principal.title,
                            "background_verified": False,
                            "confidence": 0.0,
                        }
                    )

            # Step 4: Financial health assessment
            financial_health = self._assess_financial_health_comprehensive(target)

            # Step 5: Legal and compliance deep dive
            legal_analysis = self._analyze_legal_standing(target, due_diligence)

            # Step 6: Market position analysis
            market_analysis = self._analyze_market_position(target)

            # Step 7: Investment recommendation
            investment_score = self._calculate_investment_score(
                target, due_diligence, financial_health, legal_analysis, market_analysis
            )

            recommendation = self._generate_investment_recommendation(
                investment_score, investment_type
            )

            report = {
                "target_company": target.business_name,
                "investment_type": investment_type,
                "recommendation": recommendation["decision"],
                "investment_score": investment_score,
                "confidence_level": recommendation["confidence"],
                "key_findings": {
                    "financial_health": financial_health,
                    "legal_standing": legal_analysis,
                    "market_position": market_analysis,
                    "management_team": principal_backgrounds,
                    "business_fundamentals": {
                        "entity_type": target.entity_type.value,
                        "years_in_business": target.years_in_business,
                        "active_status": target.is_active,
                        "locations": len(target.locations),
                        "compliance_status": due_diligence["compliance_check"][
                            "status"
                        ],
                    },
                },
                "risk_analysis": due_diligence["risk_assessment"],
                "deal_considerations": recommendation["considerations"],
                "next_steps": recommendation["next_steps"],
                "report_date": datetime.utcnow().isoformat(),
                "analyst": "BusinessSearchAgent Automated Screening",
            }

            print(f"📋 Investment recommendation: {recommendation['decision']}")
            print(f"📊 Investment score: {investment_score}/100")

            return report

        except Exception as e:
            print(f"❌ Investment screening failed: {e}")
            return {
                "recommendation": "ANALYSIS FAILED",
                "reason": f"Screening process error: {e}",
                "risk_level": "unknown",
            }

    def competitor_analysis_workflow(
        self, your_company: str, competitors: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze competitors for market intelligence

        Args:
            your_company: Your company name for reference
            competitors: List of competitor company names

        Returns:
            Competitive analysis report
        """
        print(
            f"🥊 Competitive analysis: {your_company} vs {len(competitors)} competitors"
        )

        # Analyze your company first
        your_profile = None
        try:
            your_results = self.business_agent.search_by_name(your_company)
            your_profile = your_results[0] if your_results else None
            print(f"📊 Your company baseline: {your_company}")
        except Exception as e:
            print(f"⚠️ Could not analyze your company: {e}")

        # Analyze competitors
        competitor_analyses = []

        for competitor in competitors:
            print(f"\n🔍 Analyzing competitor: {competitor}")

            try:
                results = self.business_agent.search_by_name(competitor)

                if not results:
                    competitor_analyses.append(
                        {
                            "company_name": competitor,
                            "found": False,
                            "threat_level": "unknown",
                        }
                    )
                    continue

                comp_profile = results[0]

                # Competitive threat assessment
                threat_assessment = self._assess_competitive_threat(
                    comp_profile, your_profile
                )

                analysis = {
                    "company_name": comp_profile.business_name,
                    "found": True,
                    "threat_level": threat_assessment["level"],
                    "threat_score": threat_assessment["score"],
                    "size_comparison": self._compare_company_size(
                        comp_profile, your_profile
                    ),
                    "market_presence": self._assess_market_presence(comp_profile),
                    "strengths": threat_assessment["strengths"],
                    "weaknesses": threat_assessment["weaknesses"],
                    "key_personnel": [
                        p.name.display_name for p in comp_profile.current_principals[:3]
                    ],
                    "business_age": comp_profile.years_in_business,
                    "locations": len(comp_profile.locations),
                }

                competitor_analyses.append(analysis)
                print(f"   Threat level: {threat_assessment['level']}")

            except Exception as e:
                print(f"   ❌ Analysis failed: {e}")
                competitor_analyses.append(
                    {
                        "company_name": competitor,
                        "found": False,
                        "threat_level": "unknown",
                        "error": str(e),
                    }
                )

        # Generate competitive landscape report
        successful_analyses = [c for c in competitor_analyses if c.get("found", False)]
        successful_analyses.sort(key=lambda x: x.get("threat_score", 0), reverse=True)

        report = {
            "your_company": your_company if your_profile else "Analysis unavailable",
            "competitors_analyzed": len(competitors),
            "successful_analyses": len(successful_analyses),
            "competitive_landscape": {
                "high_threat": [
                    c for c in successful_analyses if c["threat_level"] == "high"
                ],
                "medium_threat": [
                    c for c in successful_analyses if c["threat_level"] == "medium"
                ],
                "low_threat": [
                    c for c in successful_analyses if c["threat_level"] == "low"
                ],
            },
            "market_insights": self._generate_market_insights(
                successful_analyses, your_profile
            ),
            "strategic_recommendations": self._generate_competitive_recommendations(
                successful_analyses
            ),
            "analysis_date": datetime.utcnow().isoformat(),
        }

        print(
            f"\n🏆 Analysis complete - {len(report['competitive_landscape']['high_threat'])} high-threat competitors identified"
        )
        return report

    # Helper methods for scoring and analysis

    def _calculate_vendor_score(
        self, verification: Dict, risk: Dict, compliance: Dict
    ) -> int:
        """Calculate overall vendor score (0-100)"""
        score = 50  # Base score

        # Verification bonus/penalty
        if verification["verified"]:
            score += 30
        else:
            score -= 20

        # Risk adjustments
        risk_penalties = {"low": 0, "moderate": -10, "high": -25, "critical": -40}
        score += risk_penalties.get(risk["risk_level"], -10)

        # Compliance adjustments
        compliance_bonus = {"compliant": 20, "minor_issues": 10, "non_compliant": -20}
        score += compliance_bonus.get(compliance["status"], 0)

        return max(0, min(100, score))

    def _generate_vendor_recommendations(
        self, verification: Dict, risk: Dict, compliance: Dict
    ) -> List[str]:
        """Generate vendor-specific recommendations"""
        recommendations = []

        if not verification["verified"]:
            recommendations.append(
                "CRITICAL: Business entity verification failed - request official registration documents"
            )

        if risk["risk_level"] in ["high", "critical"]:
            recommendations.append(
                "HIGH RISK: Enhanced due diligence required before engagement"
            )
            recommendations.append(
                "Consider requiring additional insurance or guarantees"
            )

        if compliance["status"] == "non_compliant":
            recommendations.append(
                "Compliance issues detected - verify current licensing status"
            )

        if len(recommendations) == 0:
            recommendations.append(
                "Vendor passes initial screening - proceed with standard onboarding"
            )

        return recommendations

    def _calculate_partnership_score(
        self, company: BusinessProfile, due_diligence: Dict
    ) -> int:
        """Calculate partnership compatibility score"""
        score = 50  # Base score

        # Business stability
        if company.years_in_business and company.years_in_business > 5:
            score += 15

        # Active status
        if company.is_active:
            score += 10

        # Risk factors
        risk_level = due_diligence["risk_assessment"]["risk_level"]
        risk_adjustments = {"low": 20, "moderate": 5, "high": -15, "critical": -30}
        score += risk_adjustments.get(risk_level, 0)

        # Financial indicators
        if company.financial_data and company.financial_data.employee_count:
            if company.financial_data.employee_count > 10:
                score += 10

        return max(0, min(100, score))

    def _assess_financial_stability(self, company: BusinessProfile) -> str:
        """Assess financial stability"""
        if not company.financial_data:
            return "insufficient_data"

        indicators = []

        if company.financial_data.bankruptcy_filed:
            indicators.append("bankruptcy_history")

        if company.financial_data.liens:
            indicators.append("tax_liens")

        if len(indicators) == 0:
            return "stable"
        elif len(indicators) == 1:
            return "moderate_risk"
        else:
            return "high_risk"

    def _assess_market_reputation(self, company: BusinessProfile) -> str:
        """Assess market reputation"""
        # Basic assessment based on business age and status
        if (
            company.years_in_business
            and company.years_in_business > 10
            and company.is_active
        ):
            return "established"
        elif company.years_in_business and company.years_in_business > 3:
            return "developing"
        else:
            return "emerging"

    def _assess_operational_capacity(self, company: BusinessProfile) -> str:
        """Assess operational capacity"""
        capacity_score = 0

        if len(company.locations) > 1:
            capacity_score += 1

        if company.financial_data and company.financial_data.employee_count:
            if company.financial_data.employee_count > 50:
                capacity_score += 2
            elif company.financial_data.employee_count > 10:
                capacity_score += 1

        if len(company.current_principals) > 2:
            capacity_score += 1

        if capacity_score >= 3:
            return "high"
        elif capacity_score >= 1:
            return "medium"
        else:
            return "limited"

    def _identify_growth_indicators(self, company: BusinessProfile) -> List[str]:
        """Identify growth indicators"""
        indicators = []

        if company.years_in_business and company.years_in_business < 5:
            indicators.append("young_company")

        if len(company.locations) > 1:
            indicators.append("multi_location")

        if company.financial_data and company.financial_data.employee_count:
            if company.financial_data.employee_count > 25:
                indicators.append("significant_workforce")

        return indicators

    def _analyze_strategic_fit(self, company: BusinessProfile) -> str:
        """Analyze strategic fit (simplified)"""
        # This would be customized based on your business needs
        if (
            company.is_active
            and company.years_in_business
            and company.years_in_business > 2
        ):
            return "good_fit"
        else:
            return "limited_fit"

    def _generate_partnership_recommendations(self, analyses: List[Dict]) -> List[str]:
        """Generate partnership recommendations"""
        if not analyses:
            return ["No suitable partners found"]

        top_score = analyses[0]["partnership_score"]
        recommendations = []

        if top_score > 75:
            recommendations.append(
                "Excellent partnership candidates identified - proceed with detailed negotiations"
            )
        elif top_score > 50:
            recommendations.append(
                "Good partnership opportunities - conduct deeper due diligence"
            )
        else:
            recommendations.append(
                "Limited partnership options - consider expanding search criteria"
            )

        return recommendations

    def _assess_financial_health_comprehensive(
        self, company: BusinessProfile
    ) -> Dict[str, Any]:
        """Comprehensive financial health assessment"""
        health = {"overall_rating": "unknown", "indicators": [], "concerns": []}

        if not company.financial_data:
            health["overall_rating"] = "insufficient_data"
            return health

        # Positive indicators
        if (
            company.financial_data.employee_count
            and company.financial_data.employee_count > 20
        ):
            health["indicators"].append("stable_workforce")

        if not company.financial_data.bankruptcy_filed:
            health["indicators"].append("no_bankruptcy_history")

        # Concerns
        if company.financial_data.bankruptcy_filed:
            health["concerns"].append("bankruptcy_history")

        if company.financial_data.liens:
            health["concerns"].append("tax_liens_present")

        # Overall rating
        if len(health["concerns"]) == 0:
            health["overall_rating"] = "healthy"
        elif len(health["concerns"]) == 1:
            health["overall_rating"] = "moderate_risk"
        else:
            health["overall_rating"] = "high_risk"

        return health

    def _analyze_legal_standing(
        self, company: BusinessProfile, due_diligence: Dict
    ) -> Dict[str, Any]:
        """Analyze legal standing"""
        legal = {"status": "unknown", "issues": [], "compliance_rating": "unknown"}

        # Registration status
        if company.registration and company.registration.status.value == "active":
            legal["status"] = "good_standing"
        else:
            legal["status"] = "issues_detected"
            legal["issues"].append("registration_status_concern")

        # Compliance from due diligence
        compliance_status = due_diligence.get("compliance_check", {}).get(
            "status", "unknown"
        )
        legal["compliance_rating"] = compliance_status

        if compliance_status == "non_compliant":
            legal["issues"].append("compliance_violations")

        return legal

    def _analyze_market_position(self, company: BusinessProfile) -> Dict[str, Any]:
        """Analyze market position"""
        position = {"strength": "unknown", "factors": []}

        # Business age indicates market presence
        if company.years_in_business:
            if company.years_in_business > 10:
                position["factors"].append("established_presence")
                position["strength"] = "strong"
            elif company.years_in_business > 3:
                position["factors"].append("developing_presence")
                position["strength"] = "moderate"
            else:
                position["factors"].append("new_entrant")
                position["strength"] = "emerging"

        # Multi-location indicates market reach
        if len(company.locations) > 2:
            position["factors"].append("multi_location_presence")

        return position

    def _calculate_investment_score(
        self,
        company: BusinessProfile,
        due_diligence: Dict,
        financial: Dict,
        legal: Dict,
        market: Dict,
    ) -> int:
        """Calculate investment attractiveness score"""
        score = 50  # Base score

        # Financial health impact
        financial_ratings = {
            "healthy": 25,
            "moderate_risk": 10,
            "high_risk": -20,
            "insufficient_data": 0,
        }
        score += financial_ratings.get(financial["overall_rating"], 0)

        # Legal standing impact
        if legal["status"] == "good_standing":
            score += 15
        else:
            score -= 10

        # Risk assessment impact
        risk_level = due_diligence["risk_assessment"]["risk_level"]
        risk_impact = {"low": 15, "moderate": 5, "high": -20, "critical": -35}
        score += risk_impact.get(risk_level, 0)

        # Market position impact
        market_impact = {"strong": 15, "moderate": 5, "emerging": 0, "unknown": -5}
        score += market_impact.get(market["strength"], 0)

        # Business fundamentals
        if company.is_active:
            score += 10

        if company.years_in_business and company.years_in_business > 5:
            score += 10

        return max(0, min(100, score))

    def _generate_investment_recommendation(
        self, score: int, investment_type: str
    ) -> Dict[str, Any]:
        """Generate investment recommendation"""
        if score >= 80:
            decision = "STRONGLY RECOMMEND"
            confidence = "high"
        elif score >= 65:
            decision = "RECOMMEND WITH CONDITIONS"
            confidence = "medium"
        elif score >= 45:
            decision = "PROCEED WITH CAUTION"
            confidence = "low"
        else:
            decision = "DO NOT RECOMMEND"
            confidence = "high"

        considerations = []
        next_steps = []

        if score >= 65:
            considerations.append("Strong fundamentals identified")
            next_steps.append("Proceed to detailed financial analysis")
            next_steps.append("Conduct management interviews")
        elif score >= 45:
            considerations.append("Mixed indicators - thorough due diligence required")
            next_steps.append("Address identified risk factors")
            next_steps.append("Seek additional documentation")
        else:
            considerations.append("Significant risks identified")
            next_steps.append("Consider alternative targets")

        return {
            "decision": decision,
            "confidence": confidence,
            "considerations": considerations,
            "next_steps": next_steps,
        }

    def _assess_competitive_threat(
        self, competitor: BusinessProfile, your_company: BusinessProfile
    ) -> Dict[str, Any]:
        """Assess competitive threat level"""
        threat = {"level": "unknown", "score": 50, "strengths": [], "weaknesses": []}

        # Size comparison
        if competitor.financial_data and your_company and your_company.financial_data:
            if (
                competitor.financial_data.employee_count
                > your_company.financial_data.employee_count * 2
            ):
                threat["strengths"].append("significantly_larger")
                threat["score"] += 20

        # Market presence
        if len(competitor.locations) > 3:
            threat["strengths"].append("wide_geographic_presence")
            threat["score"] += 15

        # Business stability
        if competitor.years_in_business and competitor.years_in_business > 10:
            threat["strengths"].append("established_market_presence")
            threat["score"] += 10

        # Potential weaknesses
        if not competitor.is_active:
            threat["weaknesses"].append("inactive_status")
            threat["score"] -= 20

        # Determine threat level
        if threat["score"] >= 75:
            threat["level"] = "high"
        elif threat["score"] >= 55:
            threat["level"] = "medium"
        else:
            threat["level"] = "low"

        return threat

    def _compare_company_size(
        self, competitor: BusinessProfile, your_company: BusinessProfile
    ) -> str:
        """Compare company sizes"""
        if (
            not your_company
            or not competitor.financial_data
            or not your_company.financial_data
        ):
            return "unknown"

        comp_employees = competitor.financial_data.employee_count or 0
        your_employees = your_company.financial_data.employee_count or 0

        if comp_employees > your_employees * 2:
            return "much_larger"
        elif comp_employees > your_employees * 1.2:
            return "larger"
        elif comp_employees < your_employees * 0.5:
            return "much_smaller"
        elif comp_employees < your_employees * 0.8:
            return "smaller"
        else:
            return "similar_size"

    def _assess_market_presence(self, company: BusinessProfile) -> str:
        """Assess market presence"""
        presence_score = 0

        if company.years_in_business and company.years_in_business > 10:
            presence_score += 2
        elif company.years_in_business and company.years_in_business > 5:
            presence_score += 1

        if len(company.locations) > 2:
            presence_score += 2
        elif len(company.locations) > 1:
            presence_score += 1

        if company.website:
            presence_score += 1

        if presence_score >= 4:
            return "strong"
        elif presence_score >= 2:
            return "moderate"
        else:
            return "limited"

    def _generate_market_insights(
        self, competitors: List[Dict], your_company: BusinessProfile
    ) -> List[str]:
        """Generate market insights"""
        insights = []

        if len(competitors) == 0:
            insights.append("Limited competitive intelligence available")
            return insights

        # Average company age
        ages = [c.get("business_age", 0) for c in competitors if c.get("business_age")]
        if ages:
            avg_age = sum(ages) / len(ages)
            insights.append(f"Average competitor age: {avg_age:.1f} years")

        # Threat distribution
        high_threat = len([c for c in competitors if c.get("threat_level") == "high"])
        if high_threat > 0:
            insights.append(f"{high_threat} high-threat competitors identified")

        # Market consolidation
        large_competitors = len(
            [
                c
                for c in competitors
                if c.get("size_comparison") in ["much_larger", "larger"]
            ]
        )
        if large_competitors > len(competitors) * 0.5:
            insights.append("Market appears dominated by larger players")

        return insights

    def _generate_competitive_recommendations(
        self, competitors: List[Dict]
    ) -> List[str]:
        """Generate competitive strategy recommendations"""
        recommendations = []

        high_threat = [c for c in competitors if c.get("threat_level") == "high"]

        if len(high_threat) > 2:
            recommendations.append(
                "Highly competitive market - focus on differentiation strategies"
            )
            recommendations.append(
                "Monitor high-threat competitors closely for strategic moves"
            )

        if len(competitors) < 3:
            recommendations.append(
                "Limited competition detected - opportunity for market expansion"
            )

        # Size-based recommendations
        larger_competitors = [
            c
            for c in competitors
            if c.get("size_comparison") in ["much_larger", "larger"]
        ]
        if len(larger_competitors) > len(competitors) * 0.6:
            recommendations.append(
                "Consider niche market strategies to compete with larger players"
            )

        return recommendations


# Example usage and demonstration
async def main():
    """Demonstrate the due diligence workflows"""
    workflow = BusinessDueDiligenceWorkflow()

    print("🚀 Business Due Diligence Workflow Examples\n")
    print("=" * 60)

    # Example 1: Vendor Verification
    print("\n📋 EXAMPLE 1: Vendor Verification Workflow")
    vendor_info = {
        "name": "Acme Technology Solutions",
        "city": "San Francisco",
        "state": "CA",
        "verify_principals": True,
    }

    vendor_report = await workflow.vendor_verification_workflow(vendor_info)
    print(f"\nVendor Report Summary:")
    print(f"Status: {vendor_report.get('verification_status', 'Unknown')}")
    print(f"Risk Level: {vendor_report.get('risk_level', 'Unknown')}")
    print(f"Overall Score: {vendor_report.get('overall_score', 0)}/100")

    # Example 2: Partnership Analysis
    print(f"\n{'-' * 60}")
    print("🤝 EXAMPLE 2: Partnership Analysis Workflow")
    partners = [
        "Strategic Partner Corp",
        "Innovation Systems LLC",
        "Global Business Solutions",
    ]

    partnership_report = workflow.partnership_analysis_workflow(partners)
    print(f"\nPartnership Analysis Summary:")
    print(f"Companies Analyzed: {partnership_report['total_companies_analyzed']}")
    print(f"Successful Analyses: {partnership_report['successful_analyses']}")
    if partnership_report["top_partners"]:
        top_partner = partnership_report["top_partners"][0]
        print(
            f"Top Partner: {top_partner['company_name']} (Score: {top_partner['partnership_score']})"
        )

    # Example 3: Investment Screening
    print(f"\n{'-' * 60}")
    print("💰 EXAMPLE 3: Investment Screening Workflow")

    investment_report = workflow.investment_screening_workflow(
        "Target Acquisition Company", "acquisition"
    )

    print(f"\nInvestment Screening Summary:")
    print(f"Recommendation: {investment_report.get('recommendation', 'Unknown')}")
    print(f"Investment Score: {investment_report.get('investment_score', 0)}/100")
    print(f"Confidence: {investment_report.get('confidence_level', 'Unknown')}")

    # Example 4: Competitor Analysis
    print(f"\n{'-' * 60}")
    print("🥊 EXAMPLE 4: Competitor Analysis Workflow")

    competitor_report = workflow.competitor_analysis_workflow(
        "Your Company Name", ["Competitor A", "Competitor B", "Competitor C"]
    )

    print(f"\nCompetitor Analysis Summary:")
    print(f"Competitors Analyzed: {competitor_report['competitors_analyzed']}")
    high_threats = len(competitor_report["competitive_landscape"]["high_threat"])
    print(f"High-Threat Competitors: {high_threats}")

    print(f"\n{'=' * 60}")
    print("✅ All workflow examples completed successfully!")


if __name__ == "__main__":
    # Run the example workflows
    asyncio.run(main())
