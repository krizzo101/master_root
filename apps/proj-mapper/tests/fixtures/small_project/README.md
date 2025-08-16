# Small Test Project

This is a simple test project for Project Mapper testing.

## Contents

- `test_module.py`: Contains a simple Python module with classes and functions

## Usage

The `SimpleClass` in the `test_module.py` file provides basic functionality:

```python
from test_module import SimpleClass

# Create an instance
obj = SimpleClass("example")

# Set a value
obj.set_value(42)

# Get description
description = obj.describe()
```

The module also includes an `example_function` that can be used like this:

```python
from test_module import example_function

# Call the function
result = example_function("hello", 123)
```

## Architecture

This small test project demonstrates simple Python code with docstrings and corresponding
markdown documentation to test Project Mapper's ability to detect relationships between
code and documentation.

## License

This test project is for testing purposes only and has no real license.
