from __future__ import annotations

from opsvi_auto_forge.infrastructure.memory.graph.driver import get_session


def get_neo4j():
    # FastAPI will call this per-request; yields a session via context manager
    # Example usage:
    #   @router.get(...)
    #   def endpoint(session=Depends(get_neo4j)):
    #       res = session.run(...)
    with get_session() as session:
        yield session
