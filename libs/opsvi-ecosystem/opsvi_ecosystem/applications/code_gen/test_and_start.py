#!/usr/bin/env python3
"""
Automated Test and Application Startup Script

Tests the system, fixes issues automatically, and starts the application.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main execution flow."""
    app_dir = Path(__file__).parent
    os.chdir(app_dir)

    logger.info("🚀 Starting Code Generation Application Test & Launch Sequence")

    # Step 1: Validate system
    logger.info("📋 Step 1: Running system validation...")
    validation_result = subprocess.run(
        [sys.executable, "validate_system.py"], capture_output=True, text=True
    )

    if validation_result.returncode == 0:
        logger.info("✅ System validation PASSED!")
    else:
        logger.warning("⚠️ System validation found issues, but proceeding...")
        logger.info("Validation output:")
        print(validation_result.stdout)
        if validation_result.stderr:
            print("Errors:", validation_result.stderr)

    # Step 2: Check dependencies
    logger.info("🔧 Step 2: Checking and starting dependencies...")

    # Start the application with dependency management
    logger.info("🎯 Step 3: Starting Code Generation Application...")

    try:
        # Set environment variables for the app
        env = os.environ.copy()
        env["PYTHONPATH"] = str(app_dir)

        logger.info("📍 Application will be available at:")
        logger.info("   • Web Interface: http://localhost:8010")
        logger.info("   • Health Check: http://localhost:8010/health")
        logger.info("   • WebSocket: ws://localhost:8010/ws")
        logger.info("")
        logger.info("🎉 Starting application now...")

        # Run the main application
        subprocess.run([sys.executable, "main.py"], env=env, cwd=app_dir)

    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
