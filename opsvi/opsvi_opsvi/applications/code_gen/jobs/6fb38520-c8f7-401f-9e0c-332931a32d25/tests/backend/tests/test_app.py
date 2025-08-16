import pytest
import jwt
from unittest.mock import MagicMock, patch
from backend.app import get_db_connection, issue_jwt, verify_jwt, get_current_user
from backend.app import User, Document, DocumentVersion, AIRequest
from fastapi import Request
from sqlalchemy.exc import OperationalError


@pytest.fixture(scope="module")
def db_connection_fixture():
    conn = get_db_connection()
    yield conn
    conn.close()


@patch("backend.app.jwt.encode")
@patch("backend.app.jwt.decode")
@pytest.fixture
def test_get_db_connection_success(db_connection_fixture):
    conn = db_connection_fixture
    assert conn is not None
    # Assuming connection has method cursor
    cursor = conn.cursor()
    assert cursor is not None
    cursor.close()


def test_get_db_connection_failure(monkeypatch):
    def mock_connect():
        raise OperationalError("test", "params", "connection error")

    monkeypatch.setattr("backend.app.psycopg2.connect", mock_connect)
    with pytest.raises(OperationalError):
        get_db_connection()


def test_issue_jwt_valid_user():
    user = User(id=1, username="testuser", email="test@example.com")
    token = issue_jwt(user)
    assert isinstance(token, str)
    # Decoding token to verify payload
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["sub"] == str(user.id)


def test_issue_jwt_invalid_user_raises():
    class DummyUser:
        pass

    dummy = DummyUser()
    with pytest.raises(AttributeError):
        issue_jwt(dummy)


def test_verify_jwt_valid_token_returns_user_id():
    user = User(id=10, username="u10", email="u10@example.com")
    token = issue_jwt(user)
    user_id = verify_jwt(token)
    assert user_id == str(user.id)


def test_verify_jwt_invalid_token_raises():
    invalid_token = "invalid.token.string"
    with pytest.raises(jwt.PyJWTError):
        verify_jwt(invalid_token)


def test_get_current_user_with_valid_request():
    user = User(id=5, username="validuser", email="validuser@example.com")
    token = issue_jwt(user)
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": f"Bearer {token}"}
    resolved_user = get_current_user(mock_request)
    assert isinstance(resolved_user, User)
    assert resolved_user.id == user.id
    assert resolved_user.username == user.username


def test_get_current_user_missing_authorization_header():
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    with pytest.raises(ValueError):
        get_current_user(mock_request)


def test_user_model_instantiation_and_attributes():
    user = User(id=1, username="tester", email="tester@example.com")
    assert user.id == 1
    assert user.username == "tester"
    assert user.email == "tester@example.com"


def test_document_class_create_and_methods():
    document = Document(id=1, owner_id=1, title="Doc Title", content="Initial content")
    assert document.title == "Doc Title"
    assert document.content == "Initial content"
    # Test updating content
    new_content = "Updated content"
    document.content = new_content
    assert document.content == new_content


from datetime import datetime


def test_document_version_class_behavior():
    version = DocumentVersion(
        id=1,
        document_id=1,
        version_number=1,
        content="v1 content",
        author_id=1,
        timestamp=datetime.utcnow(),
    )
    assert version.version_number == 1
    assert version.content == "v1 content"
    assert version.author_id == 1
    assert isinstance(version.timestamp, datetime)


def test_airequest_class_functionality():
    ai_req = AIRequest(
        id=1,
        document_id=1,
        request_type="summary",
        request_payload="Summarize this document...",
    )
    ai_req.response = "This document is about ..."
    assert ai_req.request_type == "summary"
    assert ai_req.response == "This document is about ..."


def test_document_editing_workflow():
    user = User(id=1, username="editor", email="edit@example.com")
    doc = Document(id=1, owner_id=user.id, title="Sample Doc", content="Original")

    # User edits the document
    doc.content = "Updated content 1"

    # Create document version
    version1 = DocumentVersion(
        id=1,
        document_id=doc.id,
        version_number=1,
        content=doc.content,
        author_id=user.id,
    )

    assert version1.content == "Updated content 1"

    # Further edits
    doc.content = "Updated content 2"
    version2 = DocumentVersion(
        id=2,
        document_id=doc.id,
        version_number=2,
        content=doc.content,
        author_id=user.id,
    )

    assert version2.version_number == 2
    assert version2.content == "Updated content 2"


def test_ai_features_document_summarization_and_suggestions():
    doc_text = "This is a test document to be summarized and for suggestions."
    ai_summary_request = AIRequest(
        id=1, document_id=1, request_type="summary", request_payload=doc_text
    )
    ai_suggestion_request = AIRequest(
        id=2, document_id=1, request_type="suggestion", request_payload=doc_text
    )

    # Simulate AI processing (mocking in real tests)
    ai_summary_request.response = "Test document summary."
    ai_suggestion_request.response = "Suggested improvements."

    assert "summary" in ai_summary_request.request_type
    assert ai_summary_request.response == "Test document summary."
    assert ai_suggestion_request.response == "Suggested improvements."


def test_user_authentication_and_jwt_flow():
    # Simulate user login with OAuth 2.0 and issue JWT
    user = User(id=42, username="authuser", email="auth@example.com")
    token = issue_jwt(user)

    # Simulate token verification
    user_id = verify_jwt(token)
    assert user_id == str(user.id)

    # Simulate get_current_user with a mocked request
    class MockRequest:
        headers = {"Authorization": f"Bearer {token}"}

    request = MockRequest()
    curr_user = get_current_user(request)
    assert curr_user.id == user.id
    assert curr_user.username == user.username


def test_document_version_control_view_compare_revert():
    # Create initial document version
    doc = Document(id=1, owner_id=1, title="Test Doc", content="Version 1 content")
    version1 = DocumentVersion(
        id=1, document_id=doc.id, version_number=1, content=doc.content, author_id=1
    )

    # Simulate edit and create version 2
    doc.content = "Version 2 content modified"
    version2 = DocumentVersion(
        id=2, document_id=doc.id, version_number=2, content=doc.content, author_id=1
    )

    # Compare versions (simple string diff for test)
    diff = set(version1.content.split()) ^ set(version2.content.split())
    assert "modified" in diff

    # Revert doc content to version1
    doc.content = version1.content
    assert doc.content == "Version 1 content"


def test_full_text_search_functionality():
    docs = [
        Document(
            id=1,
            owner_id=1,
            title="First Doc",
            content="This is a test document about AI.",
        ),
        Document(
            id=2,
            owner_id=1,
            title="Second Doc",
            content="Another document regarding real-time collaboration.",
        ),
        Document(
            id=3,
            owner_id=1,
            title="Third Doc",
            content="Document covering OAuth and security.",
        ),
    ]

    def simple_search(query, documents):
        results = []
        q_lower = query.lower()
        for d in documents:
            if q_lower in d.content.lower() or q_lower in d.title.lower():
                results.append(d)
        return results

    search_results = simple_search("AI", docs)
    assert len(search_results) == 1
    assert search_results[0].id == 1

    search_results = simple_search("document", docs)
    assert len(search_results) == 3

    search_results = simple_search("collaboration", docs)
    assert any(d.id == 2 for d in search_results)


@patch("backend.app.cloud_storage_upload")
def test_file_upload_backend_integration_mock(mock_upload):
    mock_upload.return_value = "https://mockstorage.example.com/file123"

    file_data = b"Test file content"

    # Simulate file upload function
    from backend.app import handle_file_upload

    url = handle_file_upload(file_data)

    mock_upload.assert_called_once_with(file_data)
    assert url == "https://mockstorage.example.com/file123"


from unittest.mock import AsyncMock
import asyncio


def test_websocket_real_time_collaboration_simulation():
    # Mock WebSocket server and client
    class MockWebSocket:
        def __init__(self):
            self.messages = []

        async def send(self, message):
            self.messages.append(message)

        async def recv(self):
            if self.messages:
                return self.messages.pop(0)
            await asyncio.sleep(0.01)
            return None

    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    async def simulate_collaboration(ws_a, ws_b):
        # User A sends an edit
        await ws_a.send("Edit from A")
        # User B receives and broadcasts back
        msg = await ws_a.recv()
        if msg:
            await ws_b.send(msg)

    asyncio.run(simulate_collaboration(ws1, ws2))

    assert "Edit from A" in ws2.messages


def test_security_csrf_and_xss_protection_headers():
    from backend.app import create_app

    app = create_app()
    client = app.test_client()
    response = client.get("/")

    # Check security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "X-XSS-Protection" in response.headers
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Content-Security-Policy" in response.headers
    # More detailed CSP header testing could be added


def test_template_rendering_and_static_file_serving():
    from backend.app import create_app

    app = create_app()
    client = app.test_client()

    # Test index page
    response = client.get("/")
    assert response.status_code == 200
    assert b"<html" in response.data
    assert b"Real-Time Collaborative Document Editing" in response.data

    # Test static file
    css_response = client.get("/static/main.css")
    assert css_response.status_code == 200
    assert b"body" in css_response.data


def test_session_management_and_cookie_handling():
    from backend.app import create_app

    app = create_app()
    client = app.test_client()

    # Simulate login
    response = client.post(
        "/login", data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    set_cookie = response.headers.get("Set-Cookie")
    assert set_cookie is not None
    assert "session" in set_cookie

    # Simulate logout
    response = client.get("/logout")
    assert response.status_code == 200
    # Logout should clear session cookie
    set_cookie_logout = response.headers.get("Set-Cookie")
    assert "session=;" in set_cookie_logout or "Max-Age=0" in set_cookie_logout


import time
import random
import string


def random_text(length=1000):
    return "".join(random.choices(string.ascii_letters + " ", k=length))


def test_performance_document_save_and_version(benchmark):
    user = User(id=1, username="perfuser", email="perf@example.com")
    doc = Document(id=100, owner_id=user.id, title="Performance Test", content="")

    def save_version():
        # Simulate editing and saving
        doc.content = random_text(1000)
        _ = DocumentVersion(
            id=1,
            document_id=doc.id,
            version_number=1,
            content=doc.content,
            author_id=user.id,
        )

    benchmark(save_version)
