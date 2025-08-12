import pytest
from app import collab
from app.models import User


class MockWebSocket:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def accept(self):
        return None

    async def send_json(self, msg):
        self.sent.append(msg)

    async def receive_json(self):
        return {"type": "edit", "body": "new_text"}

    async def close(self):
        self.closed = True


def gen_user():
    return User(
        id="u1",
        username="alice",
        email="a@a.com",
        full_name="Alice",
        disabled=False,
        created_at=None,
    )


@pytest.mark.asyncio
async def test_join_and_edit():
    ws = MockWebSocket()
    user = gen_user()
    doc_id = "testdocid"
    await collab.join_collab_room(doc_id, ws, user)
    assert ws.closed is True
    # After simulated edit, new text should be in _DOC_STATE
    assert collab._DOC_STATE[doc_id] == "new_text"
