# Task Tool & Parallel Execution Guide

## ❌ WRONG (Sequential):
```python
# This runs sequentially, not in parallel
Task(description="Test module A", subagent_type="qa-testing-guru", prompt="...")
# Then later...
Task(description="Test module B", subagent_type="qa-testing-guru", prompt="...")
```

## ✅ CORRECT (Parallel):
```python
# Call multiple Tasks in ONE message for parallel execution
Task(description="Test module A", subagent_type="qa-testing-guru", prompt="Test auth module")
Task(description="Test module B", subagent_type="qa-testing-guru", prompt="Test database module")
Task(description="Test module C", subagent_type="qa-testing-guru", prompt="Test API endpoints")
```

## Key Points:

1. **subagent_type** is REQUIRED - specifies which system agent to use
2. **Multiple Task calls** in one message = parallel execution
3. **Agent profiles** (.claude/agents/) are for YOUR instructions, not Task tool
4. **Order**: Task(subagent_type="...", prompt="...") - subagent_type is a parameter

## Available subagent_types:

### Core Development:
- `development-specialist` - Implementation
- `qa-testing-guru` - Testing
- `test-remediation-specialist` - Fix failing tests
- `refactoring-master` - Code refactoring
- `code-analyzer` - Code review

### SDLC Phases:
- `sdlc-discovery` - Requirements gathering
- `sdlc-design` - Architecture design
- `sdlc-planning` - Task planning
- `sdlc-development` - Implementation
- `sdlc-testing` - Quality assurance
- `sdlc-deployment` - Deployment prep
- `sdlc-production` - Production readiness

### Specialized:
- `excellence-optimizer` - High-quality solutions
- `research-genius` - Information gathering
- `solution-architect` - System design
- `requirements-analyst` - Requirements analysis
- `business-analyst` - Business logic
- `prompt-generator` - Prompt optimization

## Instructing Agents:

### In CLAUDE.md:
```markdown
EXECUTION: Task(4-7 agents) for explore/test. MULTIPLE Task calls in ONE message for parallel.
```

### In agent prompts:
```markdown
For parallel execution, use Task tool with multiple calls in a single message:
- Task(subagent_type="qa-testing-guru", prompt="Test auth", description="Auth tests")
- Task(subagent_type="qa-testing-guru", prompt="Test API", description="API tests")
- Task(subagent_type="qa-testing-guru", prompt="Test DB", description="DB tests")
```

### Example instruction:
"Run tests for all modules in parallel using Task tool. Call Task multiple times in one message with subagent_type='qa-testing-guru' for each module."

## Why This Matters:

1. **Performance**: Parallel = 4-7x faster
2. **Context**: Each agent gets fresh context
3. **Specialization**: Each subagent_type optimized for its task
4. **Results**: Agents return consolidated results

## 📊 CONTEXT WINDOW BEHAVIOR (Confirmed):

**Each subagent has SEPARATE context window:**
- Independent context prevents main conversation pollution
- Clean slate for each Task invocation
- Enables longer overall sessions

**Results return to main session BUT:**
- Controlled integration preserves main context
- Results are referenceable in current session
- Still count toward limits but more efficiently

**Best practices:**
1. Use parallel Tasks liberally - each has own context
2. Instruct Tasks to return concise summaries
3. Leverage separation for exploring large codebases
4. Run 4-7 Tasks without main context pollution
5. Each Task can process large amounts independently

Example safe prompt:
```python
Task(
    subagent_type="qa-testing-guru",
    prompt="Test auth module. Return ONLY pass/fail summary and critical failures (max 500 chars)",
    description="Auth tests"
)
```

Remember: The Task tool launches SYSTEM agents (subagent_type), not your local agent profiles!
