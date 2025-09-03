from typing import List


def process_0(numbers: List[float]) -> float:
    """Process a list of numbers by filtering out negative values and returning their sum.

    Args:
        numbers: A list of numbers to process

    Returns:
        The sum of all non-negative numbers in the input list
    """
    return sum(num for num in numbers if num >= 0)
