from app.db.session import get_session


def test_get_session_context_manager_provides_session():
    with get_session() as session:
        result = session.execute("SELECT 1")
        assert result.scalar() == 1
