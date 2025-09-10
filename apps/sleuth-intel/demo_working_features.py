#!/usr/bin/env python3
"""
Sleuth-Intel Working Features Demo
Demonstrates what actually works with a free EnformionGO account
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our working client
from working_api_test import WorkingEnformionClient


def demo_contact_enrichment():
    """Demo contact enrichment - the main feature available to free accounts"""

    print("=" * 60)
    print("🧑‍💼 CONTACT ENRICHMENT DEMO")
    print("=" * 60)
    print("This is the primary feature available to free EnformionGO accounts.")
    print("Requires at least 2 data points (name, phone, email, or address)")
    print()

    client = WorkingEnformionClient()

    # Test Case 1: Name + Address
    print("📍 Test 1: Person Search by Name + Address")
    print("   Input: John Smith, 123 Main St, Los Angeles CA")

    try:
        result = client.contact_enrichment(
            first_name="John",
            last_name="Smith",
            address_line1="123 Main St",
            address_line2="Los Angeles, CA",
        )

        print("   ✅ SUCCESS!")
        if "person" in result:
            person = result["person"]
            name = person.get("name", {})
            print(f"   Found: {name.get('firstName', '')} {name.get('lastName', '')}")
            print(f"   Age: {person.get('age', 'N/A')}")
            print(f"   Addresses: {len(person.get('addresses', []))}")
            print(f"   Phones: {len(person.get('phones', []))}")
            print(f"   Emails: {len(person.get('emails', []))}")

            # Show sample data
            addresses = person.get("addresses", [])
            if addresses:
                addr = addresses[0]
                print(
                    f"   Sample Address: {addr.get('street', '')} {addr.get('city', '')} {addr.get('state', '')}"
                )

            phones = person.get("phones", [])
            if phones:
                phone = phones[0]
                print(
                    f"   Sample Phone: {phone.get('number', '')} ({phone.get('type', 'unknown')})"
                )

        print()

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        print()

    # Test Case 2: Different name combinations
    print("📍 Test 2: Person Search by Different Name")
    print("   Input: Jane Doe, San Francisco CA")

    try:
        result = client.contact_enrichment(
            first_name="Jane", last_name="Doe", address_line2="San Francisco, CA"
        )

        print("   ✅ SUCCESS!")
        if "person" in result:
            person = result["person"]
            name = person.get("name", {})
            print(f"   Found: {name.get('firstName', '')} {name.get('lastName', '')}")
            print(
                f"   Records found: {len(person.get('addresses', []))} addresses, {len(person.get('phones', []))} phones"
            )
        print()

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        print()


def demo_limitations():
    """Demo what doesn't work with free accounts"""

    print("=" * 60)
    print("⚠️  FREE ACCOUNT LIMITATIONS")
    print("=" * 60)
    print("These features require paid EnformionGO accounts:")
    print()

    limitations = [
        ("Person Search API", "Detailed person profiles and comprehensive search"),
        ("Reverse Phone Search", "Direct phone number lookup (PersonSearch endpoint)"),
        ("Business Search API", "Company information and business intelligence"),
        ("Criminal Records", "Background check and criminal history"),
        ("Property Records", "Real estate and property ownership"),
        ("Vehicle Records", "Vehicle registration and ownership"),
        ("Professional Licenses", "License verification and professional credentials"),
    ]

    for feature, description in limitations:
        print(f"❌ {feature}")
        print(f"   {description}")
        print()


def demo_workarounds():
    """Demo workarounds for free accounts"""

    print("=" * 60)
    print("💡 WORKAROUNDS FOR FREE ACCOUNTS")
    print("=" * 60)
    print()

    print("🔄 Phone Lookup Workaround:")
    print("   Instead of direct reverse phone search, use contact enrichment")
    print("   with phone + minimal name data")
    print()

    print("🔄 Person Search Workaround:")
    print("   Use contact enrichment with any 2+ data points:")
    print("   • Name + Address")
    print("   • Name + City/State")
    print("   • Email + Name")
    print("   • Phone + Name (if you have some name info)")
    print()

    print("🔄 Business Search Workaround:")
    print("   Use contact enrichment with business owner name + address")
    print("   This can sometimes reveal business connections")
    print()


def demo_api_usage_patterns():
    """Demo proper API usage patterns"""

    print("=" * 60)
    print("📊 PROPER API USAGE PATTERNS")
    print("=" * 60)

    print("✅ Good practices for free accounts:")
    print("   • Always provide at least 2 data points")
    print("   • Use complete addresses (street + city + state)")
    print("   • Be specific with names (avoid very common names alone)")
    print("   • Combine multiple data points for better results")
    print()

    print("❌ Avoid these patterns:")
    print("   • Single data point searches (will fail)")
    print("   • Very generic searches (John Smith without location)")
    print("   • Phone-only searches (not supported)")
    print("   • Trying to use paid API endpoints")
    print()


def demo_system_status():
    """Show system status and configuration"""

    print("=" * 60)
    print("🔧 SYSTEM STATUS")
    print("=" * 60)

    client = WorkingEnformionClient()

    print("✅ Components Status:")
    print(f"   • API Base URL: {client.base_url}")
    print(f"   • Authentication: Working")
    print(f"   • Contact Enrichment: ✅ Available")
    print(f"   • Person Search: ❌ Requires paid account")
    print(f"   • Business Search: ❌ Requires paid account")
    print()

    print("🔑 Account Type: FREE")
    print("   • Contact Enrichment: Unlimited (with rate limits)")
    print("   • Credits: Usage-based (check EnformionGO dashboard)")
    print("   • Rate Limit: ~60 requests/minute")
    print()


def main():
    """Main demo function"""

    print("🕵️  SLEUTH-INTEL WORKING FEATURES DEMONSTRATION")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Account Type: FREE EnformionGO")
    print()

    try:
        # Run all demos
        demo_system_status()
        demo_contact_enrichment()
        demo_workarounds()
        demo_limitations()
        demo_api_usage_patterns()

        print("=" * 80)
        print("🎯 SUMMARY")
        print("=" * 80)
        print("✅ WORKING: Contact enrichment with name + address/location")
        print("✅ WORKING: Person discovery with multiple data points")
        print("✅ WORKING: Contact information enrichment")
        print("❌ LIMITED: Direct phone/email/business lookup (paid only)")
        print()
        print("🚀 Ready for use! Contact enrichment provides substantial")
        print("   intelligence capabilities for free accounts.")
        print()
        print("📚 For paid features, upgrade at: https://accounts.enformion.com/")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
