# Project Context MCP Server - API Reference

**Version**: 0.1.0
**Protocol**: MCP (Model Context Protocol)
**Server Type**: FastMCP

## Overview

The Project Context MCP Server provides 21 specialized tools for semantic access to project intelligence data. It offers comprehensive code analysis, architecture insights, and project management capabilities through a unified MCP interface.

## Authentication

### API Key Authentication
```http
Authorization: Bearer YOUR_API_KEY
```

### Environment Variables
- `API_KEY`: Required API key for authentication
- `CORS_ORIGINS`: Allowed CORS origins (default: *)
- `RATE_LIMIT_PER_MINUTE`: Request rate limit (default: 1000)

## Base URL
- **Development**: `http://localhost:3000`
- **Production**: `https://your-domain.com/api`

## Content Types
- **Request**: `application/json`
- **Response**: `application/json`

---

## 🔍 Discovery Tools

### 1. get_file_info
**Description**: Get comprehensive information about a specific file including code elements, dependencies, and metadata.

**Parameters**:
```json
{
  "file_path": "string (required)",
  "include_content": "boolean (optional, default: false)",
  "include_dependencies": "boolean (optional, default: true)"
}
```

**Response**:
```json
{
  "file_path": "/path/to/file.py",
  "size": 1024,
  "last_modified": "2025-01-15T10:30:00Z",
  "language": "python",
  "elements": [
    {
      "name": "function_name",
      "type": "function",
      "line_start": 10,
      "line_end": 25,
      "complexity": 5.2,
      "dependencies": ["module1", "module2"]
    }
  ],
  "dependencies": {
    "imports": ["os", "sys", "json"],
    "external": ["requests", "pydantic"]
  },
  "metrics": {
    "lines_of_code": 120,
    "cyclomatic_complexity": 8.5,
    "maintainability_index": 75.2
  }
}
```

**Error Responses**:
- `404`: File not found
- `403`: Access denied
- `500`: Internal server error

**Example**:
```bash
curl -X POST https://api.example.com/tools/get_file_info \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "src/main.py", "include_dependencies": true}'
```

### 2. find_files
**Description**: Search for files matching specific patterns, types, or criteria across the project.

**Parameters**:
```json
{
  "pattern": "string (required)",
  "file_type": "string (optional)",
  "exclude_patterns": "array<string> (optional)",
  "max_results": "integer (optional, default: 100)"
}
```

**Response**:
```json
{
  "matches": [
    {
      "path": "src/components/Button.tsx",
      "size": 2048,
      "last_modified": "2025-01-15T09:15:00Z",
      "type": "typescript",
      "score": 0.95
    }
  ],
  "total_found": 25,
  "search_time_ms": 45,
  "pattern_used": "*.tsx"
}
```

### 3. find_symbols
**Description**: Locate functions, classes, variables, and other symbols across the codebase.

**Parameters**:
```json
{
  "symbol_name": "string (required)",
  "symbol_type": "string (optional: function|class|variable|interface)",
  "file_filter": "string (optional)",
  "exact_match": "boolean (optional, default: false)"
}
```

**Response**:
```json
{
  "symbols": [
    {
      "name": "UserService",
      "type": "class",
      "file_path": "src/services/UserService.ts",
      "line_start": 15,
      "line_end": 120,
      "visibility": "public",
      "signature": "class UserService implements IUserService",
      "docstring": "Service class for user management operations"
    }
  ],
  "total_found": 3
}
```

### 4. search_code
**Description**: Perform semantic and text-based search across code content.

**Parameters**:
```json
{
  "query": "string (required)",
  "file_types": "array<string> (optional)",
  "include_tests": "boolean (optional, default: false)",
  "semantic_search": "boolean (optional, default: true)",
  "limit": "integer (optional, default: 50)"
}
```

**Response**:
```json
{
  "results": [
    {
      "file_path": "src/auth/login.py",
      "line_number": 25,
      "match_text": "def authenticate_user(username: str, password: str):",
      "context_before": "    logger.info('Starting authentication')",
      "context_after": "    if not username or not password:",
      "relevance_score": 0.92,
      "match_type": "function_definition"
    }
  ],
  "query_interpretation": "Authentication function search",
  "total_matches": 12
}
```

---

## 🏗️ Architecture Tools

### 5. get_project_summary
**Description**: Get high-level overview of project structure, technologies, and metrics.

**Parameters**:
```json
{
  "include_metrics": "boolean (optional, default: true)",
  "include_dependencies": "boolean (optional, default: true)",
  "depth_limit": "integer (optional, default: 3)"
}
```

**Response**:
```json
{
  "project_name": "MyProject",
  "languages": {
    "TypeScript": {"files": 45, "lines": 12500, "percentage": 65.2},
    "Python": {"files": 23, "lines": 6800, "percentage": 34.8}
  },
  "structure": {
    "src/": {"type": "directory", "files": 68},
    "tests/": {"type": "directory", "files": 25},
    "docs/": {"type": "directory", "files": 12}
  },
  "dependencies": {
    "total_packages": 47,
    "production": 32,
    "development": 15,
    "security_issues": 2
  },
  "metrics": {
    "total_lines": 19300,
    "total_files": 68,
    "average_complexity": 6.8,
    "test_coverage": 85.3
  }
}
```

### 6. get_dependencies
**Description**: Analyze project dependencies, versions, and dependency graph.

**Parameters**:
```json
{
  "include_dev": "boolean (optional, default: false)",
  "include_transitive": "boolean (optional, default: true)",
  "vulnerability_check": "boolean (optional, default: true)",
  "outdated_check": "boolean (optional, default: true)"
}
```

### 7. get_call_graph
**Description**: Generate call graph showing function relationships and dependencies.

**Parameters**:
```json
{
  "entry_point": "string (optional)",
  "max_depth": "integer (optional, default: 5)",
  "include_external": "boolean (optional, default: false)",
  "format": "string (optional: json|graphviz|mermaid, default: json)"
}
```

### 8. get_data_models
**Description**: Extract and analyze data models, schemas, and entities.

**Parameters**:
```json
{
  "include_relationships": "boolean (optional, default: true)",
  "model_types": "array<string> (optional)",
  "generate_diagram": "boolean (optional, default: false)"
}
```

### 9. get_api_endpoints
**Description**: Discover and document API endpoints, routes, and specifications.

**Parameters**:
```json
{
  "include_middleware": "boolean (optional, default: false)",
  "include_auth": "boolean (optional, default: true)",
  "generate_openapi": "boolean (optional, default: false)"
}
```

### 10. get_entry_points
**Description**: Identify main entry points, startup files, and initialization flows.

**Parameters**:
```json
{
  "include_scripts": "boolean (optional, default: true)",
  "trace_imports": "boolean (optional, default: true)"
}
```

---

## 🧪 Testing Tools

### 11. get_tests
**Description**: Analyze test coverage, test files, and testing patterns.

**Parameters**:
```json
{
  "test_type": "string (optional: unit|integration|e2e)",
  "include_coverage": "boolean (optional, default: true)",
  "framework_info": "boolean (optional, default: true)"
}
```

**Response**:
```json
{
  "test_files": [
    {
      "path": "tests/test_auth.py",
      "framework": "pytest",
      "test_count": 15,
      "coverage_percentage": 92.5
    }
  ],
  "summary": {
    "total_tests": 245,
    "passing": 240,
    "failing": 3,
    "skipped": 2,
    "overall_coverage": 87.3
  },
  "frameworks": ["pytest", "jest"],
  "coverage_report": {
    "lines_covered": 8945,
    "lines_total": 10250,
    "branches_covered": 1245,
    "branches_total": 1580
  }
}
```

---

## 📚 Documentation Tools

### 12. get_documentation
**Description**: Extract and analyze documentation files, comments, and docstrings.

**Parameters**:
```json
{
  "doc_types": "array<string> (optional: readme|api|inline|comments)",
  "include_generated": "boolean (optional, default: false)",
  "quality_analysis": "boolean (optional, default: true)"
}
```

---

## ⚙️ Configuration Tools

### 13. get_config
**Description**: Analyze configuration files, environment variables, and settings.

**Parameters**:
```json
{
  "config_types": "array<string> (optional)",
  "include_secrets": "boolean (optional, default: false)",
  "validate_syntax": "boolean (optional, default: true)"
}
```

---

## 📝 Maintenance Tools

### 14. get_todos
**Description**: Find TODO comments, FIXME notes, and technical debt markers.

**Parameters**:
```json
{
  "todo_types": "array<string> (optional: TODO|FIXME|HACK|NOTE)",
  "include_context": "boolean (optional, default: true)",
  "priority_analysis": "boolean (optional, default: true)"
}
```

### 15. get_recent_changes
**Description**: Analyze recent code changes, commits, and modification patterns.

**Parameters**:
```json
{
  "time_range": "string (optional, default: 7d)",
  "include_authors": "boolean (optional, default: true)",
  "change_analysis": "boolean (optional, default: true)"
}
```

---

## 🔒 Security Tools

### 16. get_security_issues
**Description**: Identify potential security vulnerabilities and issues.

**Parameters**:
```json
{
  "severity_filter": "string (optional: low|medium|high|critical)",
  "include_suggestions": "boolean (optional, default: true)",
  "scan_dependencies": "boolean (optional, default: true)"
}
```

---

## 📊 Quality Tools

### 17. get_quality_metrics
**Description**: Calculate code quality metrics and maintainability scores.

**Parameters**:
```json
{
  "metrics": "array<string> (optional)",
  "include_trends": "boolean (optional, default: false)",
  "benchmark_comparison": "boolean (optional, default: true)"
}
```

### 18. get_complexity
**Description**: Analyze code complexity using various metrics.

**Parameters**:
```json
{
  "complexity_types": "array<string> (optional: cyclomatic|cognitive|halstead)",
  "threshold": "number (optional, default: 10)",
  "include_suggestions": "boolean (optional, default: true)"
}
```

---

## 🔍 Analysis Tools

### 19. get_imports
**Description**: Analyze import statements and module dependencies.

**Parameters**:
```json
{
  "include_unused": "boolean (optional, default: false)",
  "circular_detection": "boolean (optional, default: true)",
  "optimization_suggestions": "boolean (optional, default: true)"
}
```

### 20. find_agents
**Description**: Identify AI agents, automation scripts, and intelligent components.

**Parameters**:
```json
{
  "agent_types": "array<string> (optional)",
  "include_config": "boolean (optional, default: true)",
  "capability_analysis": "boolean (optional, default: false)"
}
```

### 21. validate_intelligence
**Description**: Validate project intelligence data integrity and completeness.

**Parameters**:
```json
{
  "validation_level": "string (optional: basic|comprehensive, default: basic)",
  "auto_fix": "boolean (optional, default: false)",
  "generate_report": "boolean (optional, default: true)"
}
```

---

## Error Handling

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Verify API key |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Verify file/resource exists |
| 429 | Rate Limited | Reduce request frequency |
| 500 | Server Error | Contact support |

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The 'file_path' parameter is required",
    "details": {
      "parameter": "file_path",
      "expected_type": "string"
    },
    "request_id": "req_123456789",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

---

## Rate Limits

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Free | 100 | 10 |
| Pro | 1000 | 50 |
| Enterprise | 10000 | 200 |

## SDK Examples

### Python
```python
import requests

api_key = "your-api-key"
base_url = "https://api.example.com"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Get file information
response = requests.post(
    f"{base_url}/tools/get_file_info",
    headers=headers,
    json={"file_path": "src/main.py"}
)

file_info = response.json()
print(file_info)
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://api.example.com',
  headers: {
    'Authorization': `Bearer ${process.env.API_KEY}`,
    'Content-Type': 'application/json'
  }
});

// Search for files
async function findFiles(pattern) {
  try {
    const response = await client.post('/tools/find_files', {
      pattern: pattern,
      max_results: 50
    });
    return response.data;
  } catch (error) {
    console.error('Error finding files:', error.response.data);
  }
}

findFiles('*.tsx').then(console.log);
```

### curl
```bash
# Get project summary
curl -X POST https://api.example.com/tools/get_project_summary \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"include_metrics": true, "include_dependencies": true}'
```

---

## Webhooks

### Event Types
- `file.changed`: File modification detected
- `project.analyzed`: Project analysis completed
- `security.issue_found`: Security vulnerability detected
- `quality.threshold_exceeded`: Quality metrics threshold exceeded

### Webhook Payload
```json
{
  "event": "file.changed",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "file_path": "src/components/Button.tsx",
    "change_type": "modified",
    "affected_tools": ["get_file_info", "get_complexity"]
  },
  "webhook_id": "wh_123456789"
}
```

---

## Status & Health

### Health Check Endpoint
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": "2h 15m 30s",
  "services": {
    "database": "connected",
    "redis": "connected",
    "file_system": "accessible"
  },
  "metrics": {
    "requests_per_minute": 45,
    "average_response_time": "120ms",
    "cache_hit_rate": 85.2
  }
}
```

### Status Page
Visit `https://status.your-domain.com` for real-time status updates and historical performance data.

---

## Support

- **Documentation**: https://docs.your-domain.com
- **GitHub**: https://github.com/your-org/project-context
- **Discord**: https://discord.gg/your-server
- **Email**: support@your-domain.com

## Changelog

### v0.1.0 (2025-01-15)
- Initial release with all 21 tools
- MCP protocol implementation
- Redis caching support
- Production-ready deployment
