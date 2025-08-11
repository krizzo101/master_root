# Dynamically import app
import sys

from fastapi.testclient import TestClient

sys.path.append(".")

from ..server import app

client = TestClient(app)


def rpc(method, params=None):
    return client.post(
        "/rpc",
        json={"jsonrpc": "2.0", "id": "test", "method": method, "params": params or {}},
    )


def test_list_methods():
    res = rpc("system.listMethods")
    assert res.status_code == 200
    methods = res.json()["result"]
    assert "dev_agent.generate_feature" in methods


def test_dummy_feature():
    res = rpc(
        "dev_agent.generate_feature", {"spec": "dummy spec", "repo_state_hash": "hash"}
    )
    assert res.status_code == 200
    result = res.json()["result"]
    assert "branch_name" in result
