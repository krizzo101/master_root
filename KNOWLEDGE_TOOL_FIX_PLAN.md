# Knowledge Tool Fix Plan
## Response to Critical Issues Report - 2025-08-21

### Executive Summary
This plan addresses 7 critical issues identified in the Knowledge Tool Development Issues Report. We propose a three-phase approach: **Immediate Workarounds** (Week 1), **MCP Server Fixes** (Week 2-3), and **Long-term Enhancements** (Week 4+).

---

## 🚨 ROOT CAUSE ANALYSIS

### Primary Issue: MCP Server Parameter Exposure
The MCP server (FastMCP implementation) is only exposing 2 of 5 parameters:
- ✅ `knowledge_type` (exposed)
- ✅ `content` (exposed)
- ❌ `tags` (NOT exposed through MCP)
- ❌ `context` (NOT exposed through MCP)
- ❌ `confidence` (NOT exposed through MCP)

This is a **server configuration issue**, not a Neo4j backend problem.

### Secondary Issues:
1. Parameter name inconsistencies in documentation
2. Poor error messages from Pydantic validation
3. Lack of helper functions for common patterns
4. Missing integration tests

---

## 📋 PHASE 1: IMMEDIATE WORKAROUNDS (Week 1)

### 1.1 Helper Function Library
**File:** `/home/opsvi/master_root/libs/knowledge_tool_helper.py`

```python
def safe_knowledge_store(
    knowledge_type: str,
    content: str,
    tags: List[str] = None,
    context: Dict = None,
    confidence: float = 0.8
) -> Dict:
    """
    Safely store knowledge with automatic metadata embedding.
    Works around current MCP parameter limitations.
    """
    # Embed metadata in content until MCP fix
    metadata_header = []

    if tags:
        metadata_header.append(f"Tags: {', '.join(tags)}")

    if context:
        metadata_header.append(f"Context: {json.dumps(context)}")

    metadata_header.append(f"Confidence: {confidence}")
    metadata_header.append(f"Date: {datetime.now().isoformat()}")

    enhanced_content = "\n".join(metadata_header) + "\n\n" + content

    return mcp__knowledge__knowledge_store(
        knowledge_type=knowledge_type,
        content=enhanced_content
    )
```

### 1.2 Documentation Updates
**Update:** `.claude/agents/KNOWLEDGE_TOOL_USAGE_GUIDE.md`

Add clear section:
```markdown
## ⚠️ CURRENT LIMITATIONS (As of 2025-08-21)

### MCP Interface Restrictions
Due to MCP server configuration, only these parameters work:
- `knowledge_type` ✅
- `content` ✅

These parameters will cause validation errors:
- `tags` ❌ (embed in content instead)
- `context` ❌ (embed in content instead)
- `confidence` ❌ (embed in content instead)

### Workaround Pattern
```python
# DON'T DO THIS (will fail):
mcp__knowledge__knowledge_store(
    knowledge_type="ERROR_SOLUTION",
    content="Fix for issue",
    tags=["bug", "fix"],  # ❌ WILL FAIL
    confidence=0.9  # ❌ WILL FAIL
)

# DO THIS INSTEAD (working pattern):
from knowledge_tool_helper import safe_knowledge_store

safe_knowledge_store(
    knowledge_type="ERROR_SOLUTION",
    content="Fix for issue",
    tags=["bug", "fix"],  # ✅ Will be embedded
    confidence=0.9  # ✅ Will be embedded
)
```
```

### 1.3 Update Agent Profiles
**Files to update:**
- `.claude/agents/research-genius.md`
- `.claude/agents/code-analyzer.md`
- All agents using knowledge tools

Add import and usage:
```python
# At agent start
from knowledge_tool_helper import safe_knowledge_store, safe_knowledge_query

# Replace all direct calls
# OLD: mcp__knowledge__knowledge_store(...)
# NEW: safe_knowledge_store(...)
```

---

## 🔧 PHASE 2: MCP SERVER FIXES (Week 2-3)

### 2.1 Fix Parameter Exposure in MCP Server

**File:** `/home/opsvi/master_root/libs/opsvi_mcp/servers/knowledge.py` (or equivalent)

```python
@server.tool()
async def knowledge_store(
    knowledge_type: str = Field(..., description="Type of knowledge"),
    content: str = Field(..., description="Knowledge content"),
    tags: Optional[List[str]] = Field(default=None, description="List of tags"),
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context dict"),
    confidence: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)
) -> Dict[str, Any]:
    """
    Store knowledge with full parameter support.
    """
    # Ensure all parameters are properly exposed through MCP
    pass
```

### 2.2 Fix Parameter Name Consistency

**Standardize on:**
- `confidence` (NOT `confidence_score`)
- `type` (NOT `knowledge_type`) - align with Neo4j schema
- `tags` as List[str]
- `context` as Dict[str, Any]

### 2.3 Improve Error Messages

```python
class KnowledgeValidationError(Exception):
    def __init__(self, field: str, value: Any, expected: str):
        super().__init__(
            f"Validation failed for '{field}':\n"
            f"  Received: {type(value).__name__} = {value}\n"
            f"  Expected: {expected}\n"
            f"  Example: {self.get_example(field)}"
        )

    @staticmethod
    def get_example(field: str) -> str:
        examples = {
            "tags": '["tag1", "tag2"]',
            "context": '{"key": "value"}',
            "confidence": "0.85 (float between 0.0-1.0)"
        }
        return examples.get(field, "See documentation")
```

---

## 🚀 PHASE 3: LONG-TERM ENHANCEMENTS (Week 4+)

### 3.1 Comprehensive Test Suite

**File:** `/home/opsvi/master_root/tests/test_knowledge_tools.py`

```python
import pytest
from knowledge_tool_helper import safe_knowledge_store

class TestKnowledgeTools:

    def test_parameter_validation(self):
        """Test all parameter combinations"""
        test_cases = [
            # Valid cases
            {"knowledge_type": "TEST", "content": "test"},
            {"knowledge_type": "TEST", "content": "test", "tags": ["a"]},
            {"knowledge_type": "TEST", "content": "test", "context": {"k": "v"}},

            # Invalid cases that should fail gracefully
            {"knowledge_type": "TEST", "content": "test", "tags": "string"},
            {"knowledge_type": "TEST", "content": "test", "confidence": 2.0},
        ]

        for case in test_cases:
            result = safe_knowledge_store(**case)
            assert result is not None

    def test_immediate_retrieval(self):
        """Test that stored knowledge is immediately retrievable"""
        result = safe_knowledge_store(
            knowledge_type="TEST",
            content="Immediate retrieval test"
        )

        search = safe_knowledge_query(
            query_type="search",
            query_text="Immediate retrieval test"
        )

        assert len(search) > 0
        assert result["knowledge_id"] in [r["id"] for r in search]

    def test_metadata_preservation(self):
        """Test that tags and context are preserved"""
        tags = ["test", "metadata"]
        context = {"test": True, "date": "2025-08-21"}

        result = safe_knowledge_store(
            knowledge_type="TEST",
            content="Metadata test",
            tags=tags,
            context=context
        )

        retrieved = safe_knowledge_query(
            query_type="by_id",
            knowledge_id=result["knowledge_id"]
        )

        # Until MCP fix, check metadata is in content
        assert "Tags: test, metadata" in retrieved["content"]
        assert "Context:" in retrieved["content"]
```

### 3.2 Migration Script for Existing Data

```python
# migrate_knowledge_metadata.py
"""
Extract embedded metadata from content and properly store
once MCP server is fixed.
"""

def migrate_embedded_metadata():
    # Query all knowledge entries
    entries = knowledge_query(query_type="all", limit=10000)

    for entry in entries:
        # Extract embedded metadata from content
        tags, context, confidence, clean_content = extract_metadata(entry["content"])

        # Update with proper parameters (post-MCP fix)
        knowledge_update(
            knowledge_id=entry["id"],
            tags=tags,
            context=context,
            confidence=confidence,
            content=clean_content
        )
```

### 3.3 Enhanced Query Builder

```python
class KnowledgeQueryBuilder:
    """Fluent interface for building knowledge queries"""

    def __init__(self):
        self.params = {}

    def of_type(self, *types):
        self.params["types"] = list(types)
        return self

    def with_tags(self, *tags):
        self.params["tags"] = list(tags)
        return self

    def containing(self, text):
        self.params["query_text"] = text
        return self

    def with_confidence(self, min_conf):
        self.params["min_confidence"] = min_conf
        return self

    def recent(self, days=7):
        self.params["since"] = datetime.now() - timedelta(days=days)
        return self

    def execute(self):
        return safe_knowledge_query(**self.params)

# Usage
results = (KnowledgeQueryBuilder()
    .of_type("ERROR_SOLUTION", "CODE_PATTERN")
    .with_tags("python", "async")
    .with_confidence(0.8)
    .recent(30)
    .execute())
```

---

## 📊 IMPLEMENTATION TIMELINE

### Week 1 (Immediate)
- [ ] Deploy knowledge_tool_helper.py
- [ ] Update all documentation
- [ ] Update agent profiles
- [ ] Sync to all projects using sync-claude-config.sh

### Week 2 (MCP Fixes)
- [ ] Fix parameter exposure in MCP server
- [ ] Standardize parameter names
- [ ] Improve error messages
- [ ] Deploy to test environment

### Week 3 (Testing)
- [ ] Create comprehensive test suite
- [ ] Run regression tests
- [ ] Fix any discovered issues
- [ ] Deploy to production

### Week 4 (Enhancements)
- [ ] Implement query builder
- [ ] Create migration script
- [ ] Add monitoring/metrics
- [ ] Performance optimization

---

## 🎯 SUCCESS METRICS

### Immediate (Week 1)
- Zero validation errors using helper functions
- All agents successfully storing knowledge
- Clear documentation of limitations

### Short-term (Week 2-3)
- All 5 parameters working through MCP
- Error messages provide actionable guidance
- Immediate retrieval of stored knowledge

### Long-term (Week 4+)
- 100% test coverage
- < 100ms storage latency
- < 200ms retrieval latency
- Zero data loss

---

## 🔍 VALIDATION PLAN

### Automated Testing
```bash
# Run after each phase
pytest tests/test_knowledge_tools.py -v
pytest tests/test_knowledge_integration.py -v

# Performance testing
python tests/benchmark_knowledge_tools.py
```

### Manual Testing Checklist
- [ ] Store entry with all parameters
- [ ] Immediate retrieval verification
- [ ] Cross-agent knowledge sharing
- [ ] Bulk storage (100+ entries)
- [ ] Complex query patterns

---

## 📝 ROLLBACK PLAN

If issues arise:
1. **Phase 1**: Revert to direct content storage (current state)
2. **Phase 2**: Keep helper functions, revert MCP changes
3. **Phase 3**: Maintain core fixes, defer enhancements

---

## 👥 OWNERSHIP

- **Lead**: DevOps/MCP Team
- **Contributors**: AI Engineering Team
- **Testing**: QA Team
- **Documentation**: Technical Writing Team
- **Stakeholders**: All AI Research Teams

---

## 📢 COMMUNICATION PLAN

1. **Day 1**: Announce workarounds availability
2. **Week 1 End**: Helper functions deployed
3. **Week 2 End**: MCP fixes in testing
4. **Week 3 End**: Full solution deployed
5. **Week 4 End**: Enhancements complete

---

## ✅ ACCEPTANCE CRITERIA

The fix is complete when:
1. All 5 parameters work reliably through MCP
2. Zero validation errors in normal usage
3. Clear, actionable error messages
4. Immediate knowledge retrieval works
5. All tests pass (unit, integration, performance)
6. Documentation is complete and accurate
7. Migration of existing data complete

---

*Last Updated: 2025-08-21*
*Status: PLAN APPROVED - AWAITING IMPLEMENTATION*
*Contact: AI Platform Team*
