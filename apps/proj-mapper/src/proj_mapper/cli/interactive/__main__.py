"""Main entry point for interactive mode.

This module allows running the interactive mode directly:
python -m proj_mapper.cli.interactive
"""

import sys
from proj_mapper.cli.interactive.shell import run_interactive_mode

if __name__ == "__main__":
    sys.exit(run_interactive_mode()) 