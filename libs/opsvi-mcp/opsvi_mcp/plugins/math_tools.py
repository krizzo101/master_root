"""
Math Tools Plugin for MCP Server

This plugin demonstrates how to create custom tools that can be
dynamically loaded into the MCP server.
"""

from typing import Any, Dict, List
from mcp.types import TextContent
import sys
import os

# Add parent directory to path to import BaseTool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_server_template import BaseTool


class CalculatorTool(BaseTool):
    """
    A simple calculator tool that performs basic arithmetic operations.
    """

    def __init__(self) -> None:
        super().__init__(
            name="calculator",
            description="Performs basic arithmetic calculations",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The arithmetic operation to perform",
                    },
                    "a": {
                        "type": "number",
                        "description": "First operand",
                    },
                    "b": {
                        "type": "number",
                        "description": "Second operand",
                    },
                },
                "required": ["operation", "a", "b"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the calculator operation."""
        self.validate_input(arguments)

        operation = arguments["operation"]
        a = arguments["a"]
        b = arguments["b"]

        result = None
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return [
                    TextContent(
                        type="text",
                        text="Error: Division by zero",
                    )
                ]
            result = a / b

        return [
            TextContent(
                type="text",
                text=f"Result: {a} {operation} {b} = {result}",
            )
        ]


class FactorialTool(BaseTool):
    """
    A tool that calculates the factorial of a number.
    """

    def __init__(self) -> None:
        super().__init__(
            name="factorial",
            description="Calculates the factorial of a non-negative integer",
            input_schema={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 170,  # Prevent overflow
                        "description": "The number to calculate factorial for",
                    },
                },
                "required": ["n"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Calculate the factorial."""
        self.validate_input(arguments)

        n = arguments["n"]

        # Calculate factorial
        result = 1
        for i in range(1, n + 1):
            result *= i

        return [
            TextContent(
                type="text",
                text=f"Factorial of {n} is {result}",
            )
        ]


class FibonacciTool(BaseTool):
    """
    A tool that generates Fibonacci sequence.
    """

    def __init__(self) -> None:
        super().__init__(
            name="fibonacci",
            description="Generates Fibonacci sequence up to n terms",
            input_schema={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Number of Fibonacci terms to generate",
                    },
                },
                "required": ["n"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Generate Fibonacci sequence."""
        self.validate_input(arguments)

        n = arguments["n"]

        if n == 1:
            sequence = [0]
        elif n == 2:
            sequence = [0, 1]
        else:
            sequence = [0, 1]
            for i in range(2, n):
                sequence.append(sequence[-1] + sequence[-2])

        return [
            TextContent(
                type="text",
                text=f"First {n} Fibonacci numbers: {', '.join(map(str, sequence))}",
            )
        ]
