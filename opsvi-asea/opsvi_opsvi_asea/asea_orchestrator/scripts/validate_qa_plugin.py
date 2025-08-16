# /home/opsvi/asea/asea_orchestrator/scripts/validate_qa_plugin.py
import sys
import os
import json
import asyncio
import logging

# Adjust the path to import the orchestrator's core components
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# The testing worker is no longer needed
# from celery.contrib.testing.worker import start_worker
from asea_orchestrator.celery_app import app as celery_app
from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig
from asea_orchestrator.plugins.available.qa_plugin import QAPlugin

# --- Logging Configuration ---
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "qa_validation.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
# --- End Logging Configuration ---

# The managed worker context is removed as we now use a standalone worker
# @contextmanager
# def managed_celery_worker(app): ...


async def main():
    """
    Loads and executes the QA validation workflow against a standalone Celery worker.
    """
    logger.info("--- Initializing ASEA Orchestrator for QA Validation ---")

    workflow_file = "/home/opsvi/asea/asea_orchestrator/workflows/cognitive_enhancement/validate_session_continuity.json"
    try:
        with open(workflow_file, "r") as f:
            workflow_definitions = {"validate_session_continuity": json.load(f)}
        logger.info(f"Successfully loaded workflow from {workflow_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load or parse workflow file: {e}")
        return

    # 1. Initialize WorkflowManager
    workflow_manager = WorkflowManager(workflow_definitions)

    # 2. Initialize Orchestrator
    orchestrator = Orchestrator(plugins=[QAPlugin], workflow_manager=workflow_manager)

    # 3. Configure the QA Plugin
    qa_plugin_config = {
        "QA Plugin": PluginConfig(
            name="QA Plugin", config={"test_target": "core_systems_service"}
        )
    }
    orchestrator.temp_configure_plugins(qa_plugin_config)

    # 4. Run the workflow directly
    try:
        logger.info("--- Sending task to standalone Celery worker. ---")
        final_state = await orchestrator.run_workflow("validate_session_continuity")
        logger.info("--- Workflow execution finished ---")

        logger.info(f"Final state: {json.dumps(final_state, indent=2)}")

        if final_state.get("success"):
            logger.info("✅✅✅ End-to-end validation PASSED. ✅✅✅")
        else:
            logger.error("❌❌❌ End-to-end validation FAILED. ❌❌❌")
            error_msg = final_state.get("error_message", "No error message provided.")
            logger.error(f"Reason: {error_msg}")

    except Exception as e:
        logger.critical(
            f"An unexpected error occurred during workflow execution: {e}",
            exc_info=True,
        )
    finally:
        logger.info("--- Cleaning up orchestrator resources ---")
        await orchestrator.cleanup()


if __name__ == "__main__":
    print("----------------------------------------------------------------------")
    print("IMPORTANT: Ensure both services are running in separate terminals:")
    print(
        "1. Core Systems Service: python development/autonomous_systems/start_service.py"
    )
    print(
        "2. Celery Worker: cd asea_orchestrator && celery -A src.asea_orchestrator.celery_app worker --loglevel=info"
    )
    print("----------------------------------------------------------------------")
    asyncio.run(main())
