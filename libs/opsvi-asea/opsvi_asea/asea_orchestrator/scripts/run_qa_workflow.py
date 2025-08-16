# /home/opsvi/asea/asea_orchestrator/scripts/run_qa_workflow.py
import sys
import os
import json
import asyncio
import logging
from contextlib import contextmanager

# Adjust the path to import the orchestrator's core components
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# --- Celery and Orchestrator Imports ---
from celery.contrib.testing.worker import start_worker
from asea_orchestrator.celery_app import app as celery_app
from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig
from asea_orchestrator.plugins.available.qa_plugin.entrypoint import QAPlugin

# --- Logging Configuration ---
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "qa_workflow_execution.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, mode="w"),  # Overwrite log on each run
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
# --- End Logging Configuration ---


@contextmanager
def managed_celery_worker(app):
    """Context manager to start and stop a celery worker for testing."""
    logger.info("--- Starting Celery worker for integration test ---")
    with start_worker(app, loglevel="info", perform_ping_check=False) as worker:
        logger.info("--- Celery worker started successfully ---")
        yield worker
    logger.info("--- Celery worker stopped ---")


async def main():
    """
    Loads and executes the QA validation workflow within a managed Celery worker context.
    """
    logger.info("--- Initializing ASEA Orchestrator Components ---")

    plugin_dir = (
        "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"
    )
    workflow_file = "/home/opsvi/asea/asea_orchestrator/workflows/cognitive_enhancement/validate_session_continuity.json"
    try:
        with open(workflow_file, "r") as f:
            workflow_definitions = {"validate_session_continuity": json.load(f)}
        logger.info(f"Successfully loaded workflow from {workflow_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load or parse workflow file: {e}")
        return

    # 2. Initialize WorkflowManager with the loaded dictionary
    workflow_manager = WorkflowManager(workflow_definitions)

    # 3. Initialize Orchestrator with an explicit list of plugins
    orchestrator = Orchestrator(plugins=[QAPlugin], workflow_manager=workflow_manager)

    # 4. Configure the QA Plugin
    # This configuration is passed to the plugin when the orchestrator runs the workflow
    qa_plugin_config = {
        "QA Plugin": PluginConfig(
            name="QA Plugin", config={"test_target": "core_systems_service"}
        )
    }
    orchestrator.temp_configure_plugins(qa_plugin_config)

    # 5. Run the workflow inside the managed worker context
    try:
        with managed_celery_worker(celery_app):
            logger.info("--- Worker is running. Executing workflow. ---")
            final_state = await orchestrator.run_workflow("validate_session_continuity")
            logger.info("--- Workflow execution finished ---")
            logger.info(f"Final state: {json.dumps(final_state, indent=2)}")

    except Exception as e:
        logger.critical(
            f"An unexpected error occurred during workflow execution: {e}",
            exc_info=True,
        )
    finally:
        logger.info("--- Cleaning up orchestrator resources ---")
        await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
