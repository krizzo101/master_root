import logging
from typing import List

from fastapi import FastAPI, HTTPException

from src.applications.workflow_mcp.agent_runner import EmbeddedAgentRunner
from src.applications.workflow_mcp.db import WorkflowDB
from src.applications.workflow_mcp.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunCreate,
    WorkflowRunResponse,
    WorkflowRunUpdate,
    WorkflowUpdate,
)

app = FastAPI(title="Workflow MCP Server")
db = WorkflowDB()
agent_runner = EmbeddedAgentRunner()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("workflow_mcp_server")

# --------- Workflow Endpoints ---------


@app.post("/workflows", response_model=WorkflowResponse)
def create_workflow(workflow: WorkflowCreate):
    logger.debug(f"POST /workflows called with: {workflow}")
    result = db.create_workflow(workflow.dict())
    if not result.get("success", True):
        logger.error(f"Failed to create workflow: {result}")
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to create workflow")
        )
    key = result.get("results", [{}])[0].get("_key")
    doc = db.get_workflow(key)
    if not doc.get("success"):
        logger.error("Workflow created but not found")
        raise HTTPException(status_code=500, detail="Workflow created but not found")
    logger.debug(f"Workflow created: {doc['document']}")
    return doc["document"]


@app.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: str):
    logger.debug(f"GET /workflows/{workflow_id} called")
    doc = db.get_workflow(workflow_id)
    if not doc.get("success") or not doc.get("document"):
        logger.error(f"Workflow not found: {workflow_id}")
        raise HTTPException(status_code=404, detail="Workflow not found")
    logger.debug(f"Workflow retrieved: {doc['document']}")
    return doc["document"]


@app.get("/workflows", response_model=List[WorkflowResponse])
def list_workflows(skip: int = 0, limit: int = 50):
    logger.debug(f"GET /workflows called with skip={skip}, limit={limit}")
    docs = db.list_workflows(skip=skip, limit=limit)
    if not docs.get("success"):
        logger.error("Failed to list workflows")
        raise HTTPException(status_code=500, detail="Failed to list workflows")
    logger.debug(f"Workflows listed: {len(docs.get('documents', []))} found")
    return docs.get("documents", [])


@app.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: str, updates: WorkflowUpdate):
    logger.debug(f"PUT /workflows/{workflow_id} called with: {updates}")
    result = db.update_workflow(workflow_id, updates.dict(exclude_unset=True))
    if not result.get("success"):
        logger.error(f"Failed to update workflow: {result}")
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to update workflow")
        )
    doc = db.get_workflow(workflow_id)
    if not doc.get("success") or not doc.get("document"):
        logger.error(f"Workflow not found after update: {workflow_id}")
        raise HTTPException(status_code=404, detail="Workflow not found after update")
    logger.debug(f"Workflow updated: {doc['document']}")
    return doc["document"]


@app.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: str):
    logger.debug(f"DELETE /workflows/{workflow_id} called")
    result = db.delete_workflow(workflow_id)
    if not result.get("success"):
        logger.error(f"Failed to delete workflow: {result}")
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to delete workflow")
        )
    logger.debug(f"Workflow deleted: {workflow_id}")
    return {"success": True, "deleted": workflow_id}


# --------- Workflow Run Endpoints ---------


@app.post("/workflows/{workflow_id}/run", response_model=WorkflowRunResponse)
def run_workflow(workflow_id: str, run: WorkflowRunCreate):
    logger.debug(f"POST /workflows/{workflow_id}/run called with: {run}")
    wf_doc = db.get_workflow(workflow_id)
    if not wf_doc.get("success") or not wf_doc.get("document"):
        logger.error(f"Workflow not found: {workflow_id}")
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow_spec = wf_doc["document"].get("spec")
    agent_result = agent_runner.run_workflow(workflow_spec, run.input)
    run_data = run.dict()
    run_data["workflow_id"] = workflow_id
    run_data["result"] = agent_result.get("result")
    run_data["logs"] = agent_result.get("logs")
    run_data["status"] = agent_result.get("status", "complete")
    result = db.create_run(run_data)
    if not result.get("success", True):
        logger.error(f"Failed to create workflow run: {result}")
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to create workflow run")
        )
    key = result.get("results", [{}])[0].get("_key")
    doc = db.get_run(key)
    if not doc.get("success"):
        logger.error("Run created but not found")
        raise HTTPException(status_code=500, detail="Run created but not found")
    logger.debug(f"Workflow run created: {doc['document']}")
    return doc["document"]


@app.get("/runs", response_model=List[WorkflowRunResponse])
def list_runs(skip: int = 0, limit: int = 50):
    logger.debug(f"GET /runs called with skip={skip}, limit={limit}")
    docs = db.list_runs(skip=skip, limit=limit)
    if not docs.get("success"):
        logger.error("Failed to list runs")
        raise HTTPException(status_code=500, detail="Failed to list runs")
    logger.debug(f"Runs listed: {len(docs.get('documents', []))} found")
    return docs.get("documents", [])


@app.get("/runs/{run_id}", response_model=WorkflowRunResponse)
def get_run(run_id: str):
    logger.debug(f"GET /runs/{run_id} called")
    doc = db.get_run(run_id)
    if not doc.get("success") or not doc.get("document"):
        logger.error(f"Run not found: {run_id}")
        raise HTTPException(status_code=404, detail="Run not found")
    logger.debug(f"Run retrieved: {doc['document']}")
    return doc["document"]


@app.put("/runs/{run_id}", response_model=WorkflowRunResponse)
def update_run(run_id: str, updates: WorkflowRunUpdate):
    logger.debug(f"PUT /runs/{run_id} called with: {updates}")
    result = db.update_run(run_id, updates.dict(exclude_unset=True))
    if not result.get("success"):
        logger.error(f"Failed to update run: {result}")
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to update run")
        )
    doc = db.get_run(run_id)
    if not doc.get("success") or not doc.get("document"):
        logger.error(f"Run not found after update: {run_id}")
        raise HTTPException(status_code=404, detail="Run not found after update")
    logger.debug(f"Run updated: {doc['document']}")
    return doc["document"]


@app.delete("/runs/{run_id}")
def delete_run(run_id: str):
    logger.debug(f"DELETE /runs/{run_id} called")
    result = db.delete_run(run_id)
    if not result.get("success"):
        logger.error(f"Failed to delete run: {result}")
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to delete run")
        )
    logger.debug(f"Run deleted: {run_id}")
    return {"success": True, "deleted": run_id}
