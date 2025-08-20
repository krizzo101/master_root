#!/usr/bin/env python3
"""
Main module for the test application.

This module serves as the primary entry point for the application.
"""
import os
import sys

sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from utils import Calculator, format_result


def add_numbers(a: int, b: int) -> int:
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of the two numbers
    """
    calculator = Calculator()
    return calculator.add(a, b)


def multiply_numbers(a: int, b: int) -> int:
    """
    Multiply two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of the two numbers
    """
    calculator = Calculator()
    return calculator.multiply(a, b)


def main():
    """Run the test application with examples."""
    result1 = add_numbers(5, 3)
    result2 = multiply_numbers(4, 7)

    print(format_result("Addition", 5, 3, result1))
    print(format_result("Multiplication", 4, 7, result2))


if __name__ == "__main__":
    main()
