#!/usr/bin/env python3
"""
Token Loader for Agent Orchestrator
Integrates with multi-agent-monitor's encrypted token storage
"""

import os
import sys
from pathlib import Path
from typing import List, Optional


def load_tokens_from_secrets() -> List[str]:
    """Load tokens from the encrypted secrets storage"""

    tokens = []

    # Try to load from multi-agent-monitor's secrets
    try:
        # Add multi-agent-monitor to path if not already there
        monitor_path = Path("/home/opsvi/master_root/apps/multi-agent-monitor")
        if monitor_path.exists():
            sys.path.insert(0, str(monitor_path))  # Add root path

            # Import the secrets manager
            from src.orchestration.secrets_manager import TokenSecretsManager

            # Load encrypted tokens
            secrets_mgr = TokenSecretsManager(monitor_path)
            token_dict = secrets_mgr.load_tokens()

            # Extract token values in order
            for i in range(1, 100):  # Check up to 100 tokens
                key = f"CLAUDE_CODE_TOKEN{i}"
                if key in token_dict:
                    value = token_dict[key]
                    if value and len(value) > 20:  # Basic validation
                        tokens.append(value)

            if tokens:
                print(f"✅ Loaded {len(tokens)} tokens from encrypted storage")
                return tokens
    except ImportError as e:
        print(f"⚠️  Could not import secrets manager: {e}")
    except Exception as e:
        print(f"⚠️  Could not load from encrypted storage: {e}")

    # Fallback: Check environment variables
    # Primary token
    primary = os.environ.get("CLAUDE_CODE_TOKEN")
    if primary:
        tokens.append(primary)

    # Additional numbered tokens
    for i in range(1, 10):
        # Check both formats
        for key in [f"CLAUDE_CODE_TOKEN{i}", f"CLAUDE_CODE_TOKEN_{i}"]:
            token = os.environ.get(key)
            if token:
                tokens.append(token)

    if tokens:
        print(f"✅ Loaded {len(tokens)} tokens from environment")
    else:
        print("❌ No tokens found in encrypted storage or environment")
        print("\nTo set up tokens:")
        print("1. Set CLAUDE_CODE_TOKEN environment variable, OR")
        print("2. Use multi-agent-monitor's token management:")
        print("   cd /home/opsvi/master_root/apps/multi-agent-monitor")
        print("   python3 src/orchestration/secrets_manager.py")

    return tokens


def get_token_pool():
    """Get a configured token pool with all available tokens"""
    from generic_orchestrator import TokenPool

    # Load tokens from all sources
    tokens = load_tokens_from_secrets()

    if not tokens:
        # Last resort: try to use default environment token
        return TokenPool()  # Will use CLAUDE_CODE_TOKEN if set

    return TokenPool(tokens)


if __name__ == "__main__":
    # Test token loading
    tokens = load_tokens_from_secrets()
    print(f"\nFound {len(tokens)} tokens")

    if tokens:
        print("Token sources validated (not showing actual tokens for security)")
        for i, token in enumerate(tokens, 1):
            print(f"  Token {i}: {'*' * 10}{token[-4:] if len(token) > 4 else '****'}")
    else:
        print("No tokens available - please configure tokens first")
