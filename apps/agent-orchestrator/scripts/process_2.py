from typing import List


def process_2(numbers: List[float]) -> float:
    """
    Process a list of numbers by filtering out values less than 2 and returning the sum.

    Args:
        numbers: A list of numbers to process

    Returns:
        The sum of all numbers that are greater than or equal to 2

    Examples:
        >>> process_2([1, 2, 3, 4, 5])
        14
        >>> process_2([0.5, 1.5, 2.5, 3.5])
        6.0
        >>> process_2([0, 1, 1.9])
        0
    """
    filtered_numbers = [num for num in numbers if num >= 2]
    return sum(filtered_numbers)
