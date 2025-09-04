-- ============================================
-- PGVECTOR EXTENSION SETUP FOR UNIFIED CONTEXT
-- ============================================

-- Create the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- ADD VECTOR COLUMNS TO EXISTING TABLES
-- ============================================

-- Add embedding column to context_items (1536 dimensions for OpenAI text-embedding-ada-002)
-- Also support smaller embeddings (384 for sentence-transformers)
ALTER TABLE context_items
ADD COLUMN IF NOT EXISTS embedding vector(1536),
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100),
ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMPTZ;

-- Add embedding column to code_elements
ALTER TABLE code_elements
ADD COLUMN IF NOT EXISTS embedding vector(1536),
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100),
ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMPTZ;

-- ============================================
-- CREATE VECTOR INDEXES FOR FAST SIMILARITY SEARCH
-- ============================================

-- HNSW index for context_items (best for high-recall scenarios)
CREATE INDEX IF NOT EXISTS idx_context_embedding_hnsw
ON context_items
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat index for context_items (faster build, good for most use cases)
-- Commenting out as we'll primarily use HNSW, but keeping for reference
-- CREATE INDEX IF NOT EXISTS idx_context_embedding_ivf
-- ON context_items
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- HNSW index for code_elements
CREATE INDEX IF NOT EXISTS idx_code_embedding_hnsw
ON code_elements
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================
-- SEMANTIC SEARCH FUNCTIONS
-- ============================================

-- Function to find similar context items
CREATE OR REPLACE FUNCTION find_similar_context(
    query_embedding vector(1536),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10,
    source_filter TEXT DEFAULT NULL,
    entity_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    source_type VARCHAR(50),
    entity_type VARCHAR(100),
    title TEXT,
    content TEXT,
    file_path TEXT,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        c.id,
        c.source_type,
        c.entity_type,
        c.title,
        c.content,
        c.file_path,
        (1 - (c.embedding <=> query_embedding)) AS similarity
    FROM context_items c
    WHERE c.embedding IS NOT NULL
      AND (1 - (c.embedding <=> query_embedding)) >= similarity_threshold
      AND (source_filter IS NULL OR c.source_type = source_filter)
      AND (entity_filter IS NULL OR c.entity_type = entity_filter)
    ORDER BY c.embedding <=> query_embedding
    LIMIT max_results;
$$;

-- Function to find similar code elements
CREATE OR REPLACE FUNCTION find_similar_code(
    query_embedding vector(1536),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10,
    element_type_filter TEXT DEFAULT NULL,
    language_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    file_path TEXT,
    element_type VARCHAR(50),
    element_name VARCHAR(255),
    signature TEXT,
    docstring TEXT,
    language VARCHAR(50),
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        ce.id,
        ce.file_path,
        ce.element_type,
        ce.element_name,
        ce.signature,
        ce.docstring,
        ce.language,
        (1 - (ce.embedding <=> query_embedding)) AS similarity
    FROM code_elements ce
    WHERE ce.embedding IS NOT NULL
      AND (1 - (ce.embedding <=> query_embedding)) >= similarity_threshold
      AND (element_type_filter IS NULL OR ce.element_type = element_type_filter)
      AND (language_filter IS NULL OR ce.language = language_filter)
    ORDER BY ce.embedding <=> query_embedding
    LIMIT max_results;
$$;

-- Function for hybrid search (combines text and vector similarity)
CREATE OR REPLACE FUNCTION hybrid_context_search(
    query_text TEXT,
    query_embedding vector(1536),
    text_weight FLOAT DEFAULT 0.3,
    vector_weight FLOAT DEFAULT 0.7,
    similarity_threshold FLOAT DEFAULT 0.5,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    source_type VARCHAR(50),
    entity_type VARCHAR(100),
    title TEXT,
    content TEXT,
    file_path TEXT,
    text_score FLOAT,
    vector_score FLOAT,
    combined_score FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        c.id,
        c.source_type,
        c.entity_type,
        c.title,
        c.content,
        c.file_path,
        ts_rank(c.search_vector, plainto_tsquery('english', query_text)) AS text_score,
        (1 - (c.embedding <=> query_embedding)) AS vector_score,
        (text_weight * ts_rank(c.search_vector, plainto_tsquery('english', query_text))) +
        (vector_weight * (1 - (c.embedding <=> query_embedding))) AS combined_score
    FROM context_items c
    WHERE c.embedding IS NOT NULL
      AND (
          c.search_vector @@ plainto_tsquery('english', query_text)
          OR (1 - (c.embedding <=> query_embedding)) >= similarity_threshold
      )
    ORDER BY combined_score DESC
    LIMIT max_results;
$$;

-- ============================================
-- BATCH EMBEDDING UPDATE FUNCTIONS
-- ============================================

-- Function to get items that need embeddings
CREATE OR REPLACE FUNCTION get_items_needing_embeddings(
    batch_size INTEGER DEFAULT 100,
    source_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    source_type VARCHAR(50),
    entity_type VARCHAR(100),
    content TEXT,
    title TEXT,
    summary TEXT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        c.id,
        c.source_type,
        c.entity_type,
        c.content,
        c.title,
        c.summary
    FROM context_items c
    WHERE c.embedding IS NULL
      AND c.content IS NOT NULL
      AND length(c.content) > 10
      AND (source_filter IS NULL OR c.source_type = source_filter)
    ORDER BY c.ingested_at DESC
    LIMIT batch_size;
$$;

-- Function to update embedding for a context item
CREATE OR REPLACE FUNCTION update_context_embedding(
    item_id UUID,
    new_embedding vector(1536),
    model_name TEXT DEFAULT 'text-embedding-ada-002'
)
RETURNS BOOLEAN
LANGUAGE SQL
AS $$
    UPDATE context_items
    SET
        embedding = new_embedding,
        embedding_model = model_name,
        embedding_generated_at = NOW()
    WHERE id = item_id;

    SELECT FOUND;
$$;

-- ============================================
-- VECTOR CLUSTERING AND ANALYTICS
-- ============================================

-- Function to find content clusters using k-means style grouping
CREATE OR REPLACE FUNCTION find_content_clusters(
    cluster_threshold FLOAT DEFAULT 0.8,
    min_cluster_size INTEGER DEFAULT 3
)
RETURNS TABLE (
    cluster_id INTEGER,
    item_count INTEGER,
    avg_similarity FLOAT,
    representative_title TEXT,
    source_types TEXT[]
)
LANGUAGE SQL STABLE
AS $$
    WITH similarity_pairs AS (
        SELECT
            c1.id as id1,
            c2.id as id2,
            c1.title as title1,
            c2.title as title2,
            c1.source_type as source1,
            c2.source_type as source2,
            (1 - (c1.embedding <=> c2.embedding)) AS similarity
        FROM context_items c1
        CROSS JOIN context_items c2
        WHERE c1.id < c2.id
          AND c1.embedding IS NOT NULL
          AND c2.embedding IS NOT NULL
          AND (1 - (c1.embedding <=> c2.embedding)) >= cluster_threshold
    ),
    clusters AS (
        SELECT
            ROW_NUMBER() OVER() as cluster_id,
            COUNT(*) as item_count,
            AVG(similarity) as avg_similarity,
            MIN(title1) as representative_title,
            array_agg(DISTINCT source1) || array_agg(DISTINCT source2) as source_types
        FROM similarity_pairs
        GROUP BY id1, id2
        HAVING COUNT(*) >= min_cluster_size
    )
    SELECT * FROM clusters
    ORDER BY item_count DESC, avg_similarity DESC;
$$;

-- ============================================
-- PERFORMANCE MONITORING
-- ============================================

-- View for embedding statistics
CREATE OR REPLACE VIEW embedding_stats AS
SELECT
    source_type,
    COUNT(*) as total_items,
    COUNT(embedding) as items_with_embeddings,
    ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) as embedding_coverage_pct,
    COUNT(DISTINCT embedding_model) as distinct_models,
    MAX(embedding_generated_at) as latest_embedding
FROM context_items
GROUP BY source_type
ORDER BY total_items DESC;

-- ============================================
-- GRANTS AND PERMISSIONS
-- ============================================

-- Grant execute permissions on new functions
GRANT EXECUTE ON FUNCTION find_similar_context TO opsvi;
GRANT EXECUTE ON FUNCTION find_similar_code TO opsvi;
GRANT EXECUTE ON FUNCTION hybrid_context_search TO opsvi;
GRANT EXECUTE ON FUNCTION get_items_needing_embeddings TO opsvi;
GRANT EXECUTE ON FUNCTION update_context_embedding TO opsvi;
GRANT EXECUTE ON FUNCTION find_content_clusters TO opsvi;

-- Grant select on view
GRANT SELECT ON embedding_stats TO opsvi;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension setup completed successfully!';
    RAISE NOTICE 'Added vector columns to context_items and code_elements tables';
    RAISE NOTICE 'Created HNSW indexes for fast similarity search';
    RAISE NOTICE 'Added semantic search functions:';
    RAISE NOTICE '  - find_similar_context()';
    RAISE NOTICE '  - find_similar_code()';
    RAISE NOTICE '  - hybrid_context_search()';
    RAISE NOTICE '  - get_items_needing_embeddings()';
    RAISE NOTICE '  - update_context_embedding()';
    RAISE NOTICE '  - find_content_clusters()';
    RAISE NOTICE 'Ready for semantic search operations!';
END $$;
