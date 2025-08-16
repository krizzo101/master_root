#!/usr/bin/env python3
"""
Test idea formation tools with mock OpenAI client
"""

import json
import os
import sys
from unittest.mock import Mock, patch

# Add the script directory to Python path for imports
if script_dir not in sys.path:
    sys.path.append(script_dir)


def create_mock_openai_client():
    """Create a mock OpenAI client that returns predefined responses."""

    # Mock response structure
    mock_message.content = json.dumps(
        {
            "enhanced_analysis": {
                "concept_summary": "A comprehensive mobile app for habit tracking",
                "validation_results": {
                    "clarity_score": 8.5,
                    "completeness_score": 7.8,
                    "potential_score": 8.2,
                },
                "market_analysis": {
                    "market_size": "Large and growing",
                    "target_audience": "Young professionals aged 25-40",
                    "competitive_landscape": "Moderate competition",
                },
                "feasibility_assessment": {
                    "technical_feasibility": "High",
                    "economic_feasibility": "Moderate",
                    "operational_feasibility": "High",
                },
                "recommendations": [
                    "Focus on gamification features",
                    "Implement social sharing capabilities",
                    "Consider AI-powered insights",
                ],
                "risk_assessment": {
                    "technical_risks": ["API integration challenges"],
                    "market_risks": ["User adoption uncertainty"],
                    "operational_risks": ["Data privacy concerns"],
                },
            }
        }
    )
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    # Mock the chat.completions.create method
    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


def test_idea_formation_analyzer_with_mock():
    """Test the idea formation analyzer with mock OpenAI client."""
    print("Testing IdeaFormationAnalyzer with mock OpenAI...")

    try:
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import ConfigManager
        from idea_formation_analyzer import IdeaFormationProcessor
        from o3_logger.logger import setup_logger
        from schemas.idea_formation_schemas import IdeaFormationInput

        # Setup config and logger
        setup_logger(log_config)

        # Create test input
        )

        # Create processor with mock client
        with patch("idea_formation_analyzer.OpenAI") as mock_openai:
            mock_openai.return_value = mock_client

            processor.client = mock_client  # Replace with mock client

            # Run analysis

            print(f"✅ Analysis completed: {output.success}")
            print(f"📊 Analysis items: {len(output.idea_analysis)}")
            print(f"📁 Output files: {len(output.output_files)}")
            print(f"⏱️ Generation time: {output.generation_time:.2f} seconds")

            return output.success

    except Exception as e:
        print(f"❌ Idea formation analyzer test failed: {e}")
        return False


def test_brainstorming_tool_with_mock():
    """Test the brainstorming tool with mock OpenAI client."""
    print("\nTesting BrainstormingTool with mock OpenAI...")

    try:
        from brainstorming_tool import BrainstormingProcessor
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import ConfigManager
        from o3_logger.logger import setup_logger
        from schemas.idea_formation_schemas import BrainstormingInput

        # Setup config and logger
        setup_logger(log_config)

        # Create test input
        )

        # Create processor with mock client
        with patch("brainstorming_tool.OpenAI") as mock_openai:
            mock_openai.return_value = mock_client

            processor.client = mock_client  # Replace with mock client

            # Run brainstorming

            print(f"✅ Brainstorming completed: {output.success}")
            print(f"💡 Ideas generated: {len(output.ideas)}")
            print(f"📊 Categories: {len(output.categories)}")
            print(f"📈 Prioritized ideas: {len(output.prioritized_ideas)}")
            print(f"📁 Output files: {len(output.output_files)}")
            print(f"⏱️ Generation time: {output.generation_time:.2f} seconds")

            return output.success

    except Exception as e:
        print(f"❌ Brainstorming tool test failed: {e}")
        return False


def test_market_research_with_mock():
    """Test the market research integrator with mock OpenAI client."""
    print("\nTesting MarketResearchIntegrator with mock OpenAI...")

    try:
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import ConfigManager
        from market_research_integrator import MarketResearchProcessor
        from o3_logger.logger import setup_logger
        from schemas.idea_formation_schemas import MarketResearchInput

        # Setup config and logger
        setup_logger(log_config)

        # Create test input
        )

        # Create processor with mock client
        with patch("market_research_integrator.OpenAI") as mock_openai:
            mock_openai.return_value = mock_client

            processor.client = mock_client  # Replace with mock client

            # Run market research

            print(f"✅ Market research completed: {output.success}")
            print(f"📊 Market analysis items: {len(output.market_analysis)}")
            print(f"🏢 Competitors identified: {len(output.competitors)}")
            print(f"📈 Demand assessment items: {len(output.demand_assessment)}")
            print(
                f"🎯 Market fit validation items: {len(output.market_fit_validation)}"
            )
            print(f"📁 Output files: {len(output.output_files)}")
            print(f"⏱️ Generation time: {output.generation_time:.2f} seconds")

            return output.success

    except Exception as e:
        print(f"❌ Market research test failed: {e}")
        return False


def test_feasibility_assessor_with_mock():
    """Test the feasibility assessor with mock OpenAI client."""
    print("\nTesting FeasibilityAssessor with mock OpenAI...")

    try:
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import ConfigManager
        from feasibility_assessor import FeasibilityProcessor
        from o3_logger.logger import setup_logger
        from schemas.idea_formation_schemas import FeasibilityInput

        # Setup config and logger
        setup_logger(log_config)

        # Create test input
        )

        # Create processor with mock client
        with patch("feasibility_assessor.OpenAI") as mock_openai:
            mock_openai.return_value = mock_client

            processor.client = mock_client  # Replace with mock client

            # Run feasibility assessment

            print(f"✅ Feasibility assessment completed: {output.success}")
            print(
                f"🔧 Technical feasibility items: {len(output.technical_feasibility)}"
            )
            print(f"💰 Economic feasibility items: {len(output.economic_feasibility)}")
            print(
                f"⚙️ Operational feasibility items: {len(output.operational_feasibility)}"
            )
            print(f"📋 Overall feasibility: {output.overall_feasibility}")
            print(f"💡 Recommendations: {len(output.recommendations)}")
            print(f"⚠️ Risks identified: {len(output.risks)}")
            print(f"📁 Output files: {len(output.output_files)}")
            print(f"⏱️ Generation time: {output.generation_time:.2f} seconds")

            return output.success

    except Exception as e:
        print(f"❌ Feasibility assessor test failed: {e}")
        return False


def main():
    """Run all tests with mock OpenAI client."""
    print("🧪 Testing Idea Formation Tools with Mock OpenAI")
    print("=" * 60)


    # Test each tool with mock OpenAI
    if not test_idea_formation_analyzer_with_mock():

    if not test_brainstorming_tool_with_mock():

    if not test_market_research_with_mock():

    if not test_feasibility_assessor_with_mock():

    if success:
        print("\n✅ All mock tests passed!")
        print("🎉 Idea formation tools are working correctly!")
    else:
        print("\n❌ Some mock tests failed!")

    return success


if __name__ == "__main__":
    sys.exit(0 if success else 1)
