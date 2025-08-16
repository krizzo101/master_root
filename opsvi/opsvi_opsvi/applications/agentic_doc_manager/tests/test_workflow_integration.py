import os
import sys

# Ensure project root is in sys.path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
)

from src.applications.agentic_doc_manager.agent_workflows import (
    artifact_ingestion_embedding_workflow,
    custom_task_dispatch_task,
    feedback_assign_to_agent,
    guide_onboarding,
    incident_assign_to_agent,
    incident_monitor_systems,
    knowledge_export_export_data,
    run_onboarding_workflow,
)


def test_artifact_ingestion_embedding_workflow(monkeypatch):
    # Mock dependencies
    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.ingestion.ingest_all",
        lambda root_dir: [("/tmp/test.py", "print('hello world')")],
    )
    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.embedding.embed_all",
        lambda artifacts: [(artifacts[0][0], [0.1, 0.2, 0.3])],
    )
    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.graph_manager.add_artifact",
        lambda path, content: None,
    )
    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.graph_manager.add_embedding",
        lambda path, embedding: None,
    )
    result = artifact_ingestion_embedding_workflow("/tmp")
    assert result["ingested"] == 1
    assert result["embedded"] == 1
    assert result["status"] == "success"


def test_feedback_assign_to_agent(monkeypatch):
    class DummyClient:
        def create_response(self, **kwargs):
            return {"output_text": "reviewer_agent"}

    monkeypatch.setattr(
        "src.shared.openai_interfaces.responses_interface.OpenAIResponsesInterface",
        lambda: DummyClient(),
    )
    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.graph_manager.add_artifact",
        lambda path, log_entry: None,
    )
    result = feedback_assign_to_agent("Needs more examples.", user_id="user123")
    assert result["assigned_to"] == "reviewer_agent"
    assert result["log_status"] == "logged"


def test_incident_assign_to_agent(monkeypatch):
    class DummyClient:
        def create_response(self, **kwargs):
            return {"output_text": "incident_handler"}

    monkeypatch.setattr(
        "src.shared.openai_interfaces.responses_interface.OpenAIResponsesInterface",
        lambda: DummyClient(),
    )
    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.graph_manager.add_artifact",
        lambda path, log_entry: None,
    )
    result = incident_assign_to_agent("Build failed.", context="CI pipeline")
    assert result["assigned_to"] == "incident_handler"
    assert result["log_status"] == "logged"


def test_custom_task_dispatch_task(monkeypatch):
    class DummyClient:
        def create_response(self, **kwargs):
            return {"output_text": "custom_agent"}

    monkeypatch.setattr(
        "src.shared.openai_interfaces.responses_interface.OpenAIResponsesInterface",
        lambda: DummyClient(),
    )
    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.graph_manager.add_artifact",
        lambda path, log_entry: None,
    )
    result = custom_task_dispatch_task("Summarize all docs.", user_id="user456")
    assert result["assigned_to"] == "custom_agent"
    assert result["log_status"] == "logged"


def test_knowledge_export_export_data(monkeypatch):
    class DummyCol:
        def find(self, query):
            return [{"path": "a.py", "content": "print(1)"}]

    class DummyDB:
        def collection(self, name):
            return DummyCol()

    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.graph_manager.get_db",
        lambda: DummyDB(),
    )
    monkeypatch.setattr(
        "src.applications.agentic_doc_manager.graph_manager.add_artifact",
        lambda path, log_entry: None,
    )
    result = knowledge_export_export_data({}, format="json")
    assert result["exported_count"] == 1
    assert result["log_status"] == "logged"
    assert "a.py" in result["data"]


def test_incident_monitor_systems(tmp_path, monkeypatch):
    # Create a temporary incident_input.txt
    incident_file = tmp_path / "incident_input.txt"
    incident_file.write_text("Error: Out of memory\nWarning: Disk full\n")
    monkeypatch.setattr("os.path.dirname", lambda _: str(tmp_path))
    incidents = incident_monitor_systems()
    assert isinstance(incidents, list)
    assert "Error: Out of memory" in incidents
    assert "Warning: Disk full" in incidents


def test_guide_onboarding(capsys):
    result = guide_onboarding("user42", "reviewer")
    captured = capsys.readouterr()
    assert "Guiding onboarding for user user42 with profile reviewer" in captured.out
    assert result == "onboarding_complete"


def test_run_onboarding_workflow(capsys):
    run_onboarding_workflow(
        user_id="user42", agent_profile="reviewer", artifact_batch=["docA", "codeB"]
    )
    captured = capsys.readouterr()
    assert "Onboarding Status: onboarding_complete" in captured.out
    assert "Imported 2 artifacts." in captured.out
    assert "embedded_docA_cleaned" in captured.out
    assert "embedded_codeB_cleaned" in captured.out
