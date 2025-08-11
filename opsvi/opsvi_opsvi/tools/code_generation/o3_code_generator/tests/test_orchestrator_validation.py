#!/usr/bin/env python3
"""
Test script to verify that the self-improvement orchestrator can properly
read validation results from the validation framework.
"""

from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent))

from src.tools.code_generation.o3_code_generator.config.self_improvement.run_self_improvement import SelfImprovementOrchestrator


def test_validation_integration():
    """Test that the orchestrator can properly read validation results."""
    print(
        "Testing validation integration between orchestrator and validation framework..."
    )

    # Create a test orchestrator

    # Test code
def test_function(x: int) -> int:
    return x * 2

if __name__ == "__main__":
    print(result)
"""

    # Test the validation method directly
    print("\n1. Testing _validate_improvement method...")

    # Create a temporary file with test code
    with open(temp_file, "w") as f:
        f.write(test_code)

    try:
        # Run validation through the orchestrator
            temp_file, Path(temp_file)
        )

        print("✅ Validation completed successfully!")
        print(f"Overall success: {validation_results.get('overall_success', False)}")

        # Check that the results have the correct format
        print("\n2. Checking result format...")
        for test_name, result in validation_results.items():
            if test_name != "overall_success":
                print(
                    f"  {test_name}: success field={has_success}, errors field={has_errors}"
                )

                if has_success:
                    print(f"    Success value: {success_value}")

                if has_errors and not success_value:
                    print(f"    Errors: {errors}")

        print("\n✅ Validation integration test passed!")

    except Exception as e:
        print(f"❌ Validation integration test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up
        import os

        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    test_validation_integration()
