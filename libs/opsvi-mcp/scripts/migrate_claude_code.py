#!/usr/bin/env python3
"""
Migration script for Claude Code MCP Server
Helps transition from TypeScript to Python implementation
"""

import os
import sys
import json
import shutil
from pathlib import Path


def backup_original_config(config_path: Path) -> None:
    """Backup the original MCP configuration"""
    if config_path.exists():
        backup_path = config_path.with_suffix(".json.bak")
        shutil.copy2(config_path, backup_path)
        print(f"✓ Backed up configuration to {backup_path}")


def update_mcp_config(config_path: Path) -> None:
    """Update MCP configuration to use Python implementation"""
    if not config_path.exists():
        print(f"⚠ Configuration file not found: {config_path}")
        return

    with open(config_path, "r") as f:
        config = json.load(f)

    # Check if claude-code-wrapper exists
    if "mcpServers" in config and "claude-code-wrapper" in config["mcpServers"]:
        old_config = config["mcpServers"]["claude-code-wrapper"]

        # Create new configuration
        new_config = {
            "command": "/home/opsvi/miniconda/bin/python",
            "args": ["-m", "opsvi_mcp.servers.claude_code"],
            "env": {
                "PYTHONPATH": "/home/opsvi/master_root/libs",
                "CLAUDE_CODE_TOKEN": old_config.get("env", {}).get(
                    "CLAUDE_CODE_TOKEN", "${CLAUDE_CODE_TOKEN}"
                ),
                "CLAUDE_MAX_RECURSION_DEPTH": "3",
                "CLAUDE_MAX_CONCURRENT_AT_DEPTH": "5",
                "CLAUDE_MAX_TOTAL_JOBS": "20",
                "CLAUDE_LOG_LEVEL": "INFO",
                "CLAUDE_PERF_LOGGING": "true",
                "CLAUDE_CHILD_LOGGING": "true",
                "CLAUDE_RECURSION_LOGGING": "true",
            },
        }

        # Update configuration
        config["mcpServers"]["claude-code-wrapper"] = new_config

        # Write updated configuration
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✓ Updated MCP configuration: {config_path}")
    else:
        print("⚠ claude-code-wrapper not found in configuration")


def check_dependencies() -> bool:
    """Check if required Python packages are installed"""
    required = ["mcp", "psutil", "python-dotenv"]
    missing = []

    for package in required:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"⚠ Missing dependencies: {', '.join(missing)}")
        print(f"  Install with: pip install {' '.join(missing)}")
        return False

    print("✓ All required dependencies installed")
    return True


def check_claude_token() -> bool:
    """Check if Claude Code token is configured"""
    token = os.getenv("CLAUDE_CODE_TOKEN")

    if not token:
        # Check .env file
        env_paths = [
            Path.home() / ".env",
            Path.cwd() / ".env",
            Path("/home/opsvi/master_root") / ".env",
        ]

        for env_path in env_paths:
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("CLAUDE_CODE_TOKEN="):
                            token = line.split("=", 1)[1].strip()
                            break
            if token:
                break

    if token:
        print("✓ Claude Code token found")
        return True
    else:
        print("⚠ Claude Code token not found")
        print("  Set CLAUDE_CODE_TOKEN in environment or .env file")
        return False


def create_logs_directory() -> None:
    """Create logs directory for Claude Code"""
    logs_dir = Path("/home/opsvi/master_root/logs/claude-code")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Logs directory ready: {logs_dir}")


def test_import() -> bool:
    """Test if the new implementation can be imported"""
    try:
        sys.path.insert(0, "/home/opsvi/master_root/libs")
        from opsvi_mcp.servers.claude_code import ClaudeCodeServer

        print("✓ Python implementation imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Python implementation: {e}")
        return False


def main():
    """Main migration process"""
    print("Claude Code MCP Server Migration Tool")
    print("=" * 50)

    # Check environment
    print("\n1. Checking environment...")
    if not check_dependencies():
        print("\n✗ Please install missing dependencies first")
        return 1

    if not check_claude_token():
        print("\n⚠ Warning: Claude Code token not configured")

    # Test import
    print("\n2. Testing Python implementation...")
    if not test_import():
        print("\n✗ Please ensure opsvi-mcp is installed")
        return 1

    # Create logs directory
    print("\n3. Setting up logs...")
    create_logs_directory()

    # Update configurations
    print("\n4. Updating MCP configurations...")
    config_paths = [
        Path("/home/opsvi/master_root/.cursor/mcp.json"),
        Path("/home/opsvi/master_root/.mcp.json"),
        Path("/home/opsvi/master_root/claude-code/.cursor/mcp.json"),
        Path("/home/opsvi/master_root/claude-code/.mcp.json"),
    ]

    for config_path in config_paths:
        if config_path.exists():
            backup_original_config(config_path)
            update_mcp_config(config_path)

    # Summary
    print("\n" + "=" * 50)
    print("Migration Complete!")
    print("\nNext steps:")
    print("1. Restart Cursor to load new configuration")
    print("2. Test the claude_run tool in Cursor")
    print("3. Check logs at: /home/opsvi/master_root/logs/claude-code/")
    print("\nOriginal TypeScript implementation preserved at:")
    print("  /home/opsvi/master_root/claude-code/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
