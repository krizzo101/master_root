#!/usr/bin/env python3
"""
Load real Claude Code tokens for HECATON
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

    # Export tokens with proper naming for HECATON
    # HECATON expects: CLAUDE_CODE_TOKEN, CLAUDE_CODE_TOKEN_1, CLAUDE_CODE_TOKEN_2, etc.

    token_count = 0

    # Map tokens to HECATON naming convention
    if "CLAUDE_CODE_TOKEN" in tokens:
        os.environ["CLAUDE_CODE_TOKEN"] = tokens["CLAUDE_CODE_TOKEN"]
        token_count += 1

    # Handle numbered tokens (they're stored as CLAUDE_CODE_TOKEN1, 2, etc)
    for i in range(1, 15):
        source_key = f"CLAUDE_CODE_TOKEN{i}"
        if source_key in tokens:
            # HECATON expects underscore before number
            target_key = f"CLAUDE_CODE_TOKEN_{i}"
            os.environ[target_key] = tokens[source_key]
            token_count += 1

            if token_count >= 5:  # We only need 5 for Phase 2
                break

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
