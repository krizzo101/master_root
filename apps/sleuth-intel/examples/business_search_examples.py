"""
Basic Business Search Examples
Simple examples showing how to use BusinessSearchAgent for common tasks
"""

import json
from datetime import datetime

from src.agents.business_search_agent import BusinessSearchAgent
from src.models.query import BusinessSearchQuery


def basic_business_search_examples():
    """Basic business search examples"""

    # Initialize the agent
    agent = BusinessSearchAgent()

    print("🏢 BusinessSearchAgent Examples")
    print("=" * 50)

    # Example 1: Search by business name
    print("\n1️⃣ Search by Business Name")
    try:
        results = agent.search_by_name(
            business_name="Acme Corporation", city="San Francisco", state="CA"
        )

        if results:
            business = results[0]
            print(f"Found: {business.business_name}")
            print(f"Type: {business.entity_type.value}")
            print(
                f"Status: {business.registration.status.value if business.registration else 'Unknown'}"
            )
            print(f"Confidence: {business.confidence_score:.2f}")
        else:
            print("No businesses found")

    except Exception as e:
        print(f"Search failed: {e}")

    # Example 2: Search by EIN
    print("\n2️⃣ Search by EIN (Federal Tax ID)")
    try:
        results = agent.search_by_ein("12-3456789")

        if results:
            business = results[0]
            print(f"Found: {business.business_name}")
            print(
                f"EIN: {business.registration.federal_ein if business.registration else 'Unknown'}"
            )
            print(
                f"Primary Location: {business.primary_location.address.full_address if business.primary_location else 'Unknown'}"
            )
        else:
            print("No business found with that EIN")

    except Exception as e:
        print(f"EIN search failed: {e}")

    # Example 3: Search by phone number
    print("\n3️⃣ Search by Phone Number")
    try:
        results = agent.search_by_phone("(555) 123-4567")

        if results:
            business = results[0]
            print(f"Found: {business.business_name}")
            print(
                f"Phone: {business.primary_phone.formatted if business.primary_phone else 'Unknown'}"
            )
            print(f"Years in Business: {business.years_in_business or 'Unknown'}")
        else:
            print("No business found with that phone number")

    except Exception as e:
        print(f"Phone search failed: {e}")

    # Example 4: Business entity verification
    print("\n4️⃣ Business Entity Verification")
    try:
        verification = agent.verify_business_entity(
            business_name="Acme Corporation", ein="12-3456789"
        )

        print(f"Verified: {'✅ YES' if verification['verified'] else '❌ NO'}")
        print(f"Confidence: {verification['confidence']:.2f}")
        print(f"Business Name: {verification.get('business_name', 'Unknown')}")
        print(f"Entity Type: {verification.get('entity_type', 'Unknown')}")
        print(f"Status: {verification.get('status', 'Unknown')}")

    except Exception as e:
        print(f"Verification failed: {e}")


def advanced_business_intelligence_examples():
    """Advanced business intelligence examples"""

    agent = BusinessSearchAgent()

    print("\n\n🔍 Advanced Business Intelligence Examples")
    print("=" * 60)

    # Example 1: Risk Assessment
    print("\n1️⃣ Business Risk Assessment")
    try:
        results = agent.search_by_name("Target Business Corp")

        if results:
            business = results[0]
            risk_assessment = agent.assess_business_risk(business)

            print(f"Business: {business.business_name}")
            print(f"Risk Level: {risk_assessment['risk_level'].upper()}")
            print(f"Risk Score: {risk_assessment['overall_risk_score']:.2f}")

            if risk_assessment["risk_factors"]:
                print("Risk Factors:")
                for factor in risk_assessment["risk_factors"][:3]:
                    print(f"  • {factor}")

            if risk_assessment["positive_indicators"]:
                print("Positive Indicators:")
                for indicator in risk_assessment["positive_indicators"][:3]:
                    print(f"  • {indicator}")
        else:
            print("Business not found for risk assessment")

    except Exception as e:
        print(f"Risk assessment failed: {e}")

    # Example 2: Principal Identification
    print("\n2️⃣ Principal and Executive Identification")
    try:
        results = agent.search_by_name("Executive Business LLC")

        if results:
            business = results[0]
            principals = agent.identify_principals(business)

            print(f"Business: {business.business_name}")
            print(f"Principals Found: {len(principals)}")

            for principal in principals[:3]:  # Show first 3
                print(f"  • {principal.name.display_name}")
                print(f"    Title: {principal.title or 'Unknown'}")
                print(f"    Role: {principal.role or 'Unknown'}")
                print(f"    Current: {'Yes' if principal.is_current else 'No'}")
        else:
            print("Business not found for principal analysis")

    except Exception as e:
        print(f"Principal identification failed: {e}")

    # Example 3: Corporate Filing Analysis
    print("\n3️⃣ Corporate Filing Analysis")
    try:
        results = agent.search_by_name("Filing Analysis Corp")

        if results:
            business = results[0]
            filing_analysis = agent.analyze_corporate_filings(business)

            print(f"Business: {business.business_name}")
            print(f"Total Filings: {filing_analysis['total_filings']}")
            print(f"Recent Filings: {filing_analysis['recent_filings']}")
            print(f"Compliance Status: {filing_analysis['compliance_status'].upper()}")

            if filing_analysis["risk_indicators"]:
                print("Risk Indicators:")
                for indicator in filing_analysis["risk_indicators"][:3]:
                    print(f"  • {indicator['type']}: {indicator['description']}")
        else:
            print("Business not found for filing analysis")

    except Exception as e:
        print(f"Filing analysis failed: {e}")

    # Example 4: Business Relationship Mapping
    print("\n4️⃣ Business Relationship Mapping")
    try:
        results = agent.search_by_name("Connected Business Inc")

        if results:
            business = results[0]
            relationships = agent.map_business_relationships(business)

            print(f"Business: {business.business_name}")

            if relationships["parent_company"]:
                print(f"Parent Company: {relationships['parent_company']}")

            if relationships["subsidiaries"]:
                print(f"Subsidiaries: {len(relationships['subsidiaries'])}")
                for sub in relationships["subsidiaries"][:3]:
                    print(f"  • {sub}")

            print(
                f"Relationship Confidence: {relationships['relationship_confidence']:.2f}"
            )
        else:
            print("Business not found for relationship mapping")

    except Exception as e:
        print(f"Relationship mapping failed: {e}")


def comprehensive_due_diligence_example():
    """Comprehensive due diligence example"""

    agent = BusinessSearchAgent()

    print("\n\n📋 Comprehensive Due Diligence Example")
    print("=" * 60)

    try:
        # Conduct full due diligence on a business
        report = agent.conduct_due_diligence("Due Diligence Target Corp")

        if report.get("status") == "error":
            print(f"Due diligence failed: {report.get('message')}")
            return

        business_profile = report.get("business_profile", {})
        print(f"🏢 Business: {business_profile.get('business_name', 'Unknown')}")
        print(f"📊 Confidence: {report.get('data_confidence', 0):.2f}")
        print(f"📅 Report Date: {report.get('report_timestamp', 'Unknown')}")

        # Verification Results
        verification = report.get("verification", {})
        print(
            f"\n✅ Verification: {'PASSED' if verification.get('verified') else 'FAILED'}"
        )

        # Risk Assessment
        risk = report.get("risk_assessment", {})
        print(f"⚠️ Risk Level: {risk.get('risk_level', 'Unknown').upper()}")
        print(f"📈 Risk Score: {risk.get('overall_risk_score', 0):.2f}")

        # Compliance Check
        compliance = report.get("compliance_check", {})
        print(f"📜 Compliance: {compliance.get('status', 'Unknown').upper()}")

        # Key Findings
        if risk.get("risk_factors"):
            print("\n🚨 Risk Factors:")
            for factor in risk["risk_factors"][:3]:
                print(f"  • {factor}")

        if risk.get("positive_indicators"):
            print("\n✅ Positive Indicators:")
            for indicator in risk["positive_indicators"][:3]:
                print(f"  • {indicator}")

        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations[:3]:
                print(f"  • {rec}")

        # Principal Information
        principals = report.get("principals", [])
        if principals:
            print(f"\n👥 Key Personnel ({len(principals)} found):")
            for principal in principals[:3]:
                name = principal.get("name", {}).get("full") or principal.get(
                    "name", {}
                ).get("display_name", "Unknown")
                title = principal.get("title", "Unknown")
                print(f"  • {name} - {title}")

    except Exception as e:
        print(f"Due diligence failed: {e}")


def business_search_query_examples():
    """Examples using BusinessSearchQuery for advanced searches"""

    agent = BusinessSearchAgent()

    print("\n\n🔧 Advanced Query Examples")
    print("=" * 50)

    # Example 1: Comprehensive search query
    print("\n1️⃣ Comprehensive Business Search Query")
    try:
        query = BusinessSearchQuery(
            business_name="Advanced Query Corp",
            city="Los Angeles",
            state="CA",
            phone="3105551234",
            entity_type="corporation",
            include_principals=True,
            include_filings=True,
            fuzzy_matching=True,
            max_results=5,
            min_confidence=0.6,
        )

        results = agent.search(query)

        print(f"Query Parameters:")
        print(f"  • Name: {query.business_name}")
        print(f"  • Location: {query.city}, {query.state}")
        print(f"  • Include Principals: {query.include_principals}")
        print(f"  • Min Confidence: {query.min_confidence}")
        print(f"  • Max Results: {query.max_results}")

        print(f"\nResults: {len(results)} businesses found")

        for i, business in enumerate(results[:3], 1):
            print(f"\n{i}. {business.business_name}")
            print(f"   Confidence: {business.confidence_score:.2f}")
            print(f"   Type: {business.entity_type.value}")
            print(
                f"   Status: {business.registration.status.value if business.registration else 'Unknown'}"
            )

    except Exception as e:
        print(f"Advanced query failed: {e}")

    # Example 2: Industry-specific search
    print("\n2️⃣ Industry-Specific Search")
    try:
        query = BusinessSearchQuery(
            industry="technology",
            city="San Francisco",
            state="CA",
            min_employees=25,
            max_employees=100,
            entity_type="llc",
            max_results=10,
        )

        if query.has_sufficient_params():
            results = agent.search(query)
            print(f"Industry search results: {len(results)} businesses")
        else:
            print("Query lacks sufficient parameters")

    except Exception as e:
        print(f"Industry search failed: {e}")


def export_business_data_example():
    """Example of exporting business data for analysis"""

    agent = BusinessSearchAgent()

    print("\n\n📤 Business Data Export Example")
    print("=" * 50)

    try:
        # Search for multiple businesses
        business_names = [
            "Export Example Corp",
            "Data Analysis LLC",
            "Business Intel Inc",
        ]

        all_business_data = []

        for business_name in business_names:
            try:
                results = agent.search_by_name(business_name)
                if results:
                    business = results[0]
                    business_data = business.to_summary_dict()
                    business_data["search_timestamp"] = datetime.utcnow().isoformat()
                    all_business_data.append(business_data)
                    print(f"✅ Exported: {business.business_name}")
                else:
                    print(f"❌ Not found: {business_name}")

            except Exception as e:
                print(f"❌ Error with {business_name}: {e}")

        # Export to JSON format
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_businesses": len(all_business_data),
            "businesses": all_business_data,
        }

        # Pretty print the export data
        print(f"\n📊 Export Summary:")
        print(f"Total Businesses: {len(all_business_data)}")
        print(f"Export Timestamp: {export_data['export_timestamp']}")

        print(f"\n📋 Sample Export Data (First Business):")
        if all_business_data:
            sample_business = all_business_data[0]
            for key, value in sample_business.items():
                print(f"  {key}: {value}")

        # In a real scenario, you would save this to a file:
        # with open('business_export.json', 'w') as f:
        #     json.dump(export_data, f, indent=2)
        # print("Data exported to business_export.json")

    except Exception as e:
        print(f"Export failed: {e}")


def agent_health_check_example():
    """Example of agent health checking"""

    print("\n\n🏥 Agent Health Check Example")
    print("=" * 50)

    try:
        agent = BusinessSearchAgent()
        health = agent.health_check()

        print(f"Agent Status: {health.get('status', 'Unknown').upper()}")
        print(f"Agent Name: {health.get('agent_name', 'Unknown')}")
        print(f"Provider: {health.get('provider', 'Unknown')}")

        if health.get("status") == "healthy":
            print("✅ Agent is ready for business searches")

            # Display metrics if available
            metrics = health.get("metrics", {})
            if metrics:
                print(f"\n📊 Performance Metrics:")
                print(f"  Total Requests: {metrics.get('total_requests', 0)}")
                print(f"  Success Rate: {metrics.get('success_rate', 0):.1f}%")
                print(f"  Cache Hit Rate: {metrics.get('cache_hit_rate', 0):.1f}%")
                print(
                    f"  Avg Response Time: {metrics.get('average_response_time', 0):.2f}s"
                )
        else:
            print("❌ Agent has issues:")
            print(f"Error: {health.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Health check failed: {e}")


def main():
    """Run all examples"""
    print("🚀 BusinessSearchAgent Examples")
    print("=" * 80)

    try:
        basic_business_search_examples()
        advanced_business_intelligence_examples()
        comprehensive_due_diligence_example()
        business_search_query_examples()
        export_business_data_example()
        agent_health_check_example()

        print(f"\n{'=' * 80}")
        print("✅ All examples completed successfully!")
        print(
            "💡 Tip: Customize these examples for your specific business intelligence needs"
        )

    except Exception as e:
        print(f"Examples failed: {e}")


if __name__ == "__main__":
    main()
