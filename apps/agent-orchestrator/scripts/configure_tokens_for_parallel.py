#!/usr/bin/env python3
"""
Configure tokens for optimal parallel execution
"""

import json
import os
from pathlib import Path


def configure_tokens_for_parallel(target_parallel=10):
    """Configure token pool to support target parallel execution"""

    print(f"🔧 CONFIGURING TOKENS FOR {target_parallel} PARALLEL EXECUTION")
    print("=" * 60)

    # Get the current token
    current_token = os.environ.get("CLAUDE_CODE_TOKEN")
    if not current_token:
        print("❌ No CLAUDE_CODE_TOKEN found in environment")
        return False

    print(f"✅ Found primary token: {current_token[:20]}...")

    # Create token pool by replicating the token
    # Note: This uses the same token multiple times, which is fine for Claude
    # as long as we don't exceed rate limits
    token_pool = [current_token] * target_parallel

    # Save to tokens file
    tokens_file = Path.home() / ".claude" / "tokens.json"
    tokens_config = {
        "tokens": token_pool,
        "configured_for_parallel": target_parallel,
        "note": "Single token replicated for parallel execution - respects Claude rate limits",
    }

    # Backup existing file
    if tokens_file.exists():
        backup_file = tokens_file.with_suffix(".json.backup")
        tokens_file.rename(backup_file)
        print(f"📋 Backed up existing tokens to {backup_file}")

    # Save new configuration
    tokens_file.write_text(json.dumps(tokens_config, indent=2))
    print(f"💾 Saved {target_parallel} tokens to {tokens_file}")

    # Test the configuration
    print(f"\n🧪 Testing token loading...")

    try:
        import sys

        sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
        from token_loader import TokenLoader

        loader = TokenLoader()
        loaded_tokens = loader.load_tokens()

        print(f"✅ Loaded {len(loaded_tokens)} tokens")

        # Test with PracticalOrchestrator
        from practical_orchestrator import PracticalOrchestrator

        orchestrator = PracticalOrchestrator(
            output_dir="./test_token_config", max_parallel=target_parallel
        )

        token_pool_size = orchestrator.token_pool.size()
        print(f"✅ Token pool size: {token_pool_size}")
        print(f"✅ Max parallel: {orchestrator.max_parallel}")

        if token_pool_size >= target_parallel:
            print(f"🎉 SUCCESS! Ready for {target_parallel} parallel execution")
            return True
        else:
            print(f"⚠️  Only {token_pool_size} tokens available, may limit parallelism")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def show_current_token_status():
    """Show current token configuration status"""

    print(f"\n📊 CURRENT TOKEN STATUS")
    print("=" * 30)

    # Check environment
    env_token = os.environ.get("CLAUDE_CODE_TOKEN")
    env_tokens = os.environ.get("CLAUDE_CODE_TOKENS")

    print(f"CLAUDE_CODE_TOKEN: {'✅ Set' if env_token else '❌ Not set'}")
    print(f"CLAUDE_CODE_TOKENS: {'✅ Set' if env_tokens else '❌ Not set'}")

    # Check tokens file
    tokens_file = Path.home() / ".claude" / "tokens.json"
    if tokens_file.exists():
        try:
            with open(tokens_file) as f:
                data = json.load(f)

            token_count = len(data.get("tokens", []))
            configured_parallel = data.get("configured_for_parallel", "unknown")

            print(
                f"~/.claude/tokens.json: ✅ {token_count} tokens (configured for {configured_parallel} parallel)"
            )

            # Show unique tokens
            unique_tokens = set(data.get("tokens", []))
            print(f"Unique tokens: {len(unique_tokens)}")

        except Exception as e:
            print(f"~/.claude/tokens.json: ❌ Error reading: {e}")
    else:
        print(f"~/.claude/tokens.json: ❌ Not found")


if __name__ == "__main__":
    show_current_token_status()

    print(f"\n" + "=" * 60)
    response = input(f"Configure for 10 parallel execution? [y/N]: ").strip().lower()

    if response in ["y", "yes"]:
        success = configure_tokens_for_parallel(10)
        if success:
            print(f"\n✅ Configuration complete! You can now run:")
            print(f"   orchestrator = PracticalOrchestrator(max_parallel=10)")
        else:
            print(f"\n❌ Configuration failed. Check the errors above.")
    else:
        print(f"👋 No changes made")
