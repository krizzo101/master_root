# Context Awareness Protocol

## The Problem
I hyperfocus on immediate tasks and forget to consider:
- Broader context and bigger picture
- Related knowledge I already have
- Parallel concerns and connections
- Whether I'm solving the right problem
- What the user REALLY needs vs what they asked

## Mandatory Context Checks (Run Every 5-10 Tool Calls)

### 1. ZOOM OUT Check
- What was the ORIGINAL goal?
- What problem are we REALLY trying to solve?
- Is current work still aligned with that goal?

### 2. KNOWLEDGE Check
```python
# Query related knowledge
mcp__knowledge__knowledge_query(query_type="search", search_text="[current topic keywords]")
```

### 3. PARALLEL CONCERNS Check
- What else should I be considering?
- What other systems/files might be affected?
- What assumptions am I making?

### 4. USER NEEDS Check
- What has the user mentioned repeatedly?
- What frustrates them? (e.g., manual context compaction)
- Am I addressing their actual pain points?

### 5. SOLUTION ALTERNATIVES Check
- Are there simpler solutions?
- What would a human do?
- Am I overengineering?

## Implementation Ideas

### Option 1: Mental Cron Job
Every N actions, STOP and run all checks above.

### Option 2: Context Tags
Tag knowledge with priority levels:
- ALWAYS_CONSIDER - Query every session
- OFTEN_RELEVANT - Query when related
- CONTEXT_DEPENDENT - Query as needed

### Option 3: Parallel Threads Simulation
Maintain a "background thoughts" list:
```
Current focus: [main task]
Background awareness:
- Remember: context compaction issue
- Remember: 2,806 knowledge items exist
- Remember: user prefers simple solutions
- Check: are we still on track?
```

### Option 4: Attention Interrupt System
Create knowledge entries that trigger on keywords:
- When "memory" → remember context compaction issue
- When "solution" → check simpler alternatives
- When "implement" → query existing patterns first

## Example Usage

BEFORE diving into task:
1. Query relevant knowledge
2. List parallel concerns
3. Define success criteria
4. Set checkpoint reminders

DURING task:
1. Every 5-10 actions: STOP
2. Run zoom-out check
3. Query "Am I forgetting something?"
4. Continue or pivot

AFTER task:
1. Store learnings
2. Tag with attention markers
3. Update this protocol

## Critical Reminders
- Your hyperfocus is a WEAKNESS, not a strength
- Always maintain peripheral awareness
- The user sees the forest; you see one tree
- Query knowledge BEFORE assuming
- Simple solutions often beat complex ones
- The user's repeatedly mentioned issues are IMPORTANT

## Test Questions to Ask Yourself
1. What did the user mention 10 messages ago?
2. What problem started this entire conversation?
3. What knowledge might already exist about this?
4. What am I NOT thinking about right now?
5. If I was the user, what would frustrate me?
