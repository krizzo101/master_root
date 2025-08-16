# MCP Integration Points Documentation

## Overview
This document maps all integration points between the Auto MCP middleware, Context Management, and the V2/V3 orchestration systems.

## System Components

### 1. Auto MCP Middleware (Entry Layer)
**Location**: `/home/opsvi/master_root/.claude/auto_mcp_middleware.py`
**Purpose**: Intercepts prompts and routes to appropriate Claude servers

### 2. V2 MCP Manager (Orchestration Layer)  
**Location**: `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/claude_code_v2/mcp_manager.py`
**Purpose**: Manages MCP server requirements for spawned agents

### 3. Context Manager (Specialization Layer)
**Location**: `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/claude_code_v2/context_manager.py`
**Purpose**: Provides agent specialization and context inheritance

### 4. Context Bridge (Communication Layer)
**Location**: `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/context_bridge/`
**Purpose**: Shares IDE context across all agents

## Integration Flow

```
User Prompt
    ↓
[Auto MCP Middleware]
    ├── Analyzes prompt complexity
    ├── Selects server (V1/V2/V3)
    └── Returns routing decision
         ↓
[Selected Server (e.g., V2)]
    ├── Receives task
    ├── [MCP Manager] Analyzes MCP needs
    ├── [Context Manager] Determines role
    └── Spawns specialized agent
         ↓
[Spawned Agent]
    ├── Receives MCP config via env
    ├── Receives context via env
    ├── [Context Bridge] Can query IDE state
    └── Executes task
```

## Key Integration Points

### 1. Prompt Analysis (Duplicated)

**Auto MCP Middleware**:
```python
def analyze_prompt(self, prompt: str):
    score, triggers = self._calculate_complexity_score(prompt)
    instant_server = self._check_instant_triggers(prompt.lower())
    # Returns: (use_mcp, server_type, metadata)
```

**V2 MCP Manager**:
```python
class MCPRequirementAnalyzer:
    @staticmethod
    def analyze_task(task: str) -> Set[str]:
        # Analyzes same task again for MCP needs
```

**Integration Issue**: Task is analyzed twice with similar logic

### 2. Configuration Passing

**From Auto MCP to Server**:
```python
# Auto MCP returns
{
    "use_mcp": True,
    "server": "V2",
    "config": {...},
    "tools": {...}
}
```

**From V2 to Child**:
```python
# V2 passes via environment
env.update({
    "AGENT_MCP_CONFIG": mcp_config_path,
    "AGENT_MCP_SERVERS": json.dumps(required_servers),
    "AGENT_ROLE": agent_config.get("role"),
    "AGENT_SYSTEM_PROMPT": agent_config.get("system_prompt")
})
```

**Integration Point**: Environment variables bridge parent-child communication

### 3. Context Inheritance

**Context Manager Creates**:
```python
agent_config = prepare_specialized_agent(
    job_id=job_id,
    task=task,
    parent_id=parent_id,
    inherit_session=inherit_session
)
```

**Agent Receives**:
```python
SESSION_ID = os.environ.get("AGENT_SESSION_ID")
ROLE = os.environ.get("AGENT_ROLE")
SYSTEM_PROMPT = os.environ.get("AGENT_SYSTEM_PROMPT")
PARENT_CONTEXT = json.loads(os.environ.get("AGENT_PARENT_CONTEXT"))
```

**Integration Point**: Context flows through environment variables

### 4. Context Bridge Access

**Context Bridge Provides**:
```python
@mcp.tool()
async def get_ide_context(query: Optional[Dict] = None) -> Dict:
    # Returns current IDE state
```

**Agents Can Query**:
```python
# Any agent with context_bridge MCP can access
ide_context = await mcp__context_bridge__get_ide_context()
```

**Integration Point**: MCP tools provide cross-agent communication

## Data Flow Patterns

### Pattern 1: Sequential Routing
```
Auto MCP → Server Selection → Task Execution
```

### Pattern 2: Parallel Spawning (V2)
```
V2 Parent → Analyze Tasks → Spawn N Children
    ↓
Each Child → Independent Execution → Result File
    ↓
Parent → Collect Results
```

### Pattern 3: Context Accumulation
```
Parent Context → Child 1 → Updated Context
                    ↓
              Child 2 (inherits) → Further Updates
                    ↓
              Child 3 (inherits accumulated)
```

### Pattern 4: IDE Context Sharing
```
IDE → Context Bridge → Pub/Sub
         ↓
    All Agents Subscribe → Real-time Updates
```

## Configuration Files

### 1. Auto MCP Config
**Location**: `/home/opsvi/master_root/.claude/config.json`
```json
{
  "auto_mcp": {
    "enabled": true,
    "threshold": 2,
    "default_server": "V1"
  },
  "mcp_servers": {
    "claude_code_v1": {...},
    "claude_code_v2": {...},
    "claude_code_v3": {...}
  }
}
```

### 2. MCP Server Configs
**Generated**: `/tmp/mcp_config_{instance_id}.json`
```json
{
  "mcpServers": {
    "ide": {...},
    "git": {...}
  }
}
```

### 3. Context Registry
**Location**: `/tmp/claude_sessions/session_registry.json`
```json
{
  "session_id": {
    "job_id": "...",
    "parent_session": "...",
    "status": "active"
  }
}
```

## Environment Variables

### Passed Between Layers
```bash
# Core Authentication
CLAUDE_CODE_TOKEN="..."

# Job Identification
AGENT_JOB_ID="job-123"
AGENT_OUTPUT_DIR="/tmp/results"
AGENT_RESULT_FILE="/tmp/results/job-123.json"

# MCP Configuration
AGENT_MCP_CONFIG="/tmp/mcp_config_job-123.json"
AGENT_MCP_SERVERS='["ide", "git"]'

# Context Configuration
AGENT_SESSION_ID="uuid-here"
AGENT_ROLE="debugger"
AGENT_SYSTEM_PROMPT="You are a debugging expert..."
AGENT_RESUME_SESSION="--resume parent-session-id"
AGENT_PARENT_CONTEXT='{"previous_errors": [...]}'
```

## Communication Channels

### 1. Direct Function Calls
- Auto MCP → Server tools (via MCP)
- Parent → Child (via subprocess)

### 2. File-Based
- Result files in `/tmp/claude_results/`
- MCP configs in `/tmp/mcp_config_*.json`
- Context files in `/tmp/agent_context_*.json`

### 3. Pub/Sub (Context Bridge)
- Redis channels: `context:sync`, `context:file_changed`
- In-memory fallback when Redis unavailable

### 4. Environment Variables
- Primary method for parent-child communication
- All configuration passed via env

## Synchronization Points

### 1. MCP Server Initialization
```python
# Child waits for MCP servers
if not check_mcp_ready():
    raise RuntimeError("MCP initialization timeout")
```

### 2. Result Collection
```python
# Parent polls for completion
while job.status == "running":
    await asyncio.sleep(1)
```

### 3. Context Updates
```python
# Real-time via Context Bridge
await context_bridge.publish_event(event)
```

## Error Handling Integration

### Auto MCP Fallback
```python
if server == "V3" and v3_fails:
    fallback_chain = ["V2", "V1", "direct"]
```

### V2 Job Failure
```python
if job.status == "failed":
    job.error = str(exception)
    write_error_to_result_file()
```

### Context Bridge Fallback
```python
if redis_unavailable:
    use_in_memory_pubsub()
```

## Performance Considerations

### 1. Startup Time
- **Without MCP optimization**: ~5-7 seconds (all servers)
- **With selective loading**: ~1-3 seconds (only needed servers)
- **Context overhead**: ~100-200ms

### 2. Memory Usage
- Each spawned agent: ~50-100MB
- MCP server overhead: ~10-20MB per server
- Context cache: ~1-5MB

### 3. Communication Latency
- Environment variable passing: < 1ms
- File-based results: ~10-50ms
- Redis pub/sub: ~1-5ms
- In-memory pub/sub: < 1ms

## Best Practices

### 1. Minimize Analysis Redundancy
```python
# Cache routing decisions
routing = cache.get(task_hash) or analyze_task(task)
```

### 2. Efficient Context Passing
```python
# Only pass necessary context
context = filter_relevant_context(full_context, task_type)
```

### 3. Selective MCP Loading
```python
# Load only required MCP servers
if "debug" in task:
    load_mcp(["ide"])
else:
    load_mcp([])  # No MCP needed
```

### 4. Graceful Degradation
```python
try:
    use_optimal_path()
except:
    fallback_to_simple_path()
```

## Future Integration Opportunities

### 1. Unified Configuration
- Single source of truth for all routing rules
- Shared between Auto MCP and V2/V3

### 2. Direct Context Passing
- Use shared memory or IPC instead of environment variables
- Reduce serialization overhead

### 3. Event-Driven Architecture
- Replace polling with event notifications
- Use Context Bridge for all inter-agent communication

### 4. Intelligent Caching
- Cache routing decisions
- Cache MCP availability status
- Cache context transformations

## Testing Integration Points

### Unit Tests
```python
def test_auto_mcp_to_v2_flow():
    # Test complete flow
    routing = auto_mcp.analyze("Debug all files")
    assert routing["server"] == "V2"
    
    # V2 receives and processes
    result = v2.spawn_with_routing(routing)
    assert result["mcp_servers"] == ["ide"]
```

### Integration Tests
```python
async def test_context_inheritance():
    # Parent creates context
    parent_context = create_parent_context()
    
    # Child inherits
    child_config = inherit_context(parent_context)
    
    # Verify inheritance
    assert child_config["parent_context"] == parent_context
```

### End-to-End Tests
```python
async def test_complete_orchestration():
    # User prompt through entire system
    prompt = "Fix all bugs and create tests"
    
    # Auto MCP routes
    # V2 spawns agents
    # Context flows
    # Results collected
    
    result = await execute_prompt(prompt)
    assert result["status"] == "success"
```

## Monitoring Integration Health

### Key Metrics
1. **Routing Accuracy**: Correct server selection rate
2. **Context Propagation**: Successful inheritance rate
3. **MCP Availability**: Server ready time
4. **Integration Latency**: Time between components

### Health Checks
```python
async def check_integration_health():
    return {
        "auto_mcp": check_auto_mcp_responsive(),
        "v2_spawning": check_v2_can_spawn(),
        "context_manager": check_context_creation(),
        "context_bridge": check_bridge_connectivity(),
        "mcp_servers": check_mcp_availability()
    }
```

## Troubleshooting Guide

### Issue: Routing decisions not reaching V2
**Check**: Environment variable passing
**Fix**: Ensure proper JSON serialization

### Issue: Context not inherited by children
**Check**: Parent context file creation
**Fix**: Verify file permissions and paths

### Issue: MCP servers not available in children
**Check**: MCP config file generation
**Fix**: Ensure config path is passed correctly

### Issue: Context Bridge not updating
**Check**: Pub/sub backend status
**Fix**: Verify Redis connection or fallback to in-memory