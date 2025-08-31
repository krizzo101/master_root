# HECATON Prompt Engineering Examples

## Task Prompt Best Practices

### 1. Code Generation Tasks

#### ❌ Poor Prompt:
```
"Write some code"
```
**Problems**: Vague, no specification, no constraints

#### ✅ Good Prompt:
```
"Write a Python function to calculate fibonacci numbers"
```
**Better**: Specific language and function

#### ✅✅ Excellent Prompt:
```
"Implement a Python function `fibonacci(n: int) -> int` that:
- Returns the nth Fibonacci number
- Handles n < 0 by raising ValueError
- Uses memoization for performance
- Includes docstring with examples"
```
**Best**: Clear specifications, edge cases, performance requirements

### 2. Test Generation Tasks

#### ❌ Poor Prompt:
```
"Test the function"
```

#### ✅ Good Prompt:
```
"Write tests for the fibonacci function"
```

#### ✅✅ Excellent Prompt:
```
"Create pytest tests for fibonacci(n) that verify:
- Correct values for n=0,1,5,10
- ValueError raised for n<0
- Performance: n=40 completes in <1s
- Edge case: n=0 returns 0"
```

### 3. Code Review Tasks

#### ❌ Poor Prompt:
```
"Review this code"
```

#### ✅ Good Prompt:
```
"Review this code for bugs and performance issues"
```

#### ✅✅ Excellent Prompt:
```
"Review the fibonacci implementation for:
1. Correctness of algorithm
2. Performance bottlenecks
3. Error handling completeness
4. Code style (PEP 8)
5. Missing edge cases
Prioritize issues by severity."
```

### 4. Research Tasks

#### ❌ Poor Prompt:
```
"Find information about Python"
```

#### ✅ Good Prompt:
```
"Research Python async programming patterns"
```

#### ✅✅ Excellent Prompt:
```
"Research Python async/await best practices focusing on:
- Error handling in async contexts
- Testing async code with pytest
- Common anti-patterns to avoid
- Performance comparison with threading
Provide 3-5 actionable recommendations"
```

### 5. Refactoring Tasks

#### ❌ Poor Prompt:
```
"Make this better"
```

#### ✅ Good Prompt:
```
"Refactor this function to be more readable"
```

#### ✅✅ Excellent Prompt:
```
"Refactor calculate_total() to:
- Extract tax calculation to separate method
- Replace magic numbers with constants
- Add type hints
- Reduce cyclomatic complexity below 5
- Maintain exact same behavior with all tests passing"
```

## Complete Agent Execution Examples

### Example 1: Code Agent Full Context

**Task Prompt**:
```python
task = {
    "id": "impl-auth-001",
    "type": "code",
    "prompt": """Implement a JWT authentication decorator for Flask that:
    - Validates JWT tokens from Authorization header
    - Extracts user_id and role from token
    - Handles expired tokens with 401 response
    - Handles invalid tokens with 403 response
    - Stores user info in g.current_user
    - Use PyJWT library"""
}
```

**Generated CLAUDE.md**:
```markdown
# Code Agent Instructions
You are a specialized code generation agent for HECATON.
- Write code directly without preamble
- Follow existing patterns in the codebase
- No comments unless explicitly requested
- Focus only on the specific task given

## Current Task
Implement a JWT authentication decorator for Flask that:
- Validates JWT tokens from Authorization header
- Extracts user_id and role from token
- Handles expired tokens with 401 response
- Handles invalid tokens with 403 response
- Stores user info in g.current_user
- Use PyJWT library

## Configuration
- Agent ID: impl-auth-001
- Agent Type: code
- Model: sonnet
- Allowed Tools: Write, Read, Edit

## Rules
1. Complete ONLY the assigned task
2. Use ONLY the allowed tools
3. Be concise and efficient
4. No explanations unless requested
5. Exit when task is complete
```

**System Prompt**:
```
You are a focused code generation agent. Write clean, efficient code without explanations unless asked.
```

### Example 2: Test Agent Full Context

**Task Prompt**:
```python
task = {
    "id": "test-auth-001",
    "type": "test",
    "prompt": """Write comprehensive pytest tests for jwt_required decorator:
    - Test valid token allows access
    - Test expired token returns 401
    - Test malformed token returns 403
    - Test missing token returns 401
    - Test token with invalid signature returns 403
    - Use pytest fixtures for test tokens
    - Mock time.time() for expiration testing"""
}
```

**Generated CLAUDE.md**:
```markdown
# Test Agent Instructions
You are a specialized test generation agent.
- Write pytest tests by default
- Include edge cases and error conditions
- Follow AAA pattern (Arrange, Act, Assert)
- Use mocks and fixtures appropriately

## Current Task
Write comprehensive pytest tests for jwt_required decorator:
- Test valid token allows access
- Test expired token returns 401
- Test malformed token returns 403
- Test missing token returns 401
- Test token with invalid signature returns 403
- Use pytest fixtures for test tokens
- Mock time.time() for expiration testing

## Configuration
- Agent ID: test-auth-001
- Agent Type: test
- Model: sonnet
- Allowed Tools: Write, Read, Bash

## Rules
1. Complete ONLY the assigned task
2. Use ONLY the allowed tools
3. Be concise and efficient
4. No explanations unless requested
5. Exit when task is complete
```

## Task Prompt Templates

### Code Implementation Template
```
Implement {component} that:
- {requirement_1}
- {requirement_2}
- Handles {edge_case} by {handling_strategy}
- Uses {specific_library/pattern}
- Returns {expected_output_format}
```

### Test Creation Template
```
Create {test_framework} tests for {component} that verify:
- {happy_path_scenario}
- {error_scenario_1} returns/raises {expected_error}
- {edge_case} behaves as {expected_behavior}
- Performance: {performance_requirement}
- Uses {test_pattern} pattern
```

### Review Template
```
Review {code_component} for:
1. {aspect_1} (e.g., correctness)
2. {aspect_2} (e.g., performance)
3. {aspect_3} (e.g., security)
Focus on {priority_area}
Provide {output_format}
```

### Research Template
```
Research {topic} focusing on:
- {specific_aspect_1}
- {specific_aspect_2}
- {comparison/evaluation_criteria}
Provide {number} actionable {deliverable_type}
Cite sources where applicable
```

### Refactor Template
```
Refactor {component} to:
- {improvement_1}
- {improvement_2}
- Maintain {invariant}
- Follow {pattern/principle}
- Ensure {validation_criteria}
```

## Prompt Length Guidelines

| Agent Type | Ideal Prompt Length | Max Prompt Length |
|------------|-------------------|-------------------|
| Code | 3-6 lines | 10 lines |
| Test | 4-7 lines | 12 lines |
| Review | 3-5 lines | 8 lines |
| Research | 4-6 lines | 10 lines |
| Refactor | 4-6 lines | 10 lines |
| Minimal | 1-2 lines | 3 lines |

## Prompt Clarity Checklist

Before sending a task to an agent, verify:

- [ ] **Specific**: No ambiguous terms like "some", "better", "good"
- [ ] **Measurable**: Clear success criteria
- [ ] **Actionable**: Agent knows exactly what to do
- [ ] **Relevant**: Only information needed for the task
- [ ] **Time-bound**: Clear completion criteria

## Anti-Pattern Examples

### 1. Over-Specified Prompts
❌ **Bad**: Including implementation details for a code agent
```
"Write a function using a for loop with index i starting at 0..."
```
✅ **Good**: Specify requirements, let agent choose implementation
```
"Write a function that iterates through a list and returns..."
```

### 2. Under-Specified Prompts
❌ **Bad**: Too vague
```
"Fix the bug"
```
✅ **Good**: Specific issue and context
```
"Fix the IndexError in parse_data() when input list is empty"
```

### 3. Mixed Responsibilities
❌ **Bad**: Multiple agent roles in one task
```
"Write the code, test it, and document it"
```
✅ **Good**: Single responsibility
```
"Write the authentication function"
```
(Then separately: "Write tests for the authentication function")

### 4. Explanatory Requirements
❌ **Bad**: Asking for explanations from action agents
```
"Implement the function and explain your design choices"
```
✅ **Good**: Just the action
```
"Implement the function"
```

## Prompt Performance Metrics

Track these metrics to improve prompts:

1. **Completion Rate**: % of tasks completed successfully
2. **Retry Rate**: % of tasks needing clarification
3. **Token Efficiency**: Tokens used vs expected
4. **Time to Complete**: Actual vs estimated
5. **Quality Score**: Output meets requirements

## A/B Testing Prompts

When optimizing, test variations:

### Version A (Detailed):
```
"Create a Python function that calculates the factorial of a number,
handles negative inputs by raising ValueError, uses recursion,
and includes a docstring"
```

### Version B (Concise):
```
"Implement factorial(n) in Python:
- Recursive approach
- ValueError for n<0
- Include docstring"
```

### Version C (Bullet Points):
```
"factorial(n) function:
• Python
• Recursive
• Error: n<0
• Docstring"
```

Track which version produces:
- Fastest completion
- Fewest tokens
- Best quality output

## Conclusion

Effective prompt engineering for HECATON agents requires:
1. **Clarity**: Specific, measurable requirements
2. **Brevity**: Maximum information in minimum words
3. **Structure**: Consistent format across similar tasks
4. **Focus**: Single responsibility per prompt
5. **Context**: Just enough, not too much

Well-crafted prompts are the difference between agents that struggle and agents that excel.
