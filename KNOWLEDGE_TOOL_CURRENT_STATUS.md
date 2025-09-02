# Knowledge Tool Current Status (2025-08-21)

## 🚨 CRITICAL UPDATE: Limited MCP Interface

The `mcp__knowledge__knowledge_store` tool currently has **LIMITED functionality** through the MCP interface.

### Working Parameters (Confirmed)
- `knowledge_type` (required): One of [RESEARCH_FINDINGS, CODE_PATTERN, WORKFLOW, USER_PREFERENCE, CONTEXT_PATTERN, TOOL_USAGE, ERROR_SOLUTION]
- `content` (required): String containing the knowledge to store

### Non-Working Parameters (MCP Interface Issue)
- ❌ `tags` - Not exposed through MCP (defaults to [])
- ❌ `context` - Not exposed through MCP (defaults to {})
- ❌ `confidence` - Not exposed through MCP (defaults to 0.8)

### Current Workaround Pattern

Since metadata parameters are not available, include metadata IN the content string:

```python
# Instead of this (which would fail):
mcp__knowledge__knowledge_store(
    knowledge_type="RESEARCH_FINDINGS",
    content="GPT-5 is available",
    tags=["gpt-5"],  # This will cause validation error!
    context={"date": "2025"}  # This will cause validation error!
)

# Do this (working pattern):
mcp__knowledge__knowledge_store(
    knowledge_type="RESEARCH_FINDINGS",
    content="""GPT-5 Discovery (2025-08-21)
    Tags: gpt-5, openai, model-availability
    Sources: CNBC, AI Multiple
    Confidence: High (0.85)

    Key Finding: GPT-5 confirmed available with:
    - 2x increase in coding activity
    - 8x improvement in reasoning
    - Strong enterprise adoption"""
)
```

### Storage IS Still Mandatory

Despite the limitation, research MUST still store findings because:
1. Basic storage still works (type + content)
2. Embeddings are generated for semantic search
3. Knowledge is persisted in Neo4j
4. Better than no storage at all

### Successful Storage Example

```json
{
  "success": true,
  "knowledge_id": "ff6dcc04239f7635",
  "embedding_generated": true,
  "embedding_info": {
    "generated": true,
    "dimensions": 384,
    "model": "sentence-transformers/all-MiniLM-L6-v2"
  }
}
```

### Research Validation Updated

**Minimum requirement:** At least 1 successful knowledge_store call with:
- Valid knowledge_type
- Meaningful content with embedded metadata

**Until MCP interface is fixed:**
- Include tags in content as "Tags: tag1, tag2"
- Include source in content as "Source: ..."
- Include confidence in content as "Confidence: High/Medium/Low"
- Include date in content as ISO format

### Impact on Research Agents

Research agents should:
1. Still call knowledge_store (mandatory)
2. Format content to include metadata
3. Use structured content format
4. Report successful storage IDs

### Next Steps

1. **Immediate:** Use workaround pattern for all storage
2. **Short-term:** Fix MCP interface to expose all parameters
3. **Long-term:** Implement batch storage capabilities

## Summary

The knowledge tool works but with limitations. Storage remains MANDATORY. Use content string to embed metadata until full parameter support is restored.
