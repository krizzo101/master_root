-- Neo4j Schema for Autonomous Software Factory
-- This file contains all constraints and indexes for the graph database

-- Constraints for unique identifiers
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT run_id_unique IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE;

-- Note: Dict fields are stored as JSON strings with _json suffix:
-- Project.metadata_json, Run.metadata_json, Run.inputs_json, etc.
CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT result_id_unique IF NOT EXISTS FOR (r:Result) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT critique_id_unique IF NOT EXISTS FOR (c:Critique) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT decision_id_unique IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;

-- Constraints for artifact hash uniqueness
CREATE CONSTRAINT artifact_hash_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.hash IS UNIQUE;

-- Indexes for common query patterns
CREATE INDEX project_name_index IF NOT EXISTS FOR (p:Project) ON (p.name);
CREATE INDEX project_status_index IF NOT EXISTS FOR (p:Project) ON (p.status);
CREATE INDEX project_created_at_index IF NOT EXISTS FOR (p:Project) ON (p.created_at);

CREATE INDEX run_project_id_index IF NOT EXISTS FOR (r:Run) ON (r.project_id);
CREATE INDEX run_status_index IF NOT EXISTS FOR (r:Run) ON (r.status);
CREATE INDEX run_started_at_index IF NOT EXISTS FOR (r:Run) ON (r.started_at);
CREATE INDEX run_pipeline_name_index IF NOT EXISTS FOR (r:Run) ON (r.pipeline_name);

CREATE INDEX task_run_id_index IF NOT EXISTS FOR (t:Task) ON (t.run_id);
CREATE INDEX task_agent_index IF NOT EXISTS FOR (t:Task) ON (t.agent);
CREATE INDEX task_status_index IF NOT EXISTS FOR (t:Task) ON (t.status);
CREATE INDEX task_queue_index IF NOT EXISTS FOR (t:Task) ON (t.queue);
CREATE INDEX task_priority_index IF NOT EXISTS FOR (t:Task) ON (t.priority);
CREATE INDEX task_created_at_index IF NOT EXISTS FOR (t:Task) ON (t.created_at);

CREATE INDEX artifact_task_id_index IF NOT EXISTS FOR (a:Artifact) ON (a.task_id);
CREATE INDEX artifact_type_index IF NOT EXISTS FOR (a:Artifact) ON (a.type);
CREATE INDEX artifact_path_index IF NOT EXISTS FOR (a:Artifact) ON (a.path);

CREATE INDEX result_task_id_index IF NOT EXISTS FOR (r:Result) ON (r.task_id);
CREATE INDEX result_status_index IF NOT EXISTS FOR (r:Result) ON (r.status);
CREATE INDEX result_score_index IF NOT EXISTS FOR (r:Result) ON (r.score);

CREATE INDEX critique_task_id_index IF NOT EXISTS FOR (c:Critique) ON (c.task_id);
CREATE INDEX critique_agent_id_index IF NOT EXISTS FOR (c:Critique) ON (c.agent_id);
CREATE INDEX critique_score_index IF NOT EXISTS FOR (c:Critique) ON (c.score);

CREATE INDEX decision_task_id_index IF NOT EXISTS FOR (d:Decision) ON (d.task_id);
CREATE INDEX decision_agent_index IF NOT EXISTS FOR (d:Decision) ON (d.by_agent);
CREATE INDEX decision_confidence_index IF NOT EXISTS FOR (d:Decision) ON (d.confidence);

-- Composite indexes for complex queries
CREATE INDEX task_agent_status_index IF NOT EXISTS FOR (t:Task) ON (t.agent, t.status);
CREATE INDEX task_run_status_index IF NOT EXISTS FOR (t:Task) ON (t.run_id, t.status);
CREATE INDEX run_project_status_index IF NOT EXISTS FOR (r:Run) ON (r.project_id, r.status);

-- Text search indexes (commented out - APOC not properly loaded)
-- CALL db.index.fulltext.createNodeIndex("project_search", ["Project"], ["name", "description", "requirements"]);
-- CALL db.index.fulltext.createNodeIndex("task_search", ["Task"], ["name", "inputs", "outputs"]);
-- CALL db.index.fulltext.createNodeIndex("decision_search", ["Decision"], ["why", "params"]);

-- Relationship indexes for performance (commented out - syntax not supported in Neo4j 5.x)
-- CREATE INDEX rel_part_of_index IF NOT EXISTS FOR ()-[r:PART_OF]-() ON (r);
-- CREATE INDEX rel_generates_index IF NOT EXISTS FOR ()-[r:GENERATES]-() ON (r);
-- CREATE INDEX rel_resulted_in_index IF NOT EXISTS FOR ()-[r:RESULTED_IN]-() ON (r);
-- CREATE INDEX rel_evaluated_by_index IF NOT EXISTS FOR ()-[r:EVALUATED_BY]-() ON (r);
-- CREATE INDEX rel_for_task_index IF NOT EXISTS FOR ()-[r:FOR_TASK]-() ON (r);
-- CREATE INDEX rel_of_project_index IF NOT EXISTS FOR ()-[r:OF_PROJECT]-() ON (r);

-- Show all constraints and indexes
SHOW CONSTRAINTS;
SHOW INDEXES;
