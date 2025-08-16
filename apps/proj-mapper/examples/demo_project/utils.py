"""
Utility functions and classes for the test application.

This module contains helper classes and functions used throughout the application.
"""

from typing import Any


class Calculator:
    """
    A simple calculator class for basic arithmetic operations.
    
    This class provides methods for performing basic calculations.
    """
    
    def add(self, a: int, b: int) -> int:
        """
        Add two numbers together.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Sum of the two numbers
        """
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        """
        Multiply two numbers together.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Product of the two numbers
        """
        return a * b
    
    def subtract(self, a: int, b: int) -> int:
        """
        Subtract second number from first number.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Difference between first and second number
        """
        return a - b


def format_result(operation: str, a: int, b: int, result: Any) -> str:
    """
    Format the result of a calculation as a string.
    
    Args:
        operation: Name of the operation performed
        a: First operand
        b: Second operand
        result: Result of the operation
        
    Returns:
        Formatted string with operation and result
    """
    return f"{operation}: {a} and {b} = {result}" 