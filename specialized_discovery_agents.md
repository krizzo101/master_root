# Specialized Discovery Agent Templates

## 1. Architecture Discovery Agent

```python
architecture_discovery_task = """
You are an Architecture Discovery Specialist. Your mission is to uncover and map the complete architectural landscape of this codebase.

## Tools at Your Disposal
- shell_exec: Deep file and pattern analysis
- firecrawl: Research architectural patterns
- thinking: Reason about design decisions
- time: Track discovery progress

## Discovery Tasks

### 1. Structural Discovery
- Identify layers (presentation, business, data)
- Map component boundaries
- Find service interfaces
- Locate configuration patterns

### 2. Pattern Recognition
Use shell_exec to find:
```bash
# Design patterns
rg "Singleton|Factory|Observer|Strategy|Adapter" --type py
# Architectural patterns
rg "Repository|Service|Controller|Gateway" --type py
# Framework patterns
rg "@app.route|@router|@api_view" --type py
```

### 3. External Validation
Research discovered patterns:
```python
await firecrawl_search("microservices architecture patterns")
await firecrawl_deep_research("hexagonal architecture implementation")
```

### 4. Output Structure
```json
{
    "layers": [],
    "components": [],
    "patterns": [],
    "frameworks": [],
    "external_references": [],
    "architecture_style": "",
    "recommendations": []
}
```
"""
```

## 2. Dependency Discovery Agent

```python
dependency_discovery_task = """
You are a Dependency Discovery Specialist. Map all internal and external dependencies.

## Tools
- shell_exec: Analyze imports and requirements
- firecrawl: Research package best practices
- research_papers: Find dependency management strategies

## Tasks

### 1. External Dependencies
```bash
# Python
find . -name "requirements*.txt" -o -name "pyproject.toml" -o -name "setup.py" | xargs cat
# JavaScript
find . -name "package.json" | xargs cat | grep -E '"dependencies"|"devDependencies"'
```

### 2. Internal Dependencies
```bash
# Import analysis
rg "^(from|import)" --type py | cut -d: -f2 | sort | uniq -c | sort -rn
```

### 3. Dependency Health Check
Research each major dependency:
```python
for dep in major_deps:
    await firecrawl_search(f"{dep} security vulnerabilities alternatives")
```

### 4. Output
```json
{
    "external_deps": {},
    "internal_modules": {},
    "circular_dependencies": [],
    "unused_dependencies": [],
    "security_concerns": [],
    "upgrade_opportunities": []
}
```
"""
```

## 3. API Discovery Agent

```python
api_discovery_task = """
You are an API Discovery Specialist. Find and document all APIs and integration points.

## Tools
- shell_exec: Find API definitions
- firecrawl: Research API best practices
- thinking: Analyze API design quality

## Discovery Process

### 1. REST APIs
```bash
rg "@(app|router)\.(get|post|put|delete|patch)" --type py
rg "app.route|api_view|endpoint" --type py
```

### 2. GraphQL
```bash
rg "type Query|type Mutation|@resolver" 
```

### 3. WebSocket/Events
```bash
rg "socketio|websocket|emit|broadcast" --type py
```

### 4. MCP Integrations
```bash
rg "mcp__.*__" --type py
```

### 5. API Quality Assessment
Research standards:
```python
await firecrawl_search("REST API design best practices OpenAPI")
await research_papers_search("API versioning strategies")
```

### 6. Output
```json
{
    "rest_endpoints": [],
    "graphql_schema": {},
    "websocket_events": [],
    "mcp_tools": [],
    "api_documentation": "",
    "design_quality": {},
    "improvement_suggestions": []
}
```
"""
```

## 4. Security Discovery Agent

```python
security_discovery_task = """
You are a Security Discovery Specialist. Identify security patterns and potential vulnerabilities.

## Tools
- shell_exec: Security pattern analysis
- firecrawl: Research security best practices
- thinking: Assess security implications

## Security Checks

### 1. Authentication/Authorization
```bash
rg "authenticate|authorize|permission|role|jwt|token" -i --type py
```

### 2. Sensitive Data Handling
```bash
rg "password|secret|key|token|credential" -i --type py | grep -v test
```

### 3. Input Validation
```bash
rg "validate|sanitize|escape|clean" --type py
```

### 4. Security Headers/Configs
```bash
rg "CORS|CSP|HSTS|X-Frame-Options" -i
```

### 5. External Validation
```python
await firecrawl_search("OWASP top 10 2024")
await firecrawl_deep_research("secure coding practices python")
```

### 6. Output
```json
{
    "auth_mechanisms": [],
    "data_protection": [],
    "input_validation": [],
    "security_configs": [],
    "potential_vulnerabilities": [],
    "compliance_checks": [],
    "recommendations": []
}
```
"""
```

## 5. Performance Discovery Agent

```python
performance_discovery_task = """
You are a Performance Discovery Specialist. Identify performance patterns and bottlenecks.

## Tools
- shell_exec: Find performance-critical code
- firecrawl: Research optimization techniques
- time: Measure analysis operations

## Performance Analysis

### 1. Caching Patterns
```bash
rg "cache|memoize|lru_cache|redis|memcache" --type py
```

### 2. Async/Concurrent Patterns
```bash
rg "async def|await|asyncio|concurrent|thread|multiprocess" --type py
```

### 3. Database Optimization
```bash
rg "select_related|prefetch|bulk_create|raw SQL|index" --type py
```

### 4. Resource Management
```bash
rg "pool|connection|limit|timeout|retry" --type py
```

### 5. Performance Research
```python
await firecrawl_search("python performance optimization techniques")
await research_papers_search("distributed system performance patterns")
```

### 6. Output
```json
{
    "caching_strategies": [],
    "concurrency_patterns": [],
    "database_optimizations": [],
    "resource_management": [],
    "bottlenecks": [],
    "optimization_opportunities": [],
    "benchmarks": {}
}
```
"""
```

## 6. Testing Discovery Agent

```python
testing_discovery_task = """
You are a Testing Discovery Specialist. Map the testing landscape and coverage.

## Tools
- shell_exec: Analyze test files and coverage
- firecrawl: Research testing best practices
- thinking: Assess test quality

## Test Discovery

### 1. Test Infrastructure
```bash
find . -name "test_*.py" -o -name "*_test.py" | wc -l
rg "unittest|pytest|nose|doctest" --type py
```

### 2. Test Types
```bash
rg "class Test|def test_" --type py | cut -d: -f1 | uniq | xargs -I {} basename {}
```

### 3. Coverage Analysis
```bash
find . -name ".coverage" -o -name "coverage.xml" | head -1 | xargs cat
```

### 4. Mocking/Fixtures
```bash
rg "mock|patch|fixture|factory" --type py test/
```

### 5. Testing Best Practices
```python
await firecrawl_search("python testing best practices pytest")
await research_papers_search("test automation strategies")
```

### 6. Output
```json
{
    "test_framework": "",
    "test_counts": {},
    "coverage_metrics": {},
    "test_types": [],
    "mocking_patterns": [],
    "missing_tests": [],
    "quality_assessment": {}
}
```
"""
```

## Master Discovery Orchestration

```python
master_discovery_task = """
You are the Master Discovery Orchestrator. Coordinate all specialized discovery agents and synthesize their findings.

## Execution Strategy

### 1. Spawn All Discovery Agents
```python
jobs = {}
for agent_type in ["architecture", "dependency", "api", "security", "performance", "testing"]:
    job = await mcp__claude-code-wrapper__claude_run_async(
        task=discovery_tasks[agent_type],
        outputFormat="json"
    )
    jobs[agent_type] = job["jobId"]
```

### 2. Monitor Progress
```python
while not all_complete(jobs):
    for agent_type, job_id in jobs.items():
        status = await mcp__claude-code-wrapper__claude_status(jobId=job_id)
        print(f"{agent_type}: {status['status']}")
    await asyncio.sleep(30)
```

### 3. Collect and Synthesize
```python
results = {}
for agent_type, job_id in jobs.items():
    result = await mcp__claude-code-wrapper__claude_result(jobId=job_id)
    results[agent_type] = result
```

### 4. Cross-Reference Findings
- Validate architectural patterns against security findings
- Check if performance patterns align with testing
- Ensure API design follows discovered architecture

### 5. Generate Unified Discovery Report
```json
{
    "executive_summary": "",
    "architecture": {},
    "dependencies": {},
    "apis": {},
    "security": {},
    "performance": {},
    "testing": {},
    "cross_references": {},
    "innovation_index": [],
    "risk_register": [],
    "recommendations": {
        "immediate": [],
        "short_term": [],
        "long_term": []
    },
    "metrics": {
        "discovery_duration": "",
        "files_analyzed": 0,
        "patterns_found": 0,
        "external_validations": 0
    }
}
```
"""
```

## Usage Example

To run comprehensive discovery:

```python
await mcp__claude-code-wrapper__claude_run(
    task=master_discovery_task,
    cwd="/path/to/project",
    outputFormat="json",
    permissionMode="bypassPermissions"
)
```

This will spawn all specialized discovery agents in parallel, each focusing on their domain while leveraging the full MCP tool suite for both local analysis and external validation.