# /five-monitored - Five-Step Problem Solving with Monitoring

## Purpose
Combines the `/five` problem-solving approach with agent monitoring for complex tasks

## The Five Steps (with Monitoring)

### 1. UNDERSTAND (Discovery Phase)
```python
# Spawn monitored agent for requirements gathering
await spawn_monitored_agent(
    task="Analyze and document the problem",
    timeout=300,
    enable_monitoring=True
)
```

### 2. PLAN (Design Phase)
```python
# Spawn monitored agent for solution design
await spawn_monitored_agent(
    task="Design solution architecture",
    timeout=600,
    enable_monitoring=True
)
```

### 3. IMPLEMENT (Development Phase)
```python
# Spawn monitored agent for implementation
await spawn_monitored_agent(
    task="Implement the solution",
    timeout=900,
    enable_monitoring=True
)
```

### 4. TEST (Testing Phase)
```python
# Spawn monitored agent for testing
await spawn_monitored_agent(
    task="Create and run comprehensive tests",
    timeout=600,
    enable_monitoring=True
)
```

### 5. REFINE (Optimization Phase)
```python
# Spawn monitored agent for refinement
await spawn_monitored_agent(
    task="Optimize and refactor based on test results",
    timeout=600,
    enable_monitoring=True
)
```

## Integration Example

```bash
#!/bin/bash
# five-step-monitored.sh

PROBLEM="$1"

# Step 1: Understand
echo "📖 Step 1: Understanding the problem..."
python -c "
from opsvi_mcp.servers.claude_code_v3.enhanced_orchestrator import run_sdlc
import asyncio

asyncio.run(run_sdlc(
    project_name='five-step-solution',
    requirements='$PROBLEM',
    phases=['discovery']
))
"

# Check understanding
if [ -f ".sdlc-sessions/discovery/*/session_summary.json" ]; then
    echo "✅ Problem understood"
else
    echo "❌ Failed to understand problem"
    exit 1
fi

# Step 2: Plan
echo "📋 Step 2: Planning solution..."
python -m opsvi_mcp.servers.claude_code_v3.enhanced_orchestrator \
    "five-step-solution" \
    "Based on discovery, create detailed plan" \
    --phases planning

# Step 3: Implement
echo "🔨 Step 3: Implementing solution..."
./run_monitored_sdlc.sh "implementation" "$PROBLEM"

# Step 4: Test
echo "🧪 Step 4: Testing solution..."
./tdd-monitored.sh "solution_test"

# Step 5: Refine
echo "✨ Step 5: Refining solution..."
python -c "
from opsvi_mcp.servers.claude_code_v2.server_monitored import MonitoredClaudeCodeV2Server
import asyncio

async def refine():
    server = MonitoredClaudeCodeV2Server()
    
    # Analyze all previous sessions
    sessions = []
    for phase in ['discovery', 'planning', 'development', 'testing']:
        analysis = await server.analyze_session(f'{phase}_*')
        sessions.append(analysis)
    
    # Spawn refinement agent with context
    result = await server.spawn_monitored_agent(
        task='Refine solution based on: ' + str(sessions),
        timeout=600
    )
    
    return result

asyncio.run(refine())
"

echo "✅ Five-step process complete with full monitoring!"
```

## Monitoring Dashboard

After running, check:
- `/tmp/agent_monitoring/dashboard/status.json` - Live status
- `.sdlc-sessions/*/` - Phase-specific sessions
- `.test-sessions/` - Test execution logs

## Benefits of Monitored Five-Step

1. **Visibility**: See what each step is doing
2. **Validation**: Gates between steps ensure quality
3. **Recovery**: Failed steps can be debugged and retried
4. **Metrics**: Track time and resources per step
5. **Learning**: Analyze patterns across multiple five-step runs

## Quick Command

```bash
# Run five-step with monitoring for any problem
/five-monitored "Create a REST API for user management"
```

This will:
1. Understand requirements (with monitoring)
2. Plan architecture (with validation)
3. Implement code (with session capture)
4. Test thoroughly (with coverage tracking)
5. Refine based on metrics (with recommendations)