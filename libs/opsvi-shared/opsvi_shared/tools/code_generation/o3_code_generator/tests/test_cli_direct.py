#!/usr/bin/env python3
"""
Test CLI functions directly
"""

import json
import os
import sys

# Add the script directory to Python path for imports
if script_dir not in sys.path:
    sys.path.append(script_dir)


def test_idea_analyze_function():
    """Test the run_idea_analyze function directly."""
    print("Testing run_idea_analyze function...")

    try:
        from o3_main import run_idea_analyze

        # Create a simple test input
            "concept_description": "A simple test concept for validation",
            "target_market": "Test market",
            "analysis_type": "simple",
            "include_market_research": False,
            "include_feasibility_assessment": False,
            "output_format": "json",
            "model": "o3-mini",
            "max_tokens": 1000,
        }

        with open("test_cli_input.json", "w") as f:
            json.dump(test_input, f)

        # Test the function
        run_idea_analyze("test_cli_input.json")

        # Clean up
        os.remove("test_cli_input.json")

        return True

    except Exception as e:
        print(f"❌ run_idea_analyze test failed: {e}")
        if os.path.exists("test_cli_input.json"):
            os.remove("test_cli_input.json")
        return False


def test_brainstorm_function():
    """Test the run_brainstorm function directly."""
    print("\nTesting run_brainstorm function...")

    try:
        from o3_main import run_brainstorm

        # Create a simple test input
            "problem_statement": "How to improve productivity",
            "target_audience": "Office workers",
            "idea_count": 3,
            "categories": ["Technology", "Process"],
            "include_prioritization": True,
            "output_format": "json",
            "model": "o3-mini",
            "max_tokens": 1000,
        }

        with open("test_brainstorm_input.json", "w") as f:
            json.dump(test_input, f)

        # Test the function
        run_brainstorm("test_brainstorm_input.json")

        # Clean up
        os.remove("test_brainstorm_input.json")

        return True

    except Exception as e:
        print(f"❌ run_brainstorm test failed: {e}")
        if os.path.exists("test_brainstorm_input.json"):
            os.remove("test_brainstorm_input.json")
        return False


def test_market_research_function():
    """Test the run_market_research function directly."""
    print("\nTesting run_market_research function...")

    try:
        from o3_main import run_market_research

        # Create a simple test input
            "product_concept": "A productivity app",
            "target_market": "Small businesses",
            "include_competitor_analysis": True,
            "include_demand_assessment": True,
            "include_market_fit_validation": True,
            "output_format": "json",
            "model": "o3-mini",
            "max_tokens": 1000,
        }

        with open("test_market_input.json", "w") as f:
            json.dump(test_input, f)

        # Test the function
        run_market_research("test_market_input.json")

        # Clean up
        os.remove("test_market_input.json")

        return True

    except Exception as e:
        print(f"❌ run_market_research test failed: {e}")
        if os.path.exists("test_market_input.json"):
            os.remove("test_market_input.json")
        return False


def test_feasibility_assess_function():
    """Test the run_feasibility_assess function directly."""
    print("\nTesting run_feasibility_assess function...")

    try:
        from o3_main import run_feasibility_assess

        # Create a simple test input
            "concept_description": "A simple web application",
            "include_technical_feasibility": True,
            "include_economic_feasibility": True,
            "include_operational_feasibility": True,
            "budget_constraints": "Low budget",
            "timeline_constraints": "3 months",
            "output_format": "json",
            "model": "o3-mini",
            "max_tokens": 1000,
        }

        with open("test_feasibility_input.json", "w") as f:
            json.dump(test_input, f)

        # Test the function
        run_feasibility_assess("test_feasibility_input.json")

        # Clean up
        os.remove("test_feasibility_input.json")

        return True

    except Exception as e:
        print(f"❌ run_feasibility_assess test failed: {e}")
        if os.path.exists("test_feasibility_input.json"):
            os.remove("test_feasibility_input.json")
        return False


def main():
    """Run all CLI function tests."""
    print("🧪 Testing CLI Functions")
    print("=" * 50)


    # Test each CLI function
    if not test_idea_analyze_function():

    if not test_brainstorm_function():

    if not test_market_research_function():

    if not test_feasibility_assess_function():

    if success:
        print("\n✅ All CLI function tests passed!")
    else:
        print("\n❌ Some CLI function tests failed!")

    return success


if __name__ == "__main__":
    sys.exit(0 if success else 1)
