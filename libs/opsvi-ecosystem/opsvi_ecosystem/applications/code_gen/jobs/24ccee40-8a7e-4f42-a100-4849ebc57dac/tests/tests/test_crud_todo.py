import pytest
from app.crud.todo import TodoDAL
from app.db.session import get_session


@pytest.fixture(scope="module")
def db_session():
    with get_session() as session:
        yield session


def test_tododal_crud_operations(db_session):
    dal = TodoDAL(db_session)

    # Create
    todo = dal.create(description="test todo from crud", completed=False)
    assert todo.id is not None
    assert todo.description == "test todo from crud"
    assert todo.completed is False

    # Read
    got = dal.get(todo.id)
    assert got.id == todo.id

    # Update
    updated = dal.update(todo.id, description="updated desc", completed=True)
    assert updated.description == "updated desc"
    assert updated.completed is True

    # Delete
    deleted = dal.delete(todo.id)
    assert deleted is True

    # Confirm delete
    got_after_delete = dal.get(todo.id)
    assert got_after_delete is None
