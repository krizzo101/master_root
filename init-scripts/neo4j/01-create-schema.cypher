// ============================================
// UNIFIED CONTEXT SYSTEM - NEO4J SCHEMA
// Initialize graph database for relationships
// ============================================

// Create constraints for unique identifiers
CREATE CONSTRAINT knowledge_id_unique IF NOT EXISTS FOR (k:Knowledge) REQUIRE k.knowledge_id IS UNIQUE;
CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.session_id IS UNIQUE;
CREATE CONSTRAINT code_element_unique IF NOT EXISTS FOR (c:CodeElement) REQUIRE c.element_id IS UNIQUE;
CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE;
CREATE CONSTRAINT error_id_unique IF NOT EXISTS FOR (e:Error) REQUIRE e.error_id IS UNIQUE;
CREATE CONSTRAINT container_id_unique IF NOT EXISTS FOR (cont:Container) REQUIRE cont.container_id IS UNIQUE;
CREATE CONSTRAINT agent_token_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.agent_token IS UNIQUE;

// Create indexes for performance
CREATE INDEX knowledge_content IF NOT EXISTS FOR (k:Knowledge) ON (k.content);
CREATE INDEX session_timestamp IF NOT EXISTS FOR (s:Session) ON (s.started_at);
CREATE INDEX code_element_name IF NOT EXISTS FOR (c:CodeElement) ON (c.name);
CREATE INDEX code_element_type IF NOT EXISTS FOR (c:CodeElement) ON (c.element_type);
CREATE INDEX file_language IF NOT EXISTS FOR (f:File) ON (f.language);
CREATE INDEX error_type IF NOT EXISTS FOR (e:Error) ON (e.type);
CREATE INDEX agent_type IF NOT EXISTS FOR (a:Agent) ON (a.agent_type);

// Create full-text search indexes
CALL db.index.fulltext.createNodeIndex(
    "knowledge_search",
    ["Knowledge"],
    ["content", "summary"]
) YIELD name RETURN name;

CALL db.index.fulltext.createNodeIndex(
    "code_search",
    ["CodeElement"],
    ["name", "docstring", "signature"]
) YIELD name RETURN name;

CALL db.index.fulltext.createNodeIndex(
    "file_search",
    ["File"],
    ["path", "name"]
) YIELD name RETURN name;
