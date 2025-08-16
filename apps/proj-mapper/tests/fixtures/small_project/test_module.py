"""A simple test module for testing Project Mapper."""


class SimpleClass:
    """A simple class for testing purposes.
    
    This class demonstrates documentation and code structure
    for testing the Project Mapper's analyzer components.
    """
    
    def __init__(self, name: str):
        """Initialize the SimpleClass.
        
        Args:
            name: The name of the instance
        """
        self.name = name
        self._value = 0
    
    def get_value(self) -> int:
        """Return the current value.
        
        Returns:
            The current value
        """
        return self._value
    
    def set_value(self, value: int) -> None:
        """Set the value.
        
        Args:
            value: The new value
        """
        self._value = value
    
    def describe(self) -> str:
        """Return a description of this instance.
        
        Returns:
            A string describing the instance
        """
        return f"SimpleClass(name={self.name}, value={self._value})"


def example_function(param1: str, param2: int = 0) -> str:
    """An example function for testing.
    
    This function demonstrates a simple function with
    documentation for testing purposes.
    
    Args:
        param1: The first parameter
        param2: The second parameter (default: 0)
        
    Returns:
        A formatted string
    
    Raises:
        ValueError: If param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    return f"Result: {param1} with value {param2}"


if __name__ == "__main__":
    # Test code
    obj = SimpleClass("test")
    obj.set_value(42)
    print(obj.describe())
    print(example_function("hello", 123)) 