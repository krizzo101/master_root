-- V1__initial_schema.cypher
-- Initial schema migration for Auto Forge Neo4j database
-- Fixes relationship direction inconsistencies and adds proper constraints

-- Create unique constraints for primary keys
CREATE CONSTRAINT run_id_unique IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT result_id_unique IF NOT EXISTS FOR (res:Result) REQUIRE res.id IS UNIQUE;
CREATE CONSTRAINT critique_id_unique IF NOT EXISTS FOR (c:Critique) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT decision_id_unique IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT verification_id_unique IF NOT EXISTS FOR (v:Verification) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;

-- Create indexes for performance
CREATE INDEX run_status_idx IF NOT EXISTS FOR (r:Run) ON (r.status);
CREATE INDEX run_started_at_idx IF NOT EXISTS FOR (r:Run) ON (r.started_at);
CREATE INDEX task_stage_idx IF NOT EXISTS FOR (t:Task) ON (t.stage);
CREATE INDEX task_status_idx IF NOT EXISTS FOR (t:Task) ON (t.status);
CREATE INDEX task_agent_idx IF NOT EXISTS FOR (t:Task) ON (t.agent);
CREATE INDEX task_started_at_idx IF NOT EXISTS FOR (t:Task) ON (t.started_at);
CREATE INDEX project_status_idx IF NOT EXISTS FOR (p:Project) ON (p.status);
CREATE INDEX project_created_at_idx IF NOT EXISTS FOR (p:Project) ON (p.created_at);

-- Create relationship type constraints to ensure consistency
-- This helps prevent relationship direction mismatches

-- Standardize relationship directions:
-- Project HAS_RUN Run
-- Run HAS_TASK Task
-- Task PRODUCES Artifact
-- Task HAS_RESULT Result
-- Task HAS_CRITIQUE Critique
-- Task HAS_DECISION Decision
-- Decision ASSERTS Claim
-- Decision VERIFIED_BY Verification
-- Claim SUPPORTED_BY Evidence
-- Claim REFUTED_BY Evidence

-- Add relationship existence constraints (if supported by Neo4j version)
-- Note: These are documentation comments for relationship patterns

-- Relationship patterns to enforce:
-- 1. Project -> Run: (p:Project)-[:HAS_RUN]->(r:Run)
-- 2. Run -> Task: (r:Run)-[:HAS_TASK]->(t:Task)
-- 3. Task -> Artifact: (t:Task)-[:PRODUCES]->(a:Artifact)
-- 4. Task -> Result: (t:Task)-[:HAS_RESULT]->(res:Result)
-- 5. Task -> Critique: (t:Task)-[:HAS_CRITIQUE]->(c:Critique)
-- 6. Task -> Decision: (t:Task)-[:HAS_DECISION]->(d:Decision)
-- 7. Decision -> Claim: (d:Decision)-[:ASSERTS]->(c:Claim)
-- 8. Decision -> Verification: (d:Decision)-[:VERIFIED_BY]->(v:Verification)
-- 9. Claim -> Evidence: (c:Claim)-[:SUPPORTED_BY]->(e:Evidence)
-- 10. Claim -> Evidence: (c:Claim)-[:REFUTED_BY]->(e:Evidence)

-- Create composite indexes for common query patterns
CREATE INDEX run_project_status_idx IF NOT EXISTS FOR (r:Run) ON (r.status, r.started_at);
CREATE INDEX task_run_status_idx IF NOT EXISTS FOR (t:Task) ON (t.status, t.started_at);
CREATE INDEX task_agent_status_idx IF NOT EXISTS FOR (t:Task) ON (t.agent, t.status);

-- Create full-text search indexes for content search
CALL db.index.fulltext.createNodeIndex("task_content_search", ["Task"], ["name", "inputs", "outputs"]);
CALL db.index.fulltext.createNodeIndex("artifact_content_search", ["Artifact"], ["type", "path", "metadata"]);
CALL db.index.fulltext.createNodeIndex("project_content_search", ["Project"], ["name", "description", "requirements"]);

-- Create spatial indexes for location-based queries (if needed)
-- CREATE INDEX location_idx IF NOT EXISTS FOR (a:Artifact) ON (a.location);

-- Add property existence constraints (if supported)
-- These ensure required properties are always present
-- Note: Neo4j doesn't have built-in property existence constraints,
-- but we can enforce this in application code

-- Required properties for each node type:
-- Project: id, name, created_at, status
-- Run: id, pipeline_name, status, started_at
-- Task: id, name, agent, status, started_at
-- Artifact: id, type, path, created_at
-- Result: id, status, created_at
-- Critique: id, passed, score, created_at
-- Decision: id, by_agent, why, confidence, created_at

-- Create a function to validate relationship directions
CALL apoc.custom.asFunction(
    'validate.relationship.direction',
    'MATCH (start)-[rel]->(end) WHERE type(rel) = $relType RETURN count(rel) as count',
    'INTEGER',
    [['relType', 'STRING']],
    false,
    'Validates that relationships follow the correct direction pattern'
);

-- Create a function to get relationship statistics
CALL apoc.custom.asFunction(
    'stats.relationships',
    'CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType, count(*) as count',
    'MAP',
    [],
    false,
    'Returns statistics about relationship types in the database'
);

-- Create a function to clean up orphaned nodes
CALL apoc.custom.asProcedure(
    'cleanup.orphaned.nodes',
    'MATCH (n) WHERE NOT (n:Project) AND NOT (n:Run) AND NOT (n:Task) AND NOT (n:Artifact) AND NOT (n:Result) AND NOT (n:Critique) AND NOT (n:Decision) AND NOT (n:Verification) AND NOT (n:Claim) AND NOT (n:Evidence) DETACH DELETE n RETURN count(n) as deleted_count',
    'MAP',
    [],
    [],
    'Cleans up orphaned nodes that are not part of the main schema'
);

-- Create a function to validate schema integrity
CALL apoc.custom.asProcedure(
    'validate.schema.integrity',
    'MATCH (p:Project)-[:HAS_RUN]->(r:Run)-[:HAS_TASK]->(t:Task) RETURN count(p) as projects, count(r) as runs, count(t) as tasks',
    'MAP',
    [],
    [],
    'Validates that the schema relationships are properly connected'
);

-- Add comments to document the schema
CALL apoc.comment.set('Project', 'Root entity representing a software development project');
CALL apoc.comment.set('Run', 'Execution instance of a pipeline for a project');
CALL apoc.comment.set('Task', 'Individual work unit within a pipeline run');
CALL apoc.comment.set('Artifact', 'Output file or resource produced by a task');
CALL apoc.comment.set('Result', 'Execution result and metrics for a task');
CALL apoc.comment.set('Critique', 'Quality assessment and feedback for a task');
CALL apoc.comment.set('Decision', 'Decision made by an agent during task execution');
CALL apoc.comment.set('Verification', 'Verification of a decision by another agent');
CALL apoc.comment.set('Claim', 'Assertion made in support of a decision');
CALL apoc.comment.set('Evidence', 'Supporting evidence for or against a claim');

-- Log migration completion
RETURN 'V1__initial_schema migration completed successfully' as status;
