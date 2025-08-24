# Enhanced Thinking Tool - Complete System Design

## Overview
Transform the MCP thinking tool from passive thought logging to active intelligent supervision using a lightweight triage agent and the existing consult suite for enforcement.

## Architecture Components

### 1. Enhanced MCP Thinking Server
**Location**: `mcp-servers/thinking/` (or wherever the thinking MCP server lives)

```python
class EnhancedThinkingServer:
    """
    Backwards-compatible enhancement to existing thinking server
    """
    def __init__(self):
        self.triage_enabled = os.getenv("THINKING_TRIAGE_ENABLED", "true")
        self.triage_mode = os.getenv("THINKING_TRIAGE_MODE", "learning")
        # Modes: off, learning, advisory, enforcement

        self.triage_agent = TriageAgent() if self.triage_enabled else None
        self.original_handler = OriginalThinkingHandler()
```

### 2. Intelligent Triage Agent
**Purpose**: Lightweight, fast evaluation of every thought

```python
class TriageAgent:
    def __init__(self):
        self.model = "gpt-5-nano"  # Fastest available model
        self.max_latency_ms = 100  # Must respond within 100ms
        self.context_buffer = deque(maxlen=10)  # Recent thoughts
        self.learning_store = []  # Patterns for KB

    async def evaluate(self, thought: str) -> TriageDecision:
        # Fast, focused evaluation
        # Returns: risk_level, needs_escalation, reasoning
```

### 3. Consult Suite Integration
**Purpose**: Full team analysis when triage escalates

```python
class ConsultIntegration:
    def __init__(self):
        self.session_id = f"thinking_{uuid4()}"
        self.escalation_config = {
            "low_risk": None,  # No escalation
            "medium_risk": {
                "agents": ["critic"],
                "quality": "normal",
                "max_time": 3
            },
            "high_risk": {
                "agents": ["critic", "gatekeeper", "code_review"],
                "quality": "better",
                "max_time": 5
            },
            "critical": {
                "agents": ["all"],
                "quality": "best",
                "max_time": 10,
                "block_until_resolved": True
            }
        }
```

### 4. Knowledge Base Feedback Loop
**Purpose**: Learn from interventions to improve triage

```python
class FeedbackLoop:
    def __init__(self):
        self.kb_client = KnowledgeBaseClient()

    def record_intervention(self, thought, triage_decision, consult_result, outcome):
        # Store pattern for learning
        self.kb_client.store({
            "type": "THINKING_PATTERN",
            "thought": thought,
            "triage_decision": triage_decision,
            "intervention_needed": consult_result.had_issues,
            "outcome": outcome,  # Did intervention help?
            "timestamp": now()
        })

    def get_similar_patterns(self, thought):
        # Query KB for similar past patterns
        return self.kb_client.query(f"similar to: {thought}")
```

## Implementation Phases

### Phase 1: Learning Mode (Week 1)
**Goal**: Collect data without disrupting workflow

```python
# Configuration
THINKING_TRIAGE_MODE=learning
THINKING_TRIAGE_ENABLED=true

# Behavior
- Triage evaluates every thought
- Logs decisions but DOESN'T block
- Stores patterns in KB
- Generates daily reports

# Success Metrics
- Collected 1000+ thought patterns
- Identified top 10 intervention triggers
- Baseline escalation rate established
```

### Phase 2: Advisory Mode (Week 2)
**Goal**: Provide suggestions without enforcement

```python
# Configuration
THINKING_TRIAGE_MODE=advisory

# Behavior
- Triage evaluates and suggests
- Shows warnings but doesn't block
- User can ignore suggestions
- Track suggestion acceptance rate

# Success Metrics
- 70%+ suggestion acceptance rate
- Reduced error patterns by 30%
- User feedback positive
```

### Phase 3: Enforcement Mode (Week 3+)
**Goal**: Active intervention for quality

```python
# Configuration
THINKING_TRIAGE_MODE=enforcement

# Behavior
- Critical issues BLOCK progress
- High-risk triggers consult team
- Medium-risk gets warnings
- Low-risk proceeds normally

# Success Metrics
- 50% reduction in poor thinking patterns
- 90% of interventions valuable
- Improved code quality metrics
```

## Complete Implementation

### 1. Modified Thinking MCP Server

```python
# thinking_server_enhanced.py
import asyncio
from typing import Dict, Any
from triage_agent import TriageAgent
from consult_integration import ConsultIntegration
from feedback_loop import FeedbackLoop

class EnhancedThinkingServer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mode = config.get("mode", "learning")

        # Components
        self.triage = TriageAgent() if self.mode != "off" else None
        self.consult = ConsultIntegration()
        self.feedback = FeedbackLoop()

        # Stats
        self.stats = {
            "thoughts_processed": 0,
            "escalations": 0,
            "interventions": 0,
            "blocks": 0
        }

    async def handle_thinking_request(self, request: Dict) -> Dict:
        """Main entry point - backwards compatible"""

        thought = request.get("thought", "")

        # Original response (backwards compatible)
        response = {
            "thoughtNumber": request.get("thoughtNumber"),
            "totalThoughts": request.get("totalThoughts"),
            "nextThoughtNeeded": request.get("nextThoughtNeeded")
        }

        # Enhanced processing (if enabled)
        if self.triage and self.mode != "off":
            enhancement = await self._enhance_thinking(thought, request)
            response.update(enhancement)

        self.stats["thoughts_processed"] += 1
        return response

    async def _enhance_thinking(self, thought: str, context: Dict) -> Dict:
        """Add intelligent supervision"""

        # Step 1: Triage evaluation (fast)
        triage_result = await self.triage.evaluate(thought)

        enhancement = {
            "triage": {
                "risk_level": triage_result.risk_level,
                "confidence": triage_result.confidence
            }
        }

        # Step 2: Escalate if needed
        if triage_result.needs_escalation and self.mode in ["advisory", "enforcement"]:
            consult_result = await self._run_consult(
                thought,
                triage_result
            )

            enhancement["consultation"] = consult_result

            # Step 3: Apply enforcement
            if self.mode == "enforcement" and consult_result.get("critical_issues"):
                enhancement["blocked"] = True
                enhancement["must_address"] = consult_result["requirements"]
                self.stats["blocks"] += 1

        # Step 4: Learn from interaction
        if self.mode == "learning" or triage_result.needs_escalation:
            await self.feedback.record(thought, triage_result, enhancement)

        return enhancement

    async def _run_consult(self, thought: str, triage: Any) -> Dict:
        """Run consult suite for deep analysis"""

        self.stats["escalations"] += 1

        result = await self.consult.analyze(
            thought=thought,
            risk_level=triage.risk_level,
            concern=triage.reasoning
        )

        if result.get("issues"):
            self.stats["interventions"] += 1

        return result
```

### 2. Triage Agent Implementation

```python
# triage_agent.py
import asyncio
import json
from typing import Dict, Optional
import openai

class TriageAgent:
    """Lightweight intelligent triage for every thought"""

    TRIAGE_PROMPT = """You are a triage agent evaluating if a thought needs expert review.

Thought: {thought}
Recent context: {context}
Current task: {task}

Evaluate for:
1. Risk: Could this break something?
2. Uncertainty: Is the thinker unsure?
3. Quality: Is analysis missing?
4. Patterns: Repeating past mistakes?

Respond with JSON only:
{{
    "risk_level": "low|medium|high|critical",
    "needs_escalation": boolean,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "suggested_agents": []
}}

Be selective - most thoughts are fine."""

    def __init__(self):
        self.client = openai.AsyncOpenAI()
        self.model = "gpt-5-nano"
        self.timeout = 0.1  # 100ms max
        self.context_buffer = []

    async def evaluate(self, thought: str) -> TriageDecision:
        """Fast evaluation with timeout"""

        try:
            # Build context
            prompt = self.TRIAGE_PROMPT.format(
                thought=thought,
                context=self._get_context(),
                task=self._get_current_task()
            )

            # Fast LLM call with timeout
            response = await asyncio.wait_for(
                self._call_llm(prompt),
                timeout=self.timeout
            )

            return TriageDecision(**response)

        except asyncio.TimeoutError:
            # Timeout - default to no escalation
            return TriageDecision(
                risk_level="low",
                needs_escalation=False,
                confidence=0.5,
                reasoning="Triage timeout - proceeding"
            )
        except Exception as e:
            # Error - log but don't block
            return TriageDecision(
                risk_level="low",
                needs_escalation=False,
                confidence=0.0,
                reasoning=f"Triage error: {e}"
            )

    async def _call_llm(self, prompt: str) -> Dict:
        """Actual LLM call"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=150
        )

        return json.loads(response.choices[0].message.content)
```

### 3. Consult Integration

```python
# consult_integration.py
class ConsultIntegration:
    """Bridge to consult suite for deep analysis"""

    def __init__(self):
        self.session_id = f"thinking_{uuid4()}"

    async def analyze(self, thought: str, risk_level: str, concern: str) -> Dict:
        """Run appropriate consult configuration based on risk"""

        configs = {
            "low": None,
            "medium": {
                "agent_type": "consult",
                "prompt": f"Quick review: {thought}",
                "session_id": self.session_id,
                "quality": "normal",
                "critic_override": True,
                "max_time": 3
            },
            "high": {
                "agent_type": "consult",
                "prompt": f"Careful review needed: {thought}\nConcern: {concern}",
                "session_id": self.session_id,
                "quality": "better",
                "critic_override": True,
                "gatekeeper_override": True,
                "max_time": 5
            },
            "critical": {
                "agent_type": "consult",
                "prompt": f"CRITICAL: Block if issues found: {thought}\nRisk: {concern}",
                "session_id": self.session_id,
                "quality": "best",
                "critic_override": True,
                "gatekeeper_override": True,
                "force_research": True,
                "max_time": 10
            }
        }

        config = configs.get(risk_level)
        if not config:
            return {"status": "no_escalation_needed"}

        # Call actual consult suite
        result = await mcp__consult_suite_enhanced__consult_suite(**config)

        # Parse results
        return self._parse_consult_result(result)
```

## Deployment Strategy

### 1. Prerequisites
```bash
# Install dependencies
pip install openai asyncio pydantic

# Set environment variables
export THINKING_TRIAGE_ENABLED=true
export THINKING_TRIAGE_MODE=learning
export OPENAI_API_KEY=your_key
export NEO4J_URI=bolt://localhost:7687
```

### 2. Rollout Plan

**Week 1: Shadow Mode**
```python
# Run in parallel without affecting users
config = {
    "mode": "learning",
    "report_only": True,
    "kb_collection": True
}
```

**Week 2: Opt-in Beta**
```python
# Users can enable advisory mode
config = {
    "mode": "advisory",
    "opt_in_users": ["power_users"],
    "fallback_on_error": True
}
```

**Week 3: Gradual Rollout**
```python
# Progressive enforcement
config = {
    "mode": "enforcement",
    "rollout_percentage": 10,  # Start with 10% of users
    "severity_threshold": "high"  # Only enforce high/critical
}
```

**Week 4: Full Deployment**
```python
config = {
    "mode": "enforcement",
    "rollout_percentage": 100,
    "severity_threshold": "medium"
}
```

## Monitoring & Metrics

### Key Metrics to Track
```python
METRICS = {
    "latency": {
        "triage_p50": "< 50ms",
        "triage_p99": "< 100ms",
        "consult_p50": "< 3s",
        "consult_p99": "< 10s"
    },
    "effectiveness": {
        "false_positive_rate": "< 10%",
        "false_negative_rate": "< 5%",
        "intervention_value": "> 80%"
    },
    "usage": {
        "thoughts_per_session": "track",
        "escalation_rate": "5-15%",
        "block_rate": "< 2%"
    }
}
```

### Dashboard Queries
```sql
-- Escalation patterns
SELECT risk_level, COUNT(*) as count
FROM thinking_interventions
WHERE timestamp > NOW() - INTERVAL '1 day'
GROUP BY risk_level;

-- Intervention effectiveness
SELECT
    SUM(CASE WHEN helpful = true THEN 1 ELSE 0 END) / COUNT(*) as effectiveness
FROM thinking_feedback
WHERE timestamp > NOW() - INTERVAL '1 week';
```

## Configuration Options

```yaml
# thinking_enhanced.yaml
thinking_supervisor:
  enabled: true
  mode: enforcement  # off, learning, advisory, enforcement

  triage:
    model: gpt-5-nano
    max_latency_ms: 100
    confidence_threshold: 0.7

  escalation:
    medium_risk_threshold: 0.6
    high_risk_threshold: 0.8
    critical_risk_threshold: 0.95

  consult:
    session_prefix: thinking_
    default_quality: normal
    max_wait_time: 10

  learning:
    store_patterns: true
    pattern_batch_size: 100
    kb_update_frequency: hourly

  enforcement:
    block_critical: true
    warn_high_risk: true
    suggest_medium_risk: true
    allow_override: false
```

## Success Criteria

1. **Performance**: No noticeable latency increase
2. **Quality**: 50% reduction in thinking errors
3. **Adoption**: 90% user satisfaction
4. **Learning**: 1000+ patterns identified
5. **ROI**: Prevented issues > intervention cost

## Future Enhancements

1. **Personalization**: Adjust per-user based on expertise
2. **Domain-specific**: Different rules for different codebases
3. **Predictive**: Anticipate issues before they occur
4. **Collaborative**: Multiple users' patterns inform each other
