#!/usr/bin/env python3
"""
Test individual components of idea formation tools
"""

import os
import sys

# Add the script directory to Python path for imports
if script_dir not in sys.path:
    sys.path.append(script_dir)


def test_idea_formation_analyzer():
    """Test the IdeaFormationAnalyzer class directly."""
    print("Testing IdeaFormationAnalyzer...")

    try:
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import ConfigManager
        from idea_formation_analyzer import IdeaFormationAnalyzer
        from o3_logger.logger import setup_logger

        # Setup config and logger
        setup_logger(log_config)

        # Create analyzer

        # Test concept analysis
            "A mobile app for habit tracking", "Young professionals"
        )
        print(f"✅ Concept analysis: {len(concept_result)} items")

        # Test idea validation
            "A mobile app for habit tracking", "Young professionals"
        )
        print(f"✅ Idea validation: {len(validation_result)} items")

        # Test feasibility assessment
            "A mobile app for habit tracking"
        )
        print(f"✅ Feasibility assessment: {len(feasibility_result)} items")

        return True

    except Exception as e:
        print(f"❌ IdeaFormationAnalyzer test failed: {e}")
        return False


def test_brainstorming_tool():
    """Test the BrainstormingTool class directly."""
    print("\nTesting BrainstormingTool...")

    try:
        from brainstorming_tool import BrainstormingTool
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import ConfigManager
        from o3_logger.logger import setup_logger

        # Setup config and logger
        setup_logger(log_config)

        # Create tool

        # Test idea generation
        print(f"✅ Idea generation: {len(ideas)} ideas")

        # Test concept expansion
        print(f"✅ Concept expansion: {len(expansions)} expansions")

        # Test idea categorization
        print(f"✅ Idea categorization: {len(categorized)} categories")

        # Test prioritization
        print(f"✅ Idea prioritization: {len(prioritized)} prioritized")

        return True

    except Exception as e:
        print(f"❌ BrainstormingTool test failed: {e}")
        return False


def test_market_research_integrator():
    """Test the MarketResearchIntegrator class directly."""
    print("\nTesting MarketResearchIntegrator...")

    try:
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import ConfigManager
        from market_research_integrator import MarketResearchIntegrator
        from o3_logger.logger import setup_logger

        # Setup config and logger
        setup_logger(log_config)

        # Create integrator

        # Test market analysis
            "AI-powered personal finance assistant", "Millennials and Gen Z"
        )
        print(f"✅ Market analysis: {len(market_result)} items")

        # Test competitor identification
            "AI-powered personal finance assistant", "Millennials and Gen Z"
        )
        print(f"✅ Competitor identification: {len(competitors)} competitors")

        # Test demand assessment
            "AI-powered personal finance assistant", "Millennials and Gen Z"
        )
        print(f"✅ Demand assessment: {len(demand_result)} items")

        # Test market fit validation
            "AI-powered personal finance assistant", "Millennials and Gen Z"
        )
        print(f"✅ Market fit validation: {len(fit_result)} items")

        return True

    except Exception as e:
        print(f"❌ MarketResearchIntegrator test failed: {e}")
        return False


def test_feasibility_assessor():
    """Test the FeasibilityAssessor class directly."""
    print("\nTesting FeasibilityAssessor...")

    try:
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import ConfigManager
        from feasibility_assessor import FeasibilityAssessor
        from o3_logger.logger import setup_logger

        # Setup config and logger
        setup_logger(log_config)

        # Create assessor

        # Test technical feasibility
            "Blockchain-based supply chain tracking system"
        )
        print(f"✅ Technical feasibility: {len(technical_result)} items")

        # Test economic feasibility
            "Blockchain-based supply chain tracking system"
        )
        print(f"✅ Economic feasibility: {len(economic_result)} items")

        # Test operational feasibility
            "Blockchain-based supply chain tracking system"
        )
        print(f"✅ Operational feasibility: {len(operational_result)} items")

        return True

    except Exception as e:
        print(f"❌ FeasibilityAssessor test failed: {e}")
        return False


def main():
    """Run all component tests."""
    print("🧪 Testing Idea Formation Components")
    print("=" * 50)


    # Test each component
    if not test_idea_formation_analyzer():

    if not test_brainstorming_tool():

    if not test_market_research_integrator():

    if not test_feasibility_assessor():

    if success:
        print("\n✅ All component tests passed!")
    else:
        print("\n❌ Some component tests failed!")

    return success


if __name__ == "__main__":
    sys.exit(0 if success else 1)
