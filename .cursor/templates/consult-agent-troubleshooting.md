# Consult Agent Troubleshooting and Anti-Patterns

## Common Pitfalls and Anti-Patterns

### **❌ COMMON PITFALLS TO AVOID**

**These will result in poor responses:**

1. **❌ Vague requests**: "Help me build a web app" (too broad)
2. **❌ Missing context**: No explanation of current state or requirements
3. **❌ No files included**: Consult agent can't see your actual code
4. **❌ Assumptions**: Taking for granted that the agent knows your project
5. **❌ Incomplete information**: Missing key details about constraints or goals
6. **❌ No self-review**: Not catching obvious issues before asking for help
7. **❌ Skipping the ritual**: Not completing the mandatory thinking tool process
8. **❌ Incomplete ritual**: Rushing through the 5-step process without thorough consideration
9. **❌ No file attachments**: Failing to include files identified during the ritual
10. **❌ Generic thinking**: Not providing specific, concrete answers to checklist questions

### **Poor Prompt Practices**

#### **Vague Requests**
```python
# ❌ Bad: Too broad and unclear
mcp_consult_agent_consult({
    "prompt": "Build a web app",
    "session_id": "webapp_001"
})

# ✅ Good: Specific and detailed
mcp_consult_agent_consult({
    "prompt": "### TASK\nCreate a React e-commerce application with user authentication, product catalog, and payment processing\n\n### LANGUAGE / RUNTIME\nTypeScript · React 18 · Next.js 14 · Stripe\n\n### INPUTS\n• User authentication with JWT\n• Product catalog with search and filtering\n• Shopping cart functionality\n• Stripe payment integration\n\n### CONSTRAINTS\n- Mobile-responsive design\n- SEO optimization\n- Performance optimization\n- Security best practices\n\n### OUTPUT_FORMAT\n```tsx\n// Component code with full implementation\n```",
    "session_id": "ecommerce_app_001"
})
```

#### **Missing Context**
```python
# ❌ Bad: No context about current state
mcp_consult_agent_consult({
    "prompt": "Fix this bug",
    "session_id": "bug_fix_001"
})

# ✅ Good: Comprehensive context
mcp_consult_agent_consult({
    "prompt": "### TASK\nFix authentication bug in login component\n\n### CONTEXT\n- Current implementation uses JWT tokens\n- Bug occurs when users log in from mobile devices\n- Error: 'Token validation failed' appears after successful login\n- Issue started after updating to React 18\n\n### FILES INCLUDED\n- LoginComponent.tsx (current implementation)\n- authUtils.ts (JWT utilities)\n- error.log (error messages)\n\n### CONSTRAINTS\n- Must maintain backward compatibility\n- Cannot change authentication provider\n- Must work on all mobile devices\n\n### OUTPUT_FORMAT\n```tsx\n// Fixed component code\n```",
    "session_id": "auth_bug_fix_001"
})
```

#### **No Files Included**
```python
# ❌ Bad: No files attached
mcp_consult_agent_consult({
    "prompt": "Review this component for best practices",
    "session_id": "review_001"
})

# ✅ Good: Relevant files included
mcp_consult_agent_consult({
    "prompt": "Review this React component for best practices and suggest improvements",
    "session_id": "component_review_001",
    "file_paths": [
        "/path/to/MyComponent.tsx",
        "/path/to/MyComponent.test.tsx",
        "/path/to/types.ts",
        "/path/to/package.json"
    ]
})
```

### **Inefficient Usage Patterns**

#### **Over-Iteration**
```python
# ❌ Bad: Unnecessary iterations for simple task
mcp_consult_agent_consult({
    "prompt": "Quick code review of this simple function",
    "session_id": "review_001",
    "iterate": 3  # Too many iterations for simple review
})

# ✅ Good: Appropriate iterations
mcp_consult_agent_consult({
    "prompt": "Quick code review of this simple function",
    "session_id": "review_001",
    "iterate": 1  # Single iteration for simple task
})
```

#### **Critic Disabled for Production Code**
```python
# ❌ Bad: No quality control for production code
mcp_consult_agent_consult({
    "prompt": "Create a production authentication system",
    "session_id": "auth_system_001",
    "critic_enabled": False  # Dangerous for production code
})

# ✅ Good: Quality control enabled
mcp_consult_agent_consult({
    "prompt": "Create a production authentication system",
    "session_id": "auth_system_001",
    "critic_enabled": True  # Essential for production code
})
```

#### **Wrong Artifact Type**
```python
# ❌ Bad: Wrong artifact type for task
mcp_consult_agent_consult({
    "prompt": "Design a microservices architecture",
    "session_id": "architecture_001",
    "artifact_type": "code"  # Should be "plan" for architecture
})

# ✅ Good: Correct artifact type
mcp_consult_agent_consult({
    "prompt": "Design a microservices architecture",
    "session_id": "architecture_001",
    "artifact_type": "plan"  # Correct for architecture planning
})
```

#### **Unnecessary Model Override**
```python
# ❌ Bad: Overriding auto-selection unnecessarily
mcp_consult_agent_consult({
    "prompt": "Create a simple React component",
    "session_id": "component_001",
    "model": "o3"  # Unnecessary override - auto-selects gpt-5-nano
})

# ✅ Good: Trust auto-selection
mcp_consult_agent_consult({
    "prompt": "Create a simple React component",
    "session_id": "component_001"
    # No model specified - intelligent auto-selection
})
```

### **Session Management Issues**

#### **Generic Session IDs**
```python
# ❌ Bad: Generic session IDs
mcp_consult_agent_consult({
    "prompt": "Create authentication system",
    "session_id": "test"  # Generic and unclear
})

mcp_consult_agent_consult({
    "prompt": "Create authentication system",
    "session_id": "session1"  # Generic and unclear
})

# ✅ Good: Specific, descriptive session IDs
mcp_consult_agent_consult({
    "prompt": "Create authentication system",
    "session_id": "ecommerce_auth_001"  # Specific and descriptive
})
```

#### **Session Pollution**
```python
# ❌ Bad: Mixing unrelated tasks in same session
mcp_consult_agent_consult({
    "prompt": "Create authentication system",
    "session_id": "project_001"
})

mcp_consult_agent_consult({
    "prompt": "Design database schema",  # Unrelated task
    "session_id": "project_001"  # Same session - causes pollution
})

# ✅ Good: Separate sessions for unrelated tasks
mcp_consult_agent_consult({
    "prompt": "Create authentication system",
    "session_id": "auth_system_001"
})

mcp_consult_agent_consult({
    "prompt": "Design database schema",
    "session_id": "database_schema_001"  # Separate session
})
```

#### **Context Loss**
```python
# ❌ Bad: Not maintaining session continuity
mcp_consult_agent_consult({
    "prompt": "Create authentication component",
    "session_id": "auth_001"
})

mcp_consult_agent_consult({
    "prompt": "Add error handling to the auth component",  # References previous work
    "session_id": "auth_002"  # Different session - loses context
})

# ✅ Good: Maintaining session continuity
mcp_consult_agent_consult({
    "prompt": "Create authentication component",
    "session_id": "auth_001"
})

mcp_consult_agent_consult({
    "prompt": "Add error handling to the auth component",
    "session_id": "auth_001"  # Same session - maintains context
})
```

#### **No Session Tracking**
```python
# ❌ Bad: No session tracking on requesting agent side
mcp_consult_agent_consult({
    "prompt": "Create component",
    "session_id": "component_001"
})

# Later, no way to know what session was used
mcp_consult_agent_consult({
    "prompt": "Update the component",
    "session_id": "component_002"  # Wrong session - loses context
})

# ✅ Good: Proper session tracking
current_feature = {
    "project": "admin_dashboard",
    "feature": "data_table_component",
    "session_id": "admin_datatable_001",
    "request_count": 0
}

# First request
current_feature["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "Create component",
    "session_id": current_feature["session_id"]
})

# Second request - same session
current_feature["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "Update the component",
    "session_id": current_feature["session_id"]  # Same session - maintains context
})
```

#### **Over-Reliance on Default Session**
```python
# ❌ Bad: Always using default session
mcp_consult_agent_consult({
    "prompt": "Create authentication system"
    # No session_id - uses default
})

mcp_consult_agent_consult({
    "prompt": "Create payment system"
    # No session_id - uses default, mixes unrelated tasks
})

# ✅ Good: Specific session IDs for each task
mcp_consult_agent_consult({
    "prompt": "Create authentication system",
    "session_id": "auth_system_001"
})

mcp_consult_agent_consult({
    "prompt": "Create payment system",
    "session_id": "payment_system_001"  # Separate session
})
```

#### **Session Hoarding**
```python
# ❌ Bad: Using same session for too many unrelated requests
mcp_consult_agent_consult({
    "prompt": "Create authentication system",
    "session_id": "project_001"
})

mcp_consult_agent_consult({
    "prompt": "Design database schema",
    "session_id": "project_001"  # Same session
})

mcp_consult_agent_consult({
    "prompt": "Create API documentation",
    "session_id": "project_001"  # Same session
})

mcp_consult_agent_consult({
    "prompt": "Set up CI/CD pipeline",
    "session_id": "project_001"  # Same session - too many unrelated tasks
})

# ✅ Good: Separate sessions for different task types
mcp_consult_agent_consult({
    "prompt": "Create authentication system",
    "session_id": "auth_system_001"
})

mcp_consult_agent_consult({
    "prompt": "Design database schema",
    "session_id": "database_schema_001"
})

mcp_consult_agent_consult({
    "prompt": "Create API documentation",
    "session_id": "api_docs_001"
})

mcp_consult_agent_consult({
    "prompt": "Set up CI/CD pipeline",
    "session_id": "cicd_pipeline_001"
})
```

## Troubleshooting Guide

### **Poor Response Quality**

#### **Symptoms**
- Generic, unhelpful responses
- Responses that don't address your specific situation
- Repeated requests for information you already provided
- Contradictory advice across related requests

#### **Causes**
- Missing or incomplete context
- No files attached
- Generic session IDs
- Skipping the thinking tool ritual
- Vague or unclear requests

#### **Solutions**
1. **Complete the thinking tool ritual** before making requests
2. **Include relevant files** as attachments
3. **Use specific, descriptive session IDs**
4. **Provide comprehensive context** in your prompt
5. **Be specific about requirements and constraints**

### **Session Context Loss**

#### **Symptoms**
- Agent asks for information already provided
- Inconsistent approaches across related requests
- Repetitive explanations of basic concepts
- Contradictory recommendations

#### **Causes**
- Using different session IDs for related tasks
- Generic session IDs that don't maintain context
- Session timeout (1 hour of inactivity)
- Mixing unrelated tasks in the same session

#### **Solutions**
1. **Use the same session ID** for related tasks
2. **Use descriptive session IDs** that indicate the task
3. **Track sessions locally** on the requesting agent side
4. **Separate unrelated tasks** into different sessions
5. **Reference previous work** in follow-up requests

### **Parameter Optimization Issues**

#### **Symptoms**
- Slow responses for simple tasks
- Expensive API calls for basic requests
- Poor quality responses for complex tasks
- Inconsistent parameter selection

#### **Causes**
- Unnecessary model overrides
- Wrong iteration counts
- Disabled critic for production code
- Not trusting auto-selection

#### **Solutions**
1. **Trust auto-selection** for most requests
2. **Only override parameters** when you have specific requirements
3. **Enable critic for production code**
4. **Use appropriate iteration counts** for task complexity
5. **Let the gatekeeper analyze** your request automatically

### **File Attachment Issues**

#### **Symptoms**
- Agent can't see your code or files
- Generic responses that don't reference your project
- Requests for files you already attached
- Missing context about your project structure

#### **Causes**
- No files attached to requests
- Wrong file paths
- Missing related files
- Files not accessible to the agent

#### **Solutions**
1. **Always include relevant files** as attachments
2. **Use absolute file paths** when possible
3. **Include related files** (tests, configs, dependencies)
4. **Verify file accessibility** before attaching
5. **Let the gatekeeper auto-attach** related files

### **Interactive Response Issues**

#### **Symptoms**
- Not handling questions/concerns properly
- Missing follow-up calls
- Context loss in multi-turn conversations
- Incomplete responses to agent requests

#### **Causes**
- Not detecting response types correctly
- Using different session IDs for follow-ups
- Not addressing all questions/concerns
- Rushing through multi-turn interactions

#### **Solutions**
1. **Detect response types** using the provided logic
2. **Use the same session ID** for follow-up calls
3. **Address all questions/concerns** comprehensively
4. **Take time to analyze** the agent's response
5. **Provide complete context** in follow-up requests

## Emergency Procedures

### **If You Get Poor Responses**

1. **Stop and analyze**: What went wrong?
2. **Check your ritual**: Did you complete the thinking tool ritual?
3. **Review your prompt**: Is it clear and specific?
4. **Check file attachments**: Are relevant files included?
5. **Verify session ID**: Is it descriptive and consistent?
6. **Start fresh**: Create a new session if context is polluted

### **If Session Context is Lost**

1. **Check session timeout**: Has it been more than 1 hour?
2. **Verify session ID**: Are you using the same ID consistently?
3. **Review recent requests**: Are they related to the same task?
4. **Create new session**: If context is irreparably polluted
5. **Reference previous work**: Explicitly mention previous decisions

### **If Parameters Are Wrong**

1. **Trust auto-selection**: Remove manual overrides
2. **Enable gatekeeper**: Let it analyze your request
3. **Check task complexity**: Use appropriate iteration counts
4. **Enable critic**: For production code and complex tasks
5. **Review model selection**: Let the system choose the best model

### **If Files Are Missing**

1. **Check file paths**: Are they correct and accessible?
2. **Include related files**: Tests, configs, dependencies
3. **Use absolute paths**: When possible
4. **Let gatekeeper help**: Enable auto-attachment
5. **Verify file content**: Ensure files contain relevant information

## Quality Validation Checklist

### **Pre-Request Validation**
- [ ] Completed thinking tool ritual
- [ ] Clear, specific prompt
- [ ] Relevant files attached
- [ ] Descriptive session ID
- [ ] Appropriate artifact type
- [ ] Quality control enabled (if needed)
- [ ] No unnecessary parameter overrides

### **Post-Response Validation**
- [ ] Response addresses all requirements
- [ ] No obvious errors or issues
- [ ] Production-ready (if applicable)
- [ ] Follows best practices
- [ ] Critic suggestions reviewed
- [ ] Session context maintained
- [ ] Ready for implementation or use

### **Session Quality Indicators**

#### **✅ Good Session Management**
- Agent references previous decisions
- Consistent terminology and approach
- Builds on previous work without repetition
- Maintains architectural consistency

#### **❌ Poor Session Management**
- Agent asks for information already provided
- Inconsistent approaches across related requests
- Repetitive explanations of basic concepts
- Contradictory recommendations

## Recovery Strategies

### **From Poor Quality Responses**
1. **Analyze the failure**: What went wrong?
2. **Improve your prompt**: Make it more specific and detailed
3. **Include more context**: Add relevant files and background
4. **Use a new session**: If context is polluted
5. **Try again**: With improved approach

### **From Context Loss**
1. **Reference previous work**: Explicitly mention previous decisions
2. **Provide complete context**: Re-explain the situation
3. **Include all relevant files**: Even if previously attached
4. **Use descriptive session ID**: For better context tracking
5. **Start fresh if needed**: Create new session for clean slate

### **From Parameter Issues**
1. **Remove overrides**: Let auto-selection work
2. **Enable gatekeeper**: For intelligent analysis
3. **Use appropriate settings**: Based on task complexity
4. **Trust the system**: Let it optimize for you
5. **Monitor results**: Adjust if needed

## Prevention Strategies

### **Best Practices Summary**
1. **Always complete the thinking tool ritual**
2. **Use specific, descriptive session IDs**
3. **Include relevant files as attachments**
4. **Trust auto-selection for parameters**
5. **Enable quality control for production code**
6. **Maintain session continuity for related tasks**
7. **Separate unrelated tasks into different sessions**
8. **Be specific and detailed in your prompts**
9. **Provide comprehensive context**
10. **Follow the established patterns and workflows**
