"""Main entry point for the Project Mapper package.

This module allows running the Project Mapper using:
python -m proj_mapper
"""

import sys
import logging
from proj_mapper.cli.main import cli

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    # Use Click's command execution
    sys.exit(cli()) 