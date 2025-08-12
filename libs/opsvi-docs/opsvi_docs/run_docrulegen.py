#!/usr/bin/env python3
"""
Convenience script to run docRuleGen from the root directory.
"""

import sys
import os

# Add the parent directory to Python path to make the package importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docRuleGen.docRuleGen import main

if __name__ == "__main__":
    main()
