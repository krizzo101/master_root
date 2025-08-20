# OPSVI Assistant

A demonstration application showcasing the integrated use of opsvi libraries.

## Features

- AI-powered CLI assistant using opsvi-llm
- Command-line interface built with opsvi-interfaces
- Service coordination with opsvi-core
- MCP server integration via opsvi-mcp

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export ANTHROPIC_API_KEY="your-api-key"
export OPENAI_API_KEY="your-openai-key"  # Optional
```

## Usage

```bash
# Run the assistant
python -m opsvi_assistant

# Available commands
opsvi-assistant ask "What is Python?"
opsvi-assistant code "fibonacci function"
opsvi-assistant analyze /path/to/code.py
opsvi-assistant chat  # Interactive mode
```

## Architecture

The application demonstrates:
- Clean separation of concerns using opsvi libraries
- Async/await patterns for LLM interactions
- Plugin-based command architecture
- Error handling and logging best practices