"""
Module-level tests for bad_function and BadClass.
This module defines bad_function and BadClass with type annotations and docstrings,
and provides pytest-based tests with fixtures and parameterization.
"""

import pytest


def bad_function(x: int) -> int:
    """Increments the input integer by 1 and returns the result."""
    return x + 1


class BadClass:
    """A class that multiplies an input value by its internal value."""

    def __init__(self, initial_value: int = 0) -> None:
        """Initializes BadClass with an internal value."""
        self.value: int = initial_value

    def bad_method(self, x: int) -> int:
        """Returns the product of the internal value and the input x."""
        return x * self.value


@pytest.mark.parametrize(
    "input_val, expected",
    [
        (1, 2),
        (0, 1),
        (-1, 0),
    ],
)
def test_bad_function(input_val: int, expected: int) -> None:
    """Parametrized test for bad_function."""
    assert bad_function(input_val) == expected


@pytest.fixture
def bad_class(request) -> BadClass:
    """Fixture to create BadClass instance with specified initial value."""
    initial_value: int = request.param
    return BadClass(initial_value)


@pytest.mark.parametrize(
    "bad_class, x, expected",
    [
        (0, 5, 0),
        (2, 3, 6),
        (-1, 4, -4),
    ],
    indirect=["bad_class"],
)
def test_bad_method(bad_class: BadClass, x: int, expected: int) -> None:
    """Parametrized test for BadClass.bad_method."""
    assert bad_class.bad_method(x) == expected
