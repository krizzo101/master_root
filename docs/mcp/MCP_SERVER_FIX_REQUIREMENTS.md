# MCP Server Fix Requirements
## Knowledge Tool Parameter Exposure Issue

### Problem Statement
The FastMCP server implementation for knowledge tools is only exposing 2 out of 5 critical parameters through the MCP interface, causing validation errors and forcing workarounds.

### Current State (BROKEN)
```python
# Only these work through MCP:
- knowledge_type ✅
- content ✅

# These cause validation errors:
- tags ❌
- context ❌
- confidence ❌
```

### Required Fix

#### 1. Update Server Tool Registration

**File:** `libs/opsvi_mcp/servers/knowledge.py` (or equivalent FastMCP server file)

```python
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

server = FastMCP("knowledge-server")

class KnowledgeStoreParams(BaseModel):
    """Parameters for knowledge storage with proper validation."""
    knowledge_type: str = Field(
        ...,
        description="Type of knowledge (ERROR_SOLUTION, CODE_PATTERN, etc.)"
    )
    content: str = Field(
        ...,
        description="The knowledge content to store"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="List of tags for categorization"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Context dictionary with metadata"
    )
    confidence: Optional[float] = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )

@server.tool()
async def knowledge_store(params: KnowledgeStoreParams) -> Dict[str, Any]:
    """
    Store knowledge with full parameter support.
    All parameters should be accessible through MCP.
    """
    # Extract parameters
    knowledge_type = params.knowledge_type
    content = params.content
    tags = params.tags or []
    context = params.context or {}
    confidence = params.confidence

    # Generate embedding
    embedding = await generate_embedding(content)

    # Store in Neo4j
    query = """
    CREATE (k:Knowledge {
        id: randomUUID(),
        type: $type,
        content: $content,
        tags: $tags,
        context: $context,
        confidence: $confidence,
        embedding: $embedding,
        embedding_model: $embedding_model,
        created_at: datetime()
    })
    RETURN k.id as knowledge_id
    """

    result = await neo4j_write(
        query,
        type=knowledge_type,
        content=content,
        tags=tags,
        context=context,
        confidence=confidence,
        embedding=embedding,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2"
    )

    return {
        "success": True,
        "knowledge_id": result["knowledge_id"],
        "message": "Knowledge stored successfully"
    }
```

#### 2. Fix Parameter Name Consistency

**Standardize ALL tools to use:**
- `confidence` (NOT `confidence_score`)
- `knowledge_type` (NOT `type` to avoid Python keyword conflict)

#### 3. Update Tool Descriptions

```python
@server.tool(
    name="knowledge_store",
    description="""Store knowledge with metadata.

    Parameters:
    - knowledge_type (str, required): Type of knowledge
    - content (str, required): Knowledge content
    - tags (list[str], optional): Categorization tags
    - context (dict, optional): Metadata dictionary
    - confidence (float, optional): Score 0.0-1.0, default 0.8

    Returns:
    - knowledge_id: Unique identifier for stored knowledge
    - success: Boolean indicating storage success
    """
)
```

#### 4. Add Parameter Validation with Clear Errors

```python
def validate_params(params: KnowledgeStoreParams) -> None:
    """Validate parameters with helpful error messages."""

    # Validate tags
    if params.tags is not None:
        if not isinstance(params.tags, list):
            raise ValueError(
                f"tags must be a list of strings, got {type(params.tags).__name__}\n"
                f"Example: ['tag1', 'tag2']"
            )
        for tag in params.tags:
            if not isinstance(tag, str):
                raise ValueError(
                    f"Each tag must be a string, found {type(tag).__name__}\n"
                    f"Example: ['tag1', 'tag2']"
                )

    # Validate context
    if params.context is not None:
        if not isinstance(params.context, dict):
            raise ValueError(
                f"context must be a dictionary, got {type(params.context).__name__}\n"
                f"Example: {{'key': 'value', 'date': '2025-08-21'}}"
            )

    # Validate confidence
    if params.confidence is not None:
        if not 0.0 <= params.confidence <= 1.0:
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {params.confidence}\n"
                f"Example: 0.85"
            )
```

### Testing Requirements

#### Unit Tests
```python
def test_all_parameters_exposed():
    """Verify all 5 parameters are accessible through MCP."""
    # This should work without errors
    result = mcp__knowledge__knowledge_store(
        knowledge_type="TEST",
        content="Test content",
        tags=["test", "validation"],
        context={"test": True},
        confidence=0.9
    )
    assert result["success"] is True
```

#### Integration Tests
```python
def test_mcp_tool_discovery():
    """Verify MCP exposes all parameters in tool schema."""
    tools = mcp_client.list_tools()
    knowledge_store = next(t for t in tools if t.name == "knowledge_store")

    params = knowledge_store.input_schema["properties"]
    assert "knowledge_type" in params
    assert "content" in params
    assert "tags" in params
    assert "context" in params
    assert "confidence" in params
```

### Migration Path

1. **Phase 1**: Deploy helper library (COMPLETE)
2. **Phase 2**: Fix MCP server (THIS DOCUMENT)
3. **Phase 3**: Test with both old and new clients
4. **Phase 4**: Migrate embedded metadata to proper fields
5. **Phase 5**: Deprecate helper workarounds

### Verification Checklist

- [ ] All 5 parameters accessible through MCP interface
- [ ] No validation errors with proper parameter types
- [ ] Clear error messages for invalid inputs
- [ ] Backward compatibility with existing data
- [ ] Performance maintained (<100ms overhead)
- [ ] Documentation updated
- [ ] Tests passing

### Files to Modify

1. **Server Implementation**
   - `libs/opsvi_mcp/servers/knowledge.py`
   - `libs/opsvi_mcp/tools/knowledge_tools.py`

2. **Configuration**
   - `.mcp.json` (if parameter schemas defined here)

3. **Documentation**
   - `.claude/agents/KNOWLEDGE_TOOL_USAGE_GUIDE.md`
   - API documentation

4. **Tests**
   - `tests/test_knowledge_tools.py`
   - `tests/test_mcp_integration.py`

### Success Criteria

The fix is successful when:
```python
# This works without any workarounds:
result = mcp__knowledge__knowledge_store(
    knowledge_type="SUCCESS_TEST",
    content="Direct MCP call with all parameters",
    tags=["success", "direct", "mcp"],
    context={"status": "fixed", "date": "2025-08-21"},
    confidence=0.95
)

# And returns:
{
    "success": True,
    "knowledge_id": "uuid-here",
    "message": "Knowledge stored successfully"
}
```

### Contact
- **Owner**: MCP Platform Team
- **Escalation**: AI Engineering Lead
- **Support**: #mcp-support channel

---
*Priority: CRITICAL*
*Target Fix Date: 2025-08-28*
*Impact: All AI agents using knowledge storage*
