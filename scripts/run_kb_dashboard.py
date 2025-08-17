#!/usr/bin/env python3
"""
Run Knowledge Base Visualization Dashboard
Starts the Streamlit dashboard for visualizing KB data
"""

import logging
import os
import subprocess
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are installed."""
    required = ["streamlit", "plotly", "neo4j", "pandas", "numpy"]
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.info(f"Install with: pip install {' '.join(missing)}")
        return False

    return True


def main():
    """Main function to run the dashboard."""
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Set environment variables
    os.environ["NEO4J_URI"] = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    os.environ["NEO4J_USER"] = os.getenv("NEO4J_USER", "neo4j")
    os.environ["NEO4J_PASSWORD"] = os.getenv("NEO4J_PASSWORD", "password")

    # Path to dashboard
    dashboard_path = (
        "/home/opsvi/master_root/libs/opsvi_knowledge/visualization_dashboard.py"
    )

    if not os.path.exists(dashboard_path):
        logger.error(f"Dashboard not found at {dashboard_path}")
        sys.exit(1)

    logger.info("Starting Knowledge Base Visualization Dashboard...")
    logger.info("Access at: http://localhost:8501")
    logger.info("Press Ctrl+C to stop")

    try:
        # Run streamlit
        subprocess.run(
            [
                "streamlit",
                "run",
                dashboard_path,
                "--server.port",
                "8501",
                "--server.address",
                "0.0.0.0",  # nosec B104
                "--theme.base",
                "dark",
                "--theme.primaryColor",
                "#4CAF50",
                "--theme.backgroundColor",
                "#1E1E1E",
                "--theme.secondaryBackgroundColor",
                "#2E2E2E",
                "--theme.textColor",
                "#FAFAFA",
            ]
        )
    except KeyboardInterrupt:
        logger.info("\nDashboard stopped by user")
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
