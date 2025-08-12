#!/usr/bin/env python3
"""
Simple test script for idea formation tools
"""

import json
import os
import sys

# Add the script directory to Python path for imports
if script_dir not in sys.path:
    sys.path.append(script_dir)


def test_idea_formation_imports():
    """Test if all idea formation modules can be imported."""
    print("Testing imports...")

    try:
        print("✅ Schema imports successful")
    except Exception as e:
        print(f"❌ Schema import failed: {e}")
        return False

    try:
        print("✅ Prompt imports successful")
    except Exception as e:
        print(f"❌ Prompt import failed: {e}")
        return False

    try:
        print("✅ Idea formation analyzer import successful")
    except Exception as e:
        print(f"❌ Idea formation analyzer import failed: {e}")
        return False

    try:
        print("✅ Brainstorming tool import successful")
    except Exception as e:
        print(f"❌ Brainstorming tool import failed: {e}")
        return False

    try:
        print("✅ Market research integrator import successful")
    except Exception as e:
        print(f"❌ Market research integrator import failed: {e}")
        return False

    try:
        print("✅ Feasibility assessor import successful")
    except Exception as e:
        print(f"❌ Feasibility assessor import failed: {e}")
        return False

    return True


def test_schema_validation():
    """Test schema validation with sample data."""
    print("\nTesting schema validation...")

    try:
        from schemas.idea_formation_schemas import IdeaFormationInput

        # Test input data
            "concept_description": "A mobile app for habit tracking",
            "target_market": "Young professionals",
            "analysis_type": "comprehensive",
            "include_market_research": True,
            "include_feasibility_assessment": True,
            "output_format": "json",
            "model": "o3-mini",
            "max_tokens": 4000,
        }

        # Validate input
        print("✅ Input schema validation successful")

        # Test output data
        from schemas.idea_formation_schemas import IdeaFormationOutput

            "success": True,
            "idea_analysis": {"concept_analysis": {}, "validation_results": {}},
            "output_files": [],
            "generation_time": 10.5,
            "model_used": "o3-mini",
        }

        print("✅ Output schema validation successful")

        return True

    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality without OpenAI calls."""
    print("\nTesting basic functionality...")

    try:
        # Test input loader
        import logging

        from idea_formation_analyzer import InputLoader

        # Use basic logging for test
        logging.basicConfig(level=logging.INFO)

        # Create a mock logger object with the required methods
        class MockLogger:
            def log_info(self, message):
                print(f"INFO: {message}")

            def log_error(self, error, message):
                print(f"ERROR: {message} - {error}")


        # Create a test input file
            "concept_description": "A simple test concept",
            "target_market": "Test market",
            "analysis_type": "simple",
            "include_market_research": False,
            "include_feasibility_assessment": False,
            "output_format": "json",
            "model": "o3-mini",
            "max_tokens": 1000,
        }

        with open("test_input.json", "w") as f:
            json.dump(test_input, f)

        # Test loading
        print("✅ Input loader functionality successful")

        # Clean up
        os.remove("test_input.json")

        return True

    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Idea Formation Tools")
    print("=" * 50)

    # Test imports
    if not test_idea_formation_imports():
        print("❌ Import tests failed")
        return False

    # Test schema validation
    if not test_schema_validation():
        print("❌ Schema validation tests failed")
        return False

    # Test basic functionality
    if not test_basic_functionality():
        print("❌ Basic functionality tests failed")
        return False

    print("\n✅ All tests passed!")
    return True


if __name__ == "__main__":
    sys.exit(0 if success else 1)
