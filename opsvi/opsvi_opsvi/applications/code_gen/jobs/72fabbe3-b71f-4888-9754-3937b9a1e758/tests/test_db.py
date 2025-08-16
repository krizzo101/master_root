import pytest
from backend.db import get_session


def test_get_session_yields_session():
    session_generator = get_session()
    session = next(session_generator)
    assert session is not None
    # Close generator
    try:
        next(session_generator)
    except StopIteration:
        pass
