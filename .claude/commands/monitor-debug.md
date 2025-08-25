# /monitor-debug - Integrated Monitoring & Debugging

## Purpose
Combines monitoring system with debugging tools for failed agents

## Usage
```
/monitor-debug [job_id]
```

## Workflow

1. **Identify Failed Agents**
   - Check monitoring dashboard
   - List recent failures
   - Select agent to debug

2. **Capture Session Data**
   - Export session logs
   - Capture health metrics
   - Extract error patterns

3. **Run Root Cause Analysis**
   - Use `/sc-root_cause` for systematic debugging
   - Analyze timeout vs error failures
   - Check validation gate failures

4. **Generate Recommendations**
   - Timeout adjustments
   - Error handling improvements
   - Validation fixes

## Integration Points

### With Session Debugger
```python
from opsvi_mcp.servers.claude_code_v3.session_debugger import SessionDebugger

debugger = SessionDebugger()
debugger.debug_session(job_id)
```

### With Monitoring Dashboard
```bash
cat /tmp/agent_monitoring/dashboard/status.json | jq '.failed_agents'
```

### With Violation Analyzer
```bash
python sdlc-violation-analyzer.py --session-dir .sdlc-sessions/
```

## Example Debugging Session

```bash
# 1. Find failed agents
ls .sdlc-sessions/*/job_*/session_summary.json | xargs grep -l '"status": "failed"'

# 2. Debug specific failure
python -m opsvi_mcp.servers.claude_code_v3.session_debugger --debug job_abc123

# 3. Extract recommendations
cat .sdlc-sessions/discovery/job_abc123/session_summary.json | jq '.health.recommendations'

# 4. Apply fixes based on recommendations
```

## Automated Recovery

When a phase fails:
1. This command automatically triggers
2. Analyzes the failure
3. Suggests recovery actions
4. Can retry with adjusted parameters

## Output

Generates:
- Debug report at `.sdlc-sessions/debug_reports/`
- Recommendations file
- Recovery script if applicable