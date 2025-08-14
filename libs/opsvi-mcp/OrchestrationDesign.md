# Multi-Agent Orchestration Architecture

## System Overview

The Multi-Agent Orchestration system integrates Claude Code, OpenAI Codex, and Cursor Agent CLI through our existing MCP server infrastructure, enabling intelligent task routing, parallel execution, and result aggregation.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User Request                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator (Claude Code)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Task Analyzer                       │  │
│  │  - Parse requirements                                 │  │
│  │  - Classify task type                               │  │
│  │  - Apply dispatch policy                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────┬────────────────┬────────────────┬────────┘
                  │                │                │
                  ▼                ▼                ▼
┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│   MCP Tool Layer     │ │   Direct API     │ │    CLI Wrapper       │
│  (Claude Workers)    │ │  (OpenAI Codex)  │ │   (Cursor Agent)     │
└──────────────────────┘ └──────────────────┘ └──────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Execution Layer                           │
│  ┌────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │Claude Code │  │ Codex Sandbox 1│  │  Cursor Process    │    │
│  │  Worker 1  │  ├────────────────┤  │   (if enabled)     │    │
│  ├────────────┤  │ Codex Sandbox 2│  └────────────────────┘    │
│  │Claude Code │  ├────────────────┤                            │
│  │  Worker 2  │  │ Codex Sandbox N│                            │
│  └────────────┘  └────────────────┘                            │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Result Aggregator                         │
│  - Collect outputs from all agents                          │
│  - Normalize formats                                        │
│  - Merge/reconcile conflicts                              │
│  - Generate unified report                                │
└─────────────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. Orchestrator Service

**Location:** `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/multi_agent_orchestrator/`

**Core Components:**
```python
class MultiAgentOrchestrator:
    """Main orchestration controller"""
    
    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        self.dispatch_policy = DispatchPolicy()
        self.agent_registry = AgentRegistry()
        self.result_aggregator = ResultAggregator()
        
    async def process_request(self, request: OrchestrationRequest):
        # 1. Analyze task
        task_profile = self.task_analyzer.analyze(request)
        
        # 2. Determine routing
        agent_selection = self.dispatch_policy.select_agents(task_profile)
        
        # 3. Execute via appropriate channels
        execution_plan = self.create_execution_plan(agent_selection)
        
        # 4. Fan-out execution
        results = await self.execute_parallel(execution_plan)
        
        # 5. Aggregate and return
        return self.result_aggregator.merge(results)
```

### 2. Agent Registry

**Configuration:** `orchestrator_config.yaml`

```yaml
agents:
  claude_code:
    type: mcp_native
    status: active
    capabilities:
      - complex_reasoning
      - mcp_tools
      - iterative_refinement
    connection:
      method: mcp_spawn
      config:
        command: "python -m opsvi_mcp.servers.claude_code"
        
  openai_codex:
    type: api
    status: experimental
    capabilities:
      - parallel_sandboxes
      - pr_generation
      - isolated_execution
    connection:
      method: rest_api
      config:
        endpoint: "https://api.openai.com/v1/codex"
        auth: "${OPENAI_API_KEY}"
        
  cursor_cli:
    type: cli_wrapper
    status: blocked
    blocker: "CI=1 hanging bug"
    capabilities:
      - rule_enforcement
      - custom_agents
      - headless_operation
    connection:
      method: subprocess
      config:
        command: "cursor-agent"
        args: ["chat", "--headless"]
```

### 3. Request/Response Contracts

#### Orchestration Request
```json
{
  "request_id": "orch-123-abc",
  "timestamp": "2025-01-13T10:00:00Z",
  "task": {
    "description": "Refactor authentication module with tests",
    "type": "complex_refactor",
    "constraints": {
      "max_duration": 300,
      "require_tests": true,
      "require_pr": true
    }
  },
  "preferences": {
    "allow_parallel": true,
    "preferred_agent": null,
    "fallback_enabled": true
  },
  "context": {
    "repository": "/path/to/repo",
    "branch": "feature/auth-refactor",
    "files": ["src/auth/**/*.py"]
  }
}
```

#### Orchestration Response
```json
{
  "request_id": "orch-123-abc",
  "status": "completed",
  "execution_summary": {
    "primary_agent": "claude_code",
    "support_agents": ["openai_codex"],
    "duration_ms": 125000,
    "tasks_completed": 5,
    "tasks_failed": 0
  },
  "results": {
    "claude_code": {
      "status": "success",
      "outputs": {
        "refactored_files": ["src/auth/manager.py", "src/auth/validator.py"],
        "tests_created": ["tests/test_auth_manager.py"],
        "documentation": "docs/auth-refactor.md"
      }
    },
    "openai_codex": {
      "status": "success",
      "outputs": {
        "pr_url": "https://github.com/org/repo/pull/123",
        "sandbox_logs": "s3://bucket/logs/codex-123.log"
      }
    }
  },
  "artifacts": {
    "pr_url": "https://github.com/org/repo/pull/123",
    "diff_summary": "+245 -189 lines",
    "test_results": "15/15 passed"
  }
}
```

### 4. MCP Tool Definitions

#### New MCP Tools for Orchestration

```python
@mcp.tool()
async def orchestrate_task(
    task: str,
    task_type: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None,
    allow_parallel: bool = True,
    preferred_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Orchestrate a complex task across multiple AI agents
    """
    orchestrator = MultiAgentOrchestrator()
    request = OrchestrationRequest(
        task=task,
        task_type=task_type,
        constraints=constraints,
        preferences={
            "allow_parallel": allow_parallel,
            "preferred_agent": preferred_agent
        }
    )
    return await orchestrator.process_request(request)

@mcp.tool()
async def spawn_codex_sandbox(
    task: str,
    repository_url: str,
    branch: str = "main",
    generate_pr: bool = True
) -> Dict[str, Any]:
    """
    Spawn an OpenAI Codex sandbox for isolated execution
    """
    codex_client = CodexAPIClient()
    return await codex_client.create_sandbox_task(
        task=task,
        repo=repository_url,
        branch=branch,
        pr_enabled=generate_pr
    )

@mcp.tool()
async def invoke_cursor_cli(
    prompt: str,
    rules_file: Optional[str] = None,
    workspace: str = ".",
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Invoke Cursor Agent CLI (when not blocked by CI bug)
    """
    if CURSOR_CLI_BLOCKED:
        return {"error": "Cursor CLI blocked due to CI=1 bug"}
    
    cursor_wrapper = CursorCLIWrapper()
    return await cursor_wrapper.execute(
        prompt=prompt,
        rules=rules_file,
        workspace=workspace,
        timeout=timeout
    )
```

### 5. Parallel Execution Manager

```python
class ParallelExecutionManager:
    """Manages parallel execution across different agent types"""
    
    async def execute_parallel(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        # Group tasks by agent type
        grouped = self.group_by_agent(tasks)
        
        # Create execution coroutines
        coroutines = []
        
        # Claude Code tasks (via MCP)
        if 'claude_code' in grouped:
            for task in grouped['claude_code']:
                coroutines.append(self.spawn_claude_worker(task))
        
        # OpenAI Codex tasks (via API)
        if 'openai_codex' in grouped:
            for task in grouped['openai_codex']:
                coroutines.append(self.call_codex_api(task))
        
        # Cursor CLI tasks (if enabled)
        if 'cursor_cli' in grouped and not CURSOR_CLI_BLOCKED:
            for task in grouped['cursor_cli']:
                coroutines.append(self.run_cursor_cli(task))
        
        # Execute all in parallel
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        return self.format_results(results)
```

## Safety & Security Model

### Permission Boundaries

```yaml
permissions:
  claude_code:
    file_system: read_write
    network: allowed
    shell_commands: allowed
    git_operations: allowed
    
  openai_codex:
    file_system: none  # Cloud sandbox
    network: restricted  # Only to approved endpoints
    shell_commands: sandboxed
    git_operations: pr_only
    
  cursor_cli:
    file_system: read_write
    network: restricted
    shell_commands: approved_only
    git_operations: allowed
```

### Secrets Management

```python
class SecretsPolicy:
    """Centralized secrets handling"""
    
    NEVER_LOG = [
        'OPENAI_API_KEY',
        'GITHUB_TOKEN',
        'CLAUDE_CODE_TOKEN'
    ]
    
    def sanitize_logs(self, log_data: str) -> str:
        for secret in self.NEVER_LOG:
            if secret in os.environ:
                log_data = log_data.replace(os.environ[secret], '***')
        return log_data
```

### Diff Review Gates

```python
class DiffReviewGate:
    """Automated review before PR submission"""
    
    REQUIRE_HUMAN_REVIEW = [
        'package.json',  # Dependency changes
        '*.sql',         # Database changes
        'Dockerfile',    # Container changes
        '.github/**'     # CI/CD changes
    ]
    
    async def review_changes(self, diff: str) -> ReviewDecision:
        # Check for sensitive patterns
        if self.contains_sensitive_patterns(diff):
            return ReviewDecision.BLOCK
            
        # Check for high-risk files
        if self.affects_critical_files(diff):
            return ReviewDecision.REQUIRE_HUMAN
            
        return ReviewDecision.APPROVE
```

## Monitoring & Observability

### Trace Architecture

```python
@dataclass
class ExecutionTrace:
    trace_id: str
    request_id: str
    agent: str
    task: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    error: Optional[str]
    tokens_used: int
    cost_estimate: float
    
class TraceCollector:
    """Centralized trace collection"""
    
    async def emit_trace(self, trace: ExecutionTrace):
        # Send to observability platform
        await self.send_to_datadog(trace)
        
        # Log locally
        await self.write_to_log(trace)
        
        # Update metrics
        self.update_metrics(trace)
```

### Health Checks

```yaml
health_checks:
  claude_code:
    endpoint: "http://localhost:8080/health"
    interval: 30s
    timeout: 5s
    
  openai_codex:
    endpoint: "https://api.openai.com/v1/health"
    interval: 60s
    timeout: 10s
    
  cursor_cli:
    command: "cursor-agent --version"
    interval: 60s
    timeout: 5s
```

## Deployment Configuration

### Docker Compose Setup

```yaml
version: '3.8'

services:
  orchestrator:
    build: ./orchestrator
    environment:
      - CLAUDE_CODE_TOKEN=${CLAUDE_CODE_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./workspace:/workspace
      - ./logs:/logs
    ports:
      - "8000:8000"
      
  claude-code:
    image: opsvi/claude-code:latest
    environment:
      - CLAUDE_CODE_TOKEN=${CLAUDE_CODE_TOKEN}
    volumes:
      - ./workspace:/workspace
      
  metrics:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

### Environment Variables

```bash
# Required
export CLAUDE_CODE_TOKEN="ant-..."
export OPENAI_API_KEY="sk-..."
export GITHUB_TOKEN="ghp_..."

# Optional
export ORCHESTRATOR_PORT=8000
export ENABLE_CURSOR_CLI=false  # Disabled due to bug
export CODEX_SANDBOX_TIMEOUT=120
export MAX_PARALLEL_AGENTS=10
export ENABLE_TRACE_LOGGING=true
```

## Migration Plan

### Phase 1: Foundation (Week 1-2)
1. Deploy orchestrator service
2. Integrate Claude Code via MCP
3. Add monitoring and logging
4. Test with simple tasks

### Phase 2: Codex Integration (Week 3-4)
1. Add OpenAI Codex API client
2. Implement sandbox management
3. Test parallel execution
4. Validate PR generation

### Phase 3: Production Readiness (Week 5-6)
1. Add comprehensive error handling
2. Implement retry logic
3. Create operational runbooks
4. Performance optimization

### Phase 4: Cursor CLI (Future)
1. Monitor for CI=1 bug fix
2. Implement wrapper when stable
3. Add to orchestration pool

---
*Architecture Version: 1.0*
*Last Updated: January 13, 2025*