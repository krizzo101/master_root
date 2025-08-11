"""
Main entry point for running genFileMap as a module.

This allows running the tool with:
    python -m utils.genFileMap [arguments]
"""

import sys
import os
import importlib.util

# Add the parent directory to path if running as script
if __name__ == "__main__":
    # Handle import when running as a script vs module
    if importlib.util.find_spec("utils.genFileMap") is not None:
        from utils.genFileMap.genFileMap import main
    else:
        # Running as script, import directly
        sys.path.insert(
            0,
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
        )
        from utils.genFileMap import genFileMap
        from utils.genFileMap.genFileMap import main

    main()
