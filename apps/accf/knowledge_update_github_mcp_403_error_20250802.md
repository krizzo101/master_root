# Knowledge Update: GitHub MCP Server 403 Error (Generated 2025-08-02)

## Current State (Last 12+ Months)

The GitHub MCP server at `https://api.githubcopilot.com/mcp/` is experiencing widespread 403 "Dynamic client registration failed" errors across multiple MCP clients including Claude Code, Claude Desktop, and Claude.ai. This is a known issue affecting users trying to connect to the remote GitHub MCP server.

## Best Practices & Patterns

### OAuth 2.0 Dynamic Client Registration (DCR)
- **RFC 7591 Compliance**: The MCP specification requires authorization servers to support OAuth 2.0 Dynamic Client Registration Protocol
- **Current Issue**: GitHub's MCP server does not fully implement DCR, causing 403 errors
- **Workaround**: Use Personal Access Token (PAT) authentication instead of OAuth

### Authentication Methods
1. **OAuth (Currently Broken)**: Requires DCR support which GitHub MCP server lacks
2. **Personal Access Token (PAT)**: Working alternative that bypasses DCR requirements
3. **Bearer Token**: Standard HTTP Authorization header format

## Tools & Frameworks

### GitHub MCP Server Configuration
- **Remote Server URL**: `https://api.githubcopilot.com/mcp/`
- **Local Server**: Docker-based alternative using `ghcr.io/github/github-mcp-server`
- **Supported Transports**: HTTP/SSE, Streamable HTTP

### MCP Client Support
- **VS Code**: Full support for both OAuth and PAT
- **Claude Code/Desktop**: Only supports DCR (currently broken with GitHub)
- **JetBrains IDEs**: PAT-only authentication
- **Xcode**: PAT-only authentication

## Implementation Guidance

### Working Configuration (PAT Method)
```json
{
  "mcpServers": {
    "github": {
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_GITHUB_PAT"
      }
    }
  }
}
```

### Local Server Configuration
```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
      }
    }
  }
}
```

## Limitations & Considerations

### Current Limitations
- **DCR Not Supported**: GitHub MCP server lacks Dynamic Client Registration
- **OAuth Broken**: All OAuth flows fail with 403 errors
- **Client Incompatibility**: Claude products cannot connect due to DCR requirement
- **Enterprise Restrictions**: Enterprise Managed Users with PAT restrictions cannot use PAT authentication

### Security Considerations
- **PAT Scopes**: Must include appropriate scopes (`repo`, `read:packages`, etc.)
- **Token Security**: PATs should be treated as sensitive credentials
- **Audit Trail**: PAT usage provides better audit capabilities than OAuth

### Workarounds
1. **Use PAT Authentication**: Most reliable current solution
2. **Local Server**: Docker-based alternative with full control
3. **Wait for Fix**: GitHub team is aware of the issue but no timeline provided
4. **Alternative Clients**: Use VS Code or other PAT-supporting clients

## Error Analysis

### 403 Error Meaning
A 403 Forbidden error indicates that the server understood the request but refuses to authorize it. In this context:
- **Dynamic Client Registration Failed**: The MCP client attempted to register itself with GitHub's authorization server
- **Server Rejection**: GitHub's server rejected the registration attempt
- **Authentication Required**: The server requires proper authentication that DCR cannot provide

### Root Cause
The GitHub MCP server implements OAuth 2.1 but does not support the Dynamic Client Registration Protocol (RFC 7591) that modern MCP clients expect. This creates a mismatch between client expectations and server capabilities.