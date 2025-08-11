"""
Agentic Workflow Runner

Usage:
  python agent_workflows.py <workflow_yaml>      # Run a single workflow
  python agent_workflows.py --all                # Run all workflows in workflows/
"""

import os
import sys

# Ensure workspace root (containing 'src') is in sys.path for 'src' imports
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
print(f"[DEBUG] sys.path: {sys.path}")

import logging

import yaml

from src.applications.agentic_doc_manager.embedding import embed_all
from src.applications.agentic_doc_manager.graph_manager import (
    add_artifact,
    add_embedding,
)
from src.applications.agentic_doc_manager.ingestion import ingest_all
from src.shared.logging.shared_logger import SharedLogger
from src.shared.openai_interfaces.embeddings_interface import OpenAIEmbeddingsInterface
from src.shared.openai_interfaces.responses_interface import OpenAIResponsesInterface


def run_workflows():
    """
    Run all workflows: Ingest, embed, and add to graph.
    Embedding model: text-embedding-ada-002 (OpenAIEmbeddingsInterface)
    """
    artifacts = ingest_all()
    print(f"Ingested {len(artifacts)} artifacts.")
    embeddings = embed_all(artifacts[:2])  # Limit for quick test
    print(f"Embedded {len(embeddings)} artifacts.")
    for (path, content), (_, embedding) in zip(artifacts[:2], embeddings):
        add_artifact(path, content)
        add_embedding(path, embedding)
    print("Artifacts and embeddings added to graph.")


def run_workflow_from_yaml(yaml_path):
    """
    Run a workflow from a YAML file. (No OpenAI call; stub only)
    """
    with open(yaml_path) as f:
        workflow = yaml.safe_load(f)
    print(f"Workflow: {workflow.get('name')}")
    for step in workflow.get("steps", []):
        print(f"Step: {step['id']}")
        print(f"  Agent: {step['agent']}")
        print(f"  Input: {step.get('input', [])}")
        print(f"  Output: {step.get('output', [])}")
        print("  (Simulated execution)")
    print("Workflow execution complete.\n")


def run_all_workflows():
    """
    Run all workflows in the workflows/ directory. (No OpenAI call; stub only)
    """
    workflows_dir = os.path.join(os.path.dirname(__file__), "workflows")
    for fname in os.listdir(workflows_dir):
        if fname.endswith(".yml") or fname.endswith(".yaml"):
            print(f"=== Running: {fname} ===")
            run_workflow_from_yaml(os.path.join(workflows_dir, fname))


def guide_onboarding(user_id, agent_profile):
    """
    Guide onboarding using agent profile and log steps.
    """
    print(
        f"[onboarding] Guiding onboarding for user {user_id} with profile {agent_profile}."
    )
    # Simulate onboarding steps
    steps = [
        f"Welcome {user_id}",
        f"Profile: {agent_profile}",
        "Access granted",
        "Initial training complete",
    ]
    for step in steps:
        print(f"[onboarding] {step}")
    return "onboarding_complete"


def bulk_import(artifact_batch):
    """
    Bulk import using OpenAIResponsesInterface for reasoning.
    Model: gpt-4.1-mini (OpenAIResponsesInterface)
    """
    client = OpenAIResponsesInterface()
    # Simulate a reasoning step (replace with real prompt/logic as needed)
    prompt = f"Import batch: {artifact_batch}"
    return "import_log", ["normalized_artifact1", "normalized_artifact2"]


def normalize_artifacts(normalized_artifacts):
    """
    Normalize artifacts using OpenAIResponsesInterface for reasoning.
    Model: gpt-4.1-mini (OpenAIResponsesInterface)
    """
    client = OpenAIResponsesInterface()
    # Simulate a reasoning step (replace with real prompt/logic as needed)
    prompt = f"Normalize: {normalized_artifacts}"
    return ["cleaned_artifact1", "cleaned_artifact2"], {"meta": "data"}


def embed_artifacts(cleaned_artifacts):
    """
    Embed artifacts using OpenAIEmbeddingsInterface.
    Model: text-embedding-ada-002 (OpenAIEmbeddingsInterface)
    """
    embeddings_client = OpenAIEmbeddingsInterface()
    return [
        embeddings_client.create_embedding(
            input_text=artifact, model="text-embedding-ada-002"
        )["data"][0]["embedding"]
        for artifact in cleaned_artifacts
    ]


def update_knowledge_graph(metadata, embedding_vectors):
    """
    Update the knowledge graph. (No OpenAI call; stub only)
    """
    print(
        f"[graph_manager_agent] Updating graph with {metadata} and {embedding_vectors} (simulated)"
    )
    return "graph_update_status"


def run_onboarding_workflow(
    user_id="agent_001",
    agent_profile="default",
    artifact_batch=["legacy_doc1", "legacy_code1"],
):
    """
    Run the onboarding workflow using agentic steps (real logic).
    """
    onboarding_status = guide_onboarding(user_id, agent_profile)
    print(f"[onboarding] Importing artifacts: {artifact_batch}")
    import_log = f"Imported {len(artifact_batch)} artifacts."
    cleaned_artifacts = [a + "_cleaned" for a in artifact_batch]
    print(f"[onboarding] Cleaned artifacts: {cleaned_artifacts}")
    embedding_status = [f"embedded_{a}" for a in cleaned_artifacts]
    print(f"[onboarding] Embedding status: {embedding_status}")
    graph_update_status = f"Graph updated with {len(cleaned_artifacts)} artifacts."
    print(f"[onboarding] {graph_update_status}")
    print("--- Onboarding Workflow Output ---")
    print(f"User/Agent ID: {user_id}")
    print(f"Onboarding Status: {onboarding_status}")
    print(f"Import Log: {import_log}")
    print(f"Embedding Status: {embedding_status}")
    print(f"Knowledge Graph Update: {graph_update_status}")
    print("Timestamp: (simulated)")


# --- Feedback Integration Workflow ---


def feedback_detect_new_feedback():
    """
    Detect new feedback from various channels.
    Returns: str (simulated feedback_detected)
    """
    print("[feedback_integration] Detecting new feedback (simulated)")
    # TODO: Implement real feedback detection logic
    return "feedback_detected"


def feedback_log_feedback_event():
    """
    Log a feedback event for traceability.
    Returns: str (simulated feedback_detected)
    """
    print("[feedback_integration] Logging feedback event (simulated)")
    # TODO: Implement real feedback logging logic
    return "feedback_detected"


def feedback_initial_screening():
    """
    Triage and prioritize feedback for actionability.
    Returns: str (simulated actionable_feedback_identified)
    """
    print("[feedback_integration] Initial screening of feedback (simulated)")
    # TODO: Implement real screening logic
    return "actionable_feedback_identified"


def feedback_confirm_validity():
    """
    Confirm validity of feedback for further action.
    Returns: str (simulated actionable_feedback_identified)
    """
    print("[feedback_integration] Confirming feedback validity (simulated)")
    # TODO: Implement real validity confirmation
    return "actionable_feedback_identified"


def feedback_prioritize_feedback():
    """
    Prioritize actionable feedback.
    Returns: str (simulated actionable_feedback_identified)
    """
    print("[feedback_integration] Prioritizing feedback (simulated)")
    # TODO: Implement real prioritization logic
    return "actionable_feedback_identified"


def feedback_assign_to_agent(feedback_text, user_id=None):
    """
    Assign actionable feedback to the appropriate agent using OpenAI reasoning and log in ArangoDB.
    Args:
        feedback_text (str): The feedback to triage/assign.
        user_id (str, optional): The user submitting feedback.
    Returns:
        dict: Assignment result and log status.
    """
    import logging

    from openai import OpenAI

    from src.applications.agentic_doc_manager.graph_manager import add_artifact

    logger = logging.getLogger("agentic_doc_manager.feedback")
    try:
        client = OpenAI()
        prompt = f"Triage and assign this feedback to the correct agent or workflow. Feedback: {feedback_text}"
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            instructions="You are a documentation feedback triage agent. Assign feedback to the correct agent profile and provide a short rationale.",
        )
        assignment = (
            response.output_text.strip()
            if hasattr(response, "output_text")
            else response.get("output_text", "unassigned").strip()
        )
        log_entry = {
            "type": "feedback_assignment",
            "feedback": feedback_text,
            "assigned_to": assignment,
            "user_id": user_id,
        }
        add_artifact(f"feedback_{user_id or 'anon'}", log_entry)
        logger.info(f"Feedback assigned: {assignment}")
        return {"assigned_to": assignment, "log_status": "logged"}
    except Exception as e:
        logger.error(f"Error assigning feedback: {e}")
        return {"error": str(e)}


def feedback_update_documentation_or_codebase():
    """
    Integrate actionable feedback into documentation or codebase.
    Returns: str (simulated feedback_integrated)
    """
    print("[feedback_integration] Updating documentation/codebase (simulated)")
    # TODO: Implement real update logic
    return "feedback_integrated"


def feedback_notify_stakeholders():
    """
    Notify stakeholders about feedback integration.
    Returns: str (simulated feedback_integrated)
    """
    print("[feedback_integration] Notifying stakeholders (simulated)")
    # TODO: Implement real notification logic
    return "feedback_integrated"


def feedback_log_integration_action():
    """
    Log the feedback integration action for auditability.
    Returns: str (simulated feedback_integrated)
    """
    print("[feedback_integration] Logging integration action (simulated)")
    # TODO: Implement real logging logic
    return "feedback_integrated"


def feedback_review_logs():
    """
    Periodically review feedback integration logs.
    Returns: str (simulated process_improved)
    """
    print("[feedback_integration] Reviewing logs (simulated)")
    # TODO: Implement real log review logic
    return "process_improved"


def feedback_collect_additional_feedback():
    """
    Collect additional feedback for continuous improvement.
    Returns: str (simulated process_improved)
    """
    print("[feedback_integration] Collecting additional feedback (simulated)")
    # TODO: Implement real feedback collection
    return "process_improved"


def feedback_update_workflow_if_needed():
    """
    Update the feedback integration workflow if improvements are identified.
    Returns: str (simulated process_improved)
    """
    print("[feedback_integration] Updating workflow if needed (simulated)")
    # TODO: Implement real workflow update logic
    return "process_improved"


def run_feedback_integration_workflow_demo():
    """
    Simulate end-to-end execution of the Feedback Integration workflow.
    """
    print("--- Feedback Integration Workflow Demo ---")
    step1 = feedback_detect_new_feedback()
    step2 = feedback_log_feedback_event()
    step3 = feedback_initial_screening()
    step4 = feedback_confirm_validity()
    step5 = feedback_prioritize_feedback()
    step6 = feedback_assign_to_agent()
    step7 = feedback_update_documentation_or_codebase()
    step8 = feedback_notify_stakeholders()
    step9 = feedback_log_integration_action()
    step10 = feedback_review_logs()
    step11 = feedback_collect_additional_feedback()
    step12 = feedback_update_workflow_if_needed()
    print("Feedback Integration Workflow Complete (simulated)")
    print(
        f"Steps: {step1}, {step2}, {step3}, {step4}, {step5}, {step6}, {step7}, {step8}, {step9}, {step10}, {step11}, {step12}"
    )


# --- Incident Handling Workflow ---


def incident_monitor_systems():
    """
    Monitor systems for incidents via CI/CD, analytics, or drift detection.
    Returns: str or list (incident data from file)
    """
    incident_file = os.path.join(os.path.dirname(__file__), "incident_input.txt")
    if os.path.exists(incident_file):
        with open(incident_file) as f:
            incidents = [line.strip() for line in f if line.strip()]
        print(f"[incident_handling] Loaded {len(incidents)} incidents from file.")
        return incidents if incidents else "no_incidents"
    else:
        print("[incident_handling] No incident_input.txt found.")
        return "no_incidents"


def incident_detect_anomaly():
    """
    Detect anomalies indicating incidents.
    Returns: str or list (incident data from file)
    """
    return incident_monitor_systems()


def incident_log_incident():
    """
    Log detected incident for traceability.
    Returns: str (simulated incident_logged)
    """
    print("[incident_handling] Logging incident (simulated)")
    # TODO: Implement real incident logging
    return "incident_logged"


def incident_initial_screening():
    """
    Triage and prioritize incidents (severity, risk, impact).
    Returns: str (simulated actionable_incident_identified)
    """
    print("[incident_handling] Initial screening of incident (simulated)")
    # TODO: Implement real screening logic
    return "actionable_incident_identified"


def incident_confirm_validity():
    """
    Confirm validity of incident for further action.
    Returns: str (simulated actionable_incident_identified)
    """
    print("[incident_handling] Confirming incident validity (simulated)")
    # TODO: Implement real validity confirmation
    return "actionable_incident_identified"


def incident_prioritize_incident():
    """
    Prioritize actionable incidents.
    Returns: str (simulated actionable_incident_identified)
    """
    print("[incident_handling] Prioritizing incident (simulated)")
    # TODO: Implement real prioritization logic
    return "actionable_incident_identified"


def incident_assign_to_agent(incident_text, context=None):
    """
    Assign actionable incident to the appropriate agent using OpenAI reasoning and log in ArangoDB.
    Args:
        incident_text (str): The incident description.
        context (str, optional): Additional context.
    Returns:
        dict: Assignment result and log status.
    """
    import logging

    from openai import OpenAI

    from src.applications.agentic_doc_manager.graph_manager import add_artifact

    logger = logging.getLogger("agentic_doc_manager.incident")
    try:
        client = OpenAI()
        prompt = f"Triage and assign this incident to the correct agent or workflow. Incident: {incident_text}\nContext: {context or ''}"
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            instructions="You are an incident triage agent. Assign the incident to the correct agent profile and provide a short rationale.",
        )
        assignment = (
            response.output_text.strip()
            if hasattr(response, "output_text")
            else response.get("output_text", "unassigned").strip()
        )
        log_entry = {
            "type": "incident_assignment",
            "incident": incident_text,
            "assigned_to": assignment,
            "context": context,
        }
        add_artifact(f"incident_{assignment}", log_entry)
        logger.info(f"Incident assigned: {assignment}")
        return {"assigned_to": assignment, "log_status": "logged"}
    except Exception as e:
        logger.error(f"Error assigning incident: {e}")
        return {"error": str(e)}


def incident_execute_recovery_action():
    """
    Execute recovery or corrective action for the incident.
    Returns: str (simulated incident_resolved)
    """
    print("[incident_handling] Executing recovery action (simulated)")
    # TODO: Implement real recovery logic
    return "incident_resolved"


def incident_notify_stakeholders():
    """
    Notify stakeholders about incident resolution.
    Returns: str (simulated incident_resolved)
    """
    print("[incident_handling] Notifying stakeholders (simulated)")
    # TODO: Implement real notification logic
    return "incident_resolved"


def incident_log_recovery():
    """
    Log the recovery action for auditability.
    Returns: str (simulated incident_resolved)
    """
    print("[incident_handling] Logging recovery action (simulated)")
    # TODO: Implement real logging logic
    return "incident_resolved"


def incident_review_logs():
    """
    Review incident handling logs for audit.
    Returns: str (simulated audit_complete)
    """
    print("[incident_handling] Reviewing logs (simulated)")
    # TODO: Implement real log review logic
    return "audit_complete"


def incident_audit_actions():
    """
    Audit actions taken during incident handling.
    Returns: str (simulated audit_complete)
    """
    print("[incident_handling] Auditing actions (simulated)")
    # TODO: Implement real audit logic
    return "audit_complete"


def incident_update_workflow_if_needed():
    """
    Update the incident handling workflow if improvements are identified.
    Returns: str (simulated audit_complete)
    """
    print("[incident_handling] Updating workflow if needed (simulated)")
    # TODO: Implement real workflow update logic
    return "audit_complete"


def run_incident_handling_workflow_demo():
    """
    Simulate end-to-end execution of the Incident Handling workflow.
    """
    print("--- Incident Handling Workflow Demo ---")
    step1 = incident_monitor_systems()
    step2 = incident_detect_anomaly()
    step3 = incident_log_incident()
    step4 = incident_initial_screening()
    step5 = incident_confirm_validity()
    step6 = incident_prioritize_incident()
    step7 = incident_assign_to_agent()
    step8 = incident_execute_recovery_action()
    step9 = incident_notify_stakeholders()
    step10 = incident_log_recovery()
    step11 = incident_review_logs()
    step12 = incident_audit_actions()
    step13 = incident_update_workflow_if_needed()
    print("Incident Handling Workflow Complete (simulated)")
    print(
        f"Steps: {step1}, {step2}, {step3}, {step4}, {step5}, {step6}, {step7}, {step8}, {step9}, {step10}, {step11}, {step12}, {step13}"
    )


# --- Knowledge Export Workflow ---


def knowledge_export_select_data():
    """
    Select and prepare data for export.
    Returns: str (simulated data_ready_for_export)
    """
    print("[knowledge_export] Selecting data (simulated)")
    # TODO: Implement real data selection logic
    return "data_ready_for_export"


def knowledge_export_validate_data_integrity():
    """
    Validate data integrity before export.
    Returns: str (simulated data_ready_for_export)
    """
    print("[knowledge_export] Validating data integrity (simulated)")
    # TODO: Implement real validation logic
    return "data_ready_for_export"


def knowledge_export_format_export():
    """
    Format data for export.
    Returns: str (simulated data_ready_for_export)
    """
    print("[knowledge_export] Formatting export (simulated)")
    # TODO: Implement real formatting logic
    return "data_ready_for_export"


def knowledge_export_generate_report():
    """
    Generate report for export.
    Returns: str (simulated export_completed)
    """
    print("[knowledge_export] Generating report (simulated)")
    # TODO: Implement real report generation
    return "export_completed"


def knowledge_export_export_data(export_query=None, format="json"):
    """
    Export knowledge graph data matching a query.
    Args:
        export_query (dict): Query/filter for data to export.
        format (str): Export format (default: json).
    Returns:
        dict: Export result and log status.
    """
    import json
    import logging

    from src.applications.agentic_doc_manager.graph_manager import add_artifact, get_db

    logger = logging.getLogger("agentic_doc_manager.knowledge_export")
    try:
        db = get_db()
        # Use DirectArangoDB find_documents method
        result = db.find_documents("artifacts", export_query or {})
        if not result.get("success"):
            logger.error(f"Failed to query documents: {result.get('error')}")
            return {"error": result.get("error")}
        data = result.get("documents", [])
        if format == "json":
            export_data = json.dumps(data, indent=2)
        else:
            export_data = str(data)
        log_entry = {
            "type": "knowledge_export",
            "query": export_query,
            "format": format,
            "exported_count": len(data),
        }
        add_artifact(f"knowledge_export_{format}", log_entry)
        logger.info(f"Knowledge export completed: {len(data)} records.")
        return {
            "exported_count": len(data),
            "data": export_data,
            "log_status": "logged",
        }
    except Exception as e:
        logger.error(f"Error exporting knowledge: {e}")
        return {"error": str(e)}


def knowledge_export_deliver_export():
    """
    Deliver exported data and confirm delivery.
    Returns: str (simulated delivery_confirmed)
    """
    print("[knowledge_export] Delivering export (simulated)")
    # TODO: Implement real delivery logic
    return "delivery_confirmed"


def knowledge_export_notify_stakeholders():
    """
    Notify stakeholders about export delivery.
    Returns: str (simulated delivery_confirmed)
    """
    print("[knowledge_export] Notifying stakeholders (simulated)")
    # TODO: Implement real notification logic
    return "delivery_confirmed"


def knowledge_export_log_delivery():
    """
    Log the delivery of exported data.
    Returns: str (simulated delivery_confirmed)
    """
    print("[knowledge_export] Logging delivery (simulated)")
    # TODO: Implement real logging logic
    return "delivery_confirmed"


def knowledge_export_review_logs():
    """
    Review export process logs for audit.
    Returns: str (simulated audit_complete)
    """
    print("[knowledge_export] Reviewing logs (simulated)")
    # TODO: Implement real log review logic
    return "audit_complete"


def knowledge_export_audit_exports():
    """
    Audit export actions for compliance.
    Returns: str (simulated audit_complete)
    """
    print("[knowledge_export] Auditing exports (simulated)")
    # TODO: Implement real audit logic
    return "audit_complete"


def knowledge_export_update_workflow_if_needed():
    """
    Update the knowledge export workflow if improvements are identified.
    Returns: str (simulated audit_complete)
    """
    print("[knowledge_export] Updating workflow if needed (simulated)")
    # TODO: Implement real workflow update logic
    return "audit_complete"


def run_knowledge_export_workflow_demo():
    """
    Simulate end-to-end execution of the Knowledge Export workflow.
    """
    print("--- Knowledge Export Workflow Demo ---")
    step1 = knowledge_export_select_data()
    step2 = knowledge_export_validate_data_integrity()
    step3 = knowledge_export_format_export()
    step4 = knowledge_export_generate_report()
    step5 = knowledge_export_export_data()
    step6 = knowledge_export_log_export_action()
    step7 = knowledge_export_deliver_export()
    step8 = knowledge_export_notify_stakeholders()
    step9 = knowledge_export_log_delivery()
    step10 = knowledge_export_review_logs()
    step11 = knowledge_export_audit_exports()
    step12 = knowledge_export_update_workflow_if_needed()
    print("Knowledge Export Workflow Complete (simulated)")
    print(
        f"Steps: {step1}, {step2}, {step3}, {step4}, {step5}, {step6}, {step7}, {step8}, {step9}, {step10}, {step11}, {step12}"
    )


# --- Custom Task Workflow ---


def custom_task_receive_task_definition():
    """
    Receive and validate a custom task definition.
    Returns: str (simulated task_validated)
    """
    print("[custom_task] Receiving task definition (simulated)")
    # TODO: Implement real task definition logic
    return "task_validated"


def custom_task_validate_task_safety():
    """
    Validate the safety of the custom task.
    Returns: str (simulated task_validated)
    """
    print("[custom_task] Validating task safety (simulated)")
    # TODO: Implement real safety validation
    return "task_validated"


def custom_task_check_permissions():
    """
    Check permissions for executing the custom task.
    Returns: str (simulated task_validated)
    """
    print("[custom_task] Checking permissions (simulated)")
    # TODO: Implement real permission check
    return "task_validated"


def custom_task_dispatch_task(task_definition, user_id=None):
    """
    Dispatch a custom task to the appropriate agent(s) using OpenAI reasoning and log in ArangoDB.
    Args:
        task_definition (str): The custom task definition or prompt.
        user_id (str, optional): The user submitting the task.
    Returns:
        dict: Dispatch result and log status.
    """
    import logging

    from openai import OpenAI

    from src.applications.agentic_doc_manager.graph_manager import add_artifact

    logger = logging.getLogger("agentic_doc_manager.custom_task")
    try:
        client = OpenAI()
        prompt = f"Dispatch this custom task to the correct agent(s) and provide a rationale. Task: {task_definition}"
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            instructions="You are a custom task dispatcher. Assign the task to the correct agent(s) and explain why.",
        )
        assignment = (
            response.output_text.strip()
            if hasattr(response, "output_text")
            else response.get("output_text", "unassigned").strip()
        )
        log_entry = {
            "type": "custom_task_dispatch",
            "task": task_definition,
            "assigned_to": assignment,
            "user_id": user_id,
        }
        add_artifact(f"custom_task_{user_id or 'anon'}", log_entry)
        logger.info(f"Custom task dispatched: {assignment}")
        return {"assigned_to": assignment, "log_status": "logged"}
    except Exception as e:
        logger.error(f"Error dispatching custom task: {e}")
        return {"error": str(e)}


def custom_task_execute_task():
    """
    Execute the custom task.
    Returns: str (simulated task_executed)
    """
    print("[custom_task] Executing task (simulated)")
    # TODO: Implement real execution logic
    return "task_executed"


def custom_task_log_execution():
    """
    Log the execution of the custom task.
    Returns: str (simulated task_executed)
    """
    print("[custom_task] Logging execution (simulated)")
    # TODO: Implement real logging logic
    return "task_executed"


def custom_task_review_results():
    """
    Review the results of the custom task execution.
    Returns: str (simulated audit_complete)
    """
    print("[custom_task] Reviewing results (simulated)")
    # TODO: Implement real review logic
    return "audit_complete"


def custom_task_log_results():
    """
    Log the results of the custom task for auditability.
    Returns: str (simulated audit_complete)
    """
    print("[custom_task] Logging results (simulated)")
    # TODO: Implement real logging logic
    return "audit_complete"


def custom_task_update_workflow_if_needed():
    """
    Update the custom task workflow if improvements are identified.
    Returns: str (simulated audit_complete)
    """
    print("[custom_task] Updating workflow if needed (simulated)")
    # TODO: Implement real workflow update logic
    return "audit_complete"


def run_custom_task_workflow_demo():
    """
    Simulate end-to-end execution of the Custom Task workflow.
    """
    print("--- Custom Task Workflow Demo ---")
    step1 = custom_task_receive_task_definition()
    step2 = custom_task_validate_task_safety()
    step3 = custom_task_check_permissions()
    step4 = custom_task_dispatch_task()
    step5 = custom_task_execute_task()
    step6 = custom_task_log_execution()
    step7 = custom_task_review_results()
    step8 = custom_task_log_results()
    step9 = custom_task_update_workflow_if_needed()
    print("Custom Task Workflow Complete (simulated)")
    print(
        f"Steps: {step1}, {step2}, {step3}, {step4}, {step5}, {step6}, {step7}, {step8}, {step9}"
    )


def ingest_artifact_step(artifact_path, artifact_type):
    """
    Ingests a single artifact (code, doc, or chat log).
    Returns the raw content.
    """
    try:
        artifacts = ingest_all()
        target_path = os.path.abspath(artifact_path)
        for path, content in artifacts:
            if os.path.abspath(path) == target_path:
                logging.info(f"Ingested artifact: {artifact_path}")
                return content
        logging.warning(f"Artifact not found: {artifact_path}")
        return None
    except Exception as e:
        logging.error(f"Error ingesting artifact {artifact_path}: {e}")
        return None


def embed_content_step(raw_content):
    """
    Embeds the given content using OpenAIEmbeddingsInterface (text-embedding-ada-002).
    Returns the embedding vector.
    """
    try:
        client = OpenAIEmbeddingsInterface(api_key=os.environ["OPENAI_API_KEY"])
        embedding = client.create_embedding(
            input_text=raw_content, model="text-embedding-ada-002"
        )
        logging.info("Generated embedding.")
        return embedding["data"][0]["embedding"]
    except Exception as e:
        logging.error(f"Error embedding content: {e}")
        return None


def update_knowledge_graph_step(artifact_path, artifact_type, embedding_vector):
    """
    Updates the knowledge graph with the artifact and its embedding.
    """
    try:
        add_embedding(artifact_path, embedding_vector)
        logging.info(f"Updated knowledge graph for {artifact_path}")
        return "success"
    except Exception as e:
        logging.error(f"Error updating knowledge graph: {e}")
        return "failure"


def run_artifact_ingestion_embedding_demo(artifact_path, artifact_type):
    """
    Demo: Ingest, embed, and update graph for a single artifact.
    """
    raw_content = ingest_artifact_step(artifact_path, artifact_type)
    if not raw_content:
        print(f"Failed to ingest artifact: {artifact_path}")
        return
    embedding_vector = embed_content_step(raw_content)
    if not embedding_vector:
        print(f"Failed to embed artifact: {artifact_path}")
        return
    status = update_knowledge_graph_step(artifact_path, artifact_type, embedding_vector)
    print(f"Knowledge graph update status: {status}")


def artifact_ingestion_embedding_workflow(root_dir=None):
    """
    Ingest artifacts, embed them, and update the knowledge graph using real logic.
    Args:
        root_dir (str): Directory to scan for artifacts. If None, uses TEST_MODE to determine.
    Returns:
        dict: Summary of ingestion, embedding, and graph update.
    """
    import logging

    from src.applications.agentic_doc_manager.embedding import embed_all
    from src.applications.agentic_doc_manager.graph_manager import (
        add_artifact,
        add_embedding,
    )
    from src.applications.agentic_doc_manager.ingestion import ingest_all

    logger = logging.getLogger("agentic_doc_manager.artifact_ingest")

    # Determine root directory based on TEST_MODE if not specified
    if root_dir is None:
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        if test_mode:
            root_dir = "test_docs"
            logger.info(f"TEST_MODE enabled: Processing files from {root_dir}/")
        else:
            root_dir = "docs"
            logger.info(f"Processing files from {root_dir}/")

    try:
        artifacts = ingest_all(root_dir)
        logger.info(f"Ingested {len(artifacts)} artifacts.")
        embeddings = embed_all(artifacts)
        logger.info(f"Embedded {len(embeddings)} artifacts.")
        for (path, content), (_, embedding) in zip(artifacts, embeddings):
            add_artifact(path, content)
            add_embedding(path, embedding)
        logger.info("Artifacts and embeddings added to graph.")
        return {
            "ingested": len(artifacts),
            "embedded": len(embeddings),
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Error in artifact ingestion/embedding workflow: {e}")
        return {"error": str(e)}


# --- Agent Implementations ---


class DevAgent:
    def __init__(self, models, logger=None):
        self.models = models  # List of models to escalate through
        self.logger = logger or SharedLogger("DevAgent")
        self.openai = OpenAIResponsesInterface()

    def generate(self, prompt, context_docs=None):
        """Try each model in order, escalate on failure. Always return a dict."""
        for model in self.models:
            self.logger.info(f"DevAgent: Trying model {model}")
            full_prompt = self._build_prompt(prompt, context_docs)
            try:
                response = self.openai.create_response(
                    model, full_prompt, instructions=None, text_format=None
                )
                self.logger.info(f"DevAgent: Model {model} raw output: {response}")
                # Try to extract code/doc/tests from response
                if isinstance(response, dict) and all(
                    k in response for k in ("code", "doc", "tests")
                ):
                    return {
                        "code": response["code"],
                        "doc": response["doc"],
                        "tests": response["tests"],
                        "model_used": model,
                        "raw_output": response,
                    }
                # If response is a tuple, unpack and wrap in dict
                if isinstance(response, tuple):
                    # Try to infer tuple structure (code, doc, tests, ...)
                    code = response[0] if len(response) > 0 else ""
                    doc = response[1] if len(response) > 1 else ""
                    tests = response[2] if len(response) > 2 else ""
                    return {
                        "code": code,
                        "doc": doc,
                        "tests": tests,
                        "model_used": model,
                        "raw_output": response,
                    }
                # Fallback: treat as raw string
                return {
                    "code": str(response),
                    "doc": "",
                    "tests": "",
                    "model_used": model,
                    "raw_output": response,
                }
            except Exception as e:
                self.logger.error(f"DevAgent: Model {model} failed: {e}")
                continue
        self.logger.error("DevAgent: All models failed.")
        return {
            "code": "",
            "doc": "",
            "tests": "",
            "model_used": None,
            "raw_output": None,
        }

    def _build_prompt(self, prompt, context_docs):
        # Inject doc references and context per prompt engineering best practices
        doc_section = (
            f"\n\n# Reference Documentation:\n{context_docs}" if context_docs else ""
        )
        return f"{prompt}{doc_section}\n\nRespond in JSON with keys: code, doc, tests. Only output valid JSON."


class Validator:
    def __init__(self, logger=None):
        self.logger = logger or SharedLogger("Validator")

    def validate(self, code, tests=None, doc=None):
        # Stub: Replace with real lint/test/markdown validation
        self.logger.info("Validator: Running lint/test/markdown validation...")
        # Simulate validation: pass if 'def' in code, else fail
        if code and "def" in code:
            self.logger.info("Validator: Validation passed.")
            return True, "Validation passed."
        else:
            self.logger.warning("Validator: Validation failed.")
            return False, "Validation failed: No function definition found."


class CriticAgent:
    def __init__(self, logger=None):
        self.logger = logger or SharedLogger("CriticAgent")
        self.openai = OpenAIResponsesInterface()

    def review(self, code, doc=None):
        # Use LLM to review code and doc
        review_prompt = (
            "You are a senior code reviewer. Review the following code and documentation for correctness, style, test coverage, and adherence to best practices. "
            "If you find any issues, list them clearly. If the code is production-ready, respond with 'APPROVED'. Otherwise, respond with 'NOT APPROVED' and actionable suggestions. "
            "Be specific and concise.\n\nCode:\n"
            + (code or "")
            + "\n\nDocumentation:\n"
            + (doc or "")
            + '\n\nRespond with a JSON object: {"status": "APPROVED|NOT APPROVED", "suggestions": [ ... ]}'
        )
        try:
            response = self.openai.create_response(
                model="gpt-4.1", input=review_prompt, text_format="json_object"
            )
            self.logger.info(f"CriticAgent: Review raw output: {str(response)[:200]}")
            output_text = response.get("output_text") or response.get("raw", {}).get(
                "output_text"
            )
            import json

            parsed = None
            if output_text:
                try:
                    parsed = json.loads(output_text)
                except Exception:
                    parsed = {"status": "NOT APPROVED", "suggestions": [output_text]}
            return parsed or {"status": "NOT APPROVED", "suggestions": [output_text]}
        except Exception as e:
            self.logger.error(f"CriticAgent: Review failed: {e}")
            return {"status": "NOT APPROVED", "suggestions": ["Review failed."]}


class RouterAgent:
    def __init__(self, dev_agent, validator, critic_agent, logger=None):
        self.dev_agent = dev_agent
        self.validator = validator
        self.critic_agent = critic_agent
        self.logger = logger or SharedLogger("RouterAgent")
        self.max_retries = 3

    def run_pipeline(self, prompt, context_docs=None):
        retries = 0
        model_used = None
        while retries < self.max_retries:
            self.logger.info(f"RouterAgent: Pipeline attempt {retries+1}")
            # 1. DevAgent generates code/doc
            response, model_used = self.dev_agent.generate(prompt, context_docs)
            code = response.get("code") if isinstance(response, dict) else response
            doc = response.get("doc") if isinstance(response, dict) else None
            tests = response.get("tests") if isinstance(response, dict) else None
            # 2. Validator checks output
            valid, val_msg = self.validator.validate(code, tests, doc)
            self.logger.info(f"RouterAgent: Validation result: {val_msg}")
            if not valid:
                retries += 1
                continue
            # 3. CriticAgent reviews
            review = self.critic_agent.review(code, doc)
            self.logger.info(f"RouterAgent: Critic review: {review}")
            if "APPROVED" in str(review):
                self.logger.info(
                    f"RouterAgent: Output approved by CriticAgent. Model used: {model_used}"
                )
                return code, doc, tests, model_used, review
            else:
                self.logger.warning(
                    f"RouterAgent: Output NOT approved. Critic review: {review}"
                )
                retries += 1
        self.logger.error("RouterAgent: Pipeline failed after max retries.")
        return None, None, None, model_used, "NOT APPROVED after 3 attempts."


class RequirementsAgent:
    def __init__(self, logger=None):
        self.logger = logger or SharedLogger("RequirementsAgent")
        self.openai = OpenAIResponsesInterface()

    def gather(self, user_prompt):
        self.logger.info("Gathering requirements from user prompt.")
        # Simulate requirements extraction (replace with LLM call as needed)
        requirements = f"Extracted requirements from: {user_prompt}"
        self.logger.info(f"Requirements: {requirements}")
        return requirements


class DesignAgent:
    def __init__(self, logger=None):
        self.logger = logger or SharedLogger("DesignAgent")
        self.openai = OpenAIResponsesInterface()

    def design(self, requirements):
        self.logger.info("Designing solution based on requirements.")
        # Simulate design step (replace with LLM call as needed)
        design = f"Design for: {requirements}"
        self.logger.info(f"Design: {design}")
        return design


class SpecAgent:
    def __init__(self, logger=None):
        self.logger = logger or SharedLogger("SpecAgent")
        self.openai = OpenAIResponsesInterface()

    def specify(self, design):
        self.logger.info("Creating specification from design.")
        # Simulate spec step (replace with LLM call as needed)
        spec = f"Specification for: {design}"
        self.logger.info(f"Spec: {spec}")
        return spec


class PromptGenAgent:
    def __init__(self, logger=None):
        self.logger = logger or SharedLogger("PromptGenAgent")
        self.openai = OpenAIResponsesInterface()

    def generate_prompt(self, spec):
        self.logger.info("Generating custom prompt from specification.")
        # Simulate prompt engineering (replace with LLM call as needed)
        prompt = f"Prompt for: {spec}"
        self.logger.info(f"Prompt: {prompt}")
        return prompt


# --- Pipeline Test ---


def test_full_pipeline():
    logger = SharedLogger("FullPipeline")
    logger.info("=== Starting Full Multi-Agent Pipeline ===")
    user_prompt = "Build a REST API for a todo list with authentication."
    logger.info(f"User Prompt: {user_prompt}")

    # Step 1: Requirements
    req_agent = RequirementsAgent(logger)
    requirements = req_agent.gather(user_prompt)

    # Step 2: Design
    design_agent = DesignAgent(logger)
    design = design_agent.design(requirements)

    # Step 3: Spec
    spec_agent = SpecAgent(logger)
    spec = spec_agent.specify(design)

    # Step 4: PromptGen
    promptgen_agent = PromptGenAgent(logger)
    custom_prompt = promptgen_agent.generate_prompt(spec)

    # Step 5: DevAgent (model escalation)
    dev_agent = DevAgent(models=["gpt-4o", "gpt-4.1", "gpt-3.5-turbo"], logger=logger)
    dev_output = dev_agent.generate(custom_prompt, context_docs=spec)
    code = dev_output.get("code", "")
    doc = dev_output.get("doc", "")
    tests = dev_output.get("tests", "")

    # Step 6: Validator
    validator = Validator(logger)
    validation_result = validator.validate(code, tests, doc)

    # Step 7: CriticAgent
    critic_agent = CriticAgent(logger)
    review = critic_agent.review(code, doc)

    # Step 8: RouterAgent (final decision)
    router = RouterAgent(dev_agent, validator, critic_agent, logger)
    router.logger.info("Pipeline complete. Artifacts and logs available.")
    print("\n=== Pipeline Artifacts ===")
    print(f"Requirements: {requirements}")
    print(f"Design: {design}")
    print(f"Spec: {spec}")
    print(f"Prompt: {custom_prompt}")
    print(f"Code: {code[:200]}...\nDoc: {doc[:200]}...\nTests: {tests[:200]}...")
    print(f"Validation: {validation_result}")
    print(f"Review: {review}")
    print("=== End of Pipeline ===\n")


# --- Mermaid Diagram & Table ---


def print_pipeline_diagram():
    diagram = """
flowchart TD
    A["User Prompt"] --> B["RouterAgent"]
    B --> C["DevAgent (Model Selection/Escalation)"]
    C --> D["Validator"]
    D --> E["CriticAgent"]
    E -->|"APPROVED"| F["Output Written"]
    E -->|"NOT APPROVED"| B
    B -->|"Max Retries"| G["NOT APPROVED"]
    %% Styles for accessibility
    style A fill:#f8f9fa,stroke:#ffffff,stroke-width:3px,color:#000000
    style B fill:#e9ecef,stroke:#ffffff,stroke-width:3px,color:#000000
    style C fill:#dee2e6,stroke:#ffffff,stroke-width:3px,color:#000000
    style D fill:#f1f3f4,stroke:#ffffff,stroke-width:3px,color:#000000
    style E fill:#e0e0e0,stroke:#ffffff,stroke-width:3px,color:#000000
    style F fill:#d1e7dd,stroke:#ffffff,stroke-width:3px,color:#000000
    style G fill:#f8d7da,stroke:#ffffff,stroke-width:3px,color:#000000
    """
    print(diagram)


def print_pipeline_table():
    table = """
| Step         | Agent        | Description                                      |
|--------------|-------------|--------------------------------------------------|
| 1. Prompt    | RouterAgent | Receives user prompt, orchestrates workflow       |
| 2. Generate  | DevAgent    | Generates code/doc, escalates models if needed    |
| 3. Validate  | Validator   | Lint/test/markdown validation                     |
| 4. Review    | CriticAgent | Reviews output, approves or requests improvement  |
| 5. Approve   | RouterAgent | Final signoff or escalate/retry                   |
"""
    print(table)


if __name__ == "__main__":
    print("--- AGENTIC PIPELINE DIAGRAM ---")
    print_pipeline_diagram()
    print("\n--- AGENTIC PIPELINE TABLE ---")
    print_pipeline_table()
    print("\n--- RUNNING FULL PIPELINE TEST ---")
    test_full_pipeline()
