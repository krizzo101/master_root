#!/usr/bin/env python3
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
