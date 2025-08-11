"""
Doc Cleanup Workflow Runner

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

from src.applications.doc_cleanup.embedding import embed_all
from src.applications.doc_cleanup.graph_manager import (
    add_artifact,
    add_embedding,
)
from src.applications.doc_cleanup.ingestion import ingest_all
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
    Guide onboarding using OpenAIResponsesInterface for reasoning.
    Model: gpt-4.1 (OpenAIResponsesInterface)
    """
    client = OpenAIResponsesInterface()
    # Simulate a reasoning step (replace with real prompt/logic as needed)
    prompt = f"Guide onboarding for user {user_id} with profile {agent_profile}."
    # In a real implementation, you would create a thread and call create_response
    # Here, we just return a stub value
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
    Run the onboarding workflow using doc_cleanup steps (OpenAI interfaces for reasoning/embedding).
    """
    onboarding_status = guide_onboarding(user_id, agent_profile)
    import_log, normalized_artifacts = bulk_import(artifact_batch)
    cleaned_artifacts, metadata = normalize_artifacts(normalized_artifacts)
    embedding_status = embed_artifacts(cleaned_artifacts)
    graph_update_status = update_knowledge_graph(metadata, embedding_status)
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


def feedback_assign_to_agent():
    """
    Assign actionable feedback to the appropriate agent.
    Returns: str (simulated actionable_feedback_identified)
    """
    print("[feedback_integration] Assigning feedback to agent (simulated)")
    # TODO: Implement real assignment logic
    return "actionable_feedback_identified"


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
    Returns: str (simulated incident_logged)
    """
    print("[incident_handling] Monitoring systems (simulated)")
    # TODO: Implement real monitoring logic
    return "incident_logged"


def incident_detect_anomaly():
    """
    Detect anomalies indicating incidents.
    Returns: str (simulated incident_logged)
    """
    print("[incident_handling] Detecting anomaly (simulated)")
    # TODO: Implement real anomaly detection
    return "incident_logged"


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


def incident_assign_to_agent():
    """
    Assign actionable incident to the appropriate agent.
    Returns: str (simulated actionable_incident_identified)
    """
    print("[incident_handling] Assigning incident to agent (simulated)")
    # TODO: Implement real assignment logic
    return "actionable_incident_identified"


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


def knowledge_export_export_data():
    """
    Export data to required format/location.
    Returns: str (simulated export_completed)
    """
    print("[knowledge_export] Exporting data (simulated)")
    # TODO: Implement real export logic
    return "export_completed"


def knowledge_export_log_export_action():
    """
    Log the export action for auditability.
    Returns: str (simulated export_completed)
    """
    print("[knowledge_export] Logging export action (simulated)")
    # TODO: Implement real logging logic
    return "export_completed"


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


def inventory_receive_task_definition():
    """
    Receive and validate a custom task definition.
    Returns: str (simulated task_validated)
    """
    print("[inventory] Receiving task definition (simulated)")
    # TODO: Implement real task definition logic
    return "task_validated"


def inventory_validate_task_safety():
    """
    Validate the safety of the custom task.
    Returns: str (simulated task_validated)
    """
    print("[inventory] Validating task safety (simulated)")
    # TODO: Implement real safety validation
    return "task_validated"


def inventory_check_permissions():
    """
    Check permissions for executing the custom task.
    Returns: str (simulated task_validated)
    """
    print("[inventory] Checking permissions (simulated)")
    # TODO: Implement real permission check
    return "task_validated"


def inventory_dispatch_task():
    """
    Dispatch the custom task to the appropriate agent(s).
    Returns: str (simulated task_executed)
    """
    print("[inventory] Dispatching task (simulated)")
    # TODO: Implement real dispatch logic
    return "task_executed"


def inventory_execute_task():
    """
    Execute the custom task.
    Returns: str (simulated task_executed)
    """
    print("[inventory] Executing task (simulated)")
    # TODO: Implement real execution logic
    return "task_executed"


def inventory_log_execution():
    """
    Log the execution of the custom task.
    Returns: str (simulated task_executed)
    """
    print("[inventory] Logging execution (simulated)")
    # TODO: Implement real logging logic
    return "task_executed"


def inventory_review_results():
    """
    Review the results of the custom task execution.
    Returns: str (simulated audit_complete)
    """
    print("[inventory] Reviewing results (simulated)")
    # TODO: Implement real review logic
    return "audit_complete"


def inventory_log_results():
    """
    Log the results of the custom task for auditability.
    Returns: str (simulated audit_complete)
    """
    print("[inventory] Logging results (simulated)")
    # TODO: Implement real logging logic
    return "audit_complete"


def inventory_update_workflow_if_needed():
    """
    Update the custom task workflow if improvements are identified.
    Returns: str (simulated audit_complete)
    """
    print("[inventory] Updating workflow if needed (simulated)")
    # TODO: Implement real workflow update logic
    return "audit_complete"


def run_inventory_workflow_demo():
    """
    Simulate end-to-end execution of the Custom Task workflow.
    """
    print("--- Custom Task Workflow Demo ---")
    step1 = inventory_receive_task_definition()
    step2 = inventory_validate_task_safety()
    step3 = inventory_check_permissions()
    step4 = inventory_dispatch_task()
    step5 = inventory_execute_task()
    step6 = inventory_log_execution()
    step7 = inventory_review_results()
    step8 = inventory_log_results()
    step9 = inventory_update_workflow_if_needed()
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


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            run_all_workflows()
        elif sys.argv[1] == "--onboarding-demo":
            run_onboarding_workflow()
        elif sys.argv[1] == "--feedback-demo":
            run_feedback_integration_workflow_demo()
        elif sys.argv[1] == "--incident-demo":
            run_incident_handling_workflow_demo()
        elif sys.argv[1] == "--knowledge-export-demo":
            run_knowledge_export_workflow_demo()
        elif sys.argv[1] == "--custom-task-demo":
            run_inventory_workflow_demo()
        elif sys.argv[1] == "--artifact-ingest-demo":
            if len(sys.argv) < 4:
                print(
                    "Usage: python agent_workflows.py --artifact-ingest-demo <artifact_path> <artifact_type>"
                )
            else:
                run_artifact_ingestion_embedding_demo(sys.argv[2], sys.argv[3])
        else:
            yaml_file = sys.argv[1]
            if not os.path.exists(yaml_file):
                print(f"File not found: {yaml_file}")
            else:
                run_workflow_from_yaml(yaml_file)
    else:
        print(
            "Usage: python agent_workflows.py <workflow_yaml> | --all | --onboarding-demo | --feedback-demo | --incident-demo | --knowledge-export-demo | --custom-task-demo | --artifact-ingest-demo <artifact_path> <artifact_type>"
        )
