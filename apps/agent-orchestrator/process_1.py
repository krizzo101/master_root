from typing import List


def process_1(numbers: List[float]) -> float:
    """
    Process a list of numbers by filtering out values less than 1 and returning the sum.

    Args:
        numbers: A list of numeric values to process

    Returns:
        The sum of all numbers that are greater than or equal to 1

    Examples:
        >>> process_1([0.5, 1, 2, 3, -1])
        6.0
        >>> process_1([0, 0.9, 1.5, 2.5])
        4.0
        >>> process_1([-5, -2, 0.5])
        0.0
    """
    filtered_numbers = [num for num in numbers if num >= 1]
    return sum(filtered_numbers)
