from app.models import Todo
from app.schemas import (
    Config,
    HealthCheckResponse,
    TodoBase,
    TodoCreate,
    TodoUpdate,
)
from app.schemas import (
    Todo as TodoSchema,
)


def test_todo_model_creates_with_default_values():
    todo = Todo(title="Test ORM", description="Testing ORM model")
    assert todo.title == "Test ORM"
    assert todo.description == "Testing ORM"
    assert todo.completed is False
    assert todo.id is None or isinstance(todo.id, int)


def test_todo_base_schema_validation_and_assignment():
    todo_base = TodoBase(title="Base Title", description="Base Description")
    assert todo_base.title == "Base Title"
    assert todo_base.description == "Base Description"


def test_todo_create_schema_accepts_required_fields():
    todo_create = TodoCreate(title="New Task", description="New Desc")
    assert todo_create.title == "New Task"
    assert todo_create.description == "New Desc"


def test_todo_update_schema_allows_optional_fields():
    todo_update_partial = TodoUpdate(description="Only Description")
    assert todo_update_partial.description == "Only Description"
    assert todo_update_partial.title is None

    todo_update_full = TodoUpdate(title="Title", description="Desc")
    assert todo_update_full.title == "Title"
    assert todo_update_full.description == "Desc"


def test_todo_schema_maps_to_dict_properly():
    todo_schema = TodoSchema(
        id=1, title="Schema Title", description="Schema Desc", completed=True
    )
    todo_dict = todo_schema.dict()
    assert todo_dict["id"] == 1
    assert todo_dict["title"] == "Schema Title"
    assert todo_dict["description"] == "Schema Desc"
    assert todo_dict["completed"] is True


def test_health_check_response_schema_contains_status_and_uptime():
    health = HealthCheckResponse(status="ok", uptime=123.4)
    assert health.status == "ok"
    assert health.uptime == 123.4


def test_config_schema_allows_configuration_parameters():
    config = Config(db_url="sqlite:///test.db", debug_mode=True)
    assert hasattr(config, "db_url")
    assert config.db_url == "sqlite:///test.db"
    assert config.debug_mode is True
