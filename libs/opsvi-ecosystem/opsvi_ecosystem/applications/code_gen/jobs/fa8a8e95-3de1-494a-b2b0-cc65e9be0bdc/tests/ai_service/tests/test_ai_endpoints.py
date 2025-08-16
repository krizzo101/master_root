import random

from ai_service.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def sample_tasks(n=3):
    return [
        {
            "id": f"task-{i}",
            "title": f"Task {i} main stuff",
            "description": f"{['Write code', 'Review PR', 'Deploy', 'Write docs'][i%4]}",
            "importance": random.randint(1, 10),
            "deadline": None,
            "assigned_to": None,
            "status": "pending",
            "dependencies": [],
        }
        for i in range(n)
    ]


def sample_members():
    return [
        {
            "id": "member-1",
            "name": "Alice",
            "skill_level": 8,
            "availability": 1.0,
            "role": "Developer",
        },
        {
            "id": "member-2",
            "name": "Bob",
            "skill_level": 6,
            "availability": 0.8,
            "role": "QA Engineer",
        },
    ]


def test_prioritize():
    resp = client.post(
        "/prioritize", json={"tasks": sample_tasks(3), "members": sample_members()}
    )
    assert resp.status_code == 200
    res = resp.json()
    assert "ordered_ids" in res["result"]
    assert len(res["result"]["ordered_ids"]) == 3


def test_estimate():
    resp = client.post(
        "/estimate", json={"tasks": sample_tasks(5), "members": sample_members()}
    )
    assert resp.status_code == 200
    res = resp.json()
    assert "estimates" in res["result"]
    assert len(res["result"]["estimates"]) == 5


def test_detect_dependencies():
    tasks = sample_tasks(4)
    # Two overlapping tasks
    tasks[1]["title"] = tasks[0]["title"]
    tasks[1]["description"] = tasks[0]["description"]
    resp = client.post(
        "/detect_dependencies", json={"tasks": tasks, "members": sample_members()}
    )
    assert resp.status_code == 200
    res = resp.json()
    assert "dependencies" in res["result"]
    assert set(res["result"]["dependencies"]) == {t["id"] for t in tasks}


def test_suggest_schedule():
    tasks = sample_tasks(4)
    tasks[0]["dependencies"] = [tasks[1]["id"]]
    resp = client.post(
        "/suggest_schedule", json={"tasks": tasks, "members": sample_members()}
    )
    assert resp.status_code == 200
    res = resp.json()
    assert "schedules" in res["result"]
    assert len(res["result"]["schedules"]) == 4
    for val in res["result"]["schedules"].values():
        assert "assigned_to" in val
        assert "start" in val
        assert "end" in val
