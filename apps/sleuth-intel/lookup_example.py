#!/usr/bin/env python3
"""
Example script showing how to use Sleuth Intel for reverse phone lookup
"""

import json
import sys
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.providers.enformion_client import (
    EnformionAPIError,
    EnformionClient,
    lookup_phone,
)


def demo_phone_lookup():
    """Demonstrate reverse phone lookup for the number you provided"""

    phone_number = "(910) 392-5349"

    print("🔍 Sleuth Intel - Reverse Phone Lookup")
    print("=" * 50)
    print(f"Looking up: {phone_number}")
    print()

    try:
        # Method 1: Using the convenience function
        print("📞 Using convenience function...")
        result = lookup_phone(phone_number)

        print("✅ Lookup successful!")
        print(f"Raw result: {json.dumps(result, indent=2)}")

    except EnformionAPIError as e:
        if e.status_code == 401:
            print("❌ Authentication failed - check your API credentials")
        elif e.status_code == 429:
            print("⏰ Rate limit exceeded - please wait and try again")
        else:
            print(f"❌ API Error: {e}")
            if e.response_data:
                print(f"Response: {json.dumps(e.response_data, indent=2)}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


def demo_advanced_client():
    """Demonstrate advanced client usage with multiple methods"""

    print("\n🔧 Advanced Client Demo")
    print("-" * 30)

    try:
        client = EnformionClient()

        # Multiple lookup methods for the same number
        phone = "9103925349"

        print(f"Testing multiple lookups for: {phone}")
        print()

        # Reverse phone search
        print("1. Reverse Phone Search:")
        try:
            result1 = client.reverse_phone_search(phone)
            print(f"   Result: {json.dumps(result1, indent=4)[:200]}...")
        except Exception as e:
            print(f"   Error: {e}")

        print()

        # Caller ID lookup
        print("2. Caller ID Lookup:")
        try:
            result2 = client.caller_id_lookup(phone)
            print(f"   Result: {json.dumps(result2, indent=4)[:200]}...")
        except Exception as e:
            print(f"   Error: {e}")

        print()

        # Account status
        print("3. Account Status:")
        try:
            status = client.get_account_status()
            print(f"   Status: {json.dumps(status, indent=4)}")
        except Exception as e:
            print(f"   Error: {e}")

    except Exception as e:
        print(f"❌ Client initialization failed: {e}")


def main():
    """Main demo function"""

    # First check if credentials are set up
    from src.core.secure_api_locker import api_locker_manager

    status = api_locker_manager.get_locker_status()
    if not status["providers"] or "enformion" not in status["providers"]:
        print("❌ No EnformionGO credentials found!")
        print("Please run: python3 setup_api_keys.py")
        return

    print(
        f"✅ Found {status['total_credentials']} credentials for {len(status['providers'])} providers"
    )

    # Run demos
    demo_phone_lookup()

    # Uncomment to test advanced features
    # demo_advanced_client()

    print("\n" + "=" * 50)
    print("🎯 Demo complete!")
    print()
    print("💡 Pro Tips:")
    print("• EnformionGO charges per successful match")
    print("• Free tier: 100 searches/month")
    print("• Starter tier: $0.10 per match")
    print("• Your credentials are safely encrypted")


if __name__ == "__main__":
    main()
