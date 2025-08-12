from dotenv import load_dotenv

load_dotenv()

"""
Agentic Documentation Manager
Main entry point for orchestrating automated, agent-powered documentation workflows.
"""

import argparse
import logging

from src.applications.agentic_doc_manager.agent_workflows import (
    artifact_ingestion_embedding_workflow,
    custom_task_dispatch_task,
    incident_assign_to_agent,
    knowledge_export_export_data,
)
from src.applications.agentic_doc_manager.agentic_workflow_runner import (
    run_agentic_doc_sync,
)
from src.applications.agentic_doc_manager.analytics import run_analytics
from src.applications.agentic_doc_manager.graph_manager import initialize_schema


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def load_env():
    logging.info("Environment variables loaded.")


def main():
    setup_logging()
    load_env()
    initialize_schema()
    parser = argparse.ArgumentParser(description="Agentic Documentation Manager")
    parser.add_argument(
        "--workflow",
        type=str,
        default="all",
        help="Workflow to run: artifact, analytics, incident, onboarding, drift, export, custom, all",
    )
    args = parser.parse_args()
    try:
        if args.workflow == "artifact":
            logging.info("Running artifact ingestion/embedding workflow...")
            result = artifact_ingestion_embedding_workflow()
            logging.info(f"Result: {result}")
        elif args.workflow == "analytics":
            logging.info("Running analytics workflow...")
            run_analytics()
        elif args.workflow == "incident":
            logging.info("Running incident handling workflow...")
            incident_assign_to_agent("Simulated incident", context="CI pipeline")
        elif args.workflow == "onboarding":
            logging.info("Running onboarding workflow (simulated)...")
            # Placeholder for onboarding logic
            logging.info("Onboarding workflow complete.")
        elif args.workflow == "drift":
            logging.info("Running doc drift detection/correction workflow...")
            run_agentic_doc_sync()
        elif args.workflow == "export":
            logging.info("Running knowledge export workflow...")
            result = knowledge_export_export_data({}, format="json")
            logging.info(f"Result: {result}")
        elif args.workflow == "custom":
            logging.info("Running custom task workflow...")
            custom_task_dispatch_task("Simulated custom task", user_id="user123")
        elif args.workflow == "all":
            logging.info("Running all agentic workflows in batch...")
            artifact_ingestion_embedding_workflow()
            run_analytics()
            incident_assign_to_agent("Simulated incident", context="CI pipeline")
            # Onboarding placeholder
            run_agentic_doc_sync()
            knowledge_export_export_data({}, format="json")
            custom_task_dispatch_task("Simulated custom task", user_id="user123")
            logging.info("All workflows complete.")
        else:
            logging.error(f"Unknown workflow: {args.workflow}")
    except Exception as e:
        logging.error(f"Error running workflow: {e}")


if __name__ == "__main__":
    initialize_schema()
    main()
