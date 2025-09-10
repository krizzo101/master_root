"""
EmailSearchAgent Integration Examples
Demonstrates comprehensive email intelligence capabilities
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from src.agents.base_agent import CacheConfig, RateLimitConfig
from src.agents.email_search_agent import EmailSearchAgent
from src.agents.person_search_agent import PersonSearchAgent
from src.models.query import EmailLookupQuery


def setup_email_agent():
    """Setup EmailSearchAgent with production-ready configuration"""

    # Production rate limiting (conservative for API costs)
    rate_config = RateLimitConfig(
        requests_per_second=0.25,  # 4 seconds between requests
        requests_per_minute=12,
        requests_per_hour=150,
        requests_per_day=800,
        burst_size=2,
    )

    # Cache configuration for email searches
    cache_config = CacheConfig(
        enabled=True,
        ttl_seconds=1800,  # 30 minutes for email data
        max_entries=100,
        compress=True,
        cache_dir=Path("./cache/email_searches"),
    )

    return EmailSearchAgent(
        rate_limit_config=rate_config,
        cache_config=cache_config,
        enable_breach_detection=True,
        enable_social_correlation=False,  # Privacy-safe default
        enable_mx_validation=True,
    )


def example_basic_email_validation():
    """Example: Basic email format and deliverability validation"""
    print("=== Basic Email Validation Example ===")

    agent = setup_email_agent()

    test_emails = [
        "valid@example.com",
        "invalid-email",
        "test@10minutemail.com",  # Disposable
        "contact@business.com",  # Professional
        "user@gmail.com",  # Personal
    ]

    for email in test_emails:
        print(f"\nValidating: {email}")

        # Format validation
        format_result = agent.validate_email_format(email)
        print(f"  Format Valid: {format_result['is_valid']}")

        if format_result["is_valid"]:
            # Deliverability check
            delivery_result = agent.validate_email_deliverability(email)
            print(f"  Deliverable: {delivery_result['deliverable']}")

            # Classification
            classification = agent.classify_email_type(email)
            print(
                f"  Type: {classification['type']} (confidence: {classification['confidence']:.2f})"
            )
            print(f"  Indicators: {', '.join(classification['indicators'])}")
        else:
            print(f"  Issues: {', '.join(format_result['issues'])}")


def example_email_intelligence_lookup():
    """Example: Comprehensive email intelligence lookup"""
    print("\n=== Email Intelligence Lookup Example ===")

    agent = setup_email_agent()

    # Example email for lookup
    target_email = "john.doe@example.com"

    print(f"Performing intelligence lookup for: {target_email}")

    # Reverse email lookup
    lookup_result = agent.reverse_email_lookup(target_email)

    if lookup_result["found"]:
        print("\n📧 Email Intelligence Found:")

        # Person information
        if lookup_result.get("person_info"):
            person = lookup_result["person_info"]
            print(f"  👤 Person: {person.get('full_name', 'N/A')}")
            print(f"  📅 Age: {person.get('age', 'N/A')}")

            if person.get("phones"):
                print(f"  📞 Phones: {', '.join(person['phones'])}")

            if person.get("addresses"):
                addresses = [
                    f"{addr.get('city', '')}, {addr.get('state', '')}"
                    for addr in person["addresses"]
                ]
                print(f"  🏠 Addresses: {'; '.join(filter(None, addresses))}")

        # Business information
        if lookup_result.get("business_info"):
            business = lookup_result["business_info"]
            print(f"  🏢 Business: {business.get('name', 'N/A')}")
            print(f"  🏭 Industry: {business.get('industry', 'N/A')}")
            print(f"  🌐 Website: {business.get('website', 'N/A')}")

        print(f"  🎯 Confidence Score: {lookup_result['confidence_score']:.2f}")
    else:
        print("❌ No intelligence found for this email")
        if lookup_result.get("error"):
            print(f"   Error: {lookup_result['error']}")


def example_breach_detection():
    """Example: Email breach and compromise detection"""
    print("\n=== Email Breach Detection Example ===")

    agent = setup_email_agent()

    test_emails = ["test@example.com", "compromised@breach.com", "secure@example.org"]

    for email in test_emails:
        print(f"\nChecking breaches for: {email}")

        breach_result = agent.detect_email_breaches(email)

        if breach_result.get("found_in_breaches"):
            print(f"  ⚠️  Found in {breach_result['breach_count']} breaches")
            print(f"  📊 Risk Level: {breach_result['risk_level'].upper()}")

            for breach in breach_result.get("breaches", [])[:3]:  # Show first 3
                print(
                    f"    - {breach.get('name', 'Unknown')} ({breach.get('date', 'N/A')})"
                )
        else:
            print("  ✅ No known breaches found")


def example_domain_analysis():
    """Example: Email domain analysis and business affiliation"""
    print("\n=== Domain Analysis Example ===")

    agent = setup_email_agent()

    business_emails = [
        "contact@acme-corp.com",
        "info@startup.io",
        "admin@government.gov",
    ]

    for email in business_emails:
        print(f"\nAnalyzing domain for: {email}")

        domain_info = agent.extract_domain_info(email)

        if domain_info.get("error"):
            print(f"  ❌ Error: {domain_info['error']}")
        else:
            print(f"  🌐 Domain: {domain_info['domain']}")
            print(f"  🏢 Organization: {domain_info.get('organization', 'N/A')}")
            print(f"  🌍 Country: {domain_info.get('country', 'N/A')}")
            print(f"  📅 Created: {domain_info.get('created_date', 'N/A')}")
            print(f"  ⏰ Expires: {domain_info.get('expires_date', 'N/A')}")


def example_cross_reference_with_person_search():
    """Example: Cross-reference email results with PersonSearchAgent"""
    print("\n=== Cross-Reference with Person Search Example ===")

    # Setup both agents
    email_agent = setup_email_agent()
    person_agent = PersonSearchAgent()

    target_email = "john.smith@example.com"

    print(f"Cross-referencing email: {target_email}")

    # Perform cross-reference
    cross_ref_result = email_agent.cross_reference_with_person(
        target_email, person_agent
    )

    if cross_ref_result["cross_reference_performed"]:
        print("  ✅ Cross-reference completed")

        matching_persons = cross_ref_result.get("matching_persons", [])
        if matching_persons:
            print(f"  👥 Found {len(matching_persons)} matching person(s):")

            for person in matching_persons:
                print(
                    f"    - {person['name']} (confidence: {person['confidence']:.2f})"
                )
                if person.get("phones"):
                    print(f"      📞 {', '.join(person['phones'])}")
        else:
            print("  ❌ No matching persons found")

        print(f"  🎯 Overall Confidence: {cross_ref_result['confidence_score']:.2f}")
    else:
        print("  ❌ Cross-reference not performed (insufficient email data)")


def example_comprehensive_analysis():
    """Example: Complete comprehensive email analysis"""
    print("\n=== Comprehensive Email Analysis Example ===")

    email_agent = setup_email_agent()
    person_agent = PersonSearchAgent()

    target_email = "analyst@company.com"

    print(f"Performing comprehensive analysis for: {target_email}")
    print("This may take a few moments...")

    start_time = time.time()

    # Run comprehensive analysis
    analysis = email_agent.comprehensive_email_analysis(target_email, person_agent)

    print(f"\n📊 Analysis completed in {analysis['processing_time']:.2f} seconds")
    print(f"🎯 Overall Confidence: {analysis['overall_confidence']:.2f}")

    # Format validation results
    format_val = analysis["format_validation"]
    print(f"\n📧 Format: {'✅ Valid' if format_val['is_valid'] else '❌ Invalid'}")

    # Deliverability results
    deliverability = analysis["deliverability"]
    if deliverability.get("deliverable") is not None:
        print(f"📬 Deliverable: {'✅ Yes' if deliverability['deliverable'] else '❌ No'}")

    # Classification results
    classification = analysis["classification"]
    print(
        f"🏷️  Type: {classification['type'].title()} (confidence: {classification['confidence']:.2f})"
    )

    # Domain information
    domain_info = analysis["domain_info"]
    if not domain_info.get("error"):
        print(
            f"🌐 Domain: {domain_info.get('organization', 'N/A')} ({domain_info['domain']})"
        )

    # Person information
    reverse_lookup = analysis["reverse_lookup"]
    if reverse_lookup.get("found"):
        person_info = reverse_lookup.get("person_info", {})
        if person_info.get("full_name"):
            print(f"👤 Associated Person: {person_info['full_name']}")

    # Breach information
    breach_info = analysis["breach_detection"]
    if breach_info.get("found_in_breaches"):
        print(
            f"⚠️  Security: Found in {breach_info['breach_count']} breaches ({breach_info['risk_level']} risk)"
        )
    else:
        print("🔒 Security: No known breaches")


def example_batch_email_processing():
    """Example: Process multiple emails efficiently"""
    print("\n=== Batch Email Processing Example ===")

    agent = setup_email_agent()

    # Sample email list for processing
    email_list = [
        "user1@gmail.com",
        "contact@business.com",
        "temp@10minutemail.com",
        "admin@company.org",
        "invalid-email",
    ]

    print(f"Processing {len(email_list)} emails...")

    results = []

    for i, email in enumerate(email_list, 1):
        print(f"\n[{i}/{len(email_list)}] Processing: {email}")

        try:
            # Basic analysis for batch processing
            format_result = agent.validate_email_format(email)

            if format_result["is_valid"]:
                classification = agent.classify_email_type(email)

                result = {
                    "email": email,
                    "valid": True,
                    "type": classification["type"],
                    "confidence": classification["confidence"],
                    "is_disposable": classification["is_disposable"],
                    "is_business": classification.get("is_business", False),
                }
            else:
                result = {
                    "email": email,
                    "valid": False,
                    "issues": format_result["issues"],
                }

            results.append(result)
            print(f"  ✅ Processed: {result}")

        except Exception as e:
            print(f"  ❌ Error processing {email}: {e}")
            results.append({"email": email, "valid": False, "error": str(e)})

    # Summary
    print(f"\n📊 Batch Processing Summary:")
    valid_emails = [r for r in results if r.get("valid")]
    disposable_emails = [r for r in valid_emails if r.get("is_disposable")]
    business_emails = [r for r in valid_emails if r.get("is_business")]

    print(f"  Total processed: {len(results)}")
    print(f"  Valid emails: {len(valid_emails)}")
    print(f"  Disposable emails: {len(disposable_emails)}")
    print(f"  Business emails: {len(business_emails)}")


def example_agent_health_and_metrics():
    """Example: Monitor agent health and performance metrics"""
    print("\n=== Agent Health and Metrics Example ===")

    agent = setup_email_agent()

    # Health check
    print("Performing health check...")
    health = agent.health_check()

    print(f"Agent Status: {health['status'].upper()}")
    print(
        f"Email Validation Ready: {'✅' if health.get('email_validation_ready') else '❌'}"
    )
    print(f"Breach Detection: {'✅' if health.get('breach_detection_enabled') else '❌'}")
    print(f"MX Validation: {'✅' if health.get('mx_validation_enabled') else '❌'}")
    print(f"Known Disposable Domains: {health.get('disposable_domains_count', 0)}")

    # Performance metrics (after some operations)
    print("\nPerformance Metrics:")
    metrics = agent.get_metrics()

    print(f"  Total Requests: {metrics['total_requests']}")
    print(f"  Success Rate: {metrics['success_rate']:.1f}%")
    print(f"  Cache Hit Rate: {metrics['cache_hit_rate']:.1f}%")
    print(f"  Average Response Time: {metrics['average_response_time']:.2f}s")
    print(f"  Rate Limit Hits: {metrics['rate_limit_hits']}")


def run_all_examples():
    """Run all examples in sequence"""
    print("🚀 EmailSearchAgent - Comprehensive Examples")
    print("=" * 50)

    try:
        example_basic_email_validation()
        example_email_intelligence_lookup()
        example_breach_detection()
        example_domain_analysis()
        example_cross_reference_with_person_search()
        example_comprehensive_analysis()
        example_batch_email_processing()
        example_agent_health_and_metrics()

        print("\n✅ All examples completed successfully!")

    except KeyboardInterrupt:
        print("\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
