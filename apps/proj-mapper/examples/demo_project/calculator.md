# Calculator Class Documentation

The `Calculator` class is the core component of our application. It provides several
methods for performing arithmetic operations.

## Class Methods

### add

```python
def add(a: int, b: int) -> int
```

Adds two numbers together and returns their sum.

**Parameters:**

- `a`: The first operand
- `b`: The second operand

**Returns:**
An integer representing the sum of `a` and `b`

**Example:**

```python
calculator = Calculator()
result = calculator.add(5, 3)  # result will be 8
```

### multiply

```python
def multiply(a: int, b: int) -> int
```

Multiplies two numbers together and returns their product.

**Parameters:**

- `a`: The first operand
- `b`: The second operand

**Returns:**
An integer representing the product of `a` and `b`

**Example:**

```python
calculator = Calculator()
result = calculator.multiply(4, 7)  # result will be 28
```

### subtract

```python
def subtract(a: int, b: int) -> int
```

Subtracts the second number from the first and returns the difference.

**Parameters:**

- `a`: The first operand
- `b`: The second operand

**Returns:**
An integer representing the difference between `a` and `b`

**Example:**

```python
calculator = Calculator()
result = calculator.subtract(10, 4)  # result will be 6
```

## Integration with Main Module

The `Calculator` class is used by the functions in the main module:

- `add_numbers` creates a Calculator instance and calls its `add` method
- `multiply_numbers` creates a Calculator instance and calls its `multiply` method
