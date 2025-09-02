def add_numbers(a, b):
    """Add two numbers and return the result."""
    return a + b


def test_add_numbers():
    """Test the add_numbers function."""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0
    assert add_numbers(10.5, 2.5) == 13.0
    assert add_numbers(-5, -3) == -8
    print("All tests passed!")


if __name__ == "__main__":
    test_add_numbers()
    print(f"Example: 5 + 7 = {add_numbers(5, 7)}")
