#!/usr/bin/env python3
"""Demonstrate configuration capabilities."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_code import ClaudeCodeConfig


def demonstrate_config():
    """Demonstrate configuration capabilities."""
    print("⚙️  Claude Code Clone - Configuration Demo")
    print("=" * 50)

    # Demo 1: Default configuration
    print("📋 **Demo 1: Default Configuration**")
    print("-" * 40)

    config = ClaudeCodeConfig()
    print(f"✅ Provider: {config.provider}")
    print(f"✅ Model: {config.model}")
    print(f"✅ Max Tokens: {config.max_tokens}")
    print(f"✅ Temperature: {config.temperature}")
    print(f"✅ Working Directory: {config.working_directory}")
    print(f"✅ File Operations: {config.enable_file_operations}")
    print(f"✅ Shell Operations: {config.enable_shell_operations}")
    print(f"✅ Streaming: {config.enable_streaming}")
    print(f"✅ Allowed Extensions: {len(config.allowed_file_extensions)} file types")
    print(f"✅ Max File Size: {config.max_file_size / 1024 / 1024:.1f} MB")
    print()

    # Demo 2: Custom configuration
    print("🔧 **Demo 2: Custom Configuration**")
    print("-" * 40)

    custom_config = ClaudeCodeConfig(
        provider="anthropic",
        model="claude-3-opus",
        max_tokens=8000,
        temperature=0.3,
        working_directory="/tmp/claude_code",
        enable_file_operations=True,
        enable_shell_operations=False,
        max_file_size=2 * 1024 * 1024,  # 2MB
        custom_instructions="You are a security-focused code reviewer.",
        context_window=200000,
    )

    print(f"✅ Provider: {custom_config.provider}")
    print(f"✅ Model: {custom_config.model}")
    print(f"✅ Max Tokens: {custom_config.max_tokens}")
    print(f"✅ Temperature: {custom_config.temperature}")
    print(f"✅ Working Directory: {custom_config.working_directory}")
    print(f"✅ Max File Size: {custom_config.max_file_size / 1024 / 1024:.1f} MB")
    print(f"✅ Custom Instructions: {custom_config.custom_instructions}")
    print(f"✅ Context Window: {custom_config.context_window}")
    print()

    # Demo 3: Environment variable configuration
    print("🌍 **Demo 3: Environment Variable Configuration**")
    print("-" * 40)

    # Set some environment variables
    os.environ["CLAUDE_CODE_PROVIDER"] = "perplexity"
    os.environ["CLAUDE_CODE_MODEL"] = "perplexity-pro"
    os.environ["CLAUDE_CODE_MAX_TOKENS"] = "6000"
    os.environ["CLAUDE_CODE_TEMPERATURE"] = "0.2"
    os.environ["CLAUDE_CODE_ENABLE_SHELL_OPERATIONS"] = "true"

    env_config = ClaudeCodeConfig()
    print(f"✅ Provider: {env_config.provider}")
    print(f"✅ Model: {env_config.model}")
    print(f"✅ Max Tokens: {env_config.max_tokens}")
    print(f"✅ Temperature: {env_config.temperature}")
    print(f"✅ Shell Operations: {env_config.enable_shell_operations}")
    print()

    # Demo 4: File extension validation
    print("📁 **Demo 4: File Extension Support**")
    print("-" * 40)

    print("✅ Supported file extensions:")
    extensions = sorted(config.allowed_file_extensions)
    for i, ext in enumerate(extensions):
        if i % 8 == 0:
            print()
        print(f"{ext:>6}", end="  ")
    print()
    print()

    # Demo 5: Security configuration
    print("🔒 **Demo 5: Security Configuration**")
    print("-" * 40)

    security_config = ClaudeCodeConfig(
        enable_file_operations=True,
        enable_shell_operations=False,
        allowed_shell_commands=[],
        max_file_size=1024 * 1024,  # 1MB limit
    )

    print(f"✅ File Operations: {security_config.enable_file_operations}")
    print(f"✅ Shell Operations: {security_config.enable_shell_operations}")
    print(f"✅ Allowed Shell Commands: {len(security_config.allowed_shell_commands)}")
    print(f"✅ Max File Size: {security_config.max_file_size / 1024 / 1024:.1f} MB")
    print()

    # Demo 6: Provider-specific configuration
    print("🤖 **Demo 6: Provider-Specific Configuration**")
    print("-" * 40)

    providers = [
        ("openai", "gpt-5-mini", "OpenAI GPT models"),
        ("anthropic", "claude-3-opus", "Anthropic Claude models"),
        ("perplexity", "perplexity-pro", "Perplexity Pro models"),
    ]

    for provider, model, description in providers:
        provider_config = ClaudeCodeConfig(
            provider=provider,
            model=model,
            api_key=f"{provider}_api_key_here",
        )
        print(f"✅ {provider.title()}: {model}")
        print(f"   📝 {description}")
        print(f"   🔑 API Key: {'Set' if provider_config.api_key else 'Not set'}")
        print()

    print("🎉 Configuration demonstration complete!")


if __name__ == "__main__":
    demonstrate_config()

