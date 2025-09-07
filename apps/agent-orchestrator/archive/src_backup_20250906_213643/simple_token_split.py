#!/usr/bin/env python3
"""
Simple Token Splitting for 2 Orchestrators
Split 19 tokens between chat import (15 tokens) and dashboard build (4 tokens)
"""

import json
import os
from pathlib import Path
from typing import List


def split_tokens_for_two_orchestrators() -> dict:
    """Split tokens between chat import (primary) and dashboard build (secondary)"""

    # Load all available tokens
    from token_loader import TokenLoader

    loader = TokenLoader()
    all_tokens = loader.load_tokens()

    if len(all_tokens) < 2:
        raise ValueError(f"Need at least 2 tokens, got {len(all_tokens)}")

    # Split: Chat import gets majority (15), dashboard gets minority (4)
    chat_import_count = max(15, len(all_tokens) - 4)  # At least 15 or all-4
    dashboard_count = min(4, len(all_tokens) - chat_import_count)  # Up to 4

    chat_tokens = all_tokens[:chat_import_count]
    dashboard_tokens = all_tokens[
        chat_import_count : chat_import_count + dashboard_count
    ]

    return {
        "chat_import": chat_tokens,
        "dashboard": dashboard_tokens,
        "total_tokens": len(all_tokens),
        "split": f"{len(chat_tokens)} chat + {len(dashboard_tokens)} dashboard",
    }


def save_split_tokens():
    """Save split token configuration to files"""
    split = split_tokens_for_two_orchestrators()

    claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Save chat import tokens
    chat_file = claude_dir / "tokens_chat_import.json"
    with open(chat_file, "w") as f:
        json.dump({"tokens": split["chat_import"]}, f, indent=2)

    # Save dashboard tokens
    dashboard_file = claude_dir / "tokens_dashboard.json"
    with open(dashboard_file, "w") as f:
        json.dump({"tokens": split["dashboard"]}, f, indent=2)

    print(f"✅ Token split complete: {split['split']}")
    print(f"📁 Chat import tokens: {chat_file}")
    print(f"📁 Dashboard tokens: {dashboard_file}")

    return {"chat_file": str(chat_file), "dashboard_file": str(dashboard_file), **split}


def get_tokens_for_orchestrator(orchestrator_type: str) -> List[str]:
    """Get tokens for specific orchestrator type"""

    if orchestrator_type == "chat_import":
        token_file = Path.home() / ".claude" / "tokens_chat_import.json"
    elif orchestrator_type == "dashboard":
        token_file = Path.home() / ".claude" / "tokens_dashboard.json"
    else:
        raise ValueError(f"Unknown orchestrator type: {orchestrator_type}")

    if not token_file.exists():
        # Fallback: split tokens on demand
        save_split_tokens()

    with open(token_file) as f:
        data = json.load(f)
        return data.get("tokens", [])


if __name__ == "__main__":
    print("🔄 Splitting tokens for 2 orchestrators...")
    result = save_split_tokens()

    print(f"\n📊 Distribution:")
    print(f"  Chat Import: {len(result['chat_import'])} tokens")
    print(f"  Dashboard:   {len(result['dashboard'])} tokens")
    print(f"  Total:       {result['total_tokens']} tokens")
