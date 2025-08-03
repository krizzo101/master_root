#!/usr/bin/env python3
"""
Test runner for genfilemap.

This script discovers and runs all tests for the genfilemap package.
"""

import os
import sys
import unittest

if __name__ == "__main__":
    # Discover and run all tests
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with a non-zero code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1) 