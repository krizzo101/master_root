import os

import pytest
import yaml

WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "../workflows")


@pytest.mark.parametrize(
    "fname",
    [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith(".yml") or f.endswith(".yaml")],
)
def test_workflow_structure(fname):
    path = os.path.join(WORKFLOWS_DIR, fname)
    with open(path) as f:
        workflow = yaml.safe_load(f)
    assert "steps" in workflow, f"No 'steps' in {fname}"
    assert "triggers" in workflow, f"No 'triggers' in {fname}"
    assert "outputs" in workflow, f"No 'outputs' in {fname}"
    assert "compliance" in workflow, f"No 'compliance' in {fname}"
    for step in workflow["steps"]:
        assert "id" in step, f"Step missing 'id' in {fname}"
        assert "agent" in step, f"Step missing 'agent' in {fname}"
        assert "input" in step, f"Step missing 'input' in {fname}"
        assert "output" in step, f"Step missing 'output' in {fname}"
