#!/usr/bin/env python3
"""
Temporary fix to set up authentication correctly
"""

import os
import sys
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.secure_api_locker import APICredential, api_locker_manager


def fix_auth():
    """Fix the authentication with correct values"""

    # Clear any existing items
    api_locker_manager.locker._credentials = {}
    api_locker_manager.locker._credential_indices = {}

    # Create API credential object with correct values
    enformion_cred = APICredential(
        provider="enformion",
        key_name="profile_access_key",
        key_value="feb1c32d32b54803b67687973a7d1699",  # Clear value
        password="056c8cf9dba44d6186a8acb8675e2b06",  # Clear value
        base_url="https://devapi.enformion.com",  # Updated base URL
        rate_limit=1000,
        metadata={
            "plan": "starter",
            "documentation": "https://enformiongo.readme.io/reference/overview",
            "description": "EnformionGO API for people/business data lookup",
        },
    )

    # Add to locker
    api_locker_manager.initialize_with_credentials([enformion_cred])

    print("✅ Authentication fixed and loaded")

    # Test the auth
    cred = api_locker_manager.get_credential("enformion")
    if cred:
        print(f"✅ Test auth retrieval successful")
        print(f"  Key: {cred.key_value}")
        print(f"  Pass: {cred.password}")
        print(f"  Base URL: {cred.base_url}")
    else:
        print("❌ Failed to retrieve auth")


if __name__ == "__main__":
    fix_auth()
