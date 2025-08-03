
"""
Test file for code elements extraction.
"""

import os
import typing
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0
API_BASE_URL = "https://api.example.com/v1"

def simple_function(param1: str, param2: int = 10) -> str:
    """
    A simple function that returns a string.
    
    Args:
        param1: First parameter
        param2: Second parameter with default value
        
    Returns:
        A formatted string
    """
    return f"{param1} - {param2}"

def complex_function(
    items: List[Dict[str, any]],
    config: Optional[Dict[str, any]] = None,
    *args,
    **kwargs
) -> Tuple[List[str], int]:
    """Complex function with various parameter types"""
    # Function implementation
    return (["result"], 1)

class SimpleClass:
    """A simple class for testing."""
    
    class_var = "class variable"
    
    def __init__(self, name: str, value: int = 0):
        """Initialize the class."""
        self.name = name
        self.value = value
        
    def get_name(self) -> str:
        """Return the name."""
        return self.name
        
    @property
    def formatted_value(self) -> str:
        """Return the formatted value."""
        return f"Value: {self.value}"
        
    @staticmethod
    def helper_method(input_str: str) -> str:
        """Static helper method."""
        return input_str.upper()

class ComplexClass(SimpleClass):
    """A more complex class that inherits from SimpleClass."""
    
    def __init__(self, name: str, value: int = 0, extra: List[str] = None):
        """Initialize with parent constructor and extra parameters."""
        super().__init__(name, value)
        self.extra = extra or []
        
    def process_data(self, data: Dict[str, any], options: Optional[Dict] = None) -> Dict[str, any]:
        """Process data with options."""
        result = {}
        # Implementation details
        return result

if __name__ == "__main__":
    simple = SimpleClass("test", 42)
    print(simple.get_name())
    print(simple.formatted_value) 