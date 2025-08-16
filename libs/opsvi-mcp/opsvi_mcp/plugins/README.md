# MCP Server Plugins

This directory contains plugin tools that can be dynamically loaded into the MCP server.

## How Plugins Work

The MCP server template supports a plugin system that allows you to add custom tools without modifying the core server code. Plugins are automatically discovered and loaded at server startup.

## Creating a Plugin

To create a new plugin:

1. Create a new Python file in this directory (e.g., `my_tools.py`)
2. Import the `BaseTool` class from the parent module
3. Create one or more classes that inherit from `BaseTool`
4. Implement the required methods

### Plugin Structure

```python
from typing import Any, Dict, List
from mcp.types import TextContent
import sys
import os

# Add parent directory to path to import BaseTool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_server_template import BaseTool


class MyCustomTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="my_tool",
            description="Description of what my tool does",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Parameter description"},
                    "param2": {"type": "number", "description": "Another parameter"},
                },
                "required": ["param1"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        # Tool implementation
        self.validate_input(arguments)  # Validates against input_schema
        
        # Process arguments
        result = process_somehow(arguments)
        
        return [TextContent(type="text", text=result)]
```

## Loading Plugins

Plugins are loaded automatically when the server starts. You can specify the plugin directory using:

- Command line: `python -m mcp_server_template --plugin-dir /path/to/plugins`
- Environment variable: `export MCP_PLUGIN_DIR=/path/to/plugins`
- Default location: `./plugins` (relative to where the server is run)

## Included Example Plugins

### math_tools.py
- **calculator**: Performs basic arithmetic operations (add, subtract, multiply, divide)
- **factorial**: Calculates the factorial of a number
- **fibonacci**: Generates Fibonacci sequence

### text_tools.py
- **text_stats**: Provides text statistics (word count, character count, etc.)
- **base64**: Encode/decode text using Base64
- **hash**: Generate MD5, SHA1, or SHA256 hash digests
- **regex**: Perform regex pattern matching and replacement

## Input Validation

All plugin tools automatically benefit from JSON Schema validation. The `validate_input()` method is called automatically and will:

1. Check that all required parameters are present
2. Validate parameter types (string, number, boolean, etc.)
3. Validate parameter constraints (minimum, maximum, enum values, etc.)
4. Provide clear error messages for validation failures

## Best Practices

1. **Clear Naming**: Use descriptive names for your tools and parameters
2. **Comprehensive Schemas**: Define complete input schemas with all constraints
3. **Error Handling**: Handle expected errors gracefully and return helpful error messages
4. **Documentation**: Include docstrings and clear descriptions
5. **Type Hints**: Use proper type hints for better code clarity
6. **Async Support**: Tools should be async-compatible using `async def execute()`

## Testing Plugins

To test your plugins:

1. Start the server with your plugin directory:
   ```bash
   python -m mcp_server_template --plugin-dir ./plugins
   ```

2. The server will log which plugins were loaded:
   ```
   [INFO] Loaded plugin tool 'calculator' from math_tools.py
   [INFO] Loaded plugin tool 'factorial' from math_tools.py
   ...
   ```

3. Use the MCP client to list available tools and test them

## Troubleshooting

- **Plugin not loading**: Check the server logs for error messages. Common issues:
  - Syntax errors in the plugin file
  - Missing imports
  - Invalid tool configuration
  
- **Validation errors**: The server uses JSON Schema validation. Check that:
  - Your input matches the schema exactly
  - Required fields are provided
  - Data types are correct

- **Import errors**: Ensure the plugin can import `BaseTool` by including the sys.path modification shown in the examples