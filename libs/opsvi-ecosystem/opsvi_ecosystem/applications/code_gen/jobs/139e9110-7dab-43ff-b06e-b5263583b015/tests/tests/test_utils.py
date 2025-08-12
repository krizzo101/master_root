import pytest
from backend.utils import rate_limit_middleware, paginate

import asyncio
from starlette.requests import Request
from starlette.responses import Response


@pytest.fixture
def call_next_mock():
    async def call_next(request):
        return Response("OK")

    return call_next


@pytest.mark.asyncio
async def test_rate_limit_middleware_allows_request_and_calls_next_async(
    call_next_mock,
):
    request = Request({"type": "http"})
    response = await rate_limit_middleware(request, call_next_mock)
    assert response.status_code == 200
    assert response.body == b"OK"


def test_paginate_returns_correct_page_and_length():
    items = list(range(1, 101))
    page = 2
    per_page = 10
    page_items = paginate(items, page, per_page)
    assert len(page_items) == per_page
    assert page_items[0] == 11
    assert page_items[-1] == 20

    # Test boundary page
    last_page_items = paginate(items, 11, per_page)
    assert last_page_items == []
