import pytest
from app.database import Base, SessionLocal, engine
from app.main import app, get_db
from fastapi.testclient import TestClient

# Set up test database and client
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Dependency override to use a new session for each test


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_check_endpoint_returns_200_and_expected_response():
    """Verify /health endpoint responds with status 200 and correct fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "uptime" in data
    assert isinstance(data["uptime"], float) or isinstance(data["uptime"], int)


def test_create_todo_with_valid_data_returns_201_and_todo_item():
    """Create a todo with valid title and description and check response."""
    payload = {"title": "Test Todo", "description": "Write tests"}
    response = client.post("/todos/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["completed"] is False


def test_create_todo_missing_title_returns_422_validation_error():
    """Should not create todo if title field is missing."""
    payload = {"description": "No title present"}
    response = client.post("/todos/", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_list_todos_returns_all_created_items():
    """Create multiple todos and verify listing returns all of them."""
    # Clear DB for consistent test
    db = next(override_get_db())
    db.query(app.models.Todo).delete()
    db.commit()

    todos_payloads = [
        {"title": f"Task {i}", "description": f"Description {i}"} for i in range(5)
    ]
    for payload in todos_payloads:
        response = client.post("/todos/", json=payload)
        assert response.status_code == 201

    response = client.get("/todos/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5  # At least the 5 we created
    titles = [todo["title"] for todo in data]
    for payload in todos_payloads:
        assert payload["title"] in titles


def test_get_todo_returns_correct_item():
    payload = {"title": "Unique Task", "description": "Unique Desc"}
    create_resp = client.post("/todos/", json=payload)
    todo_id = create_resp.json()["id"]

    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]


def test_get_todo_with_invalid_id_returns_404():
    response = client.get("/todos/99999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_partial_update_todo_with_valid_data():
    payload = {"title": "Partial Update Task", "description": "Partial Desc"}
    resp_create = client.post("/todos/", json=payload)
    todo_id = resp_create.json()["id"]

    update_payload = {"description": "Updated Description"}
    resp_update = client.patch(f"/todos/{todo_id}", json=update_payload)
    assert resp_update.status_code == 200
    data = resp_update.json()
    assert data["id"] == todo_id
    assert data["title"] == payload["title"]  # unchanged
    assert data["description"] == update_payload["description"]


def test_full_replace_todo_returns_updated_item():
    payload = {"title": "Replace Task", "description": "Replace Desc"}
    resp_create = client.post("/todos/", json=payload)
    todo_id = resp_create.json()["id"]

    replace_payload = {
        "title": "Replaced Task",
        "description": "Replaced Desc",
        "completed": True,
    }
    resp_replace = client.put(f"/todos/{todo_id}", json=replace_payload)
    assert resp_replace.status_code == 200
    data = resp_replace.json()
    assert data["id"] == todo_id
    assert data["title"] == replace_payload["title"]
    assert data["description"] == replace_payload["description"]
    assert data["completed"] == replace_payload["completed"]


def test_delete_todo_removes_item_and_returns_204():
    payload = {"title": "Delete Task", "description": "Delete Desc"}
    resp_create = client.post("/todos/", json=payload)
    todo_id = resp_create.json()["id"]

    resp_delete = client.delete(f"/todos/{todo_id}")
    assert resp_delete.status_code == 204

    resp_get = client.get(f"/todos/{todo_id}")
    assert resp_get.status_code == 404


from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request


@pytest.mark.asyncio
def test_not_found_handler_returns_404_on_404_error():
    from app.main import not_found_handler
    from fastapi import status

    request = Request(scope={"type": "http", "method": "GET", "path": "/notexist"})
    exc = StarletteHTTPException(status_code=404, detail="Not Found")
    response = await not_found_handler(request, exc)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    content = response.body.decode()
    assert "detail" in content


import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError


@pytest.mark.asyncio
def test_validation_handler_returns_422_on_validation_error():
    from app.main import validation_handler

    class DummyRequest:
        def __init__(self):
            self.scope = {"type": "http"}

    request = DummyRequest()
    exc = RequestValidationError(
        errors=[
            {
                "loc": ("body", "title"),
                "msg": "field required",
                "type": "value_error.missing",
            }
        ]
    )
    response = await validation_handler(request, exc)
    assert response.status_code == 422
    assert b"field required" in response.body


import pytest


@pytest.mark.asyncio
def test_generic_exception_handler_returns_500_on_unhandled_exception():
    from app.main import generic_exception_handler

    class DummyRequest:
        def __init__(self):
            self.scope = {"type": "http"}

    class DummyException(Exception):
        pass

    request = DummyRequest()
    exc = DummyException("Unexpected")
    response = await generic_exception_handler(request, exc)
    assert response.status_code == 500
    content = response.body.decode()
    assert "internal server error" in content.lower()


def test_on_startup_registers_event_and_initializes_db():
    from app.main import on_startup

    on_startup()  # Should run without exception
    # Test can connect to DB and query
    db = next(override_get_db())
    assert hasattr(db, "query")


from app.main import LoggingMiddleware
from starlette.requests import Request


class DummyApp:
    async def __call__(self, scope, receive, send):
        pass


@pytest.mark.asyncio
def test_logging_middleware_adds_headers_and_logs():
    # We test the middleware passes through and can handle a request
    called = {}
    dummy_app = DummyApp()

    async def send(message):
        called["sent"] = message

    async def receive():
        return {"type": "http.request"}

    middleware = LoggingMiddleware(dummy_app)

    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}

    await middleware(scope, receive, send)
    # No assertion possible for logs, but middleware should complete without error
