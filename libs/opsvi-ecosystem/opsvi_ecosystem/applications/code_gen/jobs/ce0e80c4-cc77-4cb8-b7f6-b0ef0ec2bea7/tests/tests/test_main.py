import asyncio

import pytest
from app.main import LoggingMiddleware
from starlette.requests import Request
from starlette.responses import Response


@pytest.fixture
def dummy_call_next():
    async def call_next(request):
        return Response(content="OK", status_code=200)

    return call_next


def test_loggingmiddleware_calls_next_and_logs(capsys, dummy_call_next):
    middleware = LoggingMiddleware(dummy_call_next)

    class DummyRequest(Request):
        def __init__(self):
            self.scope = {"type": "http", "path": "/test"}

    request = DummyRequest()
    response = asyncio.run(middleware(request))
    assert response.status_code == 200
    captured = capsys.readouterr()
    assert "HTTP request received:" in captured.out
