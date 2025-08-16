"""
Module providing arithmetic utility methods.
"""

from src.tools.code_generation.o3_code_generator.utils.logging_utils import (
    O3Logger,
    log_and_reraise,
)

__all__ = ["ArithmeticUtilities"]


class ArithmeticUtilities:
    """
    Provides arithmetic utility methods.

    Attributes:
        logger (O3Logger): Logger instance for error reporting.
    """

    def __init__(self) -> None:
        """
        Initialize ArithmeticUtilities with a logger instance.
        """
        logger_instance = O3Logger()
        self.logger = logger_instance.get_logger()
        self.logger.log_info("ArithmeticUtilities instance created.")

    @log_and_reraise(TypeError)
    def add_integers(x: int, y: int) -> int:
        """
        Add two integers and return the result.

        Args:
            x (int): The first integer to add.
            y (int): The second integer to add.

        Returns:
            int: The sum of x and y.

        Raises:
            TypeError: If x or y is not an integer.
        """
        if not isinstance(x, int) or not isinstance(y, int):
            message = f"Both x and y must be integers. Received x={x!r}, y={y!r}"
            raise TypeError(message)
        else:
            pass
        return x + y

    add_integers = staticmethod(add_integers)
