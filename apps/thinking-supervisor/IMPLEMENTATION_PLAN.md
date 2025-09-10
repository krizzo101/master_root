# Enhanced Thinking Tool - Implementation Plan

## Current State Analysis
- **Thinking MCP Server**: TypeScript implementation at `/mcp-servers-fork/src/sequentialthinking/`
- **Consult Suite**: Python at `/apps/ACCF/`
- **Knowledge Base**: Neo4j with MCP interface

## Implementation Phases

## Phase 0: Foundation (Day 1-2)
**Goal**: Set up infrastructure without touching existing code

### Tasks:
1. **Create Triage Service** (Day 1)
   ```bash
   mkdir -p /home/opsvi/master_root/apps/thinking-supervisor/triage-service
   ```
   - Standalone Python service
   - REST API for TypeScript MCP to call
   - No modifications to existing thinking server yet

2. **Set up Development Environment** (Day 1)
   ```python
   # Requirements
   openai>=1.0.0
   fastapi>=0.100.0
   asyncio
   neo4j>=5.0.0
   pydantic>=2.0.0
   ```

3. **Create Data Collection Pipeline** (Day 2)
   ```python
   # triage_collector.py
   class TriageCollector:
       async def collect(self, thought: str) -> None:
           # Just log to KB, no intervention
           await self.kb.store({
               "type": "THINKING_PATTERN",
               "thought": thought,
               "timestamp": now(),
               "session": session_id
           })
   ```

## Phase 1: Shadow Mode (Day 3-7)
**Goal**: Invisible data collection to prove concept

### Day 3: Minimal Integration
```typescript
// index.ts - Add optional webhook
if (process.env.TRIAGE_WEBHOOK_URL) {
    // Fire and forget - no blocking
    fetch(process.env.TRIAGE_WEBHOOK_URL, {
        method: 'POST',
        body: JSON.stringify({thought: data.thought}),
        headers: {'Content-Type': 'application/json'}
    }).catch(() => {}); // Ignore failures
}
```

### Day 4: Triage Agent V1
```python
# Simple risk detection without LLM first
class SimpleTriageAgent:
    def evaluate(self, thought: str) -> Dict:
        risk_indicators = {
            "delete": "high",
            "drop": "high",
            "production": "high",
            "not sure": "medium",
            "probably": "medium",
            "test": "low"
        }

        # Pattern matching as MVP
        detected_risk = "low"
        for indicator, risk in risk_indicators.items():
            if indicator in thought.lower():
                detected_risk = risk
                break

        return {"risk": detected_risk, "method": "pattern"}
```

### Day 5-6: Data Collection
- Run for 48 hours minimum
- Collect 500+ thoughts
- No user impact

### Day 7: Analysis & Validation
```sql
-- Analyze patterns
SELECT
    risk_level,
    COUNT(*) as count,
    AVG(thought_length) as avg_length
FROM thinking_patterns
GROUP BY risk_level;

-- Find intervention opportunities
SELECT thought, risk_level
FROM thinking_patterns
WHERE risk_level IN ('high', 'critical')
ORDER BY timestamp DESC
LIMIT 20;
```

**Success Gate**: Identify 10+ cases where intervention would have helped

## Phase 2: Intelligent Triage (Week 2)
**Goal**: Add LLM intelligence, still shadow mode

### Day 8-9: LLM Integration
```python
class IntelligentTriageAgent:
    def __init__(self):
        self.model = "gpt-4o-mini"  # Start with available model
        self.fallback = SimpleTriageAgent()

    async def evaluate(self, thought: str) -> Dict:
        try:
            # LLM evaluation with timeout
            result = await self._llm_evaluate(thought)
            return result
        except:
            # Fallback to patterns
            return self.fallback.evaluate(thought)
```

### Day 10: Comparison Testing
```python
# Run both agents in parallel
pattern_result = simple_agent.evaluate(thought)
llm_result = await intelligent_agent.evaluate(thought)

# Store comparison
await kb.store({
    "pattern_risk": pattern_result["risk"],
    "llm_risk": llm_result["risk"],
    "agreement": pattern_result["risk"] == llm_result["risk"]
})
```

### Day 11-12: Optimize Performance
- Measure latency: Target < 100ms P99
- Implement caching for similar thoughts
- Add circuit breaker for LLM failures

**Success Gate**: LLM identifies 30% more issues than patterns

## Phase 3: Advisory Mode (Week 3)
**Goal**: Show suggestions without blocking

### Day 13: UI Integration
```typescript
// Return suggestions in response
const response = {
    ...originalResponse,
    triageAdvisory: triageResult ? {
        risk: triageResult.risk,
        suggestion: triageResult.suggestion,
        confidence: triageResult.confidence
    } : undefined
};
```

### Day 14: Consult Integration
```python
# When high risk detected
if triage_result.risk in ["high", "critical"]:
    # Call consult suite
    consult_result = await consult_suite.analyze(
        prompt=f"Review: {thought}",
        agent_type="consult",
        quality="normal",
        max_time=3
    )

    return {
        "advisory": consult_result.get("feedback"),
        "severity": "warning"  # Not blocking yet
    }
```

### Day 15-16: User Feedback Collection
```python
# Track suggestion acceptance
class FeedbackTracker:
    def track_suggestion(self, suggestion_id: str, accepted: bool):
        self.kb.store({
            "type": "SUGGESTION_FEEDBACK",
            "suggestion_id": suggestion_id,
            "accepted": accepted,
            "timestamp": now()
        })
```

### Day 17: Measure Effectiveness
```sql
-- Acceptance rate
SELECT
    COUNT(CASE WHEN accepted THEN 1 END) / COUNT(*) as acceptance_rate
FROM suggestion_feedback
WHERE timestamp > NOW() - INTERVAL '3 days';
```

**Success Gate**: 60%+ suggestion acceptance rate

## Phase 4: Enforcement Mode (Week 4)
**Goal**: Active intervention for critical issues

### Day 18: Blocking Logic
```typescript
// Block progression for critical issues
if (triageResult?.severity === 'critical' && triageResult?.block) {
    return {
        ...response,
        blocked: true,
        mustResolve: triageResult.requirements,
        nextThoughtNeeded: true,  // Force revision
        thoughtGuidance: triageResult.guidance
    };
}
```

### Day 19: Progressive Enforcement
```python
# Start with only critical issues
enforcement_config = {
    "critical": {"action": "block", "from_day": 19},
    "high": {"action": "warn", "from_day": 21},
    "medium": {"action": "suggest", "from_day": 23}
}
```

### Day 20-21: Monitor & Adjust
- Track block rate (target < 2%)
- Monitor user frustration signals
- Adjust thresholds based on feedback

**Success Gate**: 80% of blocks prevent actual issues

## Phase 5: Production Deployment (Week 5)

### Day 22: Production Readiness
- [ ] Load testing complete
- [ ] Rollback plan documented
- [ ] Monitoring dashboards ready
- [ ] Error handling verified
- [ ] Documentation updated

### Day 23: Canary Deployment
```python
# 10% of users
if hash(user_id) % 10 == 0:
    enable_enhanced_thinking = True
```

### Day 24-25: Progressive Rollout
- 10% → 25% → 50% → 100%
- Monitor metrics between increases
- Rollback if issues detected

### Day 26: Full Deployment
```bash
# Enable for all users
export THINKING_TRIAGE_ENABLED=true
export THINKING_TRIAGE_MODE=enforcement
export THINKING_TRIAGE_SEVERITY=medium
```

## Risk Mitigation

### Potential Issues & Solutions:

1. **Performance Impact**
   - Risk: Adds latency to thinking
   - Mitigation: 100ms timeout, async processing, caching

2. **Over-blocking**
   - Risk: Frustrates users with false positives
   - Mitigation: Start with high threshold, track feedback

3. **LLM Failures**
   - Risk: Service unavailable
   - Mitigation: Pattern-based fallback, circuit breaker

4. **Cost**
   - Risk: High API costs
   - Mitigation: Use cheap models, cache responses

## Rollback Plan

```bash
# Immediate rollback
export THINKING_TRIAGE_ENABLED=false

# Or reduce severity
export THINKING_TRIAGE_MODE=advisory
export THINKING_TRIAGE_SEVERITY=critical
```

## Success Metrics

### Week 1 (Shadow)
- ✓ 500+ thoughts collected
- ✓ Zero user impact
- ✓ 10+ intervention opportunities identified

### Week 2 (Intelligent)
- ✓ LLM evaluation working
- ✓ <100ms P99 latency
- ✓ 30% better than patterns

### Week 3 (Advisory)
- ✓ Suggestions shown
- ✓ 60%+ acceptance rate
- ✓ Positive user feedback

### Week 4 (Enforcement)
- ✓ Critical issues blocked
- ✓ <2% block rate
- ✓ 80% blocks valuable

### Week 5 (Production)
- ✓ 100% rollout complete
- ✓ No performance degradation
- ✓ 50% reduction in thinking errors

## Next Steps

1. **Tomorrow**: Create triage service skeleton
2. **Day 2**: Add webhook to thinking server
3. **Day 3**: Start shadow data collection
4. **End of Week 1**: Review collected data and decide on continuation

## Command to Start:

```bash
# Create the triage service
cd /home/opsvi/master_root/apps/thinking-supervisor
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn openai neo4j
python triage_service.py
```

This plan provides a safe, incremental path from concept to production with clear checkpoints and rollback options at every stage.
