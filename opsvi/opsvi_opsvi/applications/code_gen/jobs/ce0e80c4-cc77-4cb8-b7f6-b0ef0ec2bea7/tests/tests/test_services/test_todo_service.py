import pytest
from app.services.todo_service import TodoService
from app.models import Todo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import init_db, get_db
fastapi.testclient import TestClient

@pytest.fixture(scope='module')
def test_db_session():
    # Setup in-memory SQLite database and session
    engine = create_engine('sqlite:///:memory:')
    init_db()
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_todoservice_create_and_get(test_db_session):
    service = TodoService(test_db_session)
    todo_in = {'title': 'Test Todo', 'description': 'Test Desc', 'completed': False}
    todo_created = service.create_todo(todo_in)
    assert todo_created.title == 'Test Todo'
    assert todo_created.id is not None

    todo_fetched = service.get_todo_by_id(todo_created.id)
    assert todo_fetched.id == todo_created.id
    assert todo_fetched.title == 'Test Todo'

def test_todoservice_get_all_todos_empty_and_nonempty(test_db_session):
    service = TodoService(test_db_session)
    all_empty = service.get_all_todos()
    assert isinstance(all_empty, list)
    # Insert one todo
    todo_in = {'title': 'Another Todo'}
    service.create_todo(todo_in)
    all_after_insert = service.get_all_todos()
    assert len(all_after_insert) >= 1

def test_todoservice_update_todo_existing_and_nonexistent(test_db_session):
    service = TodoService(test_db_session)
    todo_in = {'title': 'Update Test'}
    created = service.create_todo(todo_in)
    update_data = {'title': 'Updated Title', 'completed': True}
    updated = service.update_todo(created.id, update_data)
    assert updated.title == 'Updated Title'
    assert updated.completed is True

    result_none = service.update_todo(99999, update_data)
    assert result_none is None

def test_todoservice_delete_todo_existing_and_nonexistent(test_db_session):
    service = TodoService(test_db_session)
    todo_in = {'title': 'Delete Me'}
    created = service.create_todo(todo_in)
    result = service.delete_todo(created.id)
    assert result is True
    # Try to get deleted
    assert service.get_todo_by_id(created.id) is None

    result_nonexistent = service.delete_todo(99999)
    assert result_nonexistent is False
