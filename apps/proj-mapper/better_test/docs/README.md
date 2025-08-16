# Test Calculator Application

This is a simple calculator application that demonstrates basic arithmetic operations.

## Architecture

The application has a main module and a utilities module:

- `main.py`: Entry point with specific functions like `add_numbers` and `multiply_numbers`
- `utils.py`: Contains the `Calculator` class and formatting utilities

## API Reference

### Calculator Class

The `Calculator` class provides the following methods:

- `add(a, b)`: Adds two numbers together and returns their sum
- `multiply(a, b)`: Multiplies two numbers and returns their product
- `subtract(a, b)`: Subtracts the second number from the first and returns the difference

### Main Module Functions

- `add_numbers(a, b)`: Wrapper function that creates a Calculator instance and calls its add method
- `multiply_numbers(a, b)`: Wrapper function that creates a Calculator instance and calls its multiply method

### Utility Functions

- `format_result(operation, a, b, result)`: Formats calculation results into readable strings

## Usage Examples

```python
from main import add_numbers, multiply_numbers

# Adding two numbers
result = add_numbers(5, 3)  # Returns 8

# Multiplying two numbers
result = multiply_numbers(4, 7)  # Returns 28
```
