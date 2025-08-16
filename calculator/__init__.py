"""A simple, safe calculator package.

Provides a parser, evaluator, and CLI for evaluating arithmetic expressions
without using Python's eval.

Example:
    from calculator import evaluate_expression
    result = evaluate_expression("1 + 2 * 3")  # 7.0
"""

from .evaluator import evaluate
from .parser import parse


def evaluate_expression(expression: str) -> float:
    """Parse and evaluate an arithmetic expression.

    Supported features:
    - Binary operators: +, -, *, /, ^ or ** (power)
    - Unary operators: +, -
    - Parentheses: (...)
    - Integers and decimals

    Args:
        expression: The input arithmetic expression.

    Returns:
        The numeric result as a float.

    Raises:
        ValueError: If the expression is invalid.
        ZeroDivisionError: If a division by zero occurs.
    """

    ast = parse(expression)
    return float(evaluate(ast))


__all__ = [
    "evaluate_expression",
    "evaluate",
    "parse",
]
