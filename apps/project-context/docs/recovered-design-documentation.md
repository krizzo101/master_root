# Project Context MCP Server - Recovered Design Documentation

## Overview
This document reconstructs the design and requirements for the Project Context MCP server based on session history and analysis. The parallel agents generated extensive documentation that was never saved to disk, so this represents what can be recovered.

## Background and Purpose

### Problem Statement
- Agents and developers need to understand codebases quickly
- The `.proj-intel/` directory contains rich project intelligence data
- Current access requires knowledge of internal file formats and byte-offset reading
- No semantic interface exists for accessing this valuable data

### Solution
An MCP (Model Context Protocol) server that provides semantic access to project intelligence data while completely abstracting the implementation details of `.proj-intel/` directories.

## Core Design Principles

1. **Complete Abstraction**: Users should never need to know about `.proj-intel/` internals
2. **Semantic Interface**: Tools should represent domain concepts, not file operations
3. **Performance First**: Multi-level caching to minimize file I/O
4. **Async Throughout**: All operations use async/await patterns
5. **Framework-Based**: Built on FastMCP for standard MCP compliance

## Architecture

### Technology Stack
- **Framework**: FastMCP (>=0.5.0) - Python MCP server framework
- **Validation**: Pydantic (>=2.0.0) - Data validation and serialization
- **Caching**: DiskCache (>=5.6.0) - Persistent cache layer
- **Async I/O**: aiofiles (>=23.0.0) - Async file operations
- **Monitoring**: Watchdog (>=3.0.0) - File system monitoring
- **Metrics**: Prometheus-client (>=0.19.0) - Performance metrics
- **Logging**: structlog (>=24.0.0) - Structured logging
- **Serialization**: orjson (>=3.9.0) - Fast JSON handling

### Component Architecture

```
project-context/
├── server/
│   ├── main.py           # FastMCP server initialization
│   └── config.py         # Server configuration
├── core/
│   ├── reader.py         # ProjectIntelReader integration
│   ├── cache.py          # Multi-level cache manager
│   ├── models.py         # Pydantic data models
│   └── validator.py      # Data integrity checks
├── tools/
│   ├── __init__.py       # Tool registration
│   ├── discovery.py      # File/symbol discovery tools
│   ├── analysis.py       # Code analysis tools
│   ├── architecture.py   # Architecture tools
│   ├── quality.py        # Quality metrics tools
│   └── changes.py        # Change tracking tools
└── utils/
    ├── streaming.py      # JSONL streaming utilities
    └── indexing.py       # Index management

```

### Caching Strategy

#### Three-Level Cache Architecture
1. **L1 Memory Cache**: In-memory LRU cache for hot data (TTL: 60s)
2. **L2 Disk Cache**: DiskCache for persistent storage (TTL: 300s)
3. **L3 Intelligence Cache**: Cached indices from `.proj-intel/` (TTL: until change)

## The 21 Semantic Tools

Based on the analysis of `.proj-intel/` capabilities and development workflows, the server exposes these tools:

### 1. Discovery Tools
- **`get_project_summary`**: Overall project statistics and health metrics
  - File counts, LOC, language distribution
  - Top-level structure overview
  - Key metrics dashboard

- **`find_files`**: Search for files by pattern or criteria
  - Glob patterns, regex support
  - Filter by type, size, modification time
  - Returns file metadata without content

- **`get_file_info`**: Detailed information about specific files
  - Functions, classes, imports
  - Complexity metrics
  - Dependencies and dependents

- **`find_symbols`**: Search for functions, classes, variables
  - Name matching with fuzzy search
  - Filter by type (function, class, method, variable)
  - Returns location and signature

### 2. Architecture Tools
- **`get_dependencies`**: Project dependency graph
  - Internal import relationships
  - External package dependencies
  - Circular dependency detection

- **`find_agents`**: Discover agent architectures
  - Agent classes with base classes
  - Method signatures and docstrings
  - Agent interaction patterns

- **`get_entry_points`**: Find CLI and main entries
  - CLI commands (click, argparse)
  - Main functions and app entries
  - Module __main__ files

- **`get_api_endpoints`**: List API routes
  - FastAPI, Flask, Django endpoints
  - HTTP methods and paths
  - Request/response models

- **`get_data_models`**: Find data structures
  - Pydantic models
  - SQLAlchemy models
  - Dataclasses and TypedDicts

### 3. Quality and Testing Tools
- **`get_tests`**: Test file mapping
  - Test files and their targets
  - Test coverage estimation
  - Test type classification

- **`get_config`**: Configuration overview
  - Config files (.env, .yaml, .toml)
  - Environment variables used
  - Settings and parameters

- **`get_quality_metrics`**: Code quality statistics
  - Complexity scores
  - Lint issues summary
  - Code smell indicators

### 4. Change and History Tools
- **`get_recent_changes`**: Recent modifications
  - Changed files since last scan
  - Added/removed/modified classification
  - Change impact analysis

- **`search_code`**: Full-text code search
  - Content search across files
  - Context-aware matching
  - Ranked results

### 5. Analysis Tools
- **`get_call_graph`**: Function call relationships
  - Who calls what
  - Call frequency estimation
  - Call chain analysis

- **`get_imports`**: Import analysis
  - Import graph visualization data
  - Most/least imported modules
  - Import optimization suggestions

- **`get_complexity`**: Complexity metrics
  - Cyclomatic complexity
  - Cognitive complexity
  - Maintainability index

- **`get_documentation`**: Documentation coverage
  - Docstring presence/quality
  - README and docs analysis
  - Documentation gaps

### 6. Maintenance Tools
- **`get_todos`**: TODO/FIXME items
  - In-code TODO comments
  - FIXME and HACK markers
  - Technical debt tracking

- **`get_security_issues`**: Security concerns
  - Potential security patterns
  - Hardcoded secrets detection
  - Vulnerable patterns

- **`validate_intelligence`**: Data integrity check
  - Verify checksums
  - Check data freshness
  - Validate indices

## Data Models (Pydantic)

### Core Models
```python
class FileInfo(BaseModel):
    path: str
    size: int
    modified: datetime
    language: Optional[str]
    content_hash: str

class Symbol(BaseModel):
    name: str
    type: Literal["function", "class", "method", "variable"]
    file_path: str
    line_number: int
    signature: Optional[str]
    docstring: Optional[str]

class Dependency(BaseModel):
    source: str
    target: str
    import_type: Literal["internal", "external", "relative"]
    line_number: int

class Agent(BaseModel):
    name: str
    file_path: str
    base_classes: List[str]
    methods: List[str]
    docstring: Optional[str]

class QualityMetrics(BaseModel):
    file_path: str
    complexity: float
    maintainability: float
    test_coverage: Optional[float]
    issues: List[str]
```

## Implementation Details

### ProjectIntelReader Integration
The core reader (from `scripts/proj_intel_reader.py`) provides:
- Byte-offset reading from JSONL
- Reverse index lookups
- Symbol index access
- Streaming capabilities
- Block-optimized reads

### Error Handling
- All tools return structured errors
- Graceful degradation when data missing
- Validation of all inputs/outputs
- Comprehensive logging

### Performance Considerations
- Lazy loading of indices
- Streaming for large results
- Batch operations where possible
- Connection pooling for cache
- Async I/O throughout

## Usage Examples

### Basic Discovery
```python
# Find all Python files
files = await find_files(pattern="**/*.py")

# Get information about a specific file
info = await get_file_info(path="src/main.py")

# Search for a class
symbols = await find_symbols(name="UserModel", type="class")
```

### Architecture Analysis
```python
# Get dependency graph
deps = await get_dependencies()

# Find all agents
agents = await find_agents()

# Get API endpoints
endpoints = await get_api_endpoints()
```

### Quality Checking
```python
# Get quality metrics
metrics = await get_quality_metrics()

# Find TODOs
todos = await get_todos()

# Check for security issues
security = await get_security_issues()
```

## Value Proposition

### For Agents
- **Instant Context**: Understand codebase structure in seconds
- **Semantic Search**: Find what you need without implementation details
- **Change Awareness**: Know what changed since last interaction
- **Quality Insights**: Understand code health and risks

### For Developers
- **Code Navigation**: Jump to definitions and usages
- **Architecture Understanding**: See the big picture
- **Refactoring Support**: Understand impact before changes
- **Documentation Gap Analysis**: Know what needs documenting

### For Teams
- **Onboarding Acceleration**: New members understand faster
- **Code Review Enhancement**: Better context for reviews
- **Technical Debt Tracking**: Systematic debt identification
- **Quality Monitoring**: Track quality over time

## Configuration

### Server Configuration
```yaml
server:
  host: localhost
  port: 3000
  intel_dir: .proj-intel
  cache:
    enabled: true
    memory_ttl: 60
    disk_ttl: 300
    max_size: 100MB
  logging:
    level: INFO
    structured: true
  metrics:
    enabled: true
    port: 9090
```

### Tool Configuration
Each tool can be configured with:
- Result limits
- Timeout values
- Cache policies
- Filter defaults

## Testing Strategy

### Unit Tests
- Test each tool independently
- Mock ProjectIntelReader
- Validate all data models
- Test error conditions

### Integration Tests
- Test with real `.proj-intel/` data
- Validate caching behavior
- Test concurrent access
- Measure performance

### Load Tests
- Simulate multiple clients
- Test cache effectiveness
- Measure response times
- Identify bottlenecks

## Security Considerations

1. **Path Traversal Prevention**: Validate all file paths
2. **Resource Limits**: Prevent DoS through limits
3. **Input Validation**: Strict validation of all inputs
4. **Output Sanitization**: Clean sensitive data
5. **Access Control**: Optional authentication layer

## Future Enhancements

### Phase 2 Features
- WebSocket support for real-time updates
- GraphQL interface option
- Custom query language
- Machine learning insights
- IDE plugin support

### Phase 3 Features
- Multi-project support
- Distributed caching
- Historical analysis
- Trend detection
- Automated refactoring suggestions

## Migration Path

### From Direct File Access
1. Install project-context server
2. Update agent code to use MCP tools
3. Remove direct `.proj-intel/` access
4. Monitor performance
5. Optimize cache settings

### From Other Analysis Tools
1. Map existing queries to semantic tools
2. Migrate gradually, tool by tool
3. Validate results match
4. Deprecate old tools
5. Remove legacy code

## Conclusion

The Project Context MCP server transforms raw project intelligence into actionable insights through semantic tools. By abstracting implementation complexity and providing intuitive interfaces, it enables both agents and developers to understand and navigate codebases efficiently.

This design prioritizes:
- **Usability**: Semantic tools that match mental models
- **Performance**: Multi-level caching for speed
- **Reliability**: Comprehensive error handling
- **Extensibility**: Plugin architecture for future growth

The server acts as a "codebase GPS" - providing instant, accurate navigation and understanding of any project with `.proj-intel/` data.

---

*Note: This documentation was reconstructed from session history after the original parallel agent outputs were lost. Some details may be incomplete, but this represents the core design vision for the Project Context MCP server.*
