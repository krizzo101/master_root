// Knowledge Tool Schema Initialization

// Create constraints for unique IDs
CREATE CONSTRAINT knowledge_id_unique IF NOT EXISTS
FOR (k:Knowledge) REQUIRE k.knowledge_id IS UNIQUE;

// Create indexes for performance
CREATE INDEX knowledge_type_index IF NOT EXISTS
FOR (k:Knowledge) ON (k.knowledge_type);

CREATE INDEX knowledge_confidence_index IF NOT EXISTS
FOR (k:Knowledge) ON (k.confidence_score);

CREATE INDEX knowledge_timestamp_index IF NOT EXISTS
FOR (k:Knowledge) ON (k.created_at);

CREATE INDEX knowledge_deprecated_index IF NOT EXISTS
FOR (k:Knowledge) ON (k.deprecated);

// Create fulltext index for content search
CREATE FULLTEXT INDEX knowledge_content_search IF NOT EXISTS
FOR (k:Knowledge) ON EACH [k.content, k.summary, k.tags];

// Create initial knowledge types
MERGE (t:KnowledgeType {name: 'ERROR_SOLUTION'})
SET t.description = 'Solutions to errors and exceptions';

MERGE (t:KnowledgeType {name: 'CODE_PATTERN'})
SET t.description = 'Reusable code patterns and templates';

MERGE (t:KnowledgeType {name: 'WORKFLOW'})
SET t.description = 'Workflow and process definitions';

MERGE (t:KnowledgeType {name: 'USER_PREFERENCE'})
SET t.description = 'User-specific preferences and settings';

MERGE (t:KnowledgeType {name: 'CONTEXT_PATTERN'})
SET t.description = 'Context and environment patterns';

MERGE (t:KnowledgeType {name: 'TOOL_USAGE'})
SET t.description = 'Tool usage patterns and examples';

// Create relationship types structure
MERGE (r:RelationType {name: 'SIMILAR_TO'})
SET r.description = 'Indicates similarity between knowledge entries';

MERGE (r:RelationType {name: 'DERIVED_FROM'})
SET r.description = 'Shows derivation or evolution of knowledge';

MERGE (r:RelationType {name: 'REQUIRES'})
SET r.description = 'Indicates dependencies between knowledge';

MERGE (r:RelationType {name: 'CONTRADICTS'})
SET r.description = 'Marks contradicting knowledge entries';

MERGE (r:RelationType {name: 'ENHANCES'})
SET r.description = 'Shows enhancement relationships';

MERGE (r:RelationType {name: 'RELATED_TO'})
SET r.description = 'General relationship between entries';

MERGE (r:RelationType {name: 'SUPERSEDES'})
SET r.description = 'Indicates newer version superseding older';

// Create initial system knowledge entry
CREATE (k:Knowledge {
  knowledge_id: 'system-init-001',
  knowledge_type: 'TOOL_USAGE',
  content: 'Knowledge base initialized with Docker Neo4j container. Configuration: Neo4j 5.15.0 with APOC plugin, accessible at bolt://localhost:7687 with credentials neo4j/password. Embedding service at http://localhost:8000 using all-MiniLM-L6-v2 model.',
  summary: 'Knowledge base Docker initialization',
  tags: ['system', 'initialization', 'docker', 'neo4j'],
  confidence_score: 1.0,
  created_at: datetime(),
  updated_at: datetime(),
  deprecated: false,
  usage_count: 0,
  success_count: 0,
  failure_count: 0,
  success_rate: 0.0,
  quality_score: 1.0,
  version: 1
})

RETURN 'Schema initialization complete!' as message;
