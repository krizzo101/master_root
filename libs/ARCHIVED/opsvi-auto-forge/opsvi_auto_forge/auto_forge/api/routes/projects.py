"""Project management routes for the autonomous software factory."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from opsvi_auto_forge.config.models import Project, Run
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
PROJECT_OPERATION_COUNT = Counter(
    "project_operation_total", "Total project operations", ["operation", "status"]
)
PROJECT_OPERATION_DURATION = Histogram(
    "project_operation_duration_seconds", "Project operation duration", ["operation"]
)

router = APIRouter()


async def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client instance."""
    logger.info("🔍 DEBUG: get_neo4j_client called")
    client = Neo4jClient()
    await client.connect()
    logger.info("🔍 DEBUG: Neo4j client connected successfully")
    return client


@router.post("/", response_model=Project)
async def create_project(
    project: Project,
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> Project:
    """Create a new project."""
    try:
        with PROJECT_OPERATION_DURATION.labels(operation="create").time():
            # Convert project to dict and handle requirements
            project_data = project.model_dump()

            # Ensure requirements is a list of strings
            if isinstance(project_data.get("requirements"), str):
                # Split on newlines or semicolons
                requirements_str = project_data["requirements"]
                requirements_list = [
                    req.strip()
                    for req in requirements_str.replace(";", "\n").split("\n")
                    if req.strip()
                ]
                project_data["requirements"] = requirements_list
                logger.warning(
                    f"Converted string requirements to list: {requirements_list}"
                )

            # BULLETPROOF: Let the client handle all serialization
            # Just pass the data as-is, the client will handle everything

            # Create project in Neo4j
            project_id = await neo4j_client.create_project(project_data)

            # Fetch the created project
            created_project_data = await neo4j_client.get_project(project_id)
            if not created_project_data:
                raise HTTPException(
                    status_code=500, detail="Failed to retrieve created project"
                )

            PROJECT_OPERATION_COUNT.labels(operation="create", status="success").inc()
            return Project(**created_project_data)

    except HTTPException:
        raise
    except Exception as e:
        PROJECT_OPERATION_COUNT.labels(operation="create", status="error").inc()
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {e}")


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> Project:
    """Get project by ID."""
    try:
        with PROJECT_OPERATION_DURATION.labels(operation="get").time():
            project_data = await neo4j_client.get_project(str(project_id))

            if not project_data:
                raise HTTPException(status_code=404, detail="Project not found")

            PROJECT_OPERATION_COUNT.labels(operation="get", status="success").inc()
            return Project(**project_data)

    except HTTPException:
        raise
    except Exception as e:
        PROJECT_OPERATION_COUNT.labels(operation="get", status="error").inc()
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project: {e}")


@router.get("/", response_model=List[Project])
async def list_projects(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> List[Project]:
    """List projects with pagination and filtering."""
    try:
        with PROJECT_OPERATION_DURATION.labels(operation="list").time():
            # Build query with filters
            query = """
            MATCH (p:Project)
            """
            parameters = {"limit": limit, "offset": offset}

            if status:
                query += " WHERE p.status = $status"
                parameters["status"] = status

            query += """
            RETURN p
            ORDER BY p.created_at DESC
            SKIP $offset
            LIMIT $limit
            """

            result = await neo4j_client.execute_query(query, parameters)
            projects = [Project(**record["p"]) for record in result]

            PROJECT_OPERATION_COUNT.labels(operation="list", status="success").inc()
            return projects

    except Exception as e:
        PROJECT_OPERATION_COUNT.labels(operation="list", status="error").inc()
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {e}")


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: UUID,
    project_update: Dict[str, Any],
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> Project:
    """Update project by ID."""
    try:
        with PROJECT_OPERATION_DURATION.labels(operation="update").time():
            # Check if project exists
            existing_project = await neo4j_client.get_project(str(project_id))
            if not existing_project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Update project
            set_clauses = ["p.updated_at = datetime()"]
            parameters = {"project_id": str(project_id)}

            for key, value in project_update.items():
                if value is not None:
                    set_clauses.append(f"p.{key} = ${key}")
                    parameters[key] = value

            query = f"""
            MATCH (p:Project {{id: $project_id}})
            SET {', '.join(set_clauses)}
            RETURN p
            """

            result = await neo4j_client.execute_write_query(query, parameters)
            updated_project = Project(**result[0]["p"])

            PROJECT_OPERATION_COUNT.labels(operation="update", status="success").inc()
            logger.info(f"Updated project: {project_id}")

            return updated_project

    except HTTPException:
        raise
    except Exception as e:
        PROJECT_OPERATION_COUNT.labels(operation="update", status="error").inc()
        logger.error(f"Failed to update project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {e}")


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> Dict[str, str]:
    """Delete project by ID."""
    try:
        with PROJECT_OPERATION_DURATION.labels(operation="delete").time():
            # Check if project exists
            existing_project = await neo4j_client.get_project(str(project_id))
            if not existing_project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Delete project and all related data
            query = """
            MATCH (p:Project {id: $project_id})
            OPTIONAL MATCH (p)-[:HAS_RUN]->(r:Run)
            OPTIONAL MATCH (r)-[:PART_OF]->(t:Task)
            OPTIONAL MATCH (t)-[:GENERATES]->(a:Artifact)
            OPTIONAL MATCH (t)-[:RESULTED_IN]->(res:Result)
            OPTIONAL MATCH (t)<-[:EVALUATED_BY]-(c:Critique)
            OPTIONAL MATCH (t)<-[:FOR_TASK]-(d:Decision)
            DELETE a, res, c, d, t, r, p
            """

            await neo4j_client.execute_write_query(
                query, {"project_id": str(project_id)}
            )

            PROJECT_OPERATION_COUNT.labels(operation="delete", status="success").inc()
            logger.info(f"Deleted project: {project_id}")

            return {"message": f"Project {project_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        PROJECT_OPERATION_COUNT.labels(operation="delete", status="error").inc()
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {e}")


@router.get("/{project_id}/runs", response_model=List[Run])
async def get_project_runs(
    project_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> List[Run]:
    """Get runs for a specific project."""
    try:
        with PROJECT_OPERATION_DURATION.labels(operation="get_runs").time():
            # Build query with filters
            query = """
            MATCH (p:Project {id: $project_id})-[:HAS_RUN]->(r:Run)
            """
            parameters = {
                "project_id": str(project_id),
                "limit": limit,
                "offset": offset,
            }

            if status:
                query += " WHERE r.status = $status"
                parameters["status"] = status

            query += """
            RETURN r
            ORDER BY r.started_at DESC
            SKIP $offset
            LIMIT $limit
            """

            result = await neo4j_client.execute_query(query, parameters)

            # Convert metadata from JSON string back to dict for each run
            runs = []
            for record in result:
                run_data = record["r"]
                if "metadata" in run_data and isinstance(run_data["metadata"], str):
                    try:
                        import json

                        run_data["metadata"] = json.loads(run_data["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        run_data["metadata"] = {}
                runs.append(Run(**run_data))

            PROJECT_OPERATION_COUNT.labels(operation="get_runs", status="success").inc()
            return runs

    except Exception as e:
        PROJECT_OPERATION_COUNT.labels(operation="get_runs", status="error").inc()
        logger.error(f"Failed to get runs for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project runs: {e}")


@router.get("/{project_id}/lineage")
async def get_project_lineage(
    project_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> Dict[str, Any]:
    """Get complete lineage for a project."""
    try:
        with PROJECT_OPERATION_DURATION.labels(operation="get_lineage").time():
            lineage = await neo4j_client.get_project_lineage(str(project_id))

            PROJECT_OPERATION_COUNT.labels(
                operation="get_lineage", status="success"
            ).inc()
            return {
                "project_id": str(project_id),
                "lineage": lineage,
                "total_runs": len(lineage),
                "total_tasks": sum(len(run.get("tasks", [])) for run in lineage),
            }

    except Exception as e:
        PROJECT_OPERATION_COUNT.labels(operation="get_lineage", status="error").inc()
        logger.error(f"Failed to get lineage for project {project_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get project lineage: {e}"
        )
