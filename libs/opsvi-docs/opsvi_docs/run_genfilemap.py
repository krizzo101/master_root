#!/usr/bin/env python3
"""
Convenience script to run genFileMap from the root directory.
"""

import sys
import os

# Add the parent directory to Python path to make the package importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.genFileMap.genFileMap import main

if __name__ == "__main__":
    main()
