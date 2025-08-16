#!/usr/bin/env python3
"""
Convenience script to run genfilemap directly from the source directory.

Usage:
    python run.py [arguments]
    
This is equivalent to running the installed package with:
    genfilemap [arguments]
"""

import sys
import os

# Add the src directory to the path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import the main function from the genfilemap package
from genfilemap.cli import main

if __name__ == "__main__":
    # Run the main CLI function with the provided arguments
    sys.exit(main())
