import pytest


@pytest.fixture
def db():
    class DummyDB:
        def __getattr__(self, name):
            def dummy(*args, **kwargs):
                return None

            return dummy

    return DummyDB()


@pytest.fixture
def test_collection():
    return "dummy_collection"
