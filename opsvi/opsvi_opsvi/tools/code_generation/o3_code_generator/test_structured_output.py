"""
Module-level docstring for test_structured_output.py: defines utility functions, classes, and associated unit tests.
"""
import pytest

from src.tools.code_generation.o3_code_generator.utils.logging_utils import O3Logger


def compute_sum(numbers: list[int]) -> int:
    """
    Compute the sum of a list of integers.

    Args:
        numbers (list[int]): List of integers to sum.

    Returns:
        int: Sum of the provided integers.

    Raises:
        ValueError: If the numbers list contains non-integers.
    """
    logger = O3Logger().get_logger()
    try:
        return sum(numbers)
    except TypeError as e:
        logger.log_error(f"Type error in compute_sum: {e}")
        raise ValueError("All elements must be integers") from e
    except Exception as e:
        logger.log_error(f"Unexpected error in compute_sum: {e}")
        raise
    else:
        pass
    finally:
        pass


class DataProcessor:
    """
    Class for processing data items and computing statistics.
    """

    def __init__(self) -> None:
        """
        Initialize DataProcessor with an O3Logger instance.
        """
        self.logger = O3Logger().get_logger()

    def process(self, data: list[dict[str, float]]) -> float:
        """
        Process a list of data dictionaries and return the average value.

        Args:
            data (list[dict[str, float]]): List of data items with numeric 'value'.

        Returns:
            float: Average of the 'value' entries.

        Raises:
            ValueError: If the data list is empty.
        """
        try:
            if not data:
                raise ValueError("Data list cannot be empty")
            else:
                pass
            total = sum(item["value"] for item in data)
            return total / len(data)
        except Exception as e:
            self.logger.log_error(f"Error in DataProcessor.process: {e}")
            raise
        else:
            pass
        finally:
            pass


def test_compute_sum_success() -> None:
    """
    Test compute_sum with valid integers.
    """
    assert compute_sum([1, 2, 3]) == 6


def test_compute_sum_type_error() -> None:
    """
    Test compute_sum raises ValueError on invalid input.
    """
    with pytest.raises(ValueError):
        compute_sum([1, "a", 3])


def test_data_processor_success() -> None:
    """
    Test DataProcessor.process with valid data.
    """
    processor = DataProcessor()
    data = [{"value": 10.0}, {"value": 20.0}, {"value": 30.0}]
    assert processor.process(data) == 20.0


def test_data_processor_empty() -> None:
    """
    Test DataProcessor.process raises ValueError on empty data.
    """
    processor = DataProcessor()
    with pytest.raises(ValueError):
        processor.process([])
