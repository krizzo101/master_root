#!/usr/bin/env python3
"""
PersonSearchAgent Demo Script
Demonstrates usage patterns and capabilities of the PersonSearchAgent
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.person_search_agent import PersonSearchAgent
from src.models.query import PersonSearchQuery
from src.providers.enformion_client import EnformionAPIError

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_basic_name_search():
    """Demonstrate basic name-based person search"""
    print("\n=== Demo: Basic Name Search ===")

    try:
        agent = PersonSearchAgent(fuzzy_threshold=0.8)

        # Simple name search
        query = PersonSearchQuery(
            first_name="John",
            last_name="Smith",
            city="Los Angeles",
            state="CA",
            max_results=5,
        )

        print(
            f"Searching for: {query.first_name} {query.last_name} in {query.city}, {query.state}"
        )
        results = agent.search(query)

        print(f"Found {len(results)} results:")
        for i, person in enumerate(results, 1):
            print(f"\n{i}. {person.name.display_name}")
            print(f"   Confidence: {person.confidence_score:.2f}")

            if person.current_phone:
                print(f"   Phone: {person.current_phone.formatted}")

            if person.primary_email:
                print(f"   Email: {person.primary_email.address}")

            if person.current_address:
                print(f"   Address: {person.current_address.full_address}")

            if person.demographics and person.demographics.age:
                print(f"   Age: {person.demographics.age}")

    except Exception as e:
        print(f"Error in basic name search: {e}")


def demo_phone_search():
    """Demonstrate reverse phone lookup"""
    print("\n=== Demo: Phone Number Search ===")

    try:
        agent = PersonSearchAgent()

        phone_number = "555-123-4567"  # Example phone number
        print(f"Looking up phone number: {phone_number}")

        results = agent.search_by_phone(phone_number, max_results=3)

        if results:
            print(f"Found {len(results)} person(s) associated with this phone:")
            for person in results:
                print(f"\n- {person.name.display_name}")
                print(f"  Confidence: {person.confidence_score:.2f}")

                if person.current_address:
                    print(f"  Address: {person.current_address.full_address}")
        else:
            print("No persons found for this phone number")

    except Exception as e:
        print(f"Error in phone search: {e}")


def demo_age_filtered_search():
    """Demonstrate search with age range filtering"""
    print("\n=== Demo: Age-Filtered Search ===")

    try:
        agent = PersonSearchAgent()

        results = agent.search_with_age_filter(
            first_name="Michael",
            last_name="Johnson",
            age_min=30,
            age_max=50,
            state="CA",
            max_results=10,
        )

        print(f"Searching for Michael Johnson, age 30-50, in CA")
        print(f"Found {len(results)} results:")

        for person in results:
            age_str = (
                f"Age {person.demographics.age}"
                if person.demographics and person.demographics.age
                else "Age unknown"
            )
            print(
                f"- {person.name.display_name} ({age_str}) - Confidence: {person.confidence_score:.2f}"
            )

    except Exception as e:
        print(f"Error in age-filtered search: {e}")


def demo_comprehensive_search():
    """Demonstrate comprehensive search with multiple parameters"""
    print("\n=== Demo: Comprehensive Search ===")

    try:
        agent = PersonSearchAgent()

        query = PersonSearchQuery(
            first_name="Sarah",
            last_name="Williams",
            city="San Francisco",
            state="CA",
            age_min=25,
            age_max=45,
            fuzzy_matching=True,
            include_relatives=True,
            include_associates=True,
            min_confidence=0.6,
            max_results=5,
        )

        print("Performing comprehensive search with multiple parameters...")
        results = agent.search(query)

        for i, person in enumerate(results, 1):
            print(
                f"\n{i}. {person.name.display_name} (Confidence: {person.confidence_score:.2f})"
            )

            # Contact information
            print("   Contact Information:")
            for phone in person.phones[:2]:  # Show first 2 phones
                print(f"   - Phone: {phone.formatted} ({phone.type})")

            for email in person.emails[:2]:  # Show first 2 emails
                print(f"   - Email: {email.address}")

            # Addresses
            if person.addresses:
                print("   Addresses:")
                for addr in person.addresses[:2]:  # Show first 2 addresses
                    print(f"   - {addr.full_address}")

            # Associates
            if person.associates:
                print("   Associates:")
                for assoc in person.associates[:3]:  # Show first 3 associates
                    rel = assoc.relationship or "unknown relationship"
                    print(f"   - {assoc.name.display_name} ({rel})")

    except Exception as e:
        print(f"Error in comprehensive search: {e}")


def demo_caching_performance():
    """Demonstrate caching functionality"""
    print("\n=== Demo: Caching Performance ===")

    try:
        agent = PersonSearchAgent()

        query = PersonSearchQuery(
            first_name="David",
            last_name="Brown",
            city="Chicago",
            state="IL",
            max_results=3,
        )

        # First search - will hit API
        print("First search (will hit API)...")
        import time

        start_time = time.time()
        results1 = agent.search(query, use_cache=True)
        first_duration = time.time() - start_time

        print(
            f"First search took {first_duration:.2f} seconds, found {len(results1)} results"
        )

        # Second search - should use cache
        print("Second search (should use cache)...")
        start_time = time.time()
        results2 = agent.search(query, use_cache=True)
        second_duration = time.time() - start_time

        print(
            f"Second search took {second_duration:.2f} seconds, found {len(results2)} results"
        )
        print(
            f"Speed improvement: {(first_duration / max(second_duration, 0.001)):.1f}x faster"
        )

        # Show metrics
        metrics = agent.get_metrics()
        print(f"\nAgent Metrics:")
        print(f"- Total requests: {metrics['total_requests']}")
        print(f"- Cached responses: {metrics['cached_responses']}")
        print(f"- Cache hit rate: {metrics['cache_hit_rate']:.1f}%")
        print(f"- Average response time: {metrics['average_response_time']:.2f}s")

    except Exception as e:
        print(f"Error in caching demo: {e}")


def demo_duplicate_detection():
    """Demonstrate duplicate detection"""
    print("\n=== Demo: Duplicate Detection ===")

    try:
        agent = PersonSearchAgent()

        # Search with slightly different parameters that might return duplicates
        query1 = PersonSearchQuery(
            first_name="Robert",
            last_name="Davis",
            city="Miami",
            state="FL",
            max_results=10,
        )

        query2 = PersonSearchQuery(
            first_name="Bob",  # Nickname for Robert
            last_name="Davis",
            city="Miami",
            state="FL",
            max_results=10,
        )

        print("Searching for 'Robert Davis' and 'Bob Davis' in Miami, FL...")
        results1 = agent.search(query1)
        results2 = agent.search(query2)

        all_results = results1 + results2
        print(f"Total results before duplicate detection: {len(all_results)}")

        # Find duplicates
        duplicates = agent.find_duplicates(all_results, similarity_threshold=0.8)

        if duplicates:
            print(f"Found {len(duplicates)} potential duplicate(s):")
            for i, (person1, person2, similarity) in enumerate(duplicates, 1):
                print(f"\n{i}. Similarity: {similarity:.2f}")
                print(
                    f"   - {person1.name.display_name} (Confidence: {person1.confidence_score:.2f})"
                )
                print(
                    f"   - {person2.name.display_name} (Confidence: {person2.confidence_score:.2f})"
                )
        else:
            print("No duplicates found")

    except Exception as e:
        print(f"Error in duplicate detection demo: {e}")


def demo_error_handling():
    """Demonstrate error handling patterns"""
    print("\n=== Demo: Error Handling ===")

    try:
        agent = PersonSearchAgent()

        # Test insufficient parameters
        print("Testing insufficient parameters...")
        try:
            empty_query = PersonSearchQuery()  # Empty query
            agent.search(empty_query)
        except ValueError as e:
            print(f"✓ Caught expected ValueError: {e}")

        # Test invalid parameters
        print("\nTesting invalid phone number...")
        try:
            invalid_query = PersonSearchQuery(
                first_name="Test", phone="123"  # Too short
            )
        except ValueError as e:
            print(f"✓ Caught expected validation error: {e}")

        # Test API error handling (simulated)
        print("\nTesting API error handling...")
        try:
            # This will likely fail if no real credentials are configured
            query = PersonSearchQuery(
                first_name="Test", last_name="Person", max_results=1
            )
            results = agent.search(query)
            print(f"Search succeeded with {len(results)} results")

        except EnformionAPIError as e:
            print(f"✓ Caught API error (expected if no credentials): {e}")
        except Exception as e:
            print(f"✓ Caught other error: {type(e).__name__}: {e}")

    except Exception as e:
        print(f"Error in error handling demo: {e}")


def demo_health_check():
    """Demonstrate agent health monitoring"""
    print("\n=== Demo: Health Check ===")

    try:
        agent = PersonSearchAgent()

        health = agent.health_check()

        print("Agent Health Status:")
        print(f"- Status: {health['status']}")
        print(f"- Provider: {health['provider']}")
        print(f"- Agent Name: {health['agent_name']}")
        print(f"- Person Search Ready: {health.get('person_search_ready', 'Unknown')}")
        print(f"- Fuzzy Threshold: {health.get('fuzzy_threshold', 'Unknown')}")

        if health["status"] == "healthy":
            print("✓ Agent is operational")
        else:
            print(f"⚠ Agent issue: {health.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Error in health check demo: {e}")


def main():
    """Run all demonstration functions"""
    print("PersonSearchAgent Demonstration")
    print("=" * 50)

    # Run demonstrations in order
    demo_functions = [
        demo_health_check,
        demo_basic_name_search,
        demo_phone_search,
        demo_age_filtered_search,
        demo_comprehensive_search,
        demo_caching_performance,
        demo_duplicate_detection,
        demo_error_handling,
    ]

    for demo_func in demo_functions:
        try:
            demo_func()
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user")
            break
        except Exception as e:
            print(f"\nUnexpected error in {demo_func.__name__}: {e}")
            logger.exception(f"Error in {demo_func.__name__}")

        # Small pause between demos
        input("\nPress Enter to continue to next demo...")

    print("\n" + "=" * 50)
    print("Demonstration completed!")


if __name__ == "__main__":
    main()
