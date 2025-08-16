import pytest
from ai_collab_task_manager.app import create_app as create_ai_app
from ai_collab_task_manager.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def app(db_session):
    app = create_ai_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )
    yield app


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    return app.test_cli_runner()
