#!/usr/bin/env python3
"""
Test Structured Output Enforcement
==================================

Simple test to verify the structured output enforcer works correctly.
"""

import asyncio
from pathlib import Path
import sys

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.applications.oamat_sd.src.reasoning.structured_output_enforcer import (
    StructuredOutputEnforcer,
)


async def test_dynamic_config_generation():
    """Test dynamic config generation with structured output enforcement"""

    print("🔧 Testing Dynamic Config Generation with Structured Output Enforcement")

    try:
        # Initialize enforcer
        enforcer = StructuredOutputEnforcer()
        print("✅ Structured Output Enforcer initialized")
        print(f"📋 Available schemas: {enforcer.get_available_schemas()}")

        # Test prompt
        test_prompt = """
        Analyze this user request: "Create a simple data visualization tool"

        Generate optimal configuration for this request considering:
        - Simple complexity level
        - 2-3 agents maximum
        - Standard quality requirements
        - Moderate resource allocation
        """

        # Model config
        model_config = {
            "model_name": "o3-mini",
            "reasoning_effort": "low",
            "max_tokens": 8000,
            "temperature": 0.1,
        }

        print("🤖 Calling O3 with structured output enforcement...")

        # Test with timeout
        result = await asyncio.wait_for(
            enforcer.enforce_dynamic_config(
                prompt=test_prompt,
                model_config=model_config,
                context={"test_mode": True},
            ),
            timeout=30.0,
        )

        print("✅ SUCCESS! Structured output enforcement completed")
        print(f"📊 Generated config keys: {list(result.keys())}")

        # Validate specific fields
        if "models" in result:
            print("✅ Models section generated successfully")

        if "execution" in result:
            print("✅ Execution section generated successfully")

        if "quality" in result:
            print("✅ Quality section generated successfully")

        return True

    except asyncio.TimeoutError:
        print("❌ TIMEOUT: O3 call took longer than 30 seconds")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_schema_validation():
    """Test schema validation with sample data"""

    print("\n🔍 Testing Schema Validation")

    try:
        enforcer = StructuredOutputEnforcer()

        # Sample valid config
        sample_config = {
            "models": {
                "reasoning": {
                    "model_name": "o3-mini",
                    "max_tokens": 8000,
                    "reasoning_effort": "medium",
                },
                "agent": {
                    "model_name": "gpt-4.1-mini",
                    "temperature": 0.3,
                    "max_tokens": 4000,
                },
            },
            "execution": {
                "timeout_minutes": 30,
                "max_parallel_agents": 3,
                "retry_attempts": 2,
            },
            "quality": {
                "minimum_confidence": 0.8,
                "validation_enabled": True,
                "synthesis_requirements": ["completeness", "accuracy"],
            },
        }

        # Test validation
        is_valid = await enforcer.validate_existing_data(
            sample_config, "dynamic_config"
        )

        if is_valid:
            print("✅ Sample config validation PASSED")
        else:
            print("❌ Sample config validation FAILED")

        return is_valid

    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        return False


async def main():
    """Run all tests"""

    print("🚀 Starting Structured Output Enforcement Tests")
    print("=" * 60)

    # Test 1: Schema validation
    schema_result = await test_schema_validation()

    # Test 2: Dynamic config generation (only if schema validation passes)
    if schema_result:
        config_result = await test_dynamic_config_generation()

        if config_result:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Structured Output Enforcement is working correctly")
            return 0
        else:
            print("\n❌ DYNAMIC CONFIG TEST FAILED")
            return 1
    else:
        print("\n❌ SCHEMA VALIDATION TEST FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
