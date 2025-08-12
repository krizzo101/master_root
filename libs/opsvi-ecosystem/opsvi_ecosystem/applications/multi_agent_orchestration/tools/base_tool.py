"""
Base tool interface for the multi-agent orchestration system.

Defines the abstract base class that all tools must implement,
providing a consistent interface for tool integration and execution.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional

from ..common.types import ToolError, ToolSchema

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for all tools in the multi-agent system.

    Tools are pluggable components that provide specific capabilities
    to agents, such as web search, data processing, or external API access.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize the base tool.

        Args:
            name: Unique tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self._schema: Optional[ToolSchema] = None

        logger.debug(f"Tool {self.name} initialized")

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.

        Args:
            parameters: Tool execution parameters

        Returns:
            Tool execution results

        Raises:
            ToolError: If tool execution fails
        """
        pass

    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """
        Get the tool's input/output schema.

        Returns:
            ToolSchema defining the tool's interface
        """
        pass

    def validate_input(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate input parameters against the tool's schema.

        Args:
            parameters: Parameters to validate

        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            schema = self.get_schema()

            # Check required parameters
            for param in schema.required_params:
                if param not in parameters:
                    logger.error(
                        f"Missing required parameter '{param}' for tool {self.name}"
                    )
                    return False

            # Basic type validation could be added here
            # For now, we'll do simple presence checking

            return True

        except Exception as e:
            logger.error(f"Error validating input for tool {self.name}: {e}")
            return False

    async def safe_execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely execute the tool with comprehensive error handling.

        Args:
            parameters: Tool execution parameters

        Returns:
            Tool execution results with error handling
        """
        try:
            # Validate input
            if not self.validate_input(parameters):
                raise ToolError(f"Invalid input parameters for tool {self.name}")

            logger.info(f"Executing tool {self.name} with parameters: {parameters}")

            # Execute the tool
            result = await self.execute(parameters)

            logger.info(f"Tool {self.name} executed successfully")
            return {
                "success": True,
                "result": result,
                "tool_name": self.name,
                "error": None,
            }

        except ToolError as e:
            logger.error(f"Tool error in {self.name}: {e}")
            return {
                "success": False,
                "result": None,
                "tool_name": self.name,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected error in tool {self.name}: {e}")
            return {
                "success": False,
                "result": None,
                "tool_name": self.name,
                "error": f"Unexpected error: {str(e)}",
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about the tool's capabilities.

        Returns:
            Dictionary describing tool capabilities
        """
        schema = self.get_schema()
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": schema.input_schema,
            "output_schema": schema.output_schema,
            "required_params": schema.required_params,
        }

    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        """Detailed string representation of the tool."""
        return f"{self.__class__.__name__}(name='{self.name}', description='{self.description}')"
