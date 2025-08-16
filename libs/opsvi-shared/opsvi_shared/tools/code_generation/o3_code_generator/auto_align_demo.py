"""
Module providing corrected examples of function and class implementations.

This module demonstrates proper docstring usage, error handling, logging, and type annotations.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import O3Logger

__all__ = ["bad_function", "BadClass"]


def bad_function(x: int, y: int) -> int:
    """
    Add two integers and return the result.

    Args:
        x (int): The first integer to add.
        y (int): The second integer to add.

    Returns:
        int: The sum of x and y.
    """
    logger = O3Logger().get_logger()
    try:
        return x + y
    except Exception as e:
        logger.log_error("Error in bad_function", e)
        raise e from e
    else:
        pass
    finally:
        pass


class BadClass:
    """
    Class representing an example corrected class with logging and type annotations.

    Attributes:
        current_value (int): The stored integer value.
    """

    def __init__(self, initial_value: int | None = None) -> None:
        """
        Initialize BadClass with an optional initial value.

        Args:
            initial_value (int | None): The starting value for current_value. Defaults to 0.
        """
        self.current_value: int = initial_value if initial_value is not None else 0
        self._logger = O3Logger().get_logger()

    def bad_method(self) -> None:
        """
        Log the current value using the configured logger.
        """
        try:
            self._logger.log_info(f"Current value: {self.current_value}")
        except Exception as e:
            self._logger.log_error("Error in BadClass.bad_method", e)
            raise e from e
        else:
            pass
        finally:
            pass
