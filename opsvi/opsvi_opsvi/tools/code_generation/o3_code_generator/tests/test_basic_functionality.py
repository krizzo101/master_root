#!/usr/bin/env python3
"""
Test basic functionality of idea formation tools without OpenAI API calls
"""

import json
import os
from pathlib import Path
import sys

# Add the script directory to Python path for imports
if script_dir not in sys.path:
    sys.path.append(script_dir)


def test_schema_validation():
    """Test schema validation with sample data."""
    print("Testing schema validation...")

    try:
        from schemas.idea_formation_schemas import (
            BrainstormingInput,
            FeasibilityInput,
            IdeaFormationInput,
            MarketResearchInput,
        )

        # Test IdeaFormationInput
        )
        print("✅ IdeaFormationInput validation passed")

        # Test BrainstormingInput
        )
        print("✅ BrainstormingInput validation passed")

        # Test MarketResearchInput
        )
        print("✅ MarketResearchInput validation passed")

        # Test FeasibilityInput
        )
        print("✅ FeasibilityInput validation passed")

        return True

    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False


def test_basic_components():
    """Test basic components without OpenAI."""
    print("\nTesting basic components...")

    try:
        from brainstorming_tool import BrainstormingTool
        from feasibility_assessor import FeasibilityAssessor
        from idea_formation_analyzer import IdeaFormationAnalyzer
        from market_research_integrator import MarketResearchIntegrator

        # Create mock logger
        class MockLogger:
            def log_info(self, message):
                pass

            def log_error(self, error, message):
                pass


        # Test IdeaFormationAnalyzer
        print(f"✅ IdeaFormationAnalyzer: {len(concept_result)} analysis items")

        # Test BrainstormingTool
        print(f"✅ BrainstormingTool: {len(ideas)} ideas generated")

        # Test MarketResearchIntegrator
        print(f"✅ MarketResearchIntegrator: {len(market_result)} market items")

        # Test FeasibilityAssessor
        print(f"✅ FeasibilityAssessor: {len(feasibility_result)} feasibility items")

        return True

    except Exception as e:
        print(f"❌ Basic components test failed: {e}")
        return False


def test_file_generation():
    """Test file generation functionality."""
    print("\nTesting file generation...")

    try:
        # Test creating output directories
            "generated_files/idea_formation",
            "generated_files/brainstorming",
            "generated_files/market_research",
            "generated_files/feasibility",
        ]

        for dir_path in output_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Test creating sample files

        with open(test_file, "w") as f:
            json.dump(sample_data, f, indent=2)

        # Verify file was created
        if os.path.exists(test_file):
            print("✅ File generation test passed")
            os.remove(test_file)  # Clean up
            return True
        else:
            print("❌ File generation test failed")
            return False

    except Exception as e:
        print(f"❌ File generation test failed: {e}")
        return False


def test_cli_integration():
    """Test CLI integration."""
    print("\nTesting CLI integration...")

    try:
        from o3_main import (
            run_brainstorm,
            run_feasibility_assess,
            run_idea_analyze,
            run_market_research,
        )

        # Test that the functions exist and are callable
        assert callable(run_idea_analyze)
        assert callable(run_brainstorm)
        assert callable(run_market_research)
        assert callable(run_feasibility_assess)

        print("✅ CLI integration test passed")
        return True

    except Exception as e:
        print(f"❌ CLI integration test failed: {e}")
        return False


def main():
    """Run all basic functionality tests."""
    print("🧪 Testing Basic Functionality")
    print("=" * 50)


    # Test schema validation
    if not test_schema_validation():

    # Test basic components
    if not test_basic_components():

    # Test file generation
    if not test_file_generation():

    # Test CLI integration
    if not test_cli_integration():

    if success:
        print("\n✅ All basic functionality tests passed!")
        print("🎉 Core functionality is working correctly!")
        print("\n📝 Summary:")
        print("- Schema validation: ✅ Working")
        print("- Component initialization: ✅ Working")
        print("- File generation: ✅ Working")
        print("- CLI integration: ✅ Working")
        print("\n⚠️ Note: OpenAI API integration may need configuration")
    else:
        print("\n❌ Some basic functionality tests failed!")

    return success


if __name__ == "__main__":
    sys.exit(0 if success else 1)
