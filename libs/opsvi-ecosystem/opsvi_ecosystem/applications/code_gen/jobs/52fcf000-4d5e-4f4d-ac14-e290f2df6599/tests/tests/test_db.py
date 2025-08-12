from unittest.mock import MagicMock

import pytest
from app.db import get_db


def test_get_db_returns_session_and_closes(monkeypatch):
    """Ensure get_db yields a session object and closes the session after use."""
    session_mock = MagicMock()

    def session_factory():
        yield session_mock

    monkeypatch.setattr("app.db.SessionLocal", session_factory)

    db_gen = get_db()
    session = next(db_gen)
    assert session == session_mock
    # Close should not be called yet
    assert not session_mock.close.called
    # Close after generator exits
    with pytest.raises(StopIteration):
        next(db_gen)
    # Close should have been called once
    assert session_mock.close.call_count == 1
