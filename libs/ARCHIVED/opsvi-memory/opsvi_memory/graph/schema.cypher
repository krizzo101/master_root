// Neo4j Schema for Software Factory Graph Database
// This file contains the schema definition and constraints for the graph database

// Create constraints for unique properties
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT run_id_unique IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT result_id_unique IF NOT EXISTS FOR (res:Result) REQUIRE res.id IS UNIQUE;
CREATE CONSTRAINT critique_id_unique IF NOT EXISTS FOR (c:Critique) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT agent_name_unique IF NOT EXISTS FOR (agent:Agent) REQUIRE agent.name IS UNIQUE;

// Create indexes for better query performance
CREATE INDEX project_name_index IF NOT EXISTS FOR (p:Project) ON (p.name);
CREATE INDEX project_status_index IF NOT EXISTS FOR (p:Project) ON (p.status);
CREATE INDEX run_project_id_index IF NOT EXISTS FOR (r:Run) ON (r.project_id);
CREATE INDEX run_status_index IF NOT EXISTS FOR (r:Run) ON (r.status);
CREATE INDEX task_project_id_index IF NOT EXISTS FOR (t:Task) ON (t.project_id);
CREATE INDEX task_run_id_index IF NOT EXISTS FOR (t:Task) ON (t.run_id);
CREATE INDEX task_status_index IF NOT EXISTS FOR (t:Task) ON (t.status);
CREATE INDEX task_type_index IF NOT EXISTS FOR (t:Task) ON (t.task_type);
CREATE INDEX task_created_at_index IF NOT EXISTS FOR (t:Task) ON (t.created_at);
CREATE INDEX artifact_task_id_index IF NOT EXISTS FOR (a:Artifact) ON (a.task_id);
CREATE INDEX artifact_type_index IF NOT EXISTS FOR (a:Artifact) ON (a.artifact_type);
CREATE INDEX result_task_id_index IF NOT EXISTS FOR (res:Result) ON (res.task_id);
CREATE INDEX critique_task_id_index IF NOT EXISTS FOR (c:Critique) ON (c.task_id);
CREATE INDEX critique_score_index IF NOT EXISTS FOR (c:Critique) ON (c.overall_score);

// Node Labels and Properties Schema:

// Project Node
// Labels: Project
// Properties:
//   - id: String (UUID)
//   - name: String
//   - description: String
//   - request: String
//   - status: String
//   - created_at: DateTime
//   - updated_at: DateTime

// Run Node
// Labels: Run
// Properties:
//   - id: String (UUID)
//   - project_id: String (UUID)
//   - pipeline_name: String
//   - status: String
//   - current_task: String
//   - started_at: DateTime
//   - completed_at: DateTime
//   - total_tasks: Integer
//   - completed_tasks: Integer
//   - failed_tasks: Integer
//   - total_tokens: Integer
//   - total_cost_usd: Float

// Task Node
// Labels: Task
// Properties:
//   - id: String (UUID)
//   - name: String
//   - task_type: String
//   - status: String
//   - priority: String
//   - project_id: String (UUID)
//   - run_id: String (UUID)
//   - parent_task_id: String (UUID)
//   - input_data: Map
//   - output_data: Map
//   - error_message: String
//   - created_at: DateTime
//   - started_at: DateTime
//   - completed_at: DateTime
//   - tokens_used: Integer
//   - latency_ms: Integer
//   - cost_usd: Float
//   - memory_mb: Float
//   - cpu_percent: Float
//   - mocked: Boolean
//   - retry_count: Integer
//   - max_loops: Integer
//   - current_loop: Integer
//   - agent_path: String
//   - agent_config: Map

// Artifact Node
// Labels: Artifact
// Properties:
//   - id: String (UUID)
//   - name: String
//   - artifact_type: String
//   - file_path: String
//   - content_hash: String
//   - size_bytes: Integer
//   - mime_type: String
//   - task_id: String (UUID)
//   - project_id: String (UUID)
//   - run_id: String (UUID)
//   - created_at: DateTime
//   - content: String

// Result Node
// Labels: Result
// Properties:
//   - id: String (UUID)
//   - task_id: String (UUID)
//   - success: Boolean
//   - data: Map
//   - error: String
//   - warnings: List[String]
//   - tokens_used: Integer
//   - latency_ms: Integer
//   - cost_usd: Float
//   - memory_mb: Float
//   - cpu_percent: Float
//   - mocked: Boolean
//   - retry_count: Integer
//   - created_at: DateTime
//   - execution_time_ms: Integer

// Critique Node
// Labels: Critique
// Properties:
//   - id: String (UUID)
//   - task_id: String (UUID)
//   - artifact_id: String (UUID)
//   - overall_score: Float
//   - policy_scores: Map
//   - pass_threshold: Boolean
//   - reasons: List[String]
//   - patch_plan: List[Map]
//   - critic_agent: String
//   - created_at: DateTime

// Agent Node
// Labels: Agent
// Properties:
//   - name: String
//   - version: String
//   - capabilities: List[String]

// Relationship Types:

// Project -> Run: HAS_RUN
// Run -> Task: CONTAINS_TASK
// Project -> Task: HAS_TASK
// Task -> Task: DEPENDS_ON
// Task -> Result: RESULTED_IN
// Task -> Critique: EMITTED
// Task -> Artifact: PRODUCED
// Artifact -> Artifact: DERIVED_FROM
// Agent -> Task: PERFORMS

// Example queries for common operations:

// Get all tasks for a project
// MATCH (p:Project {id: $project_id})-[:HAS_RUN]->(r:Run)-[:CONTAINS_TASK]->(t:Task)
// RETURN t ORDER BY t.created_at

// Get task dependencies
// MATCH (t:Task {id: $task_id})-[:DEPENDS_ON*]->(dep:Task)
// RETURN dep

// Get task lineage
// MATCH (t:Task {id: $task_id})
// OPTIONAL MATCH (t)-[:RESULTED_IN]->(res:Result)
// OPTIONAL MATCH (t)-[:EMITTED]->(c:Critique)
// OPTIONAL MATCH (t)-[:PRODUCED]->(a:Artifact)
// RETURN t, res, c, a

// Get project metrics
// MATCH (p:Project {id: $project_id})-[:HAS_RUN]->(r:Run)
// OPTIONAL MATCH (r)-[:CONTAINS_TASK]->(t:Task)
// RETURN count(r) as total_runs,
//        count(t) as total_tasks,
//        sum(t.tokens_used) as total_tokens,
//        sum(t.cost_usd) as total_cost

// Get agent performance
// MATCH (agent:Agent)-[:PERFORMS]->(t:Task)
// WHERE t.created_at >= datetime() - duration({days: 30})
// RETURN agent.name,
//        count(t) as tasks_executed,
//        avg(t.latency_ms) as avg_latency,
//        sum(t.cost_usd) as total_cost
