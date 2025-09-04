# pgvector Semantic Search Integration

Complete semantic search capabilities for the unified context system using PostgreSQL pgvector extension and embedding service.

## 🚀 Quick Start

```bash
# Start the complete system
./start_pgvector_system.sh start

# Check system status
./start_pgvector_system.sh status

# Run integration tests
./start_pgvector_system.sh test

# Stop the system
./start_pgvector_system.sh stop
```

## 📋 Overview

This integration provides:

- **Semantic Search**: Vector-based similarity search across code, chat, and context data
- **Hybrid Search**: Combines text and vector similarity for optimal results
- **Code Intelligence**: Specialized search for code patterns and structures
- **Real-time Embedding**: On-demand embedding generation via REST API
- **Performance Monitoring**: Comprehensive benchmarking and analytics

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │  Embedding      │    │   PostgreSQL    │
│                 │    │  Service        │    │   + pgvector    │
│ - project-ctx   │◄───┤  (localhost:    │◄───┤                 │
│ - chat system   │    │   8001)         │    │ - Vector cols   │
│ - monitoring    │    │                 │    │ - HNSW indexes  │
│                 │    │ - Sentence-T    │    │ - Search funcs  │
└─────────────────┘    │ - OpenAI API    │    └─────────────────┘
                       └─────────────────┘
```

## 🛠️ Components

### 1. PostgreSQL with pgvector

- **Location**: `docker-compose.postgres.yml`
- **Extensions**: TimescaleDB + pgvector
- **Vector Columns**: 1536-dimensional embeddings
- **Indexes**: HNSW for fast similarity search

### 2. Embedding Service

- **Location**: `apps/embedding-service/`
- **Port**: localhost:8001
- **Models**:
  - Sentence Transformers (local, fast)
  - OpenAI text-embedding-ada-002 (optional)
- **API**: REST endpoints for embedding generation

### 3. Vector Search Integration

- **Location**: `apps/project-context/src/project_context/core/vector_search.py`
- **Features**:
  - Semantic search across all context types
  - Code-specific search with programming language awareness
  - Hybrid text + vector search
  - Similarity clustering and analytics

### 4. Database Schema Extensions

- **Location**: `init-scripts/02-setup-pgvector.sql`
- **Additions**:
  - Vector columns in `context_items` and `code_elements`
  - Search functions (semantic, code, hybrid)
  - Performance indexes and views

## 📊 Database Schema Changes

### New Columns Added

```sql
-- context_items table
ALTER TABLE context_items ADD COLUMN embedding vector(1536);
ALTER TABLE context_items ADD COLUMN embedding_model VARCHAR(100);
ALTER TABLE context_items ADD COLUMN embedding_generated_at TIMESTAMPTZ;

-- code_elements table
ALTER TABLE code_elements ADD COLUMN embedding vector(1536);
ALTER TABLE code_elements ADD COLUMN embedding_model VARCHAR(100);
ALTER TABLE code_elements ADD COLUMN embedding_generated_at TIMESTAMPTZ;
```

### New Functions

- `find_similar_context(query_embedding, threshold, max_results, filters...)`
- `find_similar_code(query_embedding, threshold, max_results, filters...)`
- `hybrid_context_search(text_query, vector_query, weights, ...)`
- `get_items_needing_embeddings(batch_size, source_filter)`
- `update_context_embedding(item_id, embedding, model)`
- `find_content_clusters(threshold, min_size)`

### Performance Indexes

```sql
-- HNSW index for fast vector similarity search
CREATE INDEX idx_context_embedding_hnsw
ON context_items USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## 🔌 API Endpoints

### Embedding Service (localhost:8001)

```bash
# Health check
GET /health

# Available models
GET /models

# Generate single embedding
POST /embed
{
  "text": "your text here",
  "model": "sentence-transformers"
}

# Generate batch embeddings
POST /embed/batch
{
  "texts": ["text 1", "text 2"],
  "model": "sentence-transformers"
}

# Semantic search
POST /search/semantic
{
  "query": "database error handling",
  "similarity_threshold": 0.7,
  "max_results": 10
}

# Code search
POST /search/code
{
  "query": "async function database connection",
  "similarity_threshold": 0.7,
  "element_type_filter": "function"
}

# Hybrid search
POST /search/hybrid
{
  "query": "user authentication",
  "text_weight": 0.3,
  "vector_weight": 0.7,
  "max_results": 10
}
```

## 💻 Usage Examples

### Python Integration

```python
from project_context.core.vector_search import VectorSearchClient

# Search for related context
async with VectorSearchClient() as client:
    results = await client.semantic_search(
        "handle database connection errors",
        max_results=10
    )

    for result in results:
        print(f"{result.title} (similarity: {result.similarity:.3f})")
```

### Direct SQL Usage

```sql
-- Find similar context items
SELECT * FROM find_similar_context(
    '[0.1, 0.2, ...]'::vector(1536),  -- query embedding
    0.7,                               -- similarity threshold
    10                                 -- max results
);

-- Hybrid search with text + vector
SELECT * FROM hybrid_context_search(
    'error handling',                  -- text query
    '[0.1, 0.2, ...]'::vector(1536),  -- vector query
    0.3,                               -- text weight
    0.7,                               -- vector weight
    0.5,                               -- min similarity
    10                                 -- max results
);
```

### REST API Usage

```bash
# Search for similar content
curl -X POST http://localhost:8001/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "implement user authentication",
    "similarity_threshold": 0.7,
    "max_results": 5
  }'
```

## ⚡ Performance

### Benchmarking

Run comprehensive benchmarks:

```bash
# Run all performance tests
python3 apps/project-context/benchmark_vector_search.py

# Results saved to: vector_search_benchmark_YYYYMMDD_HHMMSS.json
```

### Expected Performance

- **Search latency**: < 100ms for typical queries
- **Throughput**: > 50 queries/second
- **Index build**: ~1-2 minutes for 100K items
- **Memory usage**: ~2GB for 100K embeddings

### Optimization Tips

1. **HNSW Parameters**:
   - `m=16`: Good balance of speed/recall
   - `ef_construction=64`: Build quality
   - Increase for better recall, decrease for speed

2. **Similarity Thresholds**:
   - `0.8+`: Very similar content
   - `0.7`: Good similarity
   - `0.5`: Loose similarity
   - `< 0.5`: May include noise

3. **Batch Processing**:
   - Process embeddings in batches of 100-1000
   - Use background tasks for large datasets
   - Monitor memory usage during batch operations

## 🧪 Testing

### Integration Tests

```bash
# Complete system validation
python3 test_pgvector_integration.py

# Expected: All tests pass with detailed performance metrics
```

### Manual Verification

```bash
# 1. Check pgvector extension
psql -h localhost -U opsvi -d unified_context \
  -c "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');"

# 2. Test embedding service
curl http://localhost:8001/health

# 3. Test search function
psql -h localhost -U opsvi -d unified_context \
  -c "SELECT COUNT(*) FROM context_items WHERE embedding IS NOT NULL;"
```

## 🔧 Configuration

### Environment Variables

```bash
# Database connection
DATABASE_URL=postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context

# Embedding service
EMBEDDING_SERVICE_URL=http://localhost:8001
OPENAI_API_KEY=your_openai_key_here  # Optional

# Performance tuning
PGVECTOR_HNSW_M=16
PGVECTOR_HNSW_EF_CONSTRUCTION=64
```

### Docker Customization

Edit `docker-compose.postgres.yml` and `docker-compose.embedding.yml` for:

- Memory limits
- CPU allocation
- Volume mounts
- Network configuration

## 📈 Monitoring

### System Health

```bash
# Service status
./start_pgvector_system.sh status

# Embedding coverage
curl http://localhost:8001/stats

# Database performance
psql -h localhost -U opsvi -d unified_context -c "SELECT * FROM embedding_stats;"
```

### Performance Metrics

- **Search latency**: Monitor query execution times
- **Index size**: Track vector index disk usage
- **Memory usage**: Monitor RAM consumption
- **Error rates**: Watch for embedding generation failures

### Alerting

Set up monitoring for:

- Embedding service downtime
- Database connection issues
- High search latency (>500ms)
- Low embedding coverage (<80%)

## 🚨 Troubleshooting

### Common Issues

1. **pgvector Extension Missing**
   ```bash
   # Rebuild PostgreSQL container
   docker-compose -f docker-compose.postgres.yml down -v
   docker-compose -f docker-compose.postgres.yml up -d --build
   ```

2. **Embedding Service Not Starting**
   ```bash
   # Check logs
   docker-compose -f docker-compose.embedding.yml logs embedding-service

   # Common fixes:
   # - Install sentence-transformers
   # - Check Python dependencies
   # - Verify port availability
   ```

3. **Poor Search Results**
   ```bash
   # Check embedding coverage
   curl http://localhost:8001/stats

   # Regenerate embeddings
   curl -X POST http://localhost:8001/embeddings/update-batch
   ```

4. **Slow Search Performance**
   ```sql
   -- Check index usage
   EXPLAIN (ANALYZE, BUFFERS)
   SELECT * FROM find_similar_context('[...]'::vector(1536), 0.7, 10);

   -- Rebuild indexes if needed
   REINDEX INDEX idx_context_embedding_hnsw;
   ```

### Debug Mode

```bash
# Enable verbose logging
export PGVECTOR_DEBUG=1
export EMBEDDING_LOG_LEVEL=DEBUG

# Run tests with debug info
python3 test_pgvector_integration.py --verbose
```

## 🔮 Advanced Features

### Custom Embedding Models

Add support for domain-specific models:

```python
# In embedding_service.py
class CustomEmbeddingModel:
    def __init__(self, model_path):
        self.model = load_custom_model(model_path)

    def encode(self, texts):
        return self.model.encode(texts)
```

### Multi-modal Embeddings

Extend for code + documentation + images:

```sql
-- Add specialized columns
ALTER TABLE context_items ADD COLUMN code_embedding vector(768);
ALTER TABLE context_items ADD COLUMN doc_embedding vector(384);
ALTER TABLE context_items ADD COLUMN image_embedding vector(512);
```

### Real-time Updates

Set up change data capture:

```python
# Trigger embedding updates on data changes
@app.on_event("context_item_updated")
async def update_embedding(item_id):
    # Generate new embedding
    # Update vector index
    pass
```

## 📚 References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)
- [Sentence Transformers](https://www.sbert.net/)
- [PostgreSQL Vector Operations](https://github.com/pgvector/pgvector#querying)

## 🤝 Contributing

1. Follow existing code patterns
2. Add tests for new functionality
3. Update benchmarks for performance changes
4. Document API changes

## 📄 License

Same as the main project license.

---

**Ready for production use!** 🎉

For support, check the troubleshooting section or run the integration tests to validate your setup.
