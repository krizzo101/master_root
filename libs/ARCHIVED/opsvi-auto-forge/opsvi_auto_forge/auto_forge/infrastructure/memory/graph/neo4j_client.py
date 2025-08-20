"""Neo4j client utilities for backward compatibility."""

from neo4j import Driver

from .driver import close_driver, init_driver


def get_neo4j_driver() -> Driver:
    """
    Get Neo4j driver instance.

    Returns:
        Neo4j driver instance
    """
    return init_driver()


def close_neo4j_driver() -> None:
    """Close Neo4j driver."""
    close_driver()
