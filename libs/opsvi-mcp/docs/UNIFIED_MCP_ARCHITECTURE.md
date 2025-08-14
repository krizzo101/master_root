# Unified MCP Architecture Proposal

## Current State Analysis

### Dual Decision Systems
The current architecture has two separate MCP decision points that could be unified:

1. **Auto MCP Middleware** (Entry Point)
   - Analyzes user prompts
   - Selects Claude server (V1/V2/V3)
   - Maintains complexity scoring
   - Has instant triggers for server selection

2. **V2 MCP Manager** (Execution Layer)
   - Analyzes tasks for MCP requirements
   - Creates minimal MCP configs
   - Implements availability checking
   - Manages parent-to-child configuration passing

### Redundant Analysis
Both systems analyze similar patterns but at different layers:
```
User Prompt → Auto MCP (analyze) → V2 Server → MCP Manager (analyze again) → Spawn
```

## Proposed Unified Architecture

### Single Analysis Pipeline
```
User Prompt → Unified Analyzer → Routing Decision → Execution
                      ↓
            [Server + MCP + Context]
```

### Key Components

#### 1. Unified Task Analyzer
Combine prompt analysis with MCP requirement detection:

```python
class UnifiedTaskAnalyzer:
    def analyze(self, prompt: str) -> TaskRouting:
        return TaskRouting(
            server="V2",           # Which Claude server
            mcp_servers=["ide"],   # Which MCP servers needed
            context_role="debugger", # Agent specialization
            parallelizable=True,   # Can split into subtasks
            complexity_score=5     # Task complexity
        )
```

#### 2. Routing Decision Cache
Share analysis results across layers:

```python
class RoutingCache:
    def store_routing(self, task_hash: str, routing: TaskRouting):
        # Cache routing decision
        # Pass to child processes via context
        # Avoid re-analysis
```

#### 3. Context-Aware MCP Loading
Integrate with Context Bridge for dynamic MCP selection:

```python
class ContextAwareMCPLoader:
    async def determine_mcp_needs(self, task: str, ide_context: IDEContext):
        # Use IDE context to refine MCP selection
        if ide_context.has_errors:
            add_mcp_server("debugger")
        if ide_context.active_file.endswith(".py"):
            add_mcp_server("python_tools")
```

## Implementation Strategy

### Phase 1: Unified Analysis Layer
Create a shared analysis module used by both Auto MCP and V2/V3:

```python
# libs/opsvi-mcp/opsvi_mcp/analysis/unified_analyzer.py
class UnifiedAnalyzer:
    def __init__(self):
        self.keyword_patterns = self._load_patterns()
        self.mcp_requirements = self._load_mcp_rules()
    
    def analyze_task(self, text: str) -> CompleteRouting:
        # One analysis to rule them all
        server = self._determine_server(text)
        mcp_servers = self._determine_mcp_needs(text)
        context = self._determine_context(text)
        
        return CompleteRouting(
            server=server,
            mcp_servers=mcp_servers,
            context=context
        )
```

### Phase 2: Shared Configuration
Move configuration to a central location:

```yaml
# libs/opsvi-mcp/config/routing_rules.yaml
server_selection:
  v1_triggers: [debug, fix, error, why]
  v2_triggers: [all files, parallel, batch]
  v3_triggers: [production, robust, enterprise]

mcp_requirements:
  ide_needed: [debug, analyze, review]
  git_needed: [commit, merge, branch]
  web_needed: [fetch, scrape, api]
```

### Phase 3: Context Bridge Integration
Leverage Context Bridge for real-time routing adjustments:

```python
class DynamicRouter:
    async def route_with_context(self, task: str):
        # Get IDE context
        ide_context = await context_bridge.get_ide_context()
        
        # Adjust routing based on current state
        if ide_context.has_diagnostics_errors:
            # Force V1 for debugging
            return "V1"
        
        if len(ide_context.open_tabs) > 10:
            # Use V2 for parallel analysis
            return "V2"
```

## Benefits of Unification

### 1. Performance
- Single analysis pass (not duplicated)
- Shared caching across layers
- Faster routing decisions

### 2. Consistency
- One source of truth for routing rules
- Consistent pattern matching
- Unified configuration

### 3. Maintainability
- Centralized logic
- Easier to update rules
- Clear decision flow

### 4. Extensibility
- Easy to add new servers
- Simple to add MCP servers
- Plugin architecture possible

## Migration Path

### Step 1: Extract Common Logic
Move shared patterns to a common module:
```python
# opsvi_mcp/analysis/patterns.py
DEBUGGING_KEYWORDS = ['debug', 'fix', 'error', 'bug']
PARALLEL_KEYWORDS = ['all', 'every', 'batch', 'multiple']
```

### Step 2: Create Unified Analyzer
Build the unified analyzer using extracted logic:
```python
# opsvi_mcp/analysis/unified.py
from .patterns import *

class UnifiedAnalyzer:
    # Consolidated analysis logic
```

### Step 3: Update Auto MCP
Modify Auto MCP to use unified analyzer:
```python
# .claude/auto_mcp_middleware.py
from opsvi_mcp.analysis.unified import UnifiedAnalyzer

analyzer = UnifiedAnalyzer()
routing = analyzer.analyze_task(prompt)
```

### Step 4: Update V2/V3
Modify V2/V3 to use cached routing:
```python
# opsvi_mcp/servers/claude_code_v2/job_manager.py
# Use routing from parent instead of re-analyzing
routing = json.loads(os.environ.get("AGENT_ROUTING"))
```

## Configuration Examples

### Unified Configuration File
```json
{
  "routing_rules": {
    "instant_triggers": {
      "V1": ["debug", "fix", "error"],
      "V2": ["parallel", "all files"],
      "V3": ["production", "enterprise"]
    },
    "mcp_requirements": {
      "patterns": {
        "needs_ide": ["debug", "analyze", "review"],
        "needs_git": ["commit", "merge", "push"],
        "needs_web": ["fetch", "api", "scrape"]
      }
    },
    "context_roles": {
      "debugger": ["debug", "fix", "error"],
      "analyzer": ["analyze", "review", "audit"],
      "architect": ["design", "structure", "pattern"]
    }
  }
}
```

### Environment-Based Override
```bash
# Override routing for testing
export MCP_ROUTING_OVERRIDE='{"server":"V2","mcp":["ide","git"]}'
```

## Testing Strategy

### Unit Tests
```python
def test_unified_routing():
    analyzer = UnifiedAnalyzer()
    
    # Test V1 routing
    result = analyzer.analyze("Debug the login error")
    assert result.server == "V1"
    assert "ide" in result.mcp_servers
    
    # Test V2 routing
    result = analyzer.analyze("Analyze all Python files")
    assert result.server == "V2"
    assert result.parallelizable == True
```

### Integration Tests
```python
async def test_end_to_end_routing():
    # Test complete flow from prompt to execution
    prompt = "Fix all bugs in the codebase"
    
    # Auto MCP analyzes
    routing = auto_mcp.process_prompt(prompt)
    
    # V2 receives routing
    agent = await spawn_with_routing(routing)
    
    # Verify no re-analysis occurred
    assert agent.used_cached_routing == True
```

## Metrics and Monitoring

### Key Metrics to Track
1. **Analysis Time**: Should decrease with unified approach
2. **Cache Hit Rate**: Target > 80% for repeated patterns
3. **Routing Accuracy**: Measure correct server selection
4. **MCP Load Time**: Track improvement from selective loading

### Monitoring Dashboard
```python
class RoutingMetrics:
    def __init__(self):
        self.total_analyses = 0
        self.cache_hits = 0
        self.routing_decisions = Counter()
        self.mcp_combinations = Counter()
    
    def report(self):
        return {
            "cache_hit_rate": self.cache_hits / self.total_analyses,
            "most_common_route": self.routing_decisions.most_common(1),
            "avg_mcp_servers": np.mean([len(x) for x in self.mcp_combinations])
        }
```

## Future Enhancements

### 1. Machine Learning Integration
Train a model on routing decisions:
```python
class MLRouter:
    def __init__(self):
        self.model = load_model("routing_model.pkl")
    
    def predict_routing(self, prompt: str):
        features = extract_features(prompt)
        return self.model.predict(features)
```

### 2. Plugin Architecture
Allow custom routing rules:
```python
class RoutingPlugin:
    def should_handle(self, prompt: str) -> bool:
        # Custom logic
    
    def get_routing(self, prompt: str) -> TaskRouting:
        # Custom routing
```

### 3. A/B Testing Framework
Test routing strategies:
```python
class RoutingExperiment:
    def route_with_experiment(self, prompt: str):
        if in_experiment_group(user_id):
            return new_routing_strategy(prompt)
        else:
            return current_routing_strategy(prompt)
```

## Conclusion

The unified MCP architecture will:
1. **Eliminate redundant analysis** between layers
2. **Provide consistent routing** decisions
3. **Improve performance** through caching and optimization
4. **Enable smarter routing** with context awareness
5. **Simplify maintenance** with centralized configuration

This architecture maintains backward compatibility while providing a clear path forward for enhanced agent orchestration and MCP management.