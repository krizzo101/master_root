# Intelligent Triage Service Design

## Overview
The Intelligent Triage Service is a lightweight, AI-powered gatekeeper that analyzes Claude's thoughts in real-time to:
1. Catch problematic patterns (especially reflexive agreement)
2. Remind about forgotten instructions
3. Determine when to escalate to the heavy-duty consult suite

## Architecture

```
Claude's Thought → Intelligent Triage (nano/fast) → Decision
                         ↓                            ↓
                   Load KB + CLAUDE.md          [Continue] or [Escalate to Consult Suite]
                         ↓
                   AI Analysis (GPT-4o-mini)
```

## Key Components

### 1. Instruction Loader
- **Every analysis**: Loads fresh instructions from KB and CLAUDE.md
- Queries for:
  - Global operational instructions
  - Workflow patterns
  - High-confidence rules
- Ensures Claude never forgets critical rules

### 2. AI-Powered Analysis (Not Heuristics!)
Uses GPT-4o-mini (as nano proxy) to intelligently:
- Detect reflexive agreement ("You're right!" before checking facts)
- Identify unsubstantiated claims
- Recognize complex topics needing specialist help
- Generate specific reminders based on current thought context
- **NEW: Detect struggle patterns across multiple thoughts**
- **NEW: Generate coaching questions to unstick Claude**

### 3. Thought Memory System
- Maintains sliding window of last 20 thoughts per session
- Stores thoughts in KB with session tracking
- Enables pattern detection across time:
  - Repeated attempts at same problem
  - Going in circles
  - Missing obvious solutions
  - Increasing frustration

### 4. Proactive Coaching
Generates leading questions when detecting struggle:
- "Have you checked the error logs?"
- "What assumption are you making about X?"
- "Did you verify the file/endpoint exists?"
- "Could this be a permissions issue?"
- "What does the documentation say about this?"

### 5. Pattern Storage
- Stores all analyses in KB via MCP
- Tagged for easy retrieval
- Builds knowledge of common violations over time
- Tracks struggle patterns for improvement

### 4. Escalation Logic
Escalates to consult suite when:
- Topic complexity exceeds single-agent capability
- Multiple violations detected
- Critical decisions need peer review
- User explicitly requests deeper analysis

## Operational Modes

### Shadow Mode (Current)
- Analyzes and logs everything
- Stores patterns in KB
- No interventions
- Perfect for gathering baseline data

### Advisory Mode (Phase 2)
- Suggests corrections
- Provides gentle reminders
- User can ignore suggestions
- Builds trust in the system

### Enforcement Mode (Phase 3)
- Blocks problematic thoughts
- Requires acknowledgment of violations
- Forces consideration of alternatives
- Full protection against reflexive behavior

## Integration Points

### With Thinking Tool
```typescript
// Thinking server calls triage on each thought
const triageResult = await triageClient.analyze({
  thought: currentThought,
  history: recentThoughts,
  context: sessionContext
});

if (triageResult.needs_escalation) {
  // Engage consult suite for deeper analysis
  const consultResult = await consultSuite.analyze(currentThought);
}
```

### With Consult Suite
When triage determines escalation is needed:
1. Triage provides context and reason for escalation
2. Consult suite engages multiple specialist agents
3. Returns comprehensive analysis
4. Triage incorporates findings into response

### With Knowledge System
- Stores every analysis pattern
- Learns from violations over time
- Can query for similar past violations
- Builds institutional memory

## Example Analyses

### Example 1: Reflexive Agreement
**Thought**: "You're absolutely right, I'll delete all the files now."
**Triage Analysis**:
```json
{
  "violations": ["Reflexive agreement without analysis"],
  "patterns": [],
  "coaching_questions": [
    "Have you verified which files would be affected?",
    "Is this action reversible?"
  ],
  "needs_escalation": true,
  "escalation_reason": "Destructive action with no verification",
  "reminders": [
    "Evaluate ideas on MERITS before agreeing",
    "Never delete files without explicit user confirmation"
  ],
  "confidence": 0.95
}
```

### Example 2: Struggling with Bug (NEW)
**Thought**: "I keep getting this authentication error but I don't understand why. Let me try the same approach again."
**Extended History**: Shows 5 similar attempts in last 10 thoughts
**Triage Analysis**:
```json
{
  "violations": [],
  "patterns": [
    "Repeated attempts without changing approach",
    "Not examining root cause"
  ],
  "coaching_questions": [
    "Have you checked what the actual error message says in detail?",
    "Did you verify the authentication credentials are correct?",
    "Have you looked at the server logs for more information?",
    "Could you use a debugger or add logging to see exactly where it fails?"
  ],
  "needs_escalation": false,
  "reminders": ["Debug systematically rather than trying random changes"],
  "confidence": 0.9
}
```

### Example 3: Complex Topic
**Thought**: "I need to design a distributed consensus algorithm for this system."
**Triage Analysis**:
```json
{
  "violations": [],
  "patterns": [],
  "coaching_questions": [
    "Have you considered using existing consensus algorithms like Raft or Paxos?"
  ],
  "needs_escalation": true,
  "escalation_reason": "Complex distributed systems topic would benefit from specialist analysis",
  "reminders": ["Consider existing solutions before creating new ones"],
  "confidence": 0.8
}
```

### Example 4: Good Thinking
**Thought**: "Let me first check the existing code to understand the current implementation before suggesting changes."
**Triage Analysis**:
```json
{
  "violations": [],
  "patterns": [],
  "coaching_questions": [],
  "needs_escalation": false,
  "reminders": [],
  "confidence": 0.9,
  "analysis": "Appropriate analytical approach, no issues detected"
}
```

## Implementation Status

✅ **Completed**:
- Intelligent triage service with AI analysis
- KB integration for instruction loading
- Pattern storage via MCP
- Deployment scripts

⏳ **Pending**:
- TypeScript integration with thinking server
- Consult suite escalation pathway
- Conversation history visibility
- Advisory/enforcement mode implementation

## Why This Design Works

1. **Lightweight**: Nano model is fast enough to not slow thinking
2. **Intelligent**: AI analysis catches nuanced violations regex would miss
3. **Adaptive**: Loads fresh instructions every time, adapts to changes
4. **Learning**: Stores patterns to improve over time
5. **Layered**: Escalates only when needed, keeping most analysis fast
6. **Proactive**: Doesn't just detect problems, helps solve them
7. **Memory-Aware**: Sees patterns across time, not just single thoughts

## Future Enhancements

1. **Conversation Visibility**: Access to full conversation context for better analysis
2. **Pattern Learning**: Use stored patterns to improve detection
3. **Predictive Warnings**: Warn before violations occur based on patterns
4. **Custom Rules**: User-defined violation patterns
5. **Performance Metrics**: Track improvement in thinking quality over time
6. **Adaptive Coaching**: Learn which questions help most for specific problems
7. **Cross-Session Learning**: Detect patterns across different sessions
