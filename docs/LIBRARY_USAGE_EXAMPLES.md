# Library Usage Examples

## opsvi-llm: Using the Anthropic Provider

```python
from opsvi_llm.providers import AnthropicProvider, AnthropicConfig

# Initialize the provider
config = AnthropicConfig(
    api_key="your-api-key",  # Or set ANTHROPIC_API_KEY env var
    model="claude-3-5-sonnet-20241022",
    max_tokens=8192
)

provider = AnthropicProvider(config)

# Simple chat example
response = provider.chat({
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
})

print(response.content)

# Async chat example
import asyncio

async def chat_async():
    response = await provider.chat_async({
        "messages": [
            {"role": "user", "content": "Tell me about async programming"}
        ]
    })
    return response.content

# Run async
result = asyncio.run(chat_async())

# List available models
models = provider.list_models()
print(f"Available models: {models}")

# Get model info
info = provider.get_model_info("claude-opus-4-1-20250805")
print(f"Model info: {info}")
```

## opsvi-interfaces: Building CLI Applications

```python
from opsvi_interfaces.cli import CLIApplication

# Create a CLI application with auto-discovery
class MyApp(CLIApplication):
    def __init__(self):
        super().__init__(
            name="myapp",
            version="1.0.0",
            help="My awesome CLI application"
        )
    
    def cmd_hello(self, name: str = "World"):
        """Say hello to someone"""
        print(f"Hello, {name}!")
    
    def cmd_status(self):
        """Show application status"""
        print("Application is running")

# Run the application
if __name__ == "__main__":
    app = MyApp()
    app.run()
```

### Manual Command Registration

```python
from opsvi_interfaces.cli import BaseCLI
import click

# Create CLI
cli = BaseCLI(name="tool", version="1.0.0")

# Add commands using decorator
@cli.command()
@click.argument('filename')
@click.option('--verbose', '-v', is_flag=True)
def process(filename, verbose):
    """Process a file"""
    if verbose:
        print(f"Processing {filename} with verbose output")
    else:
        print(f"Processing {filename}")

# Add command group
@cli.group()
def database():
    """Database operations"""
    pass

@cli.command(parent='database')
def migrate():
    """Run database migrations"""
    print("Running migrations...")

# Run the CLI
if __name__ == "__main__":
    cli.run()
```

### Async Commands

```python
from opsvi_interfaces.cli import CLIApplication, async_command
import asyncio

class AsyncApp(CLIApplication):
    def __init__(self):
        super().__init__(name="async-app")
    
    @async_command()
    async def cmd_fetch(self, url: str):
        """Fetch data from URL"""
        # Simulate async operation
        await asyncio.sleep(1)
        print(f"Fetched data from {url}")

app = AsyncApp()
app.run()
```

## opsvi-mcp: MCP Server Integration

```python
from opsvi_mcp import MCPServer, MCPTool, MCPResource

# Create MCP server
server = MCPServer(
    name="my-mcp-server",
    version="1.0.0",
    description="My MCP server"
)

# Add a tool
@server.tool()
async def calculate(a: float, b: float, operation: str = "add"):
    """Perform calculation"""
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    else:
        return f"Unknown operation: {operation}"

# Add a resource
@server.resource()
async def get_config():
    """Get configuration"""
    return {
        "database": "postgresql://localhost/mydb",
        "cache": "redis://localhost:6379"
    }

# Run the server
if __name__ == "__main__":
    server.run()
```

## opsvi-core: Service Registry Example

```python
from opsvi_core import ServiceRegistry, ServiceInfo, ServiceStatus

# Create registry
registry = ServiceRegistry()

# Register a service
service = ServiceInfo(
    name="api-gateway",
    status=ServiceStatus.RUNNING,
    version="2.0.0",
    host="localhost",
    port=8080,
    metadata={"region": "us-east-1"}
)

registry.register(service)

# Discover services
api_services = registry.discover(name_pattern="api-*")
for service in api_services:
    print(f"Found: {service.name} at {service.host}:{service.port}")

# Update service status
registry.update_status("api-gateway", ServiceStatus.STOPPING)

# Health check
is_healthy = registry.health_check("api-gateway")
```

## Integration Example: CLI with LLM

```python
from opsvi_interfaces.cli import CLIApplication
from opsvi_llm.providers import AnthropicProvider
import click

class AIAssistant(CLIApplication):
    def __init__(self):
        super().__init__(
            name="ai-assistant",
            version="1.0.0",
            help="AI-powered CLI assistant"
        )
        self.llm = AnthropicProvider()
    
    def cmd_ask(self, question: str):
        """Ask the AI a question"""
        response = self.llm.chat({
            "messages": [
                {"role": "user", "content": question}
            ]
        })
        print(response.content)
    
    def cmd_code(self, description: str, language: str = "python"):
        """Generate code from description"""
        prompt = f"Generate {language} code for: {description}"
        response = self.llm.chat({
            "messages": [
                {"role": "system", "content": f"You are a {language} code generator."},
                {"role": "user", "content": prompt}
            ]
        })
        print(response.content)

if __name__ == "__main__":
    app = AIAssistant()
    app.run()
```

## Testing Your Implementation

```python
# test_anthropic_provider.py
import pytest
from opsvi_llm.providers import AnthropicProvider, AnthropicConfig

def test_provider_initialization():
    """Test provider can be initialized"""
    config = AnthropicConfig(api_key="test-key")
    provider = AnthropicProvider(config)
    assert provider is not None
    assert provider.config.api_key == "test-key"

def test_list_models():
    """Test model listing"""
    provider = AnthropicProvider(api_key="test-key")
    models = provider.list_models()
    assert "claude-3-5-sonnet-20241022" in models
    assert "claude-opus-4-1-20250805" in models

# test_cli.py
from opsvi_interfaces.cli import BaseCLI, CLIApplication

def test_cli_creation():
    """Test CLI can be created"""
    cli = BaseCLI(name="test", version="1.0.0")
    assert cli.name == "test"
    assert cli.version == "1.0.0"

def test_cli_application():
    """Test CLI application with auto-discovery"""
    class TestApp(CLIApplication):
        def cmd_test(self):
            return "test"
    
    app = TestApp(name="test-app")
    assert app.cli.name == "test-app"
```

## Environment Setup

```bash
# Install dependencies
pip install anthropic click pydantic

# Set environment variables
export ANTHROPIC_API_KEY="your-api-key"

# Run examples
python examples/llm_example.py
python examples/cli_example.py
```

## Common Patterns

### Error Handling

```python
from opsvi_llm.providers import AnthropicProvider, LLMRequestError

try:
    provider = AnthropicProvider()
    response = provider.chat({"messages": [{"role": "user", "content": "Hello"}]})
except LLMRequestError as e:
    print(f"Request failed: {e}")
```

### Configuration Management

```python
from opsvi_interfaces.config import ConfigManager

config = ConfigManager()
config.load("config.yaml")

# Access config values
api_key = config.get("anthropic.api_key")
model = config.get("anthropic.model", default="claude-3-5-sonnet-20241022")
```

### Logging

```python
import logging
from opsvi_llm.providers import AnthropicProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

provider = AnthropicProvider()
logger.info("Provider initialized")
```

## Next Steps

1. **Add more providers**: Implement OpenAI, Perplexity providers
2. **Enhance CLI**: Add more decorators, plugins, themes
3. **Core services**: Implement event bus, state manager
4. **Testing**: Add comprehensive test suites
5. **Documentation**: Generate API docs with Sphinx
6. **Examples**: Create real-world application examples