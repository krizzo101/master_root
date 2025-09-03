#!/usr/bin/env python3
"""
Add new tokens to the encrypted token storage
"""

import sys
from pathlib import Path

# Add path for imports
sys.path.insert(0, "/home/opsvi/master_root/apps/multi-agent-monitor")
from src.orchestration.secrets_manager import TokenSecretsManager


def add_new_tokens():
    """Add new tokens to encrypted storage"""

    # New tokens to add
    new_tokens = [
        "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",
        "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",
        "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",
    ]

    # Load existing token manager
    manager = TokenSecretsManager()

    # Get current tokens
    current_tokens = manager.load_tokens()
    print(f"Current token count: {len(current_tokens)}")

    # Find next available slot
    token_num = 16  # Start after the existing 15
    added_count = 0

    for token in new_tokens:
        key = f"CLAUDE_CODE_TOKEN{token_num}"
        if key not in current_tokens:
            # Add the new token
            manager.save_token(key, token)
            print(f"✅ Added {key}")
            added_count += 1
            token_num += 1
        else:
            print(f"⚠️  {key} already exists, skipping")
            token_num += 1

    # Verify the tokens were added
    updated_tokens = manager.load_tokens()
    print(f"\n✅ Token storage updated!")
    print(f"Previous count: {len(current_tokens)}")
    print(f"New tokens added: {added_count}")
    print(f"Total tokens now: {len(updated_tokens)}")

    # List all token keys
    print("\nAvailable token keys:")
    for key in sorted(updated_tokens.keys()):
        if key.startswith("CLAUDE_CODE_TOKEN"):
            print(f"  - {key}")

    return len(updated_tokens)


if __name__ == "__main__":
    total = add_new_tokens()
    print(
        f"\n🎉 Success! Orchestrator now has access to {total} tokens for parallel execution!"
    )
