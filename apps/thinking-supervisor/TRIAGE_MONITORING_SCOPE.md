# Triage Agent Monitoring Scope

## Key Constraint
**The triage agent ONLY runs when Claude uses the thinking tool**. It cannot monitor actions, tool usage, or system state directly - only thought content.

## How the Thinking Tool Works
- Called at the START of responses
- Thoughts are numbered sequentially (1, 2, 3...)
- Triage runs ON each thought as it happens
- Session resets between responses
- No "gaps" possible - it's sequential

## What Triage CAN Monitor (from thought content)

### 1. Thinking Quality Patterns
- **Reflexive agreement**: "You're absolutely right" → no analysis happening
- **Shallow thinking**: Jumping to action without understanding
- **Overthinking**: 10+ thoughts for a trivial task
- **Circular thinking**: Repeating same approach in thoughts 3, 5, 7...
- **Poor planning**: Thought 1 jumps straight to implementation

### 2. Engineering Indicators (mentioned in thoughts)
- **File changes accumulating**: "I've now modified X, Y, and Z files"
- **Errors repeating**: "Still getting that error" in multiple thoughts
- **Assumptions**: "I'll assume X works" without verification
- **Overconfidence**: "This will definitely work"

### 3. Instruction Adherence
- **Forgetting CLAUDE.md rules**: Not evaluating on merits
- **Being verbose**: Thoughts themselves are too long
- **Not being critical**: Always agreeing without questioning

### 4. Within-Session Patterns
- **Struggling**: Thoughts 3-7 all mention same problem
- **Scope creep**: Later thoughts expand beyond original task
- **Getting stuck**: Thoughts become increasingly frustrated

## What Triage CANNOT Monitor
❌ Actual tool usage (only knows if mentioned in thought)
❌ Real file system state
❌ Actual test results (unless mentioned)
❌ Git status (unless Claude thinks about it)
❌ External system responses
❌ User messages directly

## Coaching Strategy

### When detecting issues from thought content:
1. **Guide thinking quality** during the thinking process:
   - Shallow thinking → "Have you understood the problem fully?"
   - Overthinking → "Is this level of analysis needed for this task?"
   - Circular thinking → "You've considered this approach already in thought #3"

2. **Catch violations** as they happen:
   - Reflexive agreement → "You're agreeing without checking - violates CLAUDE.md"
   - Unverified assumptions → "What evidence supports this assumption?"
   - Overconfidence → "Have you tested this to be certain?"

3. **Provide coaching** for struggles:
   - Same error mentioned 3+ times → "What does the actual error message say?"
   - Stuck on approach → "What other approaches could work?"
   - Missing basics → "Have you checked if the file/endpoint exists?"

4. **Escalate to consult suite** when thoughts show:
   - Complex architectural decisions
   - Repeated failures across many thoughts
   - Genuine uncertainty about approach

## Example Detections

### From thought: "I've changed the auth module, user service, and database schema"
**Triage detects**: 3+ files mentioned as modified
**Coaching**: "You've mentioned modifying 3+ files. Have you committed your changes?"

### From thought: "The error is still happening, let me try changing the timeout again"
**Triage detects**: Repeated attempts, same approach
**Coaching**: "You seem to be trying variations of the same fix. Have you examined what the actual error message says?"

### From thought: "This will definitely fix the issue"
**Triage detects**: Overconfidence without verification
**Coaching**: "You sound confident. Have you tested this solution to verify it works?"

## Integration Notes

The triage agent should:
1. Parse thought content for these indicators
2. Track patterns across multiple thoughts in session
3. Generate helpful coaching, not criticism
4. Focus on improving engineering practices through thought analysis
5. Remember it's a guide, not a enforcer (especially in shadow mode)
