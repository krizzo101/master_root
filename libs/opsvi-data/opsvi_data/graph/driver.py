from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from neo4j import Driver, GraphDatabase, Session


class Neo4jConfig:
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.getenv("NEO4J_USER", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "password")
    database: str | None = os.getenv("NEO4J_DATABASE", None)


_driver: Driver | None = None


def init_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            Neo4jConfig.uri,
            auth=(Neo4jConfig.user, Neo4jConfig.password),
            max_connection_lifetime=3600,
        )
    return _driver


@contextmanager
def get_session() -> Generator[Session, None, None]:
    driver = init_driver()
    if Neo4jConfig.database:
        session = driver.session(database=Neo4jConfig.database)
    else:
        session = driver.session()
    try:
        yield session
    finally:
        session.close()


def close_driver() -> None:
    global _driver
    if _driver:
        _driver.close()
        _driver = None
