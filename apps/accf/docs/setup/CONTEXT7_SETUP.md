<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Context7 MCP Server Setup Guide","description":"This document provides detailed instructions for installing, configuring, and using the Context7 MCP Server, including integration with the research agent, available functions, and troubleshooting guidance.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify logical sections based on the heading hierarchy and content themes. Extract key elements such as code blocks, configuration snippets, and important concepts that aid in understanding the setup and usage of the Context7 MCP Server. Ensure all line numbers are accurate and sections do not overlap. Provide clear, descriptive names and descriptions for sections and key elements to facilitate navigation and comprehension.","sections":[{"name":"Document Title","description":"The main title of the document introducing the Context7 MCP Server Setup Guide.","line_start":7,"line_end":7},{"name":"Overview","description":"Introduction to Context7 and its role in providing technical documentation for libraries, frameworks, and APIs, and its use by the research agent.","line_start":9,"line_end":11},{"name":"Setup Instructions","description":"Step-by-step instructions for installing, configuring, and verifying the Context7 MCP Server.","line_start":12,"line_end":51},{"name":"Usage in Research Agent","description":"Explanation of how the research agent automatically utilizes Context7 based on technical keywords and context.","line_start":52,"line_end":58},{"name":"Available Functions","description":"Descriptions and code examples of the main functions provided by Context7 for library resolution, documentation retrieval, and combined search and get operations.","line_start":59,"line_end":78},{"name":"Troubleshooting","description":"Common issues encountered when using Context7 MCP Server and fallback behavior of the research agent when Context7 is unavailable.","line_start":79,"line_end":104}],"key_elements":[{"name":"Install Context7 MCP Server Code Block","description":"Bash command to globally install the Context7 MCP Server package using npm.","line":15},{"name":"MCP Server Configuration JSON","description":"JSON snippet showing how to configure the Context7 MCP Server in the .cursor/mcp.json file.","line":21},{"name":"Verify Installation Python Test Script","description":"Python asynchronous script to test the Context7 tool by resolving a library and printing results.","line":35},{"name":"Library Resolution Code Example","description":"Python code snippet demonstrating how to find libraries by name using the Context7 tool.","line":62},{"name":"Documentation Retrieval Code Example","description":"Python code snippet showing how to get documentation for a specific library and topic.","line":67},{"name":"Search and Get Documentation Code Example","description":"Python code snippet illustrating how to search for a library and retrieve documentation in one step.","line":73},{"name":"Common Issues List","description":"Enumerated list of common problems such as MCP Server not found, connection errors, and no results, with troubleshooting tips.","line":81},{"name":"Fallback Behavior Description","description":"Explanation of the research agent's fallback actions when Context7 is unavailable, including continuing research and logging warnings.","line":96}]}
-->
<!-- FILE_MAP_END -->

# Context7 MCP Server Setup Guide

## Overview
Context7 provides access to technical documentation for libraries, frameworks, and APIs. The research agent uses Context7 to fetch relevant documentation for technical questions.

## Setup Instructions

### 1. Install Context7 MCP Server
```bash
npm install -g @upstash/context7-mcp
```

### 2. Configure MCP Server
Add the following to your `.cursor/mcp.json` file:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {}
    }
  }
}
```

### 3. Verify Installation
Run the Context7 tool test:
```bash
python -c "
from capabilities.tools.context7_tool import Context7Tool
import asyncio

async def test():
    tool = Context7Tool()
    results = await tool.resolve_library('openai')
    print(f'Found {len(results)} libraries')
    for result in results[:2]:
        print(f'- {result.library_id}: {result.content[:100]}...')

asyncio.run(test())
"
```

## Usage in Research Agent

The research agent automatically uses Context7 when:
- The question contains technical keywords (API, SDK, library, framework, etc.)
- Web context suggests technical documentation would be helpful
- The agent generates Context7-specific queries based on the research question

## Available Functions

### 1. Library Resolution
```python
# Find libraries by name
results = await tool.resolve_library('openai')
```

### 2. Documentation Retrieval
```python
# Get documentation for a specific library
doc = await tool.get_documentation('openai', topic='authentication')
```

### 3. Search and Get
```python
# Search for library and get docs in one step
doc = await tool.search_and_get_docs('openai', topic='authentication')
```

## Troubleshooting

### Common Issues

1. **MCP Server Not Found**
   - Ensure the server is properly configured in `.cursor/mcp.json`
   - Check that `@upstash/context7-mcp` is installed globally

2. **Connection Errors**
   - Verify the MCP server is running
   - Check network connectivity

3. **No Results**
   - Try different library names
   - Check if the library exists in Context7's database

### Fallback Behavior
If Context7 is unavailable, the research agent will:
- Continue with web search and academic research
- Log warnings about Context7 unavailability
- Complete the research workflow without technical documentation