"""Cypher queries for Neo4j graph operations."""

# Node creation queries
CREATE_PROJECT = """
CREATE (p:Project {
    id: $id,
    name: $name,
    description: $description,
    request: $request,
    status: $status,
    created_at: datetime($created_at),
    updated_at: datetime($updated_at)
})
RETURN p
"""

CREATE_RUN = """
CREATE (r:Run {
    id: $id,
    project_id: $project_id,
    pipeline_name: $pipeline_name,
    status: $status,
    current_task: $current_task,
    started_at: datetime($started_at),
    completed_at: $completed_at,
    total_tasks: $total_tasks,
    completed_tasks: $completed_tasks,
    failed_tasks: $failed_tasks,
    total_tokens: $total_tokens,
    total_cost_usd: $total_cost_usd
})
RETURN r
"""

CREATE_TASK = """
CREATE (t:Task {
    id: $id,
    name: $name,
    task_type: $task_type,
    status: $status,
    priority: $priority,
    project_id: $project_id,
    run_id: $run_id,
    parent_task_id: $parent_task_id,
    input_data: $input_data,
    output_data: $output_data,
    error_message: $error_message,
    created_at: datetime($created_at),
    started_at: $started_at,
    completed_at: $completed_at,
    tokens_used: $tokens_used,
    latency_ms: $latency_ms,
    cost_usd: $cost_usd,
    memory_mb: $memory_mb,
    cpu_percent: $cpu_percent,
    mocked: $mocked,
    retry_count: $retry_count,
    max_loops: $max_loops,
    current_loop: $current_loop,
    agent_path: $agent_path,
    agent_config: $agent_config
})
RETURN t
"""

CREATE_ARTIFACT = """
CREATE (a:Artifact {
    id: $id,
    name: $name,
    artifact_type: $artifact_type,
    file_path: $file_path,
    content_hash: $content_hash,
    size_bytes: $size_bytes,
    mime_type: $mime_type,
    task_id: $task_id,
    project_id: $project_id,
    run_id: $run_id,
    created_at: datetime($created_at),
    content: $content
})
RETURN a
"""

CREATE_RESULT = """
CREATE (res:Result {
    id: $id,
    task_id: $task_id,
    success: $success,
    data: $data,
    error: $error,
    warnings: $warnings,
    tokens_used: $tokens_used,
    latency_ms: $latency_ms,
    cost_usd: $cost_usd,
    memory_mb: $memory_mb,
    cpu_percent: $cpu_percent,
    mocked: $mocked,
    retry_count: $retry_count,
    created_at: datetime($created_at),
    execution_time_ms: $execution_time_ms
})
RETURN res
"""

CREATE_CRITIQUE = """
CREATE (c:Critique {
    id: $id,
    task_id: $task_id,
    artifact_id: $artifact_id,
    overall_score: $overall_score,
    policy_scores: $policy_scores,
    pass_threshold: $pass_threshold,
    reasons: $reasons,
    patch_plan: $patch_plan,
    critic_agent: $critic_agent,
    created_at: datetime($created_at)
})
RETURN c
"""

# Relationship creation queries
LINK_TASK_TO_RUN = """
MATCH (t:Task {id: $task_id})
MATCH (r:Run {id: $run_id})
CREATE (r)-[:CONTAINS_TASK]->(t)
"""

LINK_TASK_TO_PROJECT = """
MATCH (t:Task {id: $task_id})
MATCH (p:Project {id: $project_id})
CREATE (p)-[:HAS_TASK]->(t)
"""

LINK_TASK_DEPENDENCY = """
MATCH (t:Task {id: $task_id})
MATCH (dep:Task {id: $depends_on_id})
CREATE (t)-[:DEPENDS_ON]->(dep)
"""

LINK_TASK_RESULT = """
MATCH (t:Task {id: $task_id})
MATCH (res:Result {id: $result_id})
CREATE (t)-[:RESULTED_IN]->(res)
"""

LINK_TASK_CRITIQUE = """
MATCH (t:Task {id: $task_id})
MATCH (c:Critique {id: $critique_id})
CREATE (t)-[:EMITTED]->(c)
"""

LINK_ARTIFACT_TASK = """
MATCH (a:Artifact {id: $artifact_id})
MATCH (t:Task {id: $task_id})
CREATE (t)-[:PRODUCED]->(a)
"""

LINK_ARTIFACT_DERIVED_FROM = """
MATCH (a:Artifact {id: $artifact_id})
MATCH (source:Artifact {id: $derived_from_id})
CREATE (a)-[:DERIVED_FROM]->(source)
"""

LINK_AGENT_PERFORMS_TASK = """
MERGE (agent:Agent {name: $agent_name})
MATCH (t:Task {id: $task_id})
CREATE (agent)-[:PERFORMS]->(t)
"""

# Query for linking project to run
LINK_PROJECT_TO_RUN = """
MATCH (p:Project {id: $project_id})
MATCH (r:Run {id: $run_id})
CREATE (p)-[:HAS_RUN]->(r)
"""

# Update queries
UPDATE_TASK_STATUS = """
MATCH (t:Task {id: $task_id})
SET t.status = $status,
    t.started_at = CASE WHEN $status = 'running' THEN datetime() ELSE t.started_at END,
    t.completed_at = CASE WHEN $status IN ['success', 'failed'] THEN datetime() ELSE t.completed_at END,
    t.output_data = $output_data,
    t.error_message = $error_message,
    t.tokens_used = $tokens_used,
    t.latency_ms = $latency_ms,
    t.cost_usd = $cost_usd,
    t.retry_count = $retry_count
RETURN t
"""

UPDATE_RUN_STATUS = """
MATCH (r:Run {id: $run_id})
SET r.status = $status,
    r.current_task = $current_task,
    r.completed_at = CASE WHEN $status IN ['completed', 'failed'] THEN datetime() ELSE r.completed_at END,
    r.completed_tasks = $completed_tasks,
    r.failed_tasks = $failed_tasks,
    r.total_tokens = $total_tokens,
    r.total_cost_usd = $total_cost_usd
RETURN r
"""

# Complex queries
GET_PROJECT_LINEAGE = """
MATCH (p:Project {id: $project_id})
OPTIONAL MATCH (p)-[:HAS_RUN]->(r:Run)
OPTIONAL MATCH (r)-[:CONTAINS_TASK]->(t:Task)
OPTIONAL MATCH (t)-[:RESULTED_IN]->(res:Result)
OPTIONAL MATCH (t)-[:EMITTED]->(c:Critique)
OPTIONAL MATCH (t)-[:PRODUCED]->(a:Artifact)
OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task)
OPTIONAL MATCH (agent:Agent)-[:PERFORMS]->(t)
RETURN p, r, t, res, c, a, dep, agent
ORDER BY t.created_at
"""

GET_RUN_STATUS = """
MATCH (r:Run {id: $run_id})
OPTIONAL MATCH (r)-[:CONTAINS_TASK]->(t:Task)
RETURN r,
       count(t) as total_tasks,
       count(CASE WHEN t.status = 'success' THEN 1 END) as completed_tasks,
       count(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks,
       count(CASE WHEN t.status = 'running' THEN 1 END) as running_tasks,
       sum(t.tokens_used) as total_tokens,
       sum(t.cost_usd) as total_cost
"""

GET_TASK_DEPENDENCIES = """
MATCH (t:Task {id: $task_id})-[:DEPENDS_ON*]->(dep:Task)
RETURN dep
ORDER BY dep.created_at
"""

GET_TASK_ARTIFACTS = """
MATCH (t:Task {id: $task_id})-[:PRODUCED]->(a:Artifact)
RETURN a
ORDER BY a.created_at
"""

GET_TASK_RESULTS = """
MATCH (t:Task {id: $task_id})-[:RESULTED_IN]->(res:Result)
RETURN res
ORDER BY res.created_at DESC
LIMIT 1
"""

GET_TASK_CRITIQUES = """
MATCH (t:Task {id: $task_id})-[:EMITTED]->(c:Critique)
RETURN c
ORDER BY c.created_at DESC
"""

# Analytics queries
GET_PROJECT_METRICS = """
MATCH (p:Project {id: $project_id})-[:HAS_RUN]->(r:Run)
OPTIONAL MATCH (r)-[:CONTAINS_TASK]->(t:Task)
OPTIONAL MATCH (t)-[:RESULTED_IN]->(res:Result)
RETURN p.name as project_name,
       count(DISTINCT r) as total_runs,
       count(t) as total_tasks,
       avg(t.latency_ms) as avg_task_latency,
       sum(t.tokens_used) as total_tokens,
       sum(t.cost_usd) as total_cost,
       count(CASE WHEN t.status = 'success' THEN 1 END) as successful_tasks,
       count(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks
"""

GET_AGENT_PERFORMANCE = """
MATCH (agent:Agent)-[:PERFORMS]->(t:Task)
WHERE t.created_at >= datetime() - duration({days: 30})
RETURN agent.name as agent_name,
       count(t) as tasks_executed,
       avg(t.latency_ms) as avg_latency,
       sum(t.tokens_used) as total_tokens,
       sum(t.cost_usd) as total_cost,
       count(CASE WHEN t.status = 'success' THEN 1 END) as successful_tasks,
       count(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks
ORDER BY tasks_executed DESC
"""

GET_CRITIQUE_STATS = """
MATCH (t:Task)-[:EMITTED]->(c:Critique)
WHERE c.created_at >= datetime() - duration({days: 30})
RETURN avg(c.overall_score) as avg_score,
       count(CASE WHEN c.pass_threshold THEN 1 END) as passed_critiques,
       count(c) as total_critiques,
       count(CASE WHEN c.pass_threshold = false THEN 1 END) as failed_critiques
"""
