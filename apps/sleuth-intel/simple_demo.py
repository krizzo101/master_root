#!/usr/bin/env python3
"""
Simple Sleuth-Intel Demo - Find People & Phone Numbers
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from working_api_test import WorkingEnformionClient


def find_person(first_name, last_name, location):
    """Find a person and their contact information"""

    client = WorkingEnformionClient()

    print(f"🔍 Searching for: {first_name} {last_name} in {location}")

    try:
        result = client.contact_enrichment(
            first_name=first_name, last_name=last_name, address_line2=location
        )

        if "person" in result:
            person = result["person"]
            name = person.get("name", {})

            print(f"✅ Found: {name.get('firstName', '')} {name.get('lastName', '')}")
            print(f"   Age: {person.get('age', 'Unknown')}")

            # Show phone numbers
            phones = person.get("phones", [])
            print(f"\n📞 Phone Numbers ({len(phones)}):")
            for phone in phones:
                number = phone.get("number", "")
                phone_type = phone.get("type", "unknown")
                connected = "✅" if phone.get("isConnected", False) else "❌"
                print(f"   {number} ({phone_type}) {connected}")

            # Show addresses
            addresses = person.get("addresses", [])
            print(f"\n📍 Addresses ({len(addresses)}):")
            for addr in addresses:
                street = addr.get("street", "")
                city = addr.get("city", "")
                state = addr.get("state", "")
                zip_code = addr.get("zip", "")
                dates = f"{addr.get('firstReportedDate', '')} - {addr.get('lastReportedDate', '')}"
                print(f"   {street}, {city} {state} {zip_code}")
                print(f"     Reported: {dates}")

            # Show emails
            emails = person.get("emails", [])
            if emails:
                print(f"\n📧 Email Addresses ({len(emails)}):")
                for email in emails:
                    print(f"   {email}")

            return True
        else:
            print("❌ No results found")
            return False

    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False


def main():
    """Demo searches"""

    print("🕵️  SLEUTH-INTEL SIMPLE DEMO")
    print("=" * 50)
    print("Find people and their contact information")
    print()

    # Example searches
    searches = [
        ("John", "Smith", "Los Angeles, CA"),
        ("Jane", "Doe", "San Francisco, CA"),
        ("Michael", "Johnson", "New York, NY"),
    ]

    for first, last, location in searches:
        find_person(first, last, location)
        print("\n" + "-" * 50 + "\n")

    print("💡 TIP: This works with any name + location combination!")
    print("   Try your own searches by modifying the script.")


if __name__ == "__main__":
    main()
