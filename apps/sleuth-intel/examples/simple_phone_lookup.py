#!/usr/bin/env python3
"""
Simple Phone Lookup Example
===========================

This example demonstrates basic phone number lookup functionality
using the sleuth-intel library.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python simple_phone_lookup.py
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import PhoneLookupRequest, PhoneLookupResponse


async def simple_phone_lookup(phone_number: str) -> Optional[PhoneLookupResponse]:
    """
    Perform a simple phone lookup for a given number.

    Args:
        phone_number: Phone number to look up (10 digits)

    Returns:
        PhoneLookupResponse object or None if error
    """
    # Initialize the client
    client = SleuthIntel()

    try:
        # Create the request
        request = PhoneLookupRequest(
            phone=phone_number,
            include_carrier=True,
            include_owner=True,
            include_location=True,
        )

        print(f"📞 Looking up phone number: {phone_number}")
        print("=" * 50)

        # Perform the lookup
        response = await client.phone_lookup(request)

        if response.success:
            # Display results
            print(f"✅ Lookup successful!")
            print(f"\nPhone Details:")
            print(f"  • Number: {response.phone_number}")
            print(f"  • Type: {response.phone_type}")
            print(f"  • Carrier: {response.carrier}")
            print(f"  • Line Type: {response.line_type}")
            print(f"  • Valid: {response.is_valid}")

            if response.owner_info:
                print(f"\nOwner Information:")
                print(f"  • Name: {response.owner_info.get('name', 'N/A')}")
                print(f"  • Address: {response.owner_info.get('address', 'N/A')}")
                print(f"  • City: {response.owner_info.get('city', 'N/A')}")
                print(f"  • State: {response.owner_info.get('state', 'N/A')}")

            if response.location_info:
                print(f"\nLocation Information:")
                print(f"  • City: {response.location_info.get('city', 'N/A')}")
                print(f"  • State: {response.location_info.get('state', 'N/A')}")
                print(f"  • ZIP: {response.location_info.get('zip_code', 'N/A')}")
                print(f"  • County: {response.location_info.get('county', 'N/A')}")
                print(f"  • Time Zone: {response.location_info.get('timezone', 'N/A')}")

            # Save raw response for debugging
            with open(
                f"phone_lookup_{phone_number}_{datetime.now():%Y%m%d_%H%M%S}.json", "w"
            ) as f:
                json.dump(response.to_dict(), f, indent=2)
                print(f"\n💾 Full response saved to {f.name}")

            return response
        else:
            print(f"❌ Lookup failed: {response.error_message}")
            return None

    except Exception as e:
        print(f"❌ Error during lookup: {str(e)}")
        return None
    finally:
        # Clean up
        await client.close()


async def batch_phone_lookup(phone_numbers: list[str]):
    """
    Perform batch phone lookups with rate limiting.

    Args:
        phone_numbers: List of phone numbers to look up
    """
    client = SleuthIntel()
    results = []

    print(f"🔍 Processing {len(phone_numbers)} phone numbers...")
    print("=" * 50)

    for i, phone in enumerate(phone_numbers, 1):
        print(f"\n[{i}/{len(phone_numbers)}] Processing {phone}...")

        try:
            request = PhoneLookupRequest(phone=phone)
            response = await client.phone_lookup(request)

            if response.success:
                print(f"  ✅ Success - {response.owner_info.get('name', 'Unknown')}")
                results.append(
                    {
                        "phone": phone,
                        "success": True,
                        "owner": response.owner_info.get("name"),
                        "carrier": response.carrier,
                        "location": f"{response.location_info.get('city', '')}, {response.location_info.get('state', '')}",
                    }
                )
            else:
                print(f"  ❌ Failed - {response.error_message}")
                results.append(
                    {"phone": phone, "success": False, "error": response.error_message}
                )

        except Exception as e:
            print(f"  ❌ Error - {str(e)}")
            results.append({"phone": phone, "success": False, "error": str(e)})

        # Rate limiting (adjust as needed)
        if i < len(phone_numbers):
            await asyncio.sleep(1)

    # Save batch results
    output_file = f"batch_phone_lookup_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Summary:")
    print(f"  • Total processed: {len(results)}")
    print(f"  • Successful: {sum(1 for r in results if r['success'])}")
    print(f"  • Failed: {sum(1 for r in results if not r['success'])}")
    print(f"  • Results saved to: {output_file}")

    await client.close()
    return results


def main():
    """Main function with example usage."""
    print("Sleuth Intel - Phone Lookup Example")
    print("=" * 50)

    # Example 1: Single phone lookup
    print("\n📌 Example 1: Single Phone Lookup")
    print("-" * 30)
    asyncio.run(simple_phone_lookup("5551234567"))

    # Example 2: Batch phone lookup
    print("\n📌 Example 2: Batch Phone Lookup")
    print("-" * 30)
    test_numbers = ["5551234567", "5559876543", "5555551212"]
    asyncio.run(batch_phone_lookup(test_numbers))

    print("\n✨ Examples completed!")


if __name__ == "__main__":
    main()
