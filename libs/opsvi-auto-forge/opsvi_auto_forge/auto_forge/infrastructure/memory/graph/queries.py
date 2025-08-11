"""Cypher queries for lineage tracking in Neo4j."""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from opsvi_auto_forge.config.models import (
    AgentRole,
    TaskStatus,
    Project,
    Run,
    TaskRecord,
    Artifact,
    Result,
    Critique,
    Decision,
)


class LineageQueries:
    """Cypher queries for lineage tracking operations."""

    # Project queries
    CREATE_PROJECT = """
    CREATE (p:Project {
        id: $project_id,
        name: $name,
        description: $description,
        requirements: $requirements,
        created_at: $created_at,
        updated_at: $updated_at,
        status: $status,
        metadata_json: apoc.convert.toJson($metadata)
    })
    RETURN p
    """

    GET_PROJECT = """
    MATCH (p:Project {id: $project_id})
    RETURN p
    """

    LIST_PROJECTS = """
    MATCH (p:Project)
    RETURN p
    ORDER BY p.created_at DESC
    """

    UPDATE_PROJECT = """
    MATCH (p:Project {id: $project_id})
    SET p.name = $name,
        p.description = $description,
        p.status = $status,
        p.metadata_json = apoc.convert.toJson($metadata),
        p.updated_at = $updated_at
    RETURN p
    """

    DELETE_PROJECT = """
    MATCH (p:Project {id: $project_id})
    DETACH DELETE p
    """

    # Run queries
    CREATE_RUN = """
    MATCH (p:Project {id: $project_id})
    CREATE (r:Run {
        id: $run_id,
        pipeline_name: $pipeline_name,
        status: $status,
        started_at: $started_at,
        ended_at: $ended_at,
        total_tasks: $total_tasks,
        completed_tasks: $completed_tasks,
        successful_tasks: $successful_tasks,
        failed_tasks: $failed_tasks,
        total_tokens: $total_tokens,
        total_cost: $total_cost,
        total_latency_ms: $total_latency_ms,
        metadata_json: apoc.convert.toJson($metadata)
    })
    CREATE (p)-[:HAS_RUN]->(r)
    RETURN r
    """

    GET_RUN = """
    MATCH (r:Run {id: $run_id})
    RETURN r
    """

    GET_PROJECT_RUNS = """
    MATCH (p:Project {id: $project_id})-[:HAS_RUN]->(r:Run)
    RETURN r
    ORDER BY r.started_at DESC
    """

    UPDATE_RUN_STATUS = """
    MATCH (r:Run {id: $run_id})
    SET r.status = $status,
        r.ended_at = $ended_at,
        r.metadata_json = apoc.convert.toJson($metadata)
    RETURN r
    """

    # Task queries
    CREATE_TASK = """
    MATCH (r:Run {id: $run_id})
    CREATE (t:Task {
        id: $task_id,
        name: $name,
        agent: $agent,
        status: $status,
        started_at: $started_at,
        ended_at: $ended_at,
        inputs: $inputs,
        outputs: $outputs,
        retry_count: $retry_count,
        max_retries: $max_retries,
        queue: $queue,
        priority: $priority,
        metadata_json: apoc.convert.toJson($metadata)
    })
    CREATE (r)-[:HAS_TASK]->(t)
    RETURN t
    """

    GET_TASK = """
    MATCH (t:Task {id: $task_id})
    RETURN t
    """

    GET_RUN_TASKS = """
    MATCH (r:Run {id: $run_id})-[:HAS_TASK]->(t:Task)
    RETURN t
    ORDER BY t.started_at ASC
    """

    UPDATE_TASK_STATUS = """
    MATCH (t:Task {id: $task_id})
    SET t.status = $status,
        t.ended_at = $ended_at,
        t.retry_count = $retry_count,
        t.metadata_json = apoc.convert.toJson($metadata)
    RETURN t
    """

    # Artifact queries
    CREATE_ARTIFACT = """
    MATCH (t:Task {id: $task_id})
    CREATE (a:Artifact {
        id: $artifact_id,
        type: $type,
        path: $path,
        hash: $hash,
        size_bytes: $size_bytes,
        created_at: $created_at,
        metadata: $metadata
    })
    CREATE (t)-[:PRODUCES]->(a)
    RETURN a
    """

    GET_TASK_ARTIFACTS = """
    MATCH (t:Task {id: $task_id})-[:PRODUCES]->(a:Artifact)
    RETURN a
    ORDER BY a.created_at ASC
    """

    # Result queries
    CREATE_RESULT = """
    MATCH (t:Task {id: $task_id})
    CREATE (r:Result {
        id: $result_id,
        status: $status,
        score: $score,
        metrics: $metrics,
        created_at: $created_at
    })
    CREATE (t)-[:HAS_RESULT]->(r)
    RETURN r
    """

    GET_TASK_RESULT = """
    MATCH (t:Task {id: $task_id})-[:HAS_RESULT]->(r:Result)
    RETURN r
    """

    # Critique queries
    CREATE_CRITIQUE = """
    MATCH (t:Task {id: $task_id})
    CREATE (c:Critique {
        id: $critique_id,
        passed: $passed,
        score: $score,
        policy_scores: $policy_scores,
        reasons: $reasons,
        patch_plan: $patch_plan,
        agent_id: $agent_id,
        created_at: $created_at
    })
    CREATE (t)-[:HAS_CRITIQUE]->(c)
    RETURN c
    """

    GET_TASK_CRITIQUE = """
    MATCH (t:Task {id: $task_id})-[:HAS_CRITIQUE]->(c:Critique)
    RETURN c
    """

    # Decision queries
    CREATE_DECISION = """
    MATCH (t:Task {id: $task_id})
    CREATE (d:Decision {
        id: $decision_id,
        by_agent: $by_agent,
        why: $why,
        confidence: $confidence,
        created_at: $created_at
    })
    CREATE (t)-[:HAS_DECISION]->(d)
    RETURN d
    """

    GET_TASK_DECISIONS = """
    MATCH (t:Task {id: $task_id})-[:HAS_DECISION]->(d:Decision)
    RETURN d
    ORDER BY d.created_at ASC
    """

    # Decision Kernel & Evidence Graph queries
    CREATE_VERIFICATION = """
    MERGE (d:Decision {id: $decision_id})
    MERGE (v:Verification {id: $ver_id})
      ON CREATE SET v += $props
    MERGE (d)-[:VERIFIED_BY]->(v)
    RETURN v.id AS id
    """

    CREATE_CLAIM = """
    MERGE (d:Decision {id: $decision_id})
    MERGE (c:Claim {id: $claim_id})
      ON CREATE SET c.text = $text, c.hash = $hash
    MERGE (d)-[:ASSERTS]->(c)
    RETURN c.id AS id
    """

    CREATE_EVIDENCE = """
    UNWIND $evidence_list AS ev
    MERGE (e:Evidence {id: ev.id})
      ON CREATE SET e += ev
    RETURN collect(e.id) AS ids
    """

    LINK_EVIDENCE_SUPPORT = """
    MATCH (c:Claim {id: $claim_id})
    UNWIND $evidence_ids AS evid
    MATCH (e:Evidence {id: evid})
    MERGE (c)-[:SUPPORTED_BY]->(e)
    RETURN count(e) AS linked
    """

    GET_DECISION_GRAPH = """
    MATCH (t:Task {id: $task_id})-[:HAS_DECISION]->(d:Decision)
    OPTIONAL MATCH (d)-[:ASSERTS]->(c:Claim)
    OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(e:Evidence)
    OPTIONAL MATCH (c)-[:REFUTED_BY]->(r:Evidence)
    OPTIONAL MATCH (d)-[:VERIFIED_BY]->(v:Verification)
    
    WITH d, c, e, r, v
    ORDER BY c.created_at ASC, e.created_at ASC, r.created_at ASC, v.created_at ASC
    
    WITH d, collect(DISTINCT c) AS claims, collect(DISTINCT e) AS evidence,
         collect(DISTINCT r) AS refutes, collect(DISTINCT v) AS verifications
    
    RETURN d, claims, evidence, refutes, verifications
    """

    # Lineage queries
    GET_FULL_LINEAGE = """
    MATCH (p:Project {id: $project_id})-[:HAS_RUN]->(r:Run)-[:HAS_TASK]->(t:Task)
    OPTIONAL MATCH (t)-[:PRODUCES]->(a:Artifact)
    OPTIONAL MATCH (t)-[:HAS_RESULT]->(res:Result)
    OPTIONAL MATCH (t)-[:HAS_CRITIQUE]->(c:Critique)
    OPTIONAL MATCH (t)-[:HAS_DECISION]->(d:Decision)
    RETURN p, r, t, a, res, c, d
    ORDER BY r.started_at DESC, t.started_at ASC
    """

    GET_TASK_LINEAGE = """
    MATCH (t:Task {id: $task_id})
    OPTIONAL MATCH (r:Run)-[:HAS_TASK]->(t)
    OPTIONAL MATCH (p:Project)-[:HAS_RUN]->(r)
    OPTIONAL MATCH (t)-[:PRODUCES]->(a:Artifact)
    OPTIONAL MATCH (t)-[:HAS_RESULT]->(res:Result)
    OPTIONAL MATCH (t)-[:HAS_CRITIQUE]->(c:Critique)
    OPTIONAL MATCH (t)-[:HAS_DECISION]->(d:Decision)
    RETURN p, r, t, a, res, c, d
    """

    GET_RUN_SUMMARY = """
    MATCH (r:Run {id: $run_id})-[:HAS_TASK]->(t:Task)
    OPTIONAL MATCH (t)-[:HAS_RESULT]->(res:Result)
    OPTIONAL MATCH (t)-[:HAS_CRITIQUE]->(c:Critique)
    RETURN r,
           count(t) as total_tasks,
           count(CASE WHEN t.status = 'SUCCESS' THEN 1 END) as successful_tasks,
           count(CASE WHEN t.status = 'FAILED' THEN 1 END) as failed_tasks,
           avg(res.score) as avg_result_score,
           avg(c.score) as avg_critique_score
    """

    # Performance queries
    GET_AGENT_PERFORMANCE = """
    MATCH (t:Task)-[:HAS_RESULT]->(res:Result)
    WHERE t.agent = $agent
    RETURN t.agent,
           count(t) as total_tasks,
           avg(res.score) as avg_score,
           min(res.score) as min_score,
           max(res.score) as max_score,
           stddev(res.score) as score_stddev
    """

    GET_TASK_STATS = """
    MATCH (t:Task)
    WHERE t.started_at >= $start_date AND t.started_at <= $end_date
    RETURN t.name,
           count(t) as execution_count,
           avg(duration.between(t.started_at, t.ended_at).seconds) as avg_duration,
           count(CASE WHEN t.status = 'SUCCESS' THEN 1 END) as success_count,
           count(CASE WHEN t.status = 'FAILED' THEN 1 END) as failure_count
    ORDER BY execution_count DESC
    """

    # Dependency queries
    GET_TASK_DEPENDENCIES = """
    MATCH (t:Task {id: $task_id})-[:DEPENDS_ON]->(dep:Task)
    RETURN dep
    ORDER BY dep.started_at ASC
    """

    GET_DEPENDENT_TASKS = """
    MATCH (dep:Task {id: $task_id})<-[:DEPENDS_ON]-(t:Task)
    RETURN t
    ORDER BY t.started_at ASC
    """

    # Search queries
    SEARCH_TASKS_BY_CONTENT = """
    MATCH (t:Task)
    WHERE t.name CONTAINS $search_term
       OR t.outputs CONTAINS $search_term
       OR t.metadata_json CONTAINS $search_term
    RETURN t
    ORDER BY t.started_at DESC
    LIMIT $limit
    """

    SEARCH_ARTIFACTS_BY_CONTENT = """
    MATCH (a:Artifact)
    WHERE a.name CONTAINS $search_term
       OR a.content CONTAINS $search_term
       OR a.metadata_json CONTAINS $search_term
    RETURN a
    ORDER BY a.created_at DESC
    LIMIT $limit
    """

    # Cleanup queries
    CLEANUP_OLD_RUNS = """
    MATCH (r:Run)
    WHERE r.started_at < $cutoff_date
    DETACH DELETE r
    """

    CLEANUP_OLD_ARTIFACTS = """
    MATCH (a:Artifact)
    WHERE a.created_at < $cutoff_date
    DETACH DELETE a
    """


class QueryExecutor:
    """Executes lineage queries with proper parameter handling."""

    def __init__(self, neo4j_client):
        """Initialize with Neo4j client."""
        self.client = neo4j_client
        self.queries = LineageQueries()

    async def create_project(self, project: Project) -> bool:
        """Create a project node."""
        try:
            await self.client.execute_query(
                self.queries.CREATE_PROJECT,
                {
                    "project_id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "requirements": project.requirements,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                    "status": project.status,
                    "metadata": json.dumps(project.metadata),
                },
            )
            return True
        except Exception as e:
            print(f"Error creating project: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def create_run(self, run: Run, project_id: UUID) -> bool:
        """Create a run node."""
        try:
            await self.client.execute_query(
                self.queries.CREATE_RUN,
                {
                    "run_id": str(run.id),
                    "project_id": str(project_id),
                    "pipeline_name": run.pipeline_name,
                    "status": run.status,
                    "started_at": (
                        run.started_at.isoformat() if run.started_at else None
                    ),
                    "ended_at": run.ended_at.isoformat() if run.ended_at else None,
                    "total_tasks": run.total_tasks,
                    "completed_tasks": run.completed_tasks,
                    "successful_tasks": run.successful_tasks,
                    "failed_tasks": run.failed_tasks,
                    "total_tokens": run.total_tokens,
                    "total_cost": run.total_cost,
                    "total_latency_ms": run.total_latency_ms,
                    "metadata": json.dumps(run.metadata),
                },
            )
            return True
        except Exception as e:
            print(f"Error creating run: {e}")
            return False

    async def create_task(self, task: TaskRecord, run_id: UUID) -> bool:
        """Create a task node."""
        try:
            # Prepare parameters with detailed logging
            params = {
                "task_id": str(task.id),
                "run_id": str(run_id),
                "name": task.name,
                "agent": task.agent,
                "status": task.status,
                "started_at": (
                    task.started_at.isoformat() if task.started_at else None
                ),
                "ended_at": task.ended_at.isoformat() if task.ended_at else None,
                "inputs": json.dumps(task.inputs),
                "outputs": json.dumps(task.outputs),
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "queue": task.queue,
                "priority": task.priority,
                "metadata": json.dumps(task.metadata),
            }

            print(f"Creating task with params: {params}")
            print(f"Task object: {task}")
            print(f"Run ID: {run_id}")

            await self.client.execute_query(
                self.queries.CREATE_TASK,
                params,
            )
            return True
        except Exception as e:
            print(f"Error creating task: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def update_task_status(
        self, task_id: UUID, status: TaskStatus, **kwargs
    ) -> bool:
        """Update task status."""
        try:
            params = {
                "task_id": str(task_id),
                "status": status,
                "ended_at": (
                    kwargs.get("ended_at").isoformat()
                    if kwargs.get("ended_at")
                    else None
                ),
                "retry_count": kwargs.get("retry_count", 0),
                "metadata": json.dumps(kwargs.get("metadata", {})),
            }
            await self.client.execute_query(self.queries.UPDATE_TASK_STATUS, params)
            return True
        except Exception as e:
            print(f"Error updating task status: {e}")
            return False

    async def create_artifact(self, artifact: Artifact, task_id: UUID) -> bool:
        """Create an artifact node."""
        try:
            # Prepare parameters with detailed logging
            params = {
                "artifact_id": str(artifact.id),
                "task_id": str(task_id),
                "type": artifact.type,
                "path": artifact.path,
                "hash": artifact.hash,
                "size_bytes": artifact.size_bytes,
                "created_at": artifact.created_at.isoformat(),
                "metadata": json.dumps(artifact.metadata),
            }

            print(f"Creating artifact with params: {params}")
            print(f"Artifact object: {artifact}")
            print(f"Task ID: {task_id}")

            await self.client.execute_query(
                self.queries.CREATE_ARTIFACT,
                params,
            )
            return True
        except Exception as e:
            print(f"Error creating artifact: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def create_result(self, result: Result, task_id: UUID) -> bool:
        """Create a result node."""
        try:
            params = {
                "result_id": str(result.id),
                "task_id": str(task_id),
                "status": result.status,
                "score": result.score,
                "metrics": json.dumps(result.metrics),
                "created_at": result.created_at.isoformat(),
            }
            print(f"Creating result with params: {params}")
            print(f"Result object: {result}")
            print(f"Task ID: {task_id}")
            await self.client.execute_query(
                self.queries.CREATE_RESULT,
                params,
            )
            return True
        except Exception as e:
            print(f"Error creating result: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def create_critique(self, critique: Critique, task_id: UUID) -> bool:
        """Create a critique node."""
        try:
            params = {
                "critique_id": str(critique.id),
                "task_id": str(task_id),
                "passed": critique.passed,
                "score": critique.score,
                "policy_scores": json.dumps(critique.policy_scores),
                "reasons": json.dumps(critique.reasons),
                "patch_plan": json.dumps(critique.patch_plan),
                "agent_id": str(critique.agent_id),
                "created_at": critique.created_at.isoformat(),
            }
            print(f"Creating critique with params: {params}")
            print(f"Critique object: {critique}")
            print(f"Task ID: {task_id}")
            await self.client.execute_query(
                self.queries.CREATE_CRITIQUE,
                params,
            )
            return True
        except Exception as e:
            print(f"Error creating critique: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def create_decision(self, decision: Decision, task_id: UUID) -> bool:
        """Create a decision node."""
        try:
            params = {
                "decision_id": str(decision.id),
                "task_id": str(task_id),
                "by_agent": decision.by_agent,
                "why": decision.why,
                "confidence": decision.confidence,
                "created_at": decision.created_at.isoformat(),
            }
            print(f"Creating decision with params: {params}")
            print(f"Decision object: {decision}")
            print(f"Task ID: {task_id}")
            await self.client.execute_query(
                self.queries.CREATE_DECISION,
                params,
            )
            return True
        except Exception as e:
            print(f"Error creating decision: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def get_full_lineage(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get full lineage for a project."""
        try:
            result = await self.client.execute_query(
                self.queries.GET_FULL_LINEAGE, {"project_id": str(project_id)}
            )
            return result or []
        except Exception as e:
            print(f"Error getting full lineage: {e}")
            return []

    async def get_run_summary(self, run_id: UUID) -> Optional[Dict[str, Any]]:
        """Get run summary with statistics."""
        try:
            result = await self.client.execute_query(
                self.queries.GET_RUN_SUMMARY, {"run_id": str(run_id)}
            )
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting run summary: {e}")
            return None

    # Decision Kernel & Evidence Graph methods
    async def create_verification(
        self, decision_id: str, ver_id: str, props: Dict[str, Any]
    ) -> bool:
        """Create a verification record for a decision."""
        try:
            result = await self.client.execute_query(
                self.queries.CREATE_VERIFICATION,
                {
                    "decision_id": decision_id,
                    "ver_id": ver_id,
                    "props": props,
                },
            )
            return bool(result)
        except Exception as e:
            print(f"Error creating verification: {e}")
            return False

    async def create_claim(
        self, decision_id: str, claim_id: str, text: str, hash: str
    ) -> bool:
        """Create a claim record for a decision."""
        try:
            result = await self.client.execute_query(
                self.queries.CREATE_CLAIM,
                {
                    "decision_id": decision_id,
                    "claim_id": claim_id,
                    "text": text,
                    "hash": hash,
                },
            )
            return bool(result)
        except Exception as e:
            print(f"Error creating claim: {e}")
            return False

    async def create_evidence(self, evidence_list: List[Dict[str, Any]]) -> List[str]:
        """Create evidence records."""
        try:
            result = await self.client.execute_query(
                self.queries.CREATE_EVIDENCE,
                {"evidence_list": evidence_list},
            )
            return result[0]["ids"] if result else []
        except Exception as e:
            print(f"Error creating evidence: {e}")
            return []

    async def link_evidence_support(
        self, claim_id: str, evidence_ids: List[str]
    ) -> int:
        """Link evidence to support a claim."""
        try:
            result = await self.client.execute_query(
                self.queries.LINK_EVIDENCE_SUPPORT,
                {
                    "claim_id": claim_id,
                    "evidence_ids": evidence_ids,
                },
            )
            return int(result[0]["linked"] or 0)
        except Exception as e:
            print(f"Error linking evidence support: {e}")
            return 0

    async def get_decision_graph(self, task_id: str) -> Dict[str, Any]:
        """Get the complete decision graph for a task."""
        try:
            result = await self.client.execute_query(
                self.queries.GET_DECISION_GRAPH,
                {"task_id": task_id},
            )
            if not result:
                return {
                    "decision": None,
                    "claims": [],
                    "evidence": [],
                    "refutes": [],
                    "verifications": [],
                }

            record = result[0]
            return {
                "decision": record["d"],
                "claims": [dict(r) for r in record["claims"] if r],
                "evidence": [dict(r) for r in record["evidence"] if r],
                "refutes": [dict(r) for r in record["refutes"] if r],
                "verifications": [dict(r) for r in record["verifications"] if r],
            }
        except Exception as e:
            print(f"Error getting decision graph: {e}")
            return {
                "decision": None,
                "claims": [],
                "evidence": [],
                "refutes": [],
                "verifications": [],
            }
