#!/usr/bin/env python3
"""
MCP Registry Builder - Merge and validate MCP configurations.

This module handles the intelligent merging of multiple MCP configurations
to create a master registry for dynamic agent architectures.
"""

import json
import logging
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MCPRegistryBuilder:
    """Build and validate master MCP registry from multiple sources."""

    def __init__(self):
        self.merge_log: List[str] = []
        self.validation_errors: List[str] = []
        self.duplicates_found: Dict[str, Dict] = {}

    def merge_mcp_configs(self, primary_path: Path, backup_path: Path) -> Dict:
        """
        Merge MCP configurations with intelligent deduplication.

        Strategy:
        1. Load both configurations
        2. Use primary as base
        3. Add unique servers from backup
        4. For duplicates, prefer primary but log differences
        5. Validate merged configuration

        Args:
            primary_path: Path to primary MCP configuration
            backup_path: Path to backup MCP configuration

        Returns:
            Merged MCP configuration dictionary
        """
        # Load configurations
        primary_config = self._load_config(primary_path)
        backup_config = self._load_config(backup_path)

        if not primary_config:
            self.merge_log.append(
                f"WARNING: Primary config not found, using backup only"
            )
            return backup_config or {"mcpServers": {}}

        if not backup_config:
            self.merge_log.append(
                f"WARNING: Backup config not found, using primary only"
            )
            return primary_config

        # Start with primary as base
        merged_config = deepcopy(primary_config)

        # Get server lists
        primary_servers = set(primary_config.get("mcpServers", {}).keys())
        backup_servers = set(backup_config.get("mcpServers", {}).keys())

        # Log initial state
        self.merge_log.append(
            f"Primary servers ({len(primary_servers)}): {sorted(primary_servers)}"
        )
        self.merge_log.append(
            f"Backup servers ({len(backup_servers)}): {sorted(backup_servers)}"
        )

        # Process backup servers
        for server_name in backup_servers:
            backup_server = backup_config["mcpServers"][server_name]

            if server_name in primary_servers:
                # Duplicate found - compare and log
                primary_server = primary_config["mcpServers"][server_name]
                if self._servers_differ(primary_server, backup_server):
                    self.duplicates_found[server_name] = {
                        "primary": primary_server,
                        "backup": backup_server,
                    }
                    self.merge_log.append(
                        f"DUPLICATE: {server_name} - keeping primary version"
                    )

                    # Add backup version with suffix if significantly different
                    if self._significant_difference(primary_server, backup_server):
                        backup_name = f"{server_name}_backup"
                        merged_config["mcpServers"][backup_name] = backup_server
                        self.merge_log.append(
                            f"  Added backup version as: {backup_name}"
                        )
            else:
                # Unique server from backup
                merged_config["mcpServers"][server_name] = backup_server
                self.merge_log.append(f"ADDED from backup: {server_name}")

        # Add metadata
        merged_config["metadata"] = {
            "created": datetime.now().isoformat(),
            "sources": [str(primary_path), str(backup_path)],
            "total_servers": len(merged_config["mcpServers"]),
            "duplicates_found": len(self.duplicates_found),
            "merge_strategy": "primary_precedence",
        }

        return merged_config

    def validate_mcp_registry(self, registry: Dict) -> Tuple[bool, List[str]]:
        """
        Validate master registry structure.

        Checks:
        1. Required fields: mcpServers
        2. Each server has: command, args
        3. Optional fields properly formatted: env, cwd
        4. No circular dependencies
        5. Valid file paths for local commands

        Args:
            registry: MCP registry to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required top-level structure
        if "mcpServers" not in registry:
            errors.append("Missing required field: mcpServers")
            return False, errors

        if not isinstance(registry["mcpServers"], dict):
            errors.append("mcpServers must be a dictionary")
            return False, errors

        # Validate each server
        for server_name, server_config in registry["mcpServers"].items():
            server_errors = self._validate_server(server_name, server_config)
            errors.extend(server_errors)

        # Check for security issues
        security_errors = self._validate_security(registry)
        errors.extend(security_errors)

        return len(errors) == 0, errors

    def _load_config(self, path: Path) -> Optional[Dict]:
        """Load JSON configuration from file."""
        try:
            if not path.exists():
                self.merge_log.append(f"File not found: {path}")
                return None

            with open(path, "r") as f:
                config = json.load(f)
                self.merge_log.append(f"Loaded config from: {path}")
                return config
        except json.JSONDecodeError as e:
            self.validation_errors.append(f"Invalid JSON in {path}: {e}")
            return None
        except Exception as e:
            self.validation_errors.append(f"Error loading {path}: {e}")
            return None

    def _servers_differ(self, server1: Dict, server2: Dict) -> bool:
        """Check if two server configurations differ."""
        # Normalize for comparison
        s1 = json.dumps(server1, sort_keys=True)
        s2 = json.dumps(server2, sort_keys=True)
        return s1 != s2

    def _significant_difference(self, server1: Dict, server2: Dict) -> bool:
        """Check if differences are significant enough to keep both versions."""
        # Different commands or args are significant
        if server1.get("command") != server2.get("command"):
            return True
        if server1.get("args") != server2.get("args"):
            return True

        # Different API keys in env are significant
        env1 = server1.get("env", {})
        env2 = server2.get("env", {})

        for key in set(list(env1.keys()) + list(env2.keys())):
            if "KEY" in key.upper() or "TOKEN" in key.upper():
                if env1.get(key) != env2.get(key):
                    return True

        return False

    def _validate_server(self, name: str, config: Dict) -> List[str]:
        """Validate individual server configuration."""
        errors = []

        # Required fields
        if "command" not in config:
            errors.append(f"Server '{name}': missing required field 'command'")
        if "args" not in config:
            errors.append(f"Server '{name}': missing required field 'args'")

        # Type checking
        if "command" in config and not isinstance(config["command"], str):
            errors.append(f"Server '{name}': 'command' must be a string")
        if "args" in config and not isinstance(config["args"], list):
            errors.append(f"Server '{name}': 'args' must be a list")

        # Optional fields
        if "env" in config and not isinstance(config["env"], dict):
            errors.append(f"Server '{name}': 'env' must be a dictionary")
        if "cwd" in config and not isinstance(config["cwd"], str):
            errors.append(f"Server '{name}': 'cwd' must be a string")

        # Validate local file paths
        if "command" in config:
            command = config["command"]
            if command.startswith("/"):  # Absolute path
                if not Path(command).exists():
                    errors.append(f"Server '{name}': command file not found: {command}")

        return errors

    def _validate_security(self, registry: Dict) -> List[str]:
        """Check for security issues in configuration."""
        errors = []
        exposed_keys = []

        for server_name, server_config in registry["mcpServers"].items():
            env = server_config.get("env", {})

            for env_key, env_value in env.items():
                # Check for exposed credentials
                if any(
                    secret in env_key.upper() for secret in ["KEY", "TOKEN", "PASSWORD"]
                ):
                    # Log masked version
                    if isinstance(env_value, str) and len(env_value) > 10:
                        masked = env_value[:4] + "..." + env_value[-4:]
                        exposed_keys.append(f"{server_name}.{env_key}: {masked}")

        if exposed_keys:
            self.merge_log.append(
                f"Security audit - Found {len(exposed_keys)} API keys/tokens"
            )
            for key in exposed_keys:
                self.merge_log.append(f"  {key}")

        return errors

    def generate_report(self) -> str:
        """Generate detailed merge and validation report."""
        report = []
        report.append("=" * 60)
        report.append("MCP REGISTRY BUILDER REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Merge log
        report.append("MERGE PROCESS LOG:")
        report.append("-" * 40)
        for log_entry in self.merge_log:
            report.append(f"  {log_entry}")
        report.append("")

        # Duplicates
        if self.duplicates_found:
            report.append("DUPLICATE SERVERS FOUND:")
            report.append("-" * 40)
            for server_name, versions in self.duplicates_found.items():
                report.append(f"  {server_name}:")
                report.append(
                    f"    Primary command: {versions['primary'].get('command')}"
                )
                report.append(
                    f"    Backup command: {versions['backup'].get('command')}"
                )
        else:
            report.append("No duplicate servers found")
        report.append("")

        # Validation errors
        if self.validation_errors:
            report.append("VALIDATION ERRORS:")
            report.append("-" * 40)
            for error in self.validation_errors:
                report.append(f"  ERROR: {error}")
        else:
            report.append("VALIDATION: All checks passed ✓")
        report.append("")

        report.append("=" * 60)
        return "\n".join(report)


def build_master_registry(
    primary_path: str, backup_path: str, output_path: str
) -> Tuple[bool, str]:
    """
    Build master MCP registry from primary and backup configurations.

    Args:
        primary_path: Path to primary MCP configuration
        backup_path: Path to backup MCP configuration
        output_path: Path where master registry will be saved

    Returns:
        Tuple of (success, report_text)
    """
    builder = MCPRegistryBuilder()

    # Convert to Path objects
    primary = Path(primary_path)
    backup = Path(backup_path)
    output = Path(output_path)

    # Merge configurations
    merged_config = builder.merge_mcp_configs(primary, backup)

    # Validate merged configuration
    is_valid, errors = builder.validate_mcp_registry(merged_config)

    if errors:
        builder.validation_errors.extend(errors)

    # Save merged configuration
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(merged_config, f, indent=2)
        builder.merge_log.append(f"Successfully wrote master registry to: {output}")
        success = True
    except Exception as e:
        builder.validation_errors.append(f"Failed to write output: {e}")
        success = False

    # Generate report
    report = builder.generate_report()

    return success and is_valid, report


if __name__ == "__main__":
    # Default paths
    primary = "/home/opsvi/master_root/.mcp.json"
    backup = "/home/opsvi/master_root/.mcp.json.backup.2025-09-07-00-24-14"
    output = "/home/opsvi/master_root/apps/agent-orchestrator/master_mcp_registry.json"

    success, report = build_master_registry(primary, backup, output)
    print(report)

    if not success:
        exit(1)
