# MCP Server Integration Scripts for Python

This directory contains comprehensive Python scripts for integrating various Model Context Protocol (MCP) servers. These scripts provide a complete framework for connecting AI applications to external tools and data sources.

## 📋 Overview

Model Context Protocol (MCP) is a protocol that enables AI applications to connect to external tools and data sources. It uses JSON-RPC 2.0 for communication and supports various transport mechanisms.

### Available Scripts

| Script | MCP Server | Purpose | API Required |
|--------|------------|---------|--------------|
| `mcp_integration_template.py` | Template | General MCP integration guide | None |
| `brave_mcp_search.py` | Brave Search | Web search functionality | Brave API Key |
| `firecrawl_mcp_client.py` | Firecrawl | Web scraping and crawling | Firecrawl API Key |
| `arxiv_mcp_client.py` | ArXiv | Research paper search/access | None |
| `context7_mcp_client.py` | Context7 | Technical documentation | None |
| `sequential_thinking_mcp_client.py` | Sequential Thinking | Complex problem solving | None |

## 🚀 Quick Start

### Prerequisites

```bash
# Install MCP Python SDK
pip install "mcp[cli]"

# Install required Node.js packages
npm install -g firecrawl-mcp
npm install -g @upstash/context7-mcp
npm install -g server-sequential-thinking
npm install -g brave-search-mcp

# Install ArXiv MCP server (Python)
pip install arxiv-mcp-server
```

### Configuration

The scripts use the `.cursor/mcp.json` configuration file. Current configuration includes:

```json
{
  "mcpServers": {
    "web_search": {
      "command": "npx",
      "args": ["-y", "brave-search-mcp"],
      "env": {
        "BRAVE_API_KEY": "your-brave-api-key"
      }
    },
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "your-firecrawl-api-key"
      }
    },
    "research_papers": {
      "command": "python",
      "args": ["-m", "arxiv_mcp_server"]
    },
    "tech_docs": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "sequential_thinking": {
      "command": "npx",
      "args": ["-y", "server-sequential-thinking"]
    }
  }
}
```

## 📚 Script Documentation

### 1. MCP Integration Template (`mcp_integration_template.py`)

A comprehensive template demonstrating how to integrate any MCP server with detailed comments and best practices.

**Features:**
- Complete MCP client framework
- Error handling patterns
- Configuration management
- Async/await patterns
- Logging and debugging

**Usage:**
```python
from mcp_integration_template import MCPClientTemplate

client = MCPClientTemplate()
# Use as reference for implementing new MCP integrations
```

### 2. Web Search (`brave_mcp_search.py`)

Integrates with Brave Search MCP server for comprehensive web searching.

**Features:**
- Web, image, news, video, and local search
- API key management from mcp.json
- Command-line interface
- Comprehensive error handling

**Usage:**
```bash
# Web search
python brave_mcp_search.py search "machine learning" --max-results 10

# Image search
python brave_mcp_search.py image "neural networks" --count 3

# News search
python brave_mcp_search.py news "AI developments" --freshness pd
```

### 3. Web Scraping (`firecrawl_mcp_client.py`)

Integrates with Firecrawl MCP server for web scraping and crawling.

**Features:**
- Single page scraping
- Website crawling
- Content search
- Markdown extraction
- Rate limiting and error handling

**Usage:**
```bash
# Scrape a single page
python firecrawl_mcp_client.py scrape "https://example.com"

# Search and scrape results
python firecrawl_mcp_client.py search "python tutorials" --limit 5

# Crawl a website
python firecrawl_mcp_client.py crawl "https://docs.python.org" --max-depth 2
```

### 4. Research Papers (`arxiv_mcp_client.py`)

Integrates with ArXiv MCP server for academic research paper access.

**Features:**
- Paper search with filters
- Paper download and conversion
- Markdown content reading
- Category and date filtering
- Local paper management

**Usage:**
```bash
# Search for papers
python arxiv_mcp_client.py search "machine learning" --max-results 5

# Download a paper
python arxiv_mcp_client.py download "2301.07041"

# Read a downloaded paper
python arxiv_mcp_client.py read "2301.07041" --summary
```

### 5. Technical Documentation (`context7_mcp_client.py`)

Integrates with Context7 MCP server for accessing up-to-date technical documentation.

**Features:**
- Library ID resolution
- Documentation retrieval
- Topic-focused searches
- Token management
- Version-specific docs

**Usage:**
```bash
# Resolve library ID
python context7_mcp_client.py resolve "react"

# Get documentation
python context7_mcp_client.py docs "/vercel/next.js" --topic "hooks"

# Search and get docs
python context7_mcp_client.py search-docs "fastapi" --topic "authentication"
```

### 6. Complex Problem Solving (`sequential_thinking_mcp_client.py`)

Integrates with Sequential Thinking MCP server for structured problem-solving.

**Features:**
- Step-by-step reasoning
- Thought revision and branching
- Session management
- Problem decomposition
- Solution synthesis

**Usage:**
```bash
# Solve a problem
python sequential_thinking_mcp_client.py solve "How to design a scalable API?"

# Single thinking step
python sequential_thinking_mcp_client.py think "Let me analyze this step by step"
```

## 🔧 Implementation Patterns

### Common MCP Integration Pattern

All scripts follow this consistent pattern:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self, config_path=".cursor/mcp.json"):
        self.config_path = config_path

    @asynccontextmanager
    async def _get_session(self):
        # Load configuration
        # Create server parameters
        # Establish connection
        yield session

    async def operation(self, **kwargs):
        async with self._get_session() as session:
            result = await session.call_tool("tool_name", arguments)
            return self._parse_result(result)
```

### Error Handling

```python
try:
    result = await session.call_tool("tool_name", arguments)
    return self._parse_result(result)
except Exception as e:
    self.logger.error(f"Operation failed: {e}")
    return ErrorResult(error=str(e))
```

### Configuration Loading

```python
config_path = Path(self.mcp_config_path)
with open(config_path, 'r') as f:
    config = json.load(f)

server_config = config.get('mcpServers', {}).get('server_name', {})
```

## 🛠️ Development Guidelines

### Adding New MCP Integrations

1. **Use the Template**: Start with `mcp_integration_template.py`
2. **Follow Patterns**: Use consistent async/await patterns
3. **Error Handling**: Implement comprehensive error handling
4. **Configuration**: Support mcp.json configuration
5. **CLI Interface**: Provide command-line access
6. **Documentation**: Include detailed docstrings
7. **Testing**: Add test cases and examples

### Best Practices

- **Async Context Managers**: Use for session management
- **Dataclasses**: Define structured data types
- **Logging**: Implement proper logging
- **Type Hints**: Use comprehensive type annotations
- **Error Classes**: Define custom exception classes
- **Validation**: Validate inputs and outputs
- **Timeouts**: Implement reasonable timeouts

## 🔍 Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   # Install MCP SDK
   pip install "mcp[cli]"

   # Install server packages
   npm install -g server-package-name
   ```

2. **Configuration Errors**
   - Check `.cursor/mcp.json` exists
   - Verify server configuration
   - Ensure API keys are correct

3. **Connection Issues**
   - Verify server is installed
   - Check network connectivity
   - Review server logs

4. **API Key Issues**
   - Confirm API keys are valid
   - Check environment variables
   - Verify mcp.json configuration

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python script_name.py --debug command arguments
```

## 📖 API References

- **MCP Specification**: https://modelcontextprotocol.io/
- **Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **Server Registry**: https://github.com/modelcontextprotocol/servers
- **Brave Search API**: https://brave.com/search/api/
- **Firecrawl API**: https://docs.firecrawl.dev/
- **ArXiv API**: https://arxiv.org/help/api
- **Context7**: https://context7.upstash.com/

## 🤝 Contributing

1. Follow the established patterns
2. Add comprehensive documentation
3. Include error handling
4. Provide CLI interfaces
5. Add test examples
6. Update this README

## 📄 License

These scripts are provided as examples and templates for MCP integration. Modify and use according to your project's license requirements.
