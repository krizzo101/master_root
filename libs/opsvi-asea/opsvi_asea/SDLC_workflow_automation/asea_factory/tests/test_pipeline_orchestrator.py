import pytest
from asea_factory.orchestrator import PipelineOrchestrator


def test_pipeline_orchestrator():
    orchestrator = PipelineOrchestrator()
    # This will run the full pipeline (ensure test environment is safe)
    result = orchestrator.run_pipeline()
    assert result is not None
    assert "requirements" in result
    assert "docs" in result
