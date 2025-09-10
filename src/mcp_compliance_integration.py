"""Universal OpenAI Compliance Integration for MCP Tools and Project Components.

This module automatically patches and enforces OpenAI API Standards 2025 compliance
across all MCP servers, agents, and tools in the project.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Import universal compliance
from universal_openai_compliance import (
    UNIVERSAL_COMPLIANCE,
    ensure_openai_compliance,
    openai_compliance_required,
    ComplianceViolation,
)

logger = logging.getLogger(__name__)


class MCPComplianceIntegrator:
    """Integrates OpenAI compliance across all MCP tools and project components."""

    def __init__(self):
        """Initialize MCP compliance integration."""
        self.patched_components = []
        self.compliance_config = {}

    def patch_mcp_config(self, config_path: str = "/home/opsvi/master_root/.mcp.json"):
        """Patch MCP configuration to enforce compliance."""
        try:
            with open(config_path, "r") as f:
                mcp_config = json.load(f)

            logger.info(f"🔐 Patching MCP configuration: {config_path}")

            # Patch each MCP server that uses OpenAI
            for server_name, server_config in mcp_config.get("mcpServers", {}).items():
                if self._server_uses_openai(server_config):
                    self._patch_server_config(server_name, server_config)

            # Write patched config
            backup_path = f"{config_path}.backup.compliance"
            os.rename(config_path, backup_path)

            with open(config_path, "w") as f:
                json.dump(mcp_config, f, indent=2)

            logger.info(f"✅ MCP configuration patched. Backup: {backup_path}")

        except Exception as e:
            logger.error(f"❌ Failed to patch MCP config: {e}")
            raise

    def _server_uses_openai(self, server_config: Dict[str, Any]) -> bool:
        """Check if MCP server uses OpenAI."""
        env = server_config.get("env", {})

        # Check for OpenAI API key
        if "OPENAI_API_KEY" in env:
            return True

        # Check command/args for OpenAI-related packages
        command = server_config.get("command", "")
        args = server_config.get("args", [])

        openai_indicators = ["openai", "gpt", "claude", "thinking"]

        if any(indicator in command.lower() for indicator in openai_indicators):
            return True

        if any(
            any(indicator in str(arg).lower() for indicator in openai_indicators)
            for arg in args
        ):
            return True

        return False

    def _patch_server_config(self, server_name: str, server_config: Dict[str, Any]):
        """Patch individual server configuration for compliance."""
        logger.info(f"🔧 Patching server: {server_name}")

        env = server_config.get("env", {})

        # Ensure compliance environment variables
        compliance_env = {
            "OPENAI_COMPLIANCE_REQUIRED": "true",
            "OPENAI_API_STANDARDS_2025": "enforced",
            "OPENAI_APPROVED_MODELS": ",".join(
                UNIVERSAL_COMPLIANCE.APPROVED_MODELS["general"]
                + UNIVERSAL_COMPLIANCE.APPROVED_MODELS["reasoning"]
            ),
        }

        # Override legacy model if set
        if "OPENAI_MODEL" in env:
            current_model = env["OPENAI_MODEL"]
            try:
                validated_model = ensure_openai_compliance(
                    model=current_model, context=f"mcp-{server_name}"
                )
                env["OPENAI_MODEL"] = validated_model
                logger.info(
                    f"✅ {server_name}: Model {current_model} → {validated_model}"
                )
            except ComplianceViolation:
                # Force to approved model
                env["OPENAI_MODEL"] = "gpt-5-mini"
                logger.warning(f"🔧 {server_name}: Forced model to gpt-5-mini")

        # Add compliance environment
        env.update(compliance_env)
        server_config["env"] = env

        # Add to patched components list
        self.patched_components.append(server_name)

    def create_compliance_wrapper_script(self):
        """Create a compliance wrapper script for Python MCP servers."""
        wrapper_content = '''#!/usr/bin/env python3
"""OpenAI API Standards 2025 Compliance Wrapper for MCP Servers."""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, "/home/opsvi/master_root/src")

# Import universal compliance BEFORE any OpenAI imports
try:
    from universal_openai_compliance import UNIVERSAL_COMPLIANCE
    logging.info("🔐 Universal OpenAI compliance loaded for MCP server")
except ImportError as e:
    logging.error(f"❌ Failed to load universal compliance: {e}")
    sys.exit(1)

# Patch environment
UNIVERSAL_COMPLIANCE._enforce_environment_compliance()

# Now execute the original MCP server
if __name__ == "__main__":
    # Get original command from environment
    original_module = os.getenv("ORIGINAL_MCP_MODULE")
    if not original_module:
        logging.error("❌ No ORIGINAL_MCP_MODULE specified")
        sys.exit(1)

    # Import and run original module
    try:
        import importlib
        module = importlib.import_module(original_module)
        if hasattr(module, "main"):
            module.main()
        else:
            logging.error(f"❌ No main() function in {original_module}")
            sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Failed to run {original_module}: {e}")
        sys.exit(1)
'''

        wrapper_path = "/home/opsvi/master_root/src/mcp_compliance_wrapper.py"
        with open(wrapper_path, "w") as f:
            f.write(wrapper_content)

        os.chmod(wrapper_path, 0o755)
        logger.info(f"✅ Created compliance wrapper: {wrapper_path}")

        return wrapper_path

    def patch_thinking_server(self):
        """Specifically patch the thinking server for compliance."""
        logger.info("🧠 Patching thinking server for OpenAI compliance")

        # The thinking server is at opsvi_mcp.servers.thinking
        # We need to ensure it uses compliant models

        thinking_patch = """
# OpenAI API Standards 2025 Compliance Patch for Thinking Server
import os
import sys

# Add compliance path
sys.path.insert(0, "/home/opsvi/master_root/src")

try:
    from universal_openai_compliance import ensure_openai_compliance

    # Patch OpenAI model environment
    original_model = os.getenv("OPENAI_MODEL", "gpt-4")
    compliant_model = ensure_openai_compliance(
        model=original_model,
        context="thinking-server"
    )
    os.environ["OPENAI_MODEL"] = compliant_model

    print(f"🔐 Thinking server: {original_model} → {compliant_model}")

except Exception as e:
    print(f"❌ Thinking server compliance patch failed: {e}")
"""

        patch_path = "/home/opsvi/master_root/src/thinking_compliance_patch.py"
        with open(patch_path, "w") as f:
            f.write(thinking_patch)

        logger.info(f"✅ Created thinking server patch: {patch_path}")

    def create_universal_startup_script(self):
        """Create a universal startup script that enforces compliance."""
        startup_script = """#!/bin/bash
# Universal OpenAI API Standards 2025 Compliance Startup Script

echo "🔐 Starting Universal OpenAI API Standards 2025 Compliance Enforcement"

# Set compliance environment variables
export OPENAI_COMPLIANCE_REQUIRED=true
export OPENAI_API_STANDARDS_2025=enforced

# Check and correct OPENAI_MODEL if needed
if [ ! -z "$OPENAI_MODEL" ]; then
    case "$OPENAI_MODEL" in
        "gpt-4"|"gpt-4o"|"gpt-4o-mini"|"gpt-3.5-turbo")
            echo "🚨 COMPLIANCE VIOLATION: Legacy model $OPENAI_MODEL detected"
            echo "🔧 CORRECTING: Setting OPENAI_MODEL to gpt-5-mini"
            export OPENAI_MODEL=gpt-5-mini
            ;;
        "gpt-5-nano"|"gpt-5-mini"|"gpt-5"|"o4-mini")
            echo "✅ Approved model: $OPENAI_MODEL"
            ;;
        *)
            echo "🚨 UNKNOWN MODEL: $OPENAI_MODEL"
            echo "🔧 DEFAULTING: Setting OPENAI_MODEL to gpt-5-mini"
            export OPENAI_MODEL=gpt-5-mini
            ;;
    esac
fi

# Add Python path for compliance
export PYTHONPATH="/home/opsvi/master_root/src:$PYTHONPATH"

echo "🔐 Universal OpenAI compliance enforcement active"

# Execute the original command
exec "$@"
"""

        script_path = "/home/opsvi/master_root/scripts/universal_compliance_startup.sh"
        os.makedirs(os.path.dirname(script_path), exist_ok=True)

        with open(script_path, "w") as f:
            f.write(startup_script)

        os.chmod(script_path, 0o755)
        logger.info(f"✅ Created universal startup script: {script_path}")

        return script_path

    def apply_universal_compliance(self):
        """Apply universal compliance across all project components."""
        logger.info("🚀 Applying Universal OpenAI API Standards 2025 Compliance")

        try:
            # 1. Patch MCP configuration
            self.patch_mcp_config()

            # 2. Create compliance wrapper
            self.create_compliance_wrapper_script()

            # 3. Patch thinking server specifically
            self.patch_thinking_server()

            # 4. Create universal startup script
            startup_script = self.create_universal_startup_script()

            # 5. Update environment file
            self._update_env_file()

            logger.info("✅ Universal OpenAI compliance applied successfully")
            logger.info(f"📊 Patched components: {len(self.patched_components)}")
            logger.info(f"🔧 Patched servers: {', '.join(self.patched_components)}")

            return {
                "success": True,
                "patched_components": self.patched_components,
                "startup_script": startup_script,
                "compliance_active": True,
            }

        except Exception as e:
            logger.error(f"❌ Universal compliance application failed: {e}")
            raise

    def _update_env_file(self):
        """Update .env file with compliance requirements."""
        env_file = "/home/opsvi/master_root/.env"

        if os.path.exists(env_file):
            # Read existing .env
            with open(env_file, "r") as f:
                lines = f.readlines()

            # Add compliance variables
            compliance_lines = [
                "\n# OpenAI API Standards 2025 Compliance\n",
                "OPENAI_COMPLIANCE_REQUIRED=true\n",
                "OPENAI_API_STANDARDS_2025=enforced\n",
                "OPENAI_APPROVED_MODELS=gpt-5-nano,gpt-5-mini,gpt-5,o4-mini\n",
            ]

            # Check if we need to update OPENAI_MODEL
            updated_lines = []
            for line in lines:
                if line.startswith("OPENAI_MODEL="):
                    current_model = line.split("=", 1)[1].strip()
                    try:
                        validated_model = ensure_openai_compliance(
                            model=current_model, context="env-file"
                        )
                        updated_lines.append(f"OPENAI_MODEL={validated_model}\n")
                        logger.info(f"✅ .env updated: OPENAI_MODEL={validated_model}")
                    except ComplianceViolation:
                        updated_lines.append("OPENAI_MODEL=gpt-5-mini\n")
                        logger.warning("🔧 .env corrected: OPENAI_MODEL=gpt-5-mini")
                else:
                    updated_lines.append(line)

            # Add compliance lines if not present
            for compliance_line in compliance_lines:
                if not any(
                    compliance_line.split("=")[0] in line for line in updated_lines
                ):
                    updated_lines.append(compliance_line)

            # Write updated .env
            with open(env_file, "w") as f:
                f.writelines(updated_lines)

            logger.info("✅ .env file updated with compliance requirements")


def apply_universal_openai_compliance():
    """Apply universal OpenAI compliance to the entire project."""
    integrator = MCPComplianceIntegrator()
    return integrator.apply_universal_compliance()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    apply_universal_openai_compliance()
