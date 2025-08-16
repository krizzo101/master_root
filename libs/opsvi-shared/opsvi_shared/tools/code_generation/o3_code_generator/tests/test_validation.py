#!/usr/bin/env python3
"""
Test script to verify validation framework is working properly.
"""

from validation_framework import ValidationFramework


def test_func(x: int) -> int:
    """Test function for validation."""
    return x * 2


def test_api_func() -> bool:
    """Test API function."""
    return True


def test_error_func() -> None:
    """Test error function."""
    raise ValueError("Test error")


def main():
    """Test the validation framework."""
    print("Testing validation framework...")

    # Initialize validation framework

    # Test code
def test_function(x: int) -> int:
    return x * 2

if __name__ == "__main__":
    print(result)
"""

    # Run validation
    )

    print("Validation Results:")
    for test_name, result in results.items():
        if test_name != "overall_success":
            print(f"  {test_name}: {status}")
            if not success and result.get("errors"):
                if isinstance(errors, list):
                    for error in errors:
                        print(f"    - {error}")
                else:
                    print(f"    - {errors}")

    print(f"\nOverall Success: {'✅ YES' if overall_success else '❌ NO'}")


if __name__ == "__main__":
    main()
