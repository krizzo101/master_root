from datetime import datetime
import logging
from typing import Any, Dict, Optional

from src.shared.interfaces.database.arango_interface import DirectArangoDB

logger = logging.getLogger("workflow_mcp_db")


class WorkflowDB:
    """
    Database access layer for workflows and workflow_runs collections in ArangoDB.
    Uses DirectArangoDB for all operations.
    """

    def __init__(self, db: Optional[DirectArangoDB] = None):
        self.db = db or DirectArangoDB()
        self.workflows_col = "workflows"
        self.runs_col = "workflow_runs"

    # ========== WORKFLOWS CRUD ==========

    def create_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new workflow document."""
        logger.debug(f"create_workflow called with: {workflow}")
        workflow["created_at"] = datetime.utcnow().isoformat()
        workflow["updated_at"] = workflow["created_at"]
        result = self.db.batch_insert(self.workflows_col, [workflow])
        logger.debug(f"create_workflow result: {result}")
        return result

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Retrieve a workflow by _key."""
        logger.debug(f"get_workflow called with: {workflow_id}")
        result = self.db.get_document(self.workflows_col, workflow_id)
        logger.debug(f"get_workflow result: {result}")
        return result

    def list_workflows(
        self, filters: Optional[Dict[str, Any]] = None, skip: int = 0, limit: int = 50
    ) -> Dict[str, Any]:
        """List workflows, optionally filtered."""
        logger.debug(
            f"list_workflows called with filters={filters}, skip={skip}, limit={limit}"
        )
        filters = filters or {}
        result = self.db.find_documents(
            self.workflows_col, filters, skip=skip, limit=limit
        )
        logger.debug(f"list_workflows result: {result}")
        return result

    def update_workflow(
        self, workflow_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a workflow by _key."""
        logger.debug(
            f"update_workflow called with workflow_id={workflow_id}, updates={updates}"
        )
        updates["updated_at"] = datetime.utcnow().isoformat()
        updates["_key"] = workflow_id
        result = self.db.update_document(self.workflows_col, updates)
        logger.debug(f"update_workflow result: {result}")
        return result

    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a workflow by _key."""
        logger.debug(f"delete_workflow called with: {workflow_id}")
        result = self.db.delete_document(self.workflows_col, workflow_id)
        logger.debug(f"delete_workflow result: {result}")
        return result

    # ========== WORKFLOW RUNS CRUD ==========

    def create_run(self, run: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new workflow run document."""
        logger.debug(f"create_run called with: {run}")
        run["started_at"] = datetime.utcnow().isoformat()
        run["status"] = run.get("status", "pending")
        result = self.db.batch_insert(self.runs_col, [run])
        logger.debug(f"create_run result: {result}")
        return result

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Retrieve a workflow run by _key."""
        logger.debug(f"get_run called with: {run_id}")
        result = self.db.get_document(self.runs_col, run_id)
        logger.debug(f"get_run result: {result}")
        return result

    def list_runs(
        self, filters: Optional[Dict[str, Any]] = None, skip: int = 0, limit: int = 50
    ) -> Dict[str, Any]:
        """List workflow runs, optionally filtered."""
        logger.debug(
            f"list_runs called with filters={filters}, skip={skip}, limit={limit}"
        )
        filters = filters or {}
        result = self.db.find_documents(self.runs_col, filters, skip=skip, limit=limit)
        logger.debug(f"list_runs result: {result}")
        return result

    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a workflow run by _key."""
        logger.debug(f"update_run called with run_id={run_id}, updates={updates}")
        updates["_key"] = run_id
        if "finished_at" not in updates and updates.get("status") in (
            "complete",
            "failed",
        ):
            updates["finished_at"] = datetime.utcnow().isoformat()
        result = self.db.update_document(self.runs_col, updates)
        logger.debug(f"update_run result: {result}")
        return result

    def delete_run(self, run_id: str) -> Dict[str, Any]:
        """Delete a workflow run by _key."""
        logger.debug(f"delete_run called with: {run_id}")
        result = self.db.delete_document(self.runs_col, run_id)
        logger.debug(f"delete_run result: {result}")
        return result
