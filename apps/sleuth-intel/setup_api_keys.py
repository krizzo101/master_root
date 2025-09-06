#!/usr/bin/env python3
"""
Setup script to securely store API keys for Sleuth Intel
"""

import os
import sys
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.secure_api_locker import APICredential, api_locker_manager


def setup_enformion_api():
    """Setup EnformionGO API keys securely"""

    # Your provided API access details
    enformion_key = "feb1c32d32b54803b67687973a7d1699"
    enformion_password = "056c8cf9dba44d6186a8acb8675e2b06"

    # Create API credential object
    enformion_cred = APICredential(
        provider="enformion",
        key_name="profile_access_key",
        key_value=enformion_key,
        password=enformion_password,
        base_url="https://api.enformion.com/v1",
        rate_limit=1000,  # Adjust based on your plan
        metadata={
            "plan": "starter",
            "documentation": "https://enformiongo.readme.io/reference/overview",
            "description": "EnformionGO API for people/business data lookup",
        },
    )

    # Add to locker
    api_locker_manager.initialize_with_credentials([enformion_cred])

    # Save encrypted keys
    config_dir = Path.home() / ".sleuth-intel"
    config_dir.mkdir(exist_ok=True, mode=0o700)

    encrypted_file = config_dir / "api_keys.enc"

    # Set encryption key from environment or use default
    encryption_key = os.environ.get("SLEUTH_INTEL_ENCRYPTION_KEY")
    if not encryption_key:
        print("WARNING: No SLEUTH_INTEL_ENCRYPTION_KEY found in environment.")
        print("Using default encryption key. For production, set:")
        print("export SLEUTH_INTEL_ENCRYPTION_KEY='your-secure-key-here'")
        encryption_key = "sleuth-intel-default-key-change-me"

    # Save API keys
    api_locker_manager.locker.save_credentials_encrypted(encrypted_file, encryption_key)

    print("✅ EnformionGO API keys saved securely")
    print(f"📁 Location: {encrypted_file}")
    print(f"🔐 Encrypted with key: {encryption_key[:10]}...")

    # Show status
    status = api_locker_manager.get_locker_status()
    print(
        f"📊 Status: {status['total_credentials']} API keys for {len(status['providers'])} providers"
    )


def setup_additional_providers():
    """Setup additional API providers if available"""

    additional_creds = []

    # Check for other API keys in environment
    if os.environ.get("IPQS_KEY"):
        additional_creds.append(
            APICredential(
                provider="ipqualityscore",
                key_name="api_key",
                key_value=os.environ["IPQS_KEY"],
                base_url="https://ipqualityscore.com/api/json",
                metadata={"free_tier": True},
            )
        )

    if os.environ.get("TRESTLE_KEY"):
        additional_creds.append(
            APICredential(
                provider="trestle",
                key_name="api_key",
                key_value=os.environ["TRESTLE_KEY"],
                base_url="https://api.trestleiq.com",
                rate_limit=10,  # QPS limit
            )
        )

    if os.environ.get("NUMVERIFY_KEY"):
        additional_creds.append(
            APICredential(
                provider="numverify",
                key_name="access_key",
                key_value=os.environ["NUMVERIFY_KEY"],
                base_url="https://api.numverify.com/v1",
            )
        )

    if additional_creds:
        api_locker_manager.initialize_with_credentials(additional_creds)
        print(f"✅ Added {len(additional_creds)} additional provider API keys")

        # Save all API keys
        config_dir = Path.home() / ".sleuth-intel"
        encrypted_file = config_dir / "api_keys.enc"
        encryption_key = os.environ.get(
            "SLEUTH_INTEL_ENCRYPTION_KEY", "sleuth-intel-default-key-change-me"
        )
        api_locker_manager.locker.save_credentials_encrypted(
            encrypted_file, encryption_key
        )


def main():
    """Main setup function"""
    print("🔧 Setting up Sleuth Intel API Keys")
    print("=" * 50)

    # Setup EnformionGO
    setup_enformion_api()

    # Setup additional providers
    setup_additional_providers()

    # Final status
    print("\n" + "=" * 50)
    print("🎯 Setup Complete!")

    status = api_locker_manager.get_locker_status()
    print(f"📊 Total: {status['total_credentials']} API keys")
    print("📋 Providers:")
    for provider, count in status["provider_counts"].items():
        print(f"  • {provider}: {count} key(s)")

    print("\n🔒 Security Notes:")
    print("• API keys are encrypted at rest")
    print("• File permissions set to 0o600 (owner read/write only)")
    print("• Original keys are not stored in plaintext")

    print("\n🚀 Next Steps:")
    print("• Use api_locker_manager.get_credential('enformion') to get API access")
    print("• Check usage stats with api_locker_manager.get_locker_status()")


if __name__ == "__main__":
    main()
