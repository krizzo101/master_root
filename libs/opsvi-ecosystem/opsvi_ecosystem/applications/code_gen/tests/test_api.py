"""API endpoint smoke tests."""

from applications.code_gen.api import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_chat_status_flow(tmp_path, monkeypatch):  # noqa: D103
    # Patch output directory to tmp_path for isolation
    import applications.code_gen.api as api_module  # noqa: WPS433

    monkeypatch.setitem(api_module.__dict__, "_jobs", {})

    res = client.post(
        "/chat", json="Create a simple web API with FastAPI for managing tasks"
    )
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    status = client.get(f"/status/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] in {"in_progress", "completed"}
