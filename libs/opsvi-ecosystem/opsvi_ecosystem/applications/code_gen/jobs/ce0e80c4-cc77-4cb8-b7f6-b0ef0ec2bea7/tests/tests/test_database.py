import pytest
import os
from app.database import init_db, get_db
from sqlalchemy import text


@pytest.fixture(scope="module")
def setup_database():
    # Initialize the database
    init_db()
    yield
    # Cleanup
    if os.path.exists("test.db"):
        os.remove("test.db")


def test_init_db_creates_database_tables(setup_database):
    # After init_db, the tables should exist
    db = next(get_db())
    result = db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table';")
    ).fetchall()
    table_names = [row[0] for row in result]
    assert "todos" in table_names or "todo" in table_names


def test_get_db_yields_session():
    db_gen = get_db()
    db_session = next(db_gen)
    assert db_session is not None
    with pytest.raises(StopIteration):
        next(db_gen)
    # No exceptions when closing generator
