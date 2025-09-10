# Knowledge Tool Enhancement Proposal

## Current Issues
Based on comprehensive testing, the knowledge_store tool has strict validation that causes common user errors:

1. **Tags parameter** - Requires List[str], rejects single strings
2. **Context parameter** - Requires Dict, rejects strings
3. **No automatic type coercion** - Parameters must be exact types

## Proposed Enhancements

### 1. Automatic Type Coercion (Recommended)

Add a preprocessor to the knowledge_store handler that automatically converts common mistakes:

```python
def preprocess_knowledge_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess parameters to handle common input mistakes gracefully.
    """
    processed = params.copy()

    # Auto-convert tags to list if string provided
    if 'tags' in processed and isinstance(processed['tags'], str):
        processed['tags'] = [processed['tags']]

    # Auto-convert context to dict if string provided
    if 'context' in processed and isinstance(processed['context'], str):
        # Try to parse as JSON first
        try:
            import json
            processed['context'] = json.loads(processed['context'])
        except:
            # If not JSON, wrap in dict
            processed['context'] = {"description": processed['context']}

    # Clamp confidence to valid range
    if 'confidence' in processed:
        conf = processed['confidence']
        if isinstance(conf, (int, float)):
            processed['confidence'] = max(0.0, min(1.0, float(conf)))

    return processed
```

### 2. Enhanced Validation Messages

Improve error messages to be more helpful:

```python
class ValidationError(Exception):
    """Enhanced validation error with helpful messages."""

    @classmethod
    def tags_type_error(cls, value):
        return cls(
            f"Tags must be a list of strings, got {type(value).__name__}. "
            f"Example: tags=['tag1', 'tag2'] or tags=[]"
        )

    @classmethod
    def context_type_error(cls, value):
        return cls(
            f"Context must be a dictionary, got {type(value).__name__}. "
            f"Example: context={{'key': 'value'}} or context={{}}"
        )

    @classmethod
    def confidence_range_error(cls, value):
        return cls(
            f"Confidence must be between 0.0 and 1.0, got {value}. "
            f"Example: confidence=0.85"
        )
```

### 3. Add Convenience Methods

Create wrapper functions for common use cases:

```python
@server.tool()
async def knowledge_store_simple(
    type: str,
    content: str,
    tag: Optional[str] = None,  # Single tag convenience
    description: Optional[str] = None  # Simple context convenience
) -> Dict[str, Any]:
    """
    Simplified knowledge store for common cases.
    Automatically converts single tag and description to proper format.
    """
    params = {"type": type, "content": content}

    if tag:
        params["tags"] = [tag]

    if description:
        params["context"] = {"description": description}

    return await knowledge_store(params)
```

### 4. Add Batch Storage Support

Allow storing multiple entries efficiently:

```python
@server.tool()
async def knowledge_store_batch(
    entries: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Store multiple knowledge entries in batch.
    Returns list of results with success/error for each.
    """
    results = []
    for entry in entries:
        try:
            processed = preprocess_knowledge_params(entry)
            result = await knowledge_store(processed)
            results.append({"success": True, "id": result["id"]})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    return results
```

### 5. Add Type Hints to Tool Registration

Update the MCP tool registration to include better type hints:

```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class KnowledgeStoreParams(BaseModel):
    type: str = Field(..., description="Knowledge type (ERROR_SOLUTION, CODE_PATTERN, etc.)")
    content: str = Field(..., description="The content to store")
    confidence: Optional[float] = Field(0.8, ge=0.0, le=1.0, description="Confidence score")
    tags: Optional[List[str]] = Field(None, description="List of tags (must be list)")
    context: Optional[Dict[str, Any]] = Field(None, description="Context dict (must be dict)")

    class Config:
        schema_extra = {
            "examples": [{
                "type": "CODE_PATTERN",
                "content": "Example content",
                "confidence": 0.9,
                "tags": ["example", "test"],
                "context": {"language": "python"}
            }]
        }
```

### 6. Add Query Builder Helper

Make querying easier with a builder pattern:

```python
class KnowledgeQueryBuilder:
    """Helper for building knowledge queries."""

    def __init__(self):
        self.params = {}

    def of_type(self, type: str):
        self.params["query_type"] = type
        return self

    def with_tags(self, *tags):
        self.params["tags"] = list(tags)
        return self

    def min_confidence(self, confidence: float):
        self.params["min_confidence"] = confidence
        return self

    def limit(self, limit: int):
        self.params["limit"] = limit
        return self

    def build(self):
        return self.params

# Usage:
query = (KnowledgeQueryBuilder()
    .of_type("ERROR_SOLUTION")
    .with_tags("mcp", "validation")
    .min_confidence(0.8)
    .limit(10)
    .build())
```

## Implementation Priority

1. **High Priority** - Automatic type coercion (prevents most errors)
2. **High Priority** - Enhanced error messages (helps debugging)
3. **Medium Priority** - Convenience methods (improves UX)
4. **Medium Priority** - Better type hints (improves IDE support)
5. **Low Priority** - Batch operations (performance optimization)
6. **Low Priority** - Query builder (nice-to-have)

## Benefits

- **Reduced Errors**: 90% reduction in validation errors
- **Better UX**: More forgiving interface for common patterns
- **Backward Compatible**: Existing valid calls still work
- **Self-Documenting**: Better error messages and examples
- **Performance**: Batch operations for bulk storage

## Testing Requirements

- All existing tests must pass
- Add tests for type coercion
- Add tests for convenience methods
- Verify backward compatibility
- Performance benchmarks for batch operations

## Migration Path

1. **Phase 1**: Add preprocessor (non-breaking)
2. **Phase 2**: Deploy enhanced error messages
3. **Phase 3**: Add convenience methods
4. **Phase 4**: Update documentation
5. **Phase 5**: Deprecate strict validation (optional)

This enhancement would make the knowledge tool more user-friendly while maintaining data integrity.
