# Knowledge Tool Usage Guide for All Agents

## CRITICAL: Correct Parameter Format for knowledge_store

### ⚠️ MANDATORY RULES

1. **`tags` MUST be a List**
   ```python
   # ❌ WRONG - Will fail validation
   "tags": "single_tag"

   # ✅ CORRECT - Always use list
   "tags": ["single_tag"]
   "tags": ["tag1", "tag2", "tag3"]
   "tags": []  # Empty list is valid
   ```

2. **`context` MUST be a Dictionary**
   ```python
   # ❌ WRONG - Will fail validation
   "context": "some context string"
   "context": json.dumps({"key": "value"})  # Still a string!

   # ✅ CORRECT - Always use dict
   "context": {"description": "some context"}
   "context": {"key": "value", "nested": {"data": true}}
   "context": {}  # Empty dict is valid
   ```

3. **`confidence` MUST be 0.0 to 1.0**
   ```python
   # ❌ WRONG - Out of range
   "confidence": 1.5
   "confidence": -0.1

   # ✅ CORRECT - Within range
   "confidence": 0.95
   "confidence": 0.0
   "confidence": 1.0
   ```

### Valid Knowledge Types
- `ERROR_SOLUTION` - For error fixes and solutions
- `CODE_PATTERN` - For code snippets and patterns
- `WORKFLOW` - For process and workflow documentation
- `USER_PREFERENCE` - For user-specific preferences
- `CONTEXT_PATTERN` - For context-aware patterns
- `TOOL_USAGE` - For tool usage documentation
- `TEST_PATTERN` - For test-related patterns

### Correct Usage Examples

#### Minimal Call
```python
mcp__knowledge__knowledge_store(
    type="CODE_PATTERN",
    content="Your content here"
)
```

#### With All Parameters
```python
mcp__knowledge__knowledge_store(
    type="ERROR_SOLUTION",
    content="Solution for validation error in MCP tools",
    confidence=0.95,
    tags=["mcp", "validation", "fix"],  # MUST be list!
    context={  # MUST be dict!
        "error_type": "ValidationError",
        "tool": "knowledge_store",
        "date": "2025-08-21"
    }
)
```

### Common Mistakes to Avoid

| Mistake | Impact | Solution |
|---------|--------|----------|
| Using string for tags | Validation error | Always use list: `["tag"]` |
| Using string for context | Validation error | Always use dict: `{"key": "value"}` |
| Confidence > 1.0 | Validation error | Keep between 0.0 and 1.0 |
| Missing type/content | Required field error | Always include both |
| Wrong type value | Invalid enum | Use valid KnowledgeType |

### Helper Function for Safe Storage

```python
def store_knowledge_safely(type_val, content, confidence=None, tags=None, context=None):
    """
    Safely store knowledge with proper validation.
    """
    params = {"type": type_val, "content": content}

    if confidence is not None:
        params["confidence"] = max(0.0, min(1.0, confidence))

    if tags is not None:
        # Ensure tags is a list
        if isinstance(tags, str):
            tags = [tags]
        params["tags"] = tags

    if context is not None:
        # Ensure context is a dict
        if isinstance(context, str):
            context = {"description": context}
        params["context"] = context

    return mcp__knowledge__knowledge_store(**params)
```

### Debugging Validation Errors

If you encounter: `'["tag1", "tag2"]' is not valid under any of the given schemas`
- This means you passed a string representation of a list
- Solution: Pass an actual list object, not a string

If you encounter: `'{"key": "value"}' is not valid under any of the given schemas`
- This means you passed a string representation of a dict
- Solution: Pass an actual dict object, not a JSON string

### Performance Tips
- Batch related knowledge entries with similar tags
- Use consistent tag naming conventions
- Keep confidence scores realistic (0.7-0.9 for most cases)
- Include timestamps in context for temporal tracking
- Use appropriate knowledge types for better retrieval

Remember: The knowledge store is critical for maintaining system memory. Always validate your parameters before calling to ensure successful storage.
