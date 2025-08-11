"""
Script Demonstrating eval() and exec() Functions Usage

This script contains examples showcasing the usage of Python's eval() and exec() built-in functions.
It is intended for educational purposes and uses only hardcoded strings for safety.

Author: Your Name
Date: 2024-06-09
"""

import logging
from typing import Any

# Configure logging for debug and information output
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed output
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def demonstrate_eval() -> None:
    """
    Demonstrates the use of the eval() function to safely evaluate an expression.
    Only hardcoded strings are used for safety.
    """
    logging.info("Starting eval() demonstration.")
    # Example 1: Evaluate a simple arithmetic expression
    expression1 = "2 + 3 * (4 - 1)"
    # The eval() function parses the string as a Python expression and evaluates it.
    try:
        result1 = eval(expression1)
        print(f"[eval()] The result of the expression '{expression1}' is: {result1}")
        logging.debug(f"Evaluated '{expression1}' -> {result1}")
    except Exception as e:
        logging.error(f"Error evaluating expression '{expression1}': {e}")

    # Example 2: Evaluate an expression using built-in functions and variables
    x = 5
    y = 8
    expression2 = "pow(x, 2) + y"
    # Provide globals/locals in eval to include variables x, y and built-in pow
    try:
        result2 = eval(expression2, {"__builtins__": {"pow": pow}}, {"x": x, "y": y})
        print(
            f"[eval()] The result of the expression '{expression2}' with x={x}, y={y} is: {result2}"
        )
        logging.debug(f"Evaluated '{expression2}' with x={x}, y={y} -> {result2}")
    except Exception as e:
        logging.error(f"Error evaluating expression '{expression2}': {e}")


def demonstrate_exec() -> None:
    """
    Demonstrates the use of the exec() function to execute a statement or code block.
    Only hardcoded statement strings are used for safety.
    """
    logging.info("Starting exec() demonstration.")

    # Example 1: Assign a variable using exec()
    code1 = "z = 10\nz = z + 2"
    environment = {}
    try:
        # The exec() function can execute statements, including assignments and multi-line code.
        exec(code1, {}, environment)
        if "z" in environment:
            print(f"[exec()] After executing code, z = {environment['z']}")
            logging.debug(f"Exec assigned z = {environment['z']}")
        else:
            print(f"[exec()] Variable 'z' was not assigned in the environment.")
    except Exception as e:
        logging.error(f"Error executing code block: {e}")

    # Example 2: Define a function dynamically and call it
    code2 = (
        "def greet(name):\n" '    return f"Hello, {name}!"\n' 'result = greet("Alice")'
    )
    environment2 = {}
    try:
        exec(code2, {}, environment2)
        if "result" in environment2:
            print(f"[exec()] Function greet executed: {environment2['result']}")
            logging.debug(f"Greet function result: {environment2['result']}")
        else:
            print("[exec()] 'result' variable not found after exec()")
    except Exception as e:
        logging.error(f"Error executing code block for function: {e}")


def main() -> None:
    """
    Main function to demonstrate the eval() and exec() functions.
    """
    print("\n==== Demonstration of eval() function ====")
    demonstrate_eval()
    print("\n==== Demonstration of exec() function ====")
    demonstrate_exec()


if __name__ == "__main__":
    main()
