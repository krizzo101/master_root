# Claude Code Clone

A powerful AI coding assistant that provides Claude Code-like functionality with multi-provider LLM support.

## Features

- **Multi-Provider Support**: Works with OpenAI, Anthropic, and Perplexity models
- **Headless Execution**: Run AI coding tasks programmatically
- **File Operations**: Analyze, generate, and refactor code files
- **Project Analysis**: Comprehensive project structure and code quality analysis
- **Streaming Responses**: Real-time streaming of AI responses
- **Interactive Mode**: Command-line interactive interface
- **Configurable**: Extensive configuration options for different use cases

## Installation

```bash
# Install from the workspace
uv add claude-code-clone

# Or install in development mode
uv pip install -e .
```

## Configuration

Set environment variables or use a `.env` file:

```bash
# Provider configuration
CLAUDE_CODE_PROVIDER=openai  # or anthropic, perplexity
CLAUDE_CODE_MODEL=gpt-5-mini
CLAUDE_CODE_API_KEY=your_api_key_here

# Optional configuration
CLAUDE_CODE_ORGANIZATION=your_org_id  # For OpenAI
CLAUDE_CODE_WORKING_DIRECTORY=.
CLAUDE_CODE_MAX_TOKENS=4000
CLAUDE_CODE_TEMPERATURE=0.1
```

## Usage

### Command Line Interface

#### Analyze a file
```bash
claude-code analyze myfile.py --analysis-type security
```

#### Generate code
```bash
claude-code generate newfile.py "Create a REST API endpoint for user authentication"
```

#### Refactor code
```bash
claude-code refactor oldfile.py --refactor-type optimize
```

#### Analyze entire project
```bash
claude-code project ./my-project --analysis-types structure,complexity,duplicates
```

#### Interactive mode
```bash
claude-code interactive
```

### Python API

```python
from claude_code import ClaudeCodeExecutor, ClaudeCodeConfig

# Configure
config = ClaudeCodeConfig(
    provider="openai",
    model="gpt-5-mini",
    api_key="your_api_key"
)

# Create executor
executor = ClaudeCodeExecutor(config)

# Analyze a file
analysis = await executor.analyze_file("myfile.py", "security")

# Generate code
code = await executor.generate_file("newfile.py", "Create a web scraper")

# Refactor code
refactored = await executor.refactor_file("oldfile.py", "optimize")

# Close when done
await executor.close()
```

## Supported File Types

- **Python**: `.py`
- **JavaScript/TypeScript**: `.js`, `.ts`, `.jsx`, `.tsx`
- **Java**: `.java`
- **C/C++**: `.c`, `.cpp`, `.h`
- **Go**: `.go`
- **Rust**: `.rs`
- **PHP**: `.php`
- **Ruby**: `.rb`
- **Swift**: `.swift`
- **Kotlin**: `.kt`
- **Scala**: `.scala`
- **Shell**: `.sh`, `.bash`, `.zsh`, `.fish`
- **PowerShell**: `.ps1`
- **Batch**: `.bat`, `.cmd`
- **SQL**: `.sql`
- **Web**: `.html`, `.css`, `.scss`, `.sass`, `.less`
- **Data**: `.json`, `.yaml`, `.yml`, `.toml`, `.xml`
- **Documentation**: `.md`, `.txt`, `.rst`

## Analysis Types

- **general**: Comprehensive code analysis
- **security**: Security vulnerability analysis
- **performance**: Performance optimization analysis
- **style**: Code style and best practices
- **bugs**: Bug detection and error analysis

## Refactoring Types

- **improve**: General code improvements
- **optimize**: Performance optimization
- **modernize**: Modern language features and best practices
- **simplify**: Code simplification while maintaining functionality

## Architecture

The application is built on top of the existing `opsvi-llm` library and follows these principles:

- **Modular Design**: Separate concerns for execution, analysis, and streaming
- **Provider Abstraction**: Unified interface for different LLM providers
- **Async/Await**: Full async support for better performance
- **Error Handling**: Comprehensive error handling and logging
- **Configuration**: Flexible configuration system
- **Security**: Built-in security features and validation

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/

# Type checking
mypy src/
```

## License

MIT License - see LICENSE file for details.
