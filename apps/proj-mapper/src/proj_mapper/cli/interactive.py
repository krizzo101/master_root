"""Interactive shell for Project Mapper.

This module provides an interactive shell for the Project Mapper tool.
This file is maintained for backward compatibility.
"""

from proj_mapper.cli.interactive.shell import run_interactive_mode

__all__ = ["run_interactive_mode"]

# For backward compatibility
if __name__ == "__main__":
    import sys
    sys.exit(run_interactive_mode()) 