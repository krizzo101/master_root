# Knowledge Base Implementation Action Plan
## Comprehensive Strategy for System Enhancement

### Executive Summary
The AI Factory Knowledge Base has grown to 49 entries with extensive infrastructure across multiple systems. This action plan addresses critical issues and outlines the path to full operational status.

## 🚨 Critical Issues (Fix Immediately)

### 1. Neo4j Authentication Failure
**Problem**: Python driver fails with "unauthorized" despite correct credentials
**Impact**: Blocks 61.2% of KB features (embeddings, semantic search)
**Solution**:
```python
# Fix in /apps/knowledge_system/knowledge_system.py line 29-31
neo4j_uri: str = "neo4j://localhost:7687"  # Change from bolt://
neo4j_user: str = "neo4j"
neo4j_password: str = "password"  # Confirmed correct

# Alternative: Use environment variables
import os
os.environ['NEO4J_AUTH'] = 'neo4j/password'
```

### 2. MCP Tool Parameter Mismatch
**Problem**: server.py imports from wrong module
**Location**: `/libs/opsvi-mcp/opsvi_mcp/servers/knowledge/server.py` line 123
**Fix**:
```python
# Change from:
from .knowledge_tools_fixed import KnowledgeTools
# To:
from .mcp_knowledge_tools import KnowledgeTools
```

## 📊 Missing Embeddings (30 Entries)

### Affected Knowledge IDs
```
orchestration_parallel_sdlc_v2
orchestration_checkpoint_recovery_v2
orchestration_saga_compensation_v2
orchestration_agent_comm_v2
orchestration_git_worktree_v2
orchestration_resource_mgmt_v2
orchestration_agent_failure_v2
orchestration_sdlc_discovery_v2
orchestration_sdlc_development_v2
orchestration_sdlc_testing_v2
orchestration_validation_testing_v2
orchestration_kb_feedback_v2
kb_schema_extension_v2
micro_agent_swarm_v2
(and 16 more recent entries)
```

### Generation Script
```bash
# Run after fixing Neo4j auth
cd /home/opsvi/master_root
python scripts/generate_missing_embeddings.py
```

## 🎯 Implementation Phases

### Phase 1: Critical Fixes (Day 1)
- [ ] Fix Neo4j connection string (neo4j:// vs bolt://)
- [ ] Update MCP tool imports
- [ ] Restart MCP servers
- [ ] Verify authentication works

### Phase 2: Embedding Generation (Day 2)
- [ ] Run embedding generation for 30 entries
- [ ] Verify all entries have 384-dim vectors
- [ ] Create Neo4j vector index
- [ ] Test semantic search

### Phase 3: System Integration (Day 3-4)
- [ ] Connect all MCP tools to live Neo4j
- [ ] Enable hybrid search (text + semantic)
- [ ] Test knowledge clustering
- [ ] Implement relationship discovery

### Phase 4: Visualization (Day 5)
- [ ] Deploy Streamlit dashboard
- [ ] Setup Neo4j Bloom (if available)
- [ ] Create D3.js force graph
- [ ] Implement UMAP embedding visualization

### Phase 5: Federation (Week 2)
- [ ] Setup sync service
- [ ] Configure project hub
- [ ] Implement conflict resolution
- [ ] Enable cross-project learning

## 🔧 Technical Implementation Details

### Neo4j Connection Fix
```python
# Test connection script
from neo4j import GraphDatabase
import os

# Try multiple URIs
uris = [
    "neo4j://localhost:7687",
    "bolt://localhost:7687",
    "neo4j+s://localhost:7687",
    "neo4j+ssc://localhost:7687"
]

for uri in uris:
    try:
        driver = GraphDatabase.driver(
            uri,
            auth=("neo4j", "password"),
            encrypted=False,
            trust=True
        )
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            print(f"✅ Success with {uri}")
            break
    except Exception as e:
        print(f"❌ Failed {uri}: {e}")
```

### Embedding Generation Pipeline
```python
# Bulk embedding generation
from embedding_service import get_embedding_service
import asyncio

async def generate_all_embeddings():
    service = get_embedding_service()

    # Get entries without embeddings
    query = """
    MATCH (k:Knowledge)
    WHERE k.embedding IS NULL
    RETURN k.knowledge_id as id, k.content as content
    """

    # Process in batches of 10
    for batch in chunks(entries, 10):
        texts = [service.prepare_knowledge_text(e) for e in batch]
        embeddings = service.generate_embeddings_batch(texts)

        # Update Neo4j
        for entry, embedding in zip(batch, embeddings):
            update_query = service.embed_knowledge_query(
                entry['id'], embedding
            )
            # Execute update
```

### Semantic Search Implementation
```python
# Test semantic search
async def test_semantic_search():
    service = get_embedding_service()

    # Generate query embedding
    query = "How to handle parallel agent timeouts"
    query_embedding = service.generate_embedding(query)

    # Search using vector similarity
    search_query = service.semantic_search_query(
        query_embedding,
        limit=5,
        min_similarity=0.7
    )

    # Execute and display results
    results = await execute_cypher(search_query)
    for r in results:
        print(f"Score: {r['similarity']:.3f} - {r['content'][:100]}")
```

## 📈 Success Metrics

### Immediate (Day 1)
- Neo4j connection successful
- MCP tools operational
- Can query knowledge via CLI

### Short-term (Week 1)
- 100% entries have embeddings
- Semantic search returns relevant results
- Visualization dashboard live
- Response time <100ms

### Medium-term (Week 2)
- Federation sync working
- Cross-project knowledge sharing
- Auto-categorization active
- 90%+ search accuracy

### Long-term (Month 1)
- 40% reduction in development time
- 60% reduction in error rates
- 35% knowledge reuse rate
- Full production deployment

## 🛠️ Testing Commands

```bash
# Test Neo4j connection
echo "MATCH (k:Knowledge) RETURN count(k)" | cypher-shell -u neo4j -p password

# Test MCP knowledge tools
claude "Use knowledge_query tool to search for 'parallel execution'"

# Test embedding service
python -c "from embedding_service import get_embedding_service; s = get_embedding_service(); print(len(s.generate_embedding('test')))"

# Monitor real-time stats
watch -n 5 'echo "MATCH (k:Knowledge) RETURN count(k) as total, count(k.embedding) as with_embeddings" | cypher-shell -u neo4j -p password'
```

## 🚀 Quick Start Commands

```bash
# 1. Fix and restart services
cd /home/opsvi/master_root
./scripts/fix_neo4j_auth.sh
claude mcp restart

# 2. Generate embeddings
python scripts/generate_missing_embeddings.py

# 3. Test search
python -m apps.knowledge_system.knowledge_system query --query "agent orchestration"

# 4. Launch dashboard
streamlit run apps/knowledge_system/dashboard.py
```

## 📝 Validation Checklist

- [ ] Neo4j accepts connections
- [ ] All 49 entries readable
- [ ] 30 new embeddings generated
- [ ] Semantic search returns results
- [ ] MCP tools work without errors
- [ ] Dashboard displays metrics
- [ ] Federation sync initiates
- [ ] Cross-project query works

## Next Actions

1. **Immediate**: Execute Phase 1 fixes
2. **Today**: Complete embedding generation
3. **Tomorrow**: Deploy visualization
4. **This Week**: Enable federation
5. **Next Week**: Production deployment

---

*Generated: 2025-08-17 | Status: Action Required | Priority: CRITICAL*
