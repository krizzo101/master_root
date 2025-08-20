import os
import sys

sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


"""Main entry point for interactive mode.

This module allows running the interactive mode directly:
python -m proj_mapper.cli.interactive
"""

import sys

from proj_mapper.cli.interactive.shell import run_interactive_mode

if __name__ == "__main__":
    sys.exit(run_interactive_mode())
