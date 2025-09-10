#!/usr/bin/env python3
"""
Simple script to add Claude tokens to encrypted storage
Use this after running 'claude setup-token' in a real terminal
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.orchestration.secrets_manager import TokenSecretsManager


def main():
    print("=" * 60)
    print("Claude Token Storage Helper")
    print("=" * 60)

    manager = TokenSecretsManager(app_root=Path(__file__).parent)

    # Show current status
    existing_tokens = manager.list_tokens()
    print(f"\n📦 Currently stored tokens: {len(existing_tokens)}")
    if existing_tokens:
        print(
            f"   Numbers: {', '.join(sorted(existing_tokens, key=lambda x: int(x) if x.isdigit() else 0))}"
        )

    print("\n" + "-" * 60)
    print("Instructions:")
    print("1. Open a real terminal (outside Claude Code)")
    print("2. Run: claude setup-token")
    print("3. Click 'Authorize' in the browser")
    print("4. Copy the token that appears")
    print("5. Paste it below")
    print("-" * 60)

    # Get token from user
    print("\nPaste your Claude token (it will be hidden):")
    token = getpass.getpass("Token: ").strip()

    if not token:
        print("❌ No token provided")
        return 1

    # Validate format
    if not token.startswith("sk-ant-"):
        print(f"\n⚠️  Warning: Token doesn't start with 'sk-ant-'")
        print(f"Token starts with: {token[:10]}...")
        if input("Save anyway? (y/n): ").lower() != "y":
            print("❌ Cancelled")
            return 1

    # Find next token number
    token_numbers = [int(t) for t in existing_tokens if t.isdigit()]
    next_num = max(token_numbers) + 1 if token_numbers else 1

    # Save token
    try:
        manager.add_token(next_num, token)
        print(f"\n✅ Token saved as CLAUDE_CODE_TOKEN{next_num}")

        # Show updated summary
        all_tokens = manager.list_tokens()
        print(f"\n📊 Updated Token Storage:")
        print(f"   Total tokens: {len(all_tokens)}")
        print(
            f"   Token numbers: {', '.join(sorted(all_tokens, key=lambda x: int(x) if x.isdigit() else 0))}"
        )

        # Validate
        validation = manager.validate_tokens()
        invalid = [k for k, v in validation.items() if not v]
        if invalid:
            print(f"   ⚠️  Invalid tokens: {', '.join(invalid)}")
        else:
            print(f"   ✅ All tokens validated successfully")

        print(f"\n🔐 Token securely stored in encrypted storage")
        print(f"Location: {manager.tokens_file}")

        return 0

    except Exception as e:
        print(f"\n❌ Error saving token: {e}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
