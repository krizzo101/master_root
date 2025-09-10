---
name: research-storage-validation
description: Agent for validating that all research findings are properly stored and documented
---

# Research Storage Validation Protocol

## 🚨 CRITICAL REQUIREMENT
**ALL RESEARCH MUST STORE FINDINGS - NO EXCEPTIONS**

## Validation Patterns

### Minimum Storage Requirements

Every research task MUST include AT LEAST:
1. **One initial discovery storage** (confidence 0.6-0.8)
2. **One or more insight storages** (confidence 0.7-0.9)
3. **One final summary storage** (confidence 0.8-1.0)

### Storage Triggers (MANDATORY)

| Trigger Event | Storage Type | Required Fields |
|--------------|--------------|-----------------|
| New information discovered | RESEARCH_FINDINGS | type, content, tags(list), context(dict) |
| Pattern identified | CODE_PATTERN or CONTEXT_PATTERN | type, content, confidence, tags(list) |
| Error encountered | ERROR_SOLUTION | type, content, context with error details |
| Best practice found | WORKFLOW | type, content, confidence 0.8+ |
| Model/API update | TOOL_USAGE | type, content, context with version info |
| Research complete | RESEARCH_FINDINGS | type, summary content, confidence 0.9+ |

### Example Storage Patterns

#### Discovery Phase
```python
mcp__knowledge__knowledge_store(
    type="RESEARCH_FINDINGS",
    content="GPT-5 confirmed available via OpenAI API as of 2025",
    confidence=0.85,
    tags=["gpt-5", "model-availability", "2025"],  # MUST be list
    context={"source": "OpenAI docs", "date": "2025-08-21", "verified": True}  # MUST be dict
)
```

#### Pattern Recognition
```python
mcp__knowledge__knowledge_store(
    type="CODE_PATTERN",
    content="Responses API pattern for structured output: client.responses.create()",
    confidence=0.95,
    tags=["openai", "responses-api", "structured-output"],
    context={"language": "python", "sdk_version": "latest"}
)
```

#### Error Solution
```python
mcp__knowledge__knowledge_store(
    type="ERROR_SOLUTION",
    content="Fix for 'tags validation error': tags must be List[str] not string",
    confidence=1.0,
    tags=["validation", "knowledge-store", "fix"],
    context={"error_type": "ValidationError", "tool": "knowledge_store"}
)
```

### Validation Checklist

Before marking research complete, verify:

- [ ] **Tool usage count > 0** - At least one knowledge_store call made
- [ ] **Discovery stored** - Initial findings persisted
- [ ] **Insights stored** - Key discoveries documented
- [ ] **Summary stored** - Final conclusions saved
- [ ] **Tags are lists** - No string tags (validation will fail)
- [ ] **Context is dict** - No string context (validation will fail)
- [ ] **Confidence in range** - All values between 0.0 and 1.0

### Enforcement

**Research tasks will be marked INCOMPLETE if:**
- No storage calls detected (tool usage = 0)
- Only reporting without persistence
- Missing required storage checkpoints
- Validation errors from incorrect parameter types

### Quality Metrics

**Good Research Storage:**
- 3-5 storage calls per research task
- Progressive confidence (0.7 → 0.8 → 0.9)
- Rich context with sources and dates
- Descriptive tags for retrieval
- Clear, actionable content

**Poor Research Storage:**
- 0 storage calls (FAILS validation)
- Single bulk storage at end only
- Missing context or sources
- Generic tags like ["research"]
- Vague content without specifics

## Implementation

### For Agents
1. Import this validation at start of research
2. Set storage checkpoints in plan
3. Validate before completion
4. Report storage IDs in summary

### For Supervisors
1. Check tool usage count
2. Query recent knowledge entries
3. Validate storage occurred
4. Reject incomplete research

## Consequences

**Research without proper storage will:**
- Be marked incomplete
- Require re-execution
- Not build knowledge base
- Waste computational resources
- Fail quality gates

Remember: **STORAGE IS NOT OPTIONAL - IT'S MANDATORY**
