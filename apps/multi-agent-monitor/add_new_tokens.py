#!/usr/bin/env python3
"""
Add new tokens from new_keys.txt to encrypted storage
"""

import sys
from pathlib import Path

# Add parent directory to path to avoid import issues
sys.path.insert(0, str(Path(__file__).parent))
from src.orchestration.secrets_manager import TokenSecretsManager


def add_tokens_from_file():
    """Add new tokens to encrypted storage"""

    # Read new tokens from file
    keys_file = Path(__file__).parent / ".secrets" / "new_keys.txt"
    if not keys_file.exists():
        print(f"❌ File not found: {keys_file}")
        return

    new_tokens = []
    with open(keys_file, "r") as f:
        for line in f:
            token = line.strip()
            if token and token.startswith("sk-ant-"):
                new_tokens.append(token)

    print(f"Found {len(new_tokens)} new tokens to add")

    # Load existing token manager
    manager = TokenSecretsManager()

    # Get current tokens
    current_tokens = manager.load_tokens()
    print(f"Current token count: {len(current_tokens)}")

    # Find the highest existing token number
    max_num = 0
    for key in current_tokens.keys():
        if key.startswith("CLAUDE_CODE_TOKEN"):
            try:
                num_str = key.replace("CLAUDE_CODE_TOKEN", "")
                if num_str.isdigit():
                    max_num = max(max_num, int(num_str))
            except:
                pass

    print(f"Highest existing token number: {max_num}")

    # Add new tokens starting from next available number
    token_num = max_num + 1
    added_count = 0

    # Load current tokens and add new ones
    all_tokens = current_tokens.copy()

    for token in new_tokens:
        key = f"CLAUDE_CODE_TOKEN{token_num}"
        if key not in all_tokens:
            # Add the new token
            all_tokens[key] = token
            print(f"✅ Added {key}")
            added_count += 1
            token_num += 1
        else:
            print(f"⚠️  {key} already exists, trying next number...")
            token_num += 1

    # Save all tokens back
    manager.save_tokens(all_tokens)

    # Verify the tokens were added
    updated_tokens = manager.load_tokens()
    print(f"\n✅ Token storage updated!")
    print(f"Previous count: {len(current_tokens)}")
    print(f"New tokens added: {added_count}")
    print(f"Total tokens now: {len(updated_tokens)}")

    # List all token keys
    print("\nAll token keys in storage:")
    token_keys = sorted(
        [k for k in updated_tokens.keys() if k.startswith("CLAUDE_CODE_TOKEN")]
    )
    for key in token_keys:
        print(f"  - {key}")

    return len(updated_tokens)


if __name__ == "__main__":
    try:
        total = add_tokens_from_file()
        print(f"\n🎉 Success! Token pool now has {total} tokens for parallel execution!")
    except Exception as e:
        print(f"❌ Error adding tokens: {e}")
        import traceback

        traceback.print_exc()
