#!/usr/bin/env python3
"""
Fixed token loader for HECATON - handles numbered tokens properly
"""

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet


def load_real_tokens():
    """Load actual Claude Code tokens from encrypted storage"""

    # Path to multi-agent-monitor secrets
    secrets_dir = Path("/home/opsvi/master_root/apps/multi-agent-monitor/.secrets")

    # Load the key
    key_file = secrets_dir / ".key"
    with open(key_file, "rb") as f:
        key = f.read()

    cipher = Fernet(key)

    # Load encrypted tokens
    tokens_file = secrets_dir / "tokens.encrypted"
    with open(tokens_file, "rb") as f:
        encrypted = f.read()

    # Decrypt
    decrypted = cipher.decrypt(encrypted)
    tokens = json.loads(decrypted.decode())

    print(f"Debug: Found these tokens: {list(tokens.keys())[:5]}...")

    # HECATON expects: CLAUDE_CODE_TOKEN, CLAUDE_CODE_TOKEN_1, CLAUDE_CODE_TOKEN_2, etc.
    # But we have: CLAUDE_CODE_TOKEN1, CLAUDE_CODE_TOKEN2, etc.

    token_count = 0

    # Check if we have a base token
    if "CLAUDE_CODE_TOKEN" in tokens:
        os.environ["CLAUDE_CODE_TOKEN"] = tokens["CLAUDE_CODE_TOKEN"]
        token_count += 1

        # Then add numbered ones with underscores
        for i in range(1, 5):
            source_key = f"CLAUDE_CODE_TOKEN{i}"
            if source_key in tokens:
                target_key = f"CLAUDE_CODE_TOKEN_{i}"
                os.environ[target_key] = tokens[source_key]
                token_count += 1
    else:
        # No base token, so use CLAUDE_CODE_TOKEN1 as base
        if "CLAUDE_CODE_TOKEN1" in tokens:
            # Map CLAUDE_CODE_TOKEN1 -> CLAUDE_CODE_TOKEN (base)
            os.environ["CLAUDE_CODE_TOKEN"] = tokens["CLAUDE_CODE_TOKEN1"]
            token_count += 1

            # Map CLAUDE_CODE_TOKEN2 -> CLAUDE_CODE_TOKEN_1
            # Map CLAUDE_CODE_TOKEN3 -> CLAUDE_CODE_TOKEN_2, etc.
            for i in range(2, 6):  # 2 through 5
                source_key = f"CLAUDE_CODE_TOKEN{i}"
                if source_key in tokens:
                    target_key = f"CLAUDE_CODE_TOKEN_{i-1}"
                    os.environ[target_key] = tokens[source_key]
                    token_count += 1

    print(f"✅ Loaded {token_count} tokens for HECATON")

    # Verify what we have
    available = []
    for i in range(5):
        if i == 0:
            key = "CLAUDE_CODE_TOKEN"
        else:
            key = f"CLAUDE_CODE_TOKEN_{i}"

        if os.environ.get(key):
            available.append(key)

    print(f"Available tokens: {available}")

    # Always clear ANTHROPIC_API_KEY as instructed
    os.environ["ANTHROPIC_API_KEY"] = ""

    return token_count


if __name__ == "__main__":
    count = load_real_tokens()
    if count >= 5:
        print("\n🚀 Ready for 5-agent parallel execution!")
    else:
        print(f"\n⚠️ Only {count} tokens available, need 5 for full parallel")
