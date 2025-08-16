# OPSVI MCP Server API Reference

## Table of Contents
1. [Claude Code Server](#claude-code-server)
2. [OpenAI Codex Server](#openai-codex-server)
3. [Cursor Agent Server](#cursor-agent-server)
4. [Context Bridge Server](#context-bridge-server)
5. [Database Integration Server](#database-integration-server)
6. [Monitoring & Observability Server](#monitoring--observability-server)
7. [Testing & QA Server](#testing--qa-server)
8. [Security Analysis Server](#security-analysis-server)

---

## Claude Code Server

### Overview
Recursive agent execution for complex multi-step tasks with parallel processing capabilities.

### MCP Tools

#### `claude_run`
**Description**: Execute a task synchronously
**Parameters**:
- `task` (string, required): Task description
- `cwd` (string, optional): Working directory
- `outputFormat` (string, optional): Output format (json/text)
- `permissionMode` (string, optional): Permission mode
- `verbose` (boolean, optional): Enable verbose output

**Returns**: Task execution result

#### `claude_run_async`
**Description**: Execute a task asynchronously
**Parameters**:
- `task` (string, required): Task description
- `cwd` (string, optional): Working directory
- `outputFormat` (string, optional): Output format (json/text)
- `permissionMode` (string, optional): Permission mode
- `parentJobId` (string, optional): Parent job for recursion tracking

**Returns**: 
```json
{
  "jobId": "uuid",
  "status": "started",
  "message": "Job started successfully"
}
```

#### `claude_status`
**Description**: Check job status
**Parameters**:
- `jobId` (string, required): Job identifier

**Returns**: Job status information

#### `claude_result`
**Description**: Get completed job result
**Parameters**:
- `jobId` (string, required): Job identifier

**Returns**: Job execution result

#### `claude_list_jobs`
**Description**: List all jobs
**Parameters**: None

**Returns**: Array of job information

#### `claude_kill_job`
**Description**: Terminate a running job
**Parameters**:
- `jobId` (string, required): Job identifier

**Returns**: Success status

#### `claude_dashboard`
**Description**: Get system performance metrics
**Parameters**: None

**Returns**: Dashboard metrics

#### `claude_recursion_stats`
**Description**: Get recursion statistics
**Parameters**: None

**Returns**: Recursion configuration and stats

---

## OpenAI Codex Server

### Overview
Code generation, completion, and analysis using OpenAI's GPT-4.

### MCP Tools

#### `codex_generate`
**Description**: Generate code from natural language
**Parameters**:
- `prompt` (string, required): Natural language description
- `language` (string, required): Programming language
- `context_files` (array, optional): Files for context
- `streaming` (boolean, optional): Enable streaming

**Returns**: Generated code

#### `codex_complete`
**Description**: Complete partial code
**Parameters**:
- `code` (string, required): Partial code to complete
- `language` (string, required): Programming language
- `context` (string, optional): Additional context

**Returns**: Completed code

#### `codex_explain`
**Description**: Explain code functionality
**Parameters**:
- `code` (string, required): Code to explain
- `language` (string, required): Programming language
- `detail_level` (string, optional): brief/detailed/comprehensive

**Returns**: Code explanation

#### `codex_refactor`
**Description**: Refactor and improve code
**Parameters**:
- `code` (string, required): Code to refactor
- `language` (string, required): Programming language
- `focus` (string, optional): Refactoring focus

**Returns**: Refactored code

#### `codex_debug`
**Description**: Debug and fix code issues
**Parameters**:
- `code` (string, required): Code with issues
- `error` (string, optional): Error message
- `language` (string, required): Programming language

**Returns**: Fixed code with explanations

#### `codex_test`
**Description**: Generate test cases
**Parameters**:
- `code` (string, required): Code to test
- `language` (string, required): Programming language
- `framework` (string, optional): Test framework

**Returns**: Generated tests

#### `codex_document`
**Description**: Generate documentation
**Parameters**:
- `code` (string, required): Code to document
- `language` (string, required): Programming language
- `format` (string, optional): docstring/markdown/jsdoc

**Returns**: Generated documentation

#### `codex_review`
**Description**: Review code quality
**Parameters**:
- `code` (string, required): Code to review
- `language` (string, required): Programming language
- `checklist` (array, optional): Review criteria

**Returns**: Code review with recommendations

#### `codex_translate`
**Description**: Translate between languages
**Parameters**:
- `code` (string, required): Source code
- `source_language` (string, required): Source language
- `target_language` (string, required): Target language

**Returns**: Translated code

---

## Cursor Agent Server

### Overview
Programmatic interaction with Cursor IDE agents for visualization, review, and documentation.

### MCP Tools

#### `invoke_cursor_agent`
**Description**: Invoke any Cursor agent
**Parameters**:
- `agent` (string, required): Agent name (e.g., @diagram)
- `prompt` (string, required): Agent prompt
- `context_files` (array, optional): Context files
- `timeout` (integer, optional): Timeout in seconds

**Returns**: Agent response

#### `create_diagram`
**Description**: Create diagrams
**Parameters**:
- `data` (object, required): Diagram data
- `diagram_type` (string, required): flowchart/sequence/class/etc.
- `theme` (string, optional): Diagram theme
- `format` (string, optional): mermaid/plantuml

**Returns**: Diagram code/image

#### `review_code`
**Description**: Review code using @code_review
**Parameters**:
- `code` (string, required): Code to review
- `language` (string, required): Programming language
- `focus_areas` (array, optional): Review focus

**Returns**: Code review results

#### `generate_documentation`
**Description**: Generate docs using @documentation
**Parameters**:
- `code` (string, required): Code to document
- `format` (string, optional): Documentation format
- `include_examples` (boolean, optional): Include examples

**Returns**: Generated documentation

#### `invoke_custom_agent`
**Description**: Invoke custom agents
**Parameters**:
- `agent_name` (string, required): Custom agent name
- `prompt` (string, required): Agent prompt
- `parameters` (object, optional): Agent parameters

**Returns**: Custom agent response

#### `list_available_agents`
**Description**: List all available agents
**Parameters**: None

**Returns**: Array of available agents

---

## Context Bridge Server

### Overview
Bridge context between different MCP servers and tools with Redis pub/sub support.

### MCP Tools

#### `store_context`
**Description**: Store context data
**Parameters**:
- `key` (string, required): Context key
- `value` (object, required): Context value
- `ttl` (integer, optional): Time to live in seconds
- `tags` (array, optional): Context tags

**Returns**: Storage confirmation

#### `retrieve_context`
**Description**: Retrieve context data
**Parameters**:
- `key` (string, required): Context key

**Returns**: Context value

#### `update_context`
**Description**: Update existing context
**Parameters**:
- `key` (string, required): Context key
- `updates` (object, required): Updates to apply
- `merge` (boolean, optional): Merge or replace

**Returns**: Updated context

#### `delete_context`
**Description**: Delete context data
**Parameters**:
- `key` (string, required): Context key

**Returns**: Deletion confirmation

#### `list_contexts`
**Description**: List all contexts
**Parameters**:
- `tags` (array, optional): Filter by tags
- `pattern` (string, optional): Key pattern

**Returns**: Array of context keys

#### `aggregate_knowledge`
**Description**: Aggregate knowledge from sources
**Parameters**:
- `sources` (array, required): Knowledge sources
- `strategy` (string, optional): Aggregation strategy

**Returns**: Aggregated knowledge

#### `share_with_agent`
**Description**: Share context with agent
**Parameters**:
- `agent_id` (string, required): Target agent
- `context_key` (string, required): Context to share
- `permissions` (object, optional): Access permissions

**Returns**: Sharing confirmation

#### `subscribe_to_events`
**Description**: Subscribe to context events
**Parameters**:
- `event_types` (array, required): Event types
- `filter` (object, optional): Event filter

**Returns**: Subscription ID

---

## Database Integration Server

### Overview
Database operations with support for PostgreSQL and MySQL.

### MCP Tools

#### `db_connect`
**Description**: Connect to database
**Parameters**:
- `database_type` (string, required): postgres/mysql
- `connection_string` (string, required): Connection URL
- `pool_size` (integer, optional): Connection pool size

**Returns**: Connection ID

#### `db_query`
**Description**: Execute SQL query
**Parameters**:
- `connection_id` (string, required): Connection ID
- `query` (string, required): SQL query
- `parameters` (array, optional): Query parameters

**Returns**: Query results

#### `db_execute`
**Description**: Execute SQL command
**Parameters**:
- `connection_id` (string, required): Connection ID
- `command` (string, required): SQL command
- `parameters` (array, optional): Command parameters

**Returns**: Execution result

#### `db_transaction`
**Description**: Execute transaction
**Parameters**:
- `connection_id` (string, required): Connection ID
- `operations` (array, required): Transaction operations

**Returns**: Transaction result

#### `db_migrate`
**Description**: Run database migrations
**Parameters**:
- `connection_id` (string, required): Connection ID
- `migration_dir` (string, required): Migration directory
- `direction` (string, optional): up/down

**Returns**: Migration result

#### `db_schema`
**Description**: Get database schema
**Parameters**:
- `connection_id` (string, required): Connection ID
- `table` (string, optional): Specific table

**Returns**: Schema information

#### `db_disconnect`
**Description**: Close database connection
**Parameters**:
- `connection_id` (string, required): Connection ID

**Returns**: Disconnection confirmation

---

## Monitoring & Observability Server

### Overview
System monitoring with Prometheus metrics and OpenTelemetry tracing.

### MCP Tools

#### `metrics_collect`
**Description**: Collect metrics
**Parameters**:
- `metric_name` (string, required): Metric name
- `value` (number, required): Metric value
- `labels` (object, optional): Metric labels
- `timestamp` (integer, optional): Unix timestamp

**Returns**: Collection confirmation

#### `metrics_query`
**Description**: Query metrics
**Parameters**:
- `query` (string, required): PromQL query
- `time_range` (object, optional): Time range

**Returns**: Query results

#### `trace_start`
**Description**: Start trace span
**Parameters**:
- `operation` (string, required): Operation name
- `attributes` (object, optional): Span attributes

**Returns**: Span ID

#### `trace_end`
**Description**: End trace span
**Parameters**:
- `span_id` (string, required): Span ID
- `status` (string, optional): Span status

**Returns**: Trace confirmation

#### `alert_create`
**Description**: Create alert rule
**Parameters**:
- `name` (string, required): Alert name
- `condition` (string, required): Alert condition
- `actions` (array, required): Alert actions

**Returns**: Alert ID

#### `dashboard_create`
**Description**: Create monitoring dashboard
**Parameters**:
- `name` (string, required): Dashboard name
- `panels` (array, required): Dashboard panels

**Returns**: Dashboard URL

#### `logs_aggregate`
**Description**: Aggregate logs
**Parameters**:
- `source` (string, required): Log source
- `filters` (object, optional): Log filters
- `time_range` (object, optional): Time range

**Returns**: Aggregated logs

---

## Testing & QA Server

### Overview
Automated testing with coverage analysis and performance testing.

### MCP Tools

#### `test_generate`
**Description**: Generate tests
**Parameters**:
- `code` (string, required): Code to test
- `language` (string, required): Programming language
- `test_type` (string, required): unit/integration/e2e
- `framework` (string, optional): Test framework

**Returns**: Generated tests

#### `coverage_analyze`
**Description**: Analyze test coverage
**Parameters**:
- `project_path` (string, required): Project path
- `test_command` (string, required): Test command

**Returns**: Coverage report

#### `performance_test`
**Description**: Run performance tests
**Parameters**:
- `target_url` (string, required): Target URL
- `scenarios` (array, required): Test scenarios
- `duration` (integer, optional): Test duration

**Returns**: Performance metrics

#### `load_test`
**Description**: Run load tests
**Parameters**:
- `target_url` (string, required): Target URL
- `users` (integer, required): Number of users
- `ramp_up` (integer, optional): Ramp up time

**Returns**: Load test results

#### `mutation_test`
**Description**: Run mutation testing
**Parameters**:
- `project_path` (string, required): Project path
- `test_command` (string, required): Test command

**Returns**: Mutation score

#### `test_run`
**Description**: Execute test suite
**Parameters**:
- `project_path` (string, required): Project path
- `test_pattern` (string, optional): Test file pattern
- `parallel` (boolean, optional): Run in parallel

**Returns**: Test results

---

## Security Analysis Server

### Overview
Security analysis with vulnerability scanning and dependency auditing.

### MCP Tools

#### `security_scan`
**Description**: Scan for vulnerabilities
**Parameters**:
- `project_path` (string, required): Project path
- `scan_type` (string, required): sast/dependencies/secrets
- `severity_threshold` (string, optional): low/medium/high/critical

**Returns**: Security findings

#### `dependency_audit`
**Description**: Audit dependencies
**Parameters**:
- `project_path` (string, required): Project path
- `fix` (boolean, optional): Auto-fix vulnerabilities

**Returns**: Audit report

#### `secret_detect`
**Description**: Detect secrets in code
**Parameters**:
- `project_path` (string, required): Project path
- `include_history` (boolean, optional): Scan git history

**Returns**: Detected secrets

#### `license_check`
**Description**: Check license compliance
**Parameters**:
- `project_path` (string, required): Project path
- `allowed_licenses` (array, optional): Allowed licenses

**Returns**: License report

#### `best_practices_check`
**Description**: Check security best practices
**Parameters**:
- `project_path` (string, required): Project path
- `language` (string, required): Programming language

**Returns**: Best practices report

#### `vulnerability_fix`
**Description**: Fix known vulnerabilities
**Parameters**:
- `project_path` (string, required): Project path
- `vulnerability_id` (string, required): CVE ID

**Returns**: Fix result

---

## Common Response Formats

### Success Response
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {}
  }
}
```

### Async Job Response
```json
{
  "jobId": "uuid",
  "status": "pending|running|completed|failed",
  "progress": 50,
  "result": {},
  "error": null
}
```

## Rate Limits

- Default: 100 requests per minute
- Heavy operations: 10 requests per minute
- Async jobs: 50 concurrent jobs

## Authentication

All servers support authentication via:
- API tokens (environment variables)
- OAuth 2.0 (optional)
- mTLS (optional)

## WebSocket Support

Servers with real-time features support WebSocket connections:
- Context Bridge: Event subscriptions
- Monitoring: Live metrics
- Testing: Real-time test results

## Error Codes

| Code | Description |
|------|-------------|
| AUTH_001 | Authentication failed |
| CONN_001 | Connection error |
| EXEC_001 | Execution error |
| LIMIT_001 | Rate limit exceeded |
| VALID_001 | Validation error |
| PERM_001 | Permission denied |

## Version History

- v0.1.0: Initial release with core servers
- v0.2.0: Added Database and Monitoring servers
- v0.3.0: Added Testing and Security servers
- v0.4.0: Context Bridge enhancements

## Support

For issues and questions:
- GitHub: https://github.com/opsvi/opsvi-mcp
- Documentation: https://docs.opsvi.com/mcp