
#!/usr/bin/env python3
"""
Basic tests for the GenFileMap package.

This script performs simple tests to ensure the GenFileMap package loads
correctly and its core functionality is accessible.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the src directory to the path for importing the package
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Now we can import from the package
from genfilemap import __version__
from genfilemap.config import load_config, get_config_value, DEFAULT_CONFIG
from genfilemap.models.schemas import load_schema

class BasicTests(unittest.TestCase):
    """Basic tests for the GenFileMap package."""
    
    def test_import(self):
        """Test that the package can be imported successfully."""
        # If we got this far without an import error, the test passes
        self.assertTrue(True)
    
    def test_version(self):
        """Test that the package has a version number."""
        self.assertIsNotNone(__version__)
        self.assertTrue(isinstance(__version__, str))
    
    def test_config(self):
        """Test that configuration functions work correctly."""
        # Test loading default config
        config = load_config()
        self.assertIsNotNone(config)
        
        # Test getting a value with dot notation
        path_value = get_config_value(config, "path")
        self.assertEqual(path_value, ".")
        
        # Test getting a nested value
        model_value = get_config_value(config, "api.model")
        self.assertEqual(model_value, DEFAULT_CONFIG["api"]["model"])
    
    def test_schema(self):
        """Test that the schema can be loaded."""
        schema = load_schema()
        self.assertIsNotNone(schema)
        self.assertTrue(isinstance(schema, dict))
        # Check that the schema has the expected structure
        self.assertIn("properties", schema)
        self.assertIn("file_metadata", schema["properties"])
        self.assertIn("sections", schema["properties"])

if __name__ == "__main__":
    unittest.main() 